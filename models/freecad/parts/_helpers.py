"""
Helpers shared by all part builders.

These are imported by each part file. Keep this dependency-free (no
FreeCAD imports here) so we can also unit-test the geometry math.
"""
import math


def centered_x(L, cx=0.0):
    """Return (xmin, xmax) for a box of length L centered at cx on X."""
    return (cx - L / 2.0, cx + L / 2.0)


def add_feature(doc, name, shape):
    """Add a shape to `doc` as a Part::Feature, return the new object."""
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    return obj


def box(L, W, H, x=0.0, y=0.0, z=0.0):
    """Return a Part.Shape box of (L, W, H) with one corner at (x, y, z).

    L runs along X, W along Y, H along Z. (Y is up; Z is south.)
    """
    import Part
    import FreeCAD as App
    shape = Part.makeBox(L, W, H)
    shape.translate(App.Vector(x, y, z))
    return shape


def cylinder(r, h, x=0.0, y=0.0, z=0.0, axis="Y"):
    """Return a vertical (default Y-axis) cylinder of radius r, height h,
    with its base at (x, y, z).
    """
    import Part
    import FreeCAD as App
    if axis == "Y":
        c = Part.makeCylinder(r, h, App.Vector(x, y, z), App.Vector(0, 1, 0))
    elif axis == "X":
        c = Part.makeCylinder(r, h, App.Vector(x, y, z), App.Vector(1, 0, 0))
    elif axis == "Z":
        c = Part.makeCylinder(r, h, App.Vector(x, y, z), App.Vector(0, 0, 1))
    else:
        raise ValueError(f"axis must be X, Y, or Z, got {axis}")
    return c


def rotate(shape, axis_point, axis_dir, angle_deg):
    """Rotate a shape around an arbitrary axis. axis_dir is a unit vector."""
    import FreeCAD as App
    p = App.Vector(*axis_point)
    d = App.Vector(*axis_dir)
    return shape.rotate(p, d, angle_deg)


# ---- geometry calculations ---------------------------------------------------

def half_lap_notch(thickness_in, depth_in, height_in):
    """Return a box for a half-lap notch in the END of a board.

    Used to cut the corner joints on the bed walls. The notch is `depth_in`
    long × `height_in` tall × `thickness_in/2` deep, positioned so that the
    OUTER half of the board is removed at the joint end.

    For a 2x12 wall (1.5 × 11.25), call:
        notch = half_lap_notch(1.5, 3.0, 11.25)   # 3" wide, full height, 0.75" deep
    Then `wall_shape.cut(notch_placed_at_east_end)`.
    """
    import FreeCAD as App
    # box at origin, with x in [0, depth], y in [0, height], z in [0, thickness/2]
    return box(depth_in, height_in, thickness_in / 2.0)


# ---- nominal lumber → actual dimensions --------------------------------------

def actual_cross_section(nominal):
    """Return (thickness, height) of dressed lumber for a nominal size.

    E.g. '2x6' → (1.5, 5.5). See models/freecad/materials.py.
    """
    from models.freecad.materials import LUMBER
    return (LUMBER[nominal]["actual_t"], LUMBER[nominal]["actual_h"])
