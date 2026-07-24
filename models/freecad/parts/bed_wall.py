"""
Bed walls — 1x6 cedar skin over vertical 2x4 cleats, 2x6 caps.

Construction (see BED_WALL in wattplot_params.py):
  - Skin: 4 courses of 1x6 cedar (5.5" actual) = 22" wall. Non-structural.
  - Cleats: vertical 2x4s (<= 24" o.c.) carry the lateral soil pressure.
    5 per long wall, 3 per short wall. Corners join cleat-to-cleat.
  - Caps: a 2x6 laid flat on the south (hinge) and north (strut) walls.
    Hinge and strut-shoe screws bite into the cap, never the 3/4" skin.

All square cuts — no notches, no miters (the old 2x12 half-lap corner
design is retired with the wheelchair-accessible height pivot).

Coordinates: X = bed length, Y = up, Z = bed width (south positive).
Walls sit on the skids (base at SKID_H).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED, BED_WALL
from models.freecad.parts.lumber import make_lumber, actual_dims
from models.freecad.parts._helpers import add_feature
from models.freecad.materials import LUMBER

import FreeCAD as App
import Part


# Dimensions from params
SKIN_NOM = BED_WALL["skin_nominal"]                 # "1x6"
SKIN_T, COURSE_H = actual_dims(SKIN_NOM)            # 0.75, 5.5
COURSES = BED_WALL["courses"]                       # 4
WALL_H = COURSES * COURSE_H                         # 22.0
CLEAT_T, CLEAT_W = actual_dims(BED_WALL["cleat_nominal"])   # 1.5, 3.5
HEADER_T, HEADER_W = actual_dims(BED_WALL["header_nominal"]) # 1.5, 3.5 (2x4 on wide face)

BED_L = BED["outer_L_in"]          # 96
BED_W = BED["outer_W_in"]          # 44.6
SKID_H = BED["skid_h_in"]          # 3.0 (wall sits on top of skids)

# Corner posts (4x4 PT, 3.5" actual). The walls fit BETWEEN the posts,
# so the wall length is the bed outer dimension minus 2x the post thickness.
# This makes the short walls flush with the bed outer face (no 0.75" recess
# from the long-wall end) and gives the panel a solid 4x4 post at each
# outside corner to rest on.
POST_T = LUMBER["4x4"]["actual_t"]  # 3.5
LONG_WALL_L = BED_L - 2.0 * POST_T   # 89" for LONGi (96 - 2*3.5)
SHORT_WALL_L = BED_W - 2.0 * POST_T  # 37.6" for LONGi (44.6 - 2*3.5)


def _cleat_positions(wall_len, n):
    """Evenly space n cleats along a wall: one at each end, rest between.

    Returns the coordinates of each cleat's near edge (cleat is CLEAT_W
    wide along the wall).
    """
    if n < 2:
        return [wall_len / 2.0 - CLEAT_W / 2.0]
    step = (wall_len - CLEAT_W) / (n - 1)
    return [i * step for i in range(n)]


def make_bed_long_wall(doc, side="north", name=None):
    """Long wall (96" along X) on the north or south edge.

    Skin courses + 5 vertical cleats + a 2x4 header on top (the
    header is 2x4 cedar laid on its wide face, 1.5" tall × 3.5" wide,
    centered on the wall, spanning between the corner posts).
    """
    if name is None:
        name = f"BedLongWall_{side}"
    if side not in ("north", "south"):
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    z_outer = -BED_W / 2.0 if side == "north" else +BED_W / 2.0
    # Skin box corner (z_min face of the skin board)
    z_skin = z_outer if side == "north" else z_outer - SKIN_T
    # Cleats sit against the skin's inner face, extending into the bed
    z_cleat = (z_outer + SKIN_T) if side == "north" else (z_outer - SKIN_T - CLEAT_T)

    shapes = []

    # Skin: COURSES stacked 1x6 boards, spanning between the corner posts
    for i in range(COURSES):
        y = SKID_H + i * COURSE_H
        shapes.append(make_lumber(SKIN_NOM, length=LONG_WALL_L, axis="X",
                                  origin=(-LONG_WALL_L / 2.0, y, z_skin)))

    # Cleats: vertical 2x4s, CLEAT_W along X, CLEAT_T into the bed (Z)
    for x_edge in _cleat_positions(LONG_WALL_L, BED_WALL["cleats_long_wall"]):
        cleat = Part.makeBox(CLEAT_W, WALL_H, CLEAT_T)
        cleat.translate(App.Vector(-LONG_WALL_L / 2.0 + x_edge, SKID_H, z_cleat))
        shapes.append(cleat)

    # Header: 2x4 cedar on its wide face, flush with the wall's
    # outer face (NO external overhang), extending 3.5" inward
    # (toward the bed center). The first 0.75" sits directly above
    # the 0.75"-thick wall; the remaining 2.75" extends past the
    # wall's inner face into the bed.
    z_header = z_outer if z_outer < 0 else z_outer - HEADER_W
    header = Part.makeBox(LONG_WALL_L, HEADER_T, HEADER_W)
    header.translate(App.Vector(-LONG_WALL_L / 2.0, SKID_H + WALL_H, z_header))
    shapes.append(header)

    wall = shapes[0].multiFuse(shapes[1:])
    return add_feature(doc, name, wall)


def make_bed_short_wall(doc, side="west", name=None):
    """Short wall (along Z) on the west or east end of the bed.

    Skin courses + 3 vertical cleats + a 2x4 header on top (the
    header is 2x4 cedar laid on its wide face, 1.5" tall × 3.5" wide,
    centered on the wall, spanning between the corner posts).
    """
    if name is None:
        name = f"BedShortWall_{side}"
    if side not in ("west", "east"):
        raise ValueError(f"side must be 'west' or 'east', got {side!r}")

    # Short wall spans between the corner posts (NOT between the long-wall
    # skins). This puts the short wall's outer face flush with the bed
    # outer face — no 0.75" recess at the corners.
    short_L = SHORT_WALL_L

    x_outer = -BED_L / 2.0 if side == "west" else +BED_L / 2.0
    x_skin = x_outer if side == "west" else x_outer - SKIN_T
    x_cleat = (x_outer + SKIN_T) if side == "west" else (x_outer - SKIN_T - CLEAT_T)

    shapes = []

    # Skin: COURSES stacked 1x6 boards
    for i in range(COURSES):
        y = SKID_H + i * COURSE_H
        shapes.append(make_lumber(SKIN_NOM, length=short_L, axis="Z",
                                  origin=(x_skin, y, -short_L / 2.0)))

    # Cleats: vertical 2x4s, CLEAT_W along Z, CLEAT_T into the bed (X)
    for z_edge in _cleat_positions(short_L, BED_WALL["cleats_short_wall"]):
        cleat = Part.makeBox(CLEAT_T, WALL_H, CLEAT_W)
        cleat.translate(App.Vector(x_cleat, SKID_H, -short_L / 2.0 + z_edge))
        shapes.append(cleat)

    # Header: 2x4 cedar on its wide face, flush with the wall's
    # outer face (NO external overhang), extending 3.5" inward
    # (toward the bed center). The first 0.75" sits directly above
    # the 0.75"-thick wall; the remaining 2.75" extends past the
    # wall's inner face into the bed.
    x_header = x_outer if x_outer < 0 else x_outer - HEADER_W
    header = Part.makeBox(HEADER_W, HEADER_T, short_L)
    header.translate(App.Vector(x_header, SKID_H + WALL_H, -short_L / 2.0))
    shapes.append(header)

    wall = shapes[0].multiFuse(shapes[1:])
    return add_feature(doc, name, wall)


# ---- bottom slats (mesh + soil ballast) ------------------------------------

def make_bottom_slats(doc, bed_L_in=None, bed_W_in=None, skid_h_in=None,
                      num_slats=7, slat_nominal="1x2", name_prefix="BottomSlat"):
    """Build the bottom slats that support the mesh/soil ballast.

    1x2 CEDAR (not PT) slats span the bed width (along Z), spaced evenly
    along the bed length (along X). Cedar because the slats are above
    ground (sit on top of the footers) — soil sits on top of them.

    The slats are sized to fit ON TOP OF the footers and BETWEEN the
    planter wall inner faces:
      - Wall inner face is at z = ±(bed_W/2 - SKIN_T) (the 0.75"-thick
        wall skin sits with its outer face at the bed outer dimension).
      - So the slat length = bed_W - 2*SKIN_T (e.g., 44.6 - 1.5 = 43.1").
      - Slat origin Z = -slat_length/2 (centered on the bed center).
    This keeps the slats fully supported by the long footers (2x4 PT
    on wide side, 3.5" wide, with their outer face flush with the bed
    outer at z = ±22.30) and hidden behind the walls. The slat ends
    sit in the inner 2.75" of each long footer (from z = ±18.80 to
    z = ±21.55) — plenty of grip for the soil load.

    Hardware cloth (1/2" galvanized) is stapled to the tops of the slats,
    and the soil sits on the mesh. Soil is the actual ballast (the bed
    weighs 3,000-4,000 lb when full, no ground anchors needed).

    Slats are laid flat: 1x2 PT (0.75" thick x 1.5" tall), running across
    the bed, with their tops at y = SKID_H + 1.5" (just above the skids).
    This puts the mesh at y = SKID_H + 1.5", supporting the soil.

    Default 7 slats across an 8-ft bed: 13" gap between slats — plenty
    stiff for 1/2" hardware cloth under wet soil load. For 1/4" mesh,
    bump to 10-12 slats.

    Args:
        doc: FreeCAD document.
        bed_L_in: bed outer length (X). Defaults to wattplot_params.BED.
        bed_W_in: bed outer width (Z). Defaults to wattplot_params.BED.
        skid_h_in: skid height (Y bottom of walls). Defaults to BED.
        num_slats: number of slats across the bed length.
        slat_nominal: nominal lumber size (catalog key, e.g. "1x2").
        name_prefix: FreeCAD object name prefix.

    Returns:
        list of Part::Feature slat objects (in X order).
    """
    if bed_L_in is None:
        bed_L_in = BED["outer_L_in"]
    if bed_W_in is None:
        bed_W_in = BED["outer_W_in"]
    if skid_h_in is None:
        skid_h_in = BED["skid_h_in"]

    slat_t = LUMBER[slat_nominal]["actual_t"]   # 0.75 for 1x2
    spacing = bed_L_in / num_slats

    # Slats fit between the wall inner faces (z = ±(bed_W/2 - SKIN_T))
    # so they sit fully on the footers and don't poke past the wall.
    # bed_W=44.6" - 2*SKIN_T=0.75" = 43.1" for the LONGi bed.
    slat_length = bed_W_in - 2.0 * SKIN_T

    slats = []
    for i in range(num_slats):
        # Center each slat on its slot, evenly distributed across bed_L
        center_x = -bed_L_in / 2.0 + spacing * (i + 0.5)
        # axis="Z": X=slat_t (thin), Y=slat_h (vertical), Z=slat_length
        # origin.x is the box's min X corner → offset by -slat_t/2 to center
        # origin.z is the box's min Z corner → -slat_length/2 to center on bed
        slat = make_lumber(
            slat_nominal,
            length=slat_length,
            axis="Z",
            origin=(center_x - slat_t / 2.0, skid_h_in, -slat_length / 2.0),
        )
        slat_obj = add_feature(doc, f"{name_prefix}_{i+1}", slat)
        slats.append(slat_obj)

    return slats


# ---- quick test -------------------------------------------------------------

if __name__ == "__main__":
    doc = App.newDocument("test_bed_walls")
    n = make_bed_long_wall(doc, "north")
    s = make_bed_long_wall(doc, "south")
    w = make_bed_short_wall(doc, "west")
    e = make_bed_short_wall(doc, "east")
    doc.recompute()
    for o in (n, s, w, e):
        print(f"  {o.Name}: vol = {o.Shape.Volume:.1f} in^3, "
              f"bbox = {o.Shape.BoundBox}")
    total_vol = sum(o.Shape.Volume for o in (n, s, w, e))
    print(f"  Total wood volume: {total_vol:.1f} in^3 "
          f"(~{total_vol / 12**3:.2f} ft^3)")
