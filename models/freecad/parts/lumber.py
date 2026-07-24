"""
Lumber library — a thin wrapper over FreeCAD primitives that reads like
a lumber yard.

The hard work is in `_helpers.py` and `materials.py`. This module
just gives you a clean API: "give me a 2x6 at 42 inches" instead of
"give me a box of 1.5 × 5.5 × 42 at origin".

Usage:

    from models.freecad.parts.lumber import (
        make_lumber, make_half_lap_notch, make_end_notch,
        LUMBER_CATALOG, list_lumber, board_mass_lb,
    )

    # Place a 2x6 stud, 42" long, along the X axis at origin
    stud = make_lumber("2x6", length=42)

    # Place a 2x4 at (10, 0, 0), running along Z (so length is in Z)
    brace = make_lumber("2x4", length=21, axis="Z", origin=(10, 0, 0))

    # Cut a half-lap notch at the end of the stud (3" wide, 0.75" deep)
    notch = make_half_lap_notch(thickness=1.5, length=3.0, height=5.5)
    stud_with_notch = stud.cut(notch.translate(App.Vector(0, 0, 0)))

    # Or: use the end-notch helper, sized for the board automatically
    end_cut = make_end_notch("2x6", length=3.0, end="+X")
    stud_with_notch = stud.cut(end_cut.translate(...))

The catalog and dimensions are imported from `materials.py` so there's
no duplication. Every size in LUMBER_CATALOG is a real dressed-lumber
size (PT DF, S4S) — no fractional-inch stock lengths, by design rule.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.freecad.materials import LUMBER, LUMBER_WEIGHT_LB_PER_FT

# Lazy FreeCAD imports so the file can be imported for non-CAD use
# (e.g., by wattplot.py or a build calculator).
_FreeCAD_imports = None


def _fc():
    """Lazy-import FreeCAD + Part. Cached after first call."""
    global _FreeCAD_imports
    if _FreeCAD_imports is None:
        import FreeCAD as App  # noqa: F401
        import Part
        _FreeCAD_imports = (App, Part)
    return _FreeCAD_imports


# =============================================================================
# Catalog access
# =============================================================================

LUMBER_CATALOG = list(LUMBER.keys())  # canonical list of nominal sizes


def list_lumber():
    """Print all available lumber sizes (thickness × height, in inches)."""
    print(f"{'Nominal':<8} {'Actual T':<10} {'Actual H':<10} {'lb/ft (PT DF)':<14}")
    print("-" * 44)
    for n in LUMBER_CATALOG:
        t = LUMBER[n]["actual_t"]
        h = LUMBER[n]["actual_h"]
        w = LUMBER_WEIGHT_LB_PER_FT.get(n, "?")
        print(f"{n:<8} {t:<10.2f} {h:<10.2f} {w:<14}")


def actual_dims(nominal):
    """Return (thickness, height) in inches for a nominal lumber size.

    Raises ValueError if the size isn't in the catalog.
    """
    if nominal not in LUMBER:
        raise ValueError(
            f"Unknown lumber size: {nominal!r}. Known: {LUMBER_CATALOG}"
        )
    return (LUMBER[nominal]["actual_t"], LUMBER[nominal]["actual_h"])


def board_mass_lb(nominal, length_in, density_factor=1.0):
    """Return the mass in pounds of a board of given nominal size and length.

    Uses the LUMBER_WEIGHT_LB_PER_FT table for PT Douglas Fir (~35 pcf).
    density_factor adjusts for kiln-dried (0.85) or green (1.1) lumber.
    """
    if nominal not in LUMBER_WEIGHT_LB_PER_FT:
        raise ValueError(f"Unknown lumber size: {nominal!r}")
    return LUMBER_WEIGHT_LB_PER_FT[nominal] * (length_in / 12.0) * density_factor


# =============================================================================
# Primitive creation
# =============================================================================


def make_lumber(nominal, length, axis="X", origin=(0, 0, 0)):
    """Create a FreeCAD Part.Shape for a board of `nominal` size, `length` long.

    Args:
        nominal: lumber nominal size string ("2x4", "2x6", "1x2", etc.)
        length: length in inches (must be > 0)
        axis: which axis the board runs along ("X", "Y", or "Z")
        origin: (x, y, z) tuple for the corner of the board closest to origin.

    Returns:
        Part.Shape. The board's cross-section is centered on the axis line.
        For example, `make_lumber("2x4", length=42, axis="X", origin=(0, 0, 0))`
        produces a box of (42, 3.5, 1.5) with the bottom corner at (0, 0, 0).
        The (thickness, height) plane is (Y, Z) when axis="X".

    Raises:
        ValueError: if nominal size is unknown or length <= 0.
    """
    if length <= 0:
        raise ValueError(f"length must be > 0, got {length}")
    t, h = actual_dims(nominal)

    App, Part = _fc()
    ox, oy, oz = origin

    if axis == "X":
        # Length along X, height (vertical) along Y, thickness along Z.
        # For a 2x12 wall lying flat: 96" long (X), 11.25" tall (Y), 1.5" thick (Z).
        shape = Part.makeBox(length, h, t)
        shape.translate(App.Vector(ox, oy, oz))
    elif axis == "Y":
        # Vertical post: length along Y, square cross-section (t x t) in X/Z.
        shape = Part.makeBox(t, length, t)
        shape.translate(App.Vector(ox, oy, oz))
    elif axis == "Z":
        # Length along Z, height (vertical) along Y, thickness along X.
        # For a short wall running perpendicular to the bed length.
        shape = Part.makeBox(t, h, length)
        shape.translate(App.Vector(ox, oy, oz))
    else:
        raise ValueError(f"axis must be X, Y, or Z, got {axis!r}")

    return shape


# =============================================================================
# Common cuts (as separate shapes, ready to .cut() from a board)
# =============================================================================


def make_half_lap_notch(thickness, length, height, axis="X"):
    """Create a half-lap notch shape (to be subtracted from a board end).

    A half-lap notch removes the outer half of a board at a joint so two
    boards can overlap flush. The notch is `length` long along the board,
    `height` tall, and `thickness/2` deep.

    The notch orientation depends on the board's axis:
      - axis="X" (default): notch extends along +X, depth in Z
      - axis="Y": notch extends along +Y (vertical board), depth in X
      - axis="Z": notch extends along +Z, depth in X

    For a 2x12 wall (1.5 × 11.25), call:
        notch = make_half_lap_notch(1.5, length=3.0, height=11.25, axis="X")
    Then place it at the end of the wall and subtract.

    Args:
        thickness: full thickness of the board (inches)
        length: notch length along the board's long axis (inches)
        height: full height of the board (inches)
        axis: which axis the board runs along ("X", "Y", or "Z")
    """
    App, Part = _fc()
    if axis == "X":
        # length along X, height along Y, depth in Z
        return Part.makeBox(length, height, thickness / 2.0)
    elif axis == "Y":
        # depth in X, length along Y, height along Z
        return Part.makeBox(thickness / 2.0, length, height)
    elif axis == "Z":
        # depth in X, height along Y, length along Z
        return Part.makeBox(thickness / 2.0, height, length)
    else:
        raise ValueError(f"axis must be X, Y, or Z, got {axis!r}")


def make_end_notch(nominal, length, axis="X", height=None):
    """Create a half-lap notch sized for a specific lumber nominal size.

    Convenience wrapper around `make_half_lap_notch` that uses the catalog
    dimensions. The notch is positioned at the end of a board running
    along the given axis.

    Args:
        nominal: lumber size ("2x4", "2x6", etc.)
        length: notch length along the board's axis (inches)
        axis: which axis the board runs along ("X", "Y", or "Z")
        height: override height (default = full board height)
    """
    t, h = actual_dims(nominal)
    return make_half_lap_notch(t, length,
                              h if height is None else height,
                              axis=axis)


def make_dado(thickness, length, depth, height):
    """Create a dado (slot) shape for cutting across the middle of a board.

    Args:
        thickness: full thickness of the board (inches)
        length: length of the dado across the board (inches)
        depth: depth of the dado into the board (inches)
        height: full height of the board (inches)

    Returns:
        Part.Shape. A box at origin sized (length, depth, height) — caller
        positions it inside the board and subtracts.
    """
    App, Part = _fc()
    return Part.makeBox(length, depth, height)


def make_drilled_hole(diameter, axis="Y", depth=None, through=False):
    """Create a cylinder shape for a hole (to be cut from a board).

    Args:
        diameter: hole diameter in inches
        axis: axis the hole runs along ("X", "Y", or "Z")
        depth: depth of the hole (inches). If through=True, depth is
               ignored and the hole is sized to be very long.
        through: if True, the cylinder is long enough to punch through
                 any reasonable board (use for bolt holes).
    """
    App, Part = _fc()
    r = diameter / 2.0
    if through:
        # Long enough to punch through a 2x12 (12") + margin
        length = 24.0
    else:
        if depth is None:
            raise ValueError("Either `depth` or `through=True` is required")
        length = depth
    return Part.makeCylinder(r, length, App.Vector(0, 0, 0),
                            App.Vector(1 if axis == "X" else 0,
                                       1 if axis == "Y" else 0,
                                       1 if axis == "Z" else 0))


# =============================================================================
# Convenience: full cut + translate in one call
# =============================================================================


def cut_end_notch(board, nominal, length, end_offset, end_axis="X"):
    """Cut a half-lap notch at one end of a board, return the new shape.

    Args:
        board: a Part.Shape to cut from
        nominal: lumber size of the board (for notch sizing)
        length: notch length along the board (inches)
        end_offset: position of the notch from origin (inches along the
                    board's axis). For a board running along X with the
                    notch at the +X end, end_offset = (board_length - length).
        end_axis: which axis the board runs along ("X", "Y", or "Z")
    """
    App, Part = _fc()
    notch = make_end_notch(nominal, length)

    if end_axis == "X":
        notch.translate(App.Vector(end_offset, 0, 0))
    elif end_axis == "Y":
        notch.translate(App.Vector(0, end_offset, 0))
    elif end_axis == "Z":
        notch.translate(App.Vector(0, 0, end_offset))
    else:
        raise ValueError(f"end_axis must be X, Y, or Z, got {end_axis!r}")

    return board.cut(notch)


def cut_half_lap(board, nominal, length, position, axis="X"):
    """Cut a half-lap notch at an absolute 3D position on a board.

    Unlike `cut_end_notch` (which assumes a board at origin), this takes
    the absolute position of the notch's near corner in (x, y, z) world
    coordinates. Use this when the board is offset from origin (which
    is most real assemblies).

    Args:
        board: a Part.Shape to cut from
        nominal: lumber size of the board (for notch sizing)
        length: notch length along the board (inches)
        position: (x, y, z) absolute world coordinates of the notch's
                  near corner (the corner closest to origin)
        axis: which axis the board runs along (so the notch is oriented
              correctly for the board's geometry)
    """
    App, Part = _fc()
    notch = make_end_notch(nominal, length, axis=axis)
    notch.translate(App.Vector(*position))
    return board.cut(notch)


# =============================================================================
# Hardware: a few common off-the-shelf items, parametric from the catalog
# =============================================================================


def make_bolt(diameter, length, head_diameter=None, head_height=None):
    """Make a parametric hex bolt (simplified, no thread detail).

    Useful for showing bolt placement in the model. Not for fabrication.
    For real bolt models, use vendor STEP files (see HARDWARE_PATHS).
    """
    App, Part = _fc()
    head_d = head_diameter or diameter * 1.7  # standard hex head
    head_h = head_height or diameter * 0.625
    # Hex head as a cylinder (simplified — real hex would use a prism)
    head = Part.makeCylinder(head_d / 2.0, head_h, App.Vector(0, 0, 0),
                             App.Vector(0, 1, 0))
    shaft = Part.makeCylinder(diameter / 2.0, length, App.Vector(0, head_h, 0),
                              App.Vector(0, 1, 0))
    return head.fuse(shaft)


def make_panel_rect(L, W, thickness, origin=(0, 0, 0)):
    """Make a flat rectangular panel (like a solar panel).

    Args:
        L: length in inches (along X)
        W: width in inches (along Z)
        thickness: panel thickness in inches (along Y)
        origin: (x, y, z) corner of the panel
    """
    App, Part = _fc()
    shape = Part.makeBox(L, thickness, W)
    shape.translate(App.Vector(*origin))
    return shape


# =============================================================================
# Where to put vendor STEP files for hardware
# =============================================================================
# If you download STEP files for the actual hardware (hinges, panel clamps,
# actuators), put them in this directory and reference by name below.
# FreeCAD can import STEP and use it as a Part::Feature.
#
# Suggested naming:
#   vendor/butt_hinge_4x4.step       - 4×4 butt hinge, 1/2" pin
#   vendor/mid_clamp_ironridge.step  - IronRidge / Unirac mid clamp
#   vendor/actuator_eco_worthy.step  - ECO-WORTHY linear actuator
#   vendor/panel_longi_620W.step     - LONGi Hi-MO X10 panel (if you can find one)
#
# Then in your part file:
#   Part.importStep("models/freecad/parts/vendor/butt_hinge_4x4.step")
VENDOR_DIR = os.path.join(HERE, "vendor")


def load_vendor_part(filename):
    """Import a STEP file from the vendor directory. Returns the Part.Shape.

    Raises FileNotFoundError with a helpful message if the file is missing.
    """
    import Part
    path = os.path.join(VENDOR_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Vendor part not found: {path}\n"
            f"Download a STEP file and place it in {VENDOR_DIR}"
        )
    shape = Part.Shape()
    shape.read(path)
    return shape


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    # Run as: `freecadcmd -c "exec(open('lumber.py').read())"`
    # or from another script. Useful for sanity-checking the catalog.
    list_lumber()
    print()
    print("Sample weights (PT DF, 35 pcf):")
    for nom in ("2x4", "2x6", "2x12"):
        m = board_mass_lb(nom, length_in=96)
        print(f"  {nom} × 8 ft: {m:.2f} lb")
