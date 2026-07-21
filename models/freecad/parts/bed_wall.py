"""
Bed walls — 2x12 PT DF, half-lap corners.

A bed wall is a 2x12 board on one of the four edges of the bed:
  - Long wall: 96" along X, at the -Z (north) or +Z (south) edge
  - Short wall: 41.6" along Z, at the -X (west) or +X (east) edge

Both get half-lap notches at their ends so the corners interlock.
The notch is `thickness/2` deep (Z direction for long walls, X for short),
`height` tall (full wall height), and 3" wide (along the wall length).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, add_feature, half_lap_notch

import FreeCAD as App
import Part


# 2x12 actual dimensions (PT DF, dressed)
NOMINAL = "2x12"
T = LUMBER[NOMINAL]["actual_t"]    # 1.5
H = LUMBER[NOMINAL]["actual_h"]    # 11.25

# Bed outer dimensions
BED_L = BED["outer_L_in"]          # 96
BED_W = BED["outer_W_in"]          # 44.6
SKID_H = BED["skid_h_in"]          # 3.0  (wall sits on top of skids)

# Half-lap notch size (3" wide along wall length, 0.75" deep)
NOTCH_DEPTH = 3.0


def _half_lap_notch_long():
    """Notch box for the end of a long wall. 3" wide along X, full height,
    0.75" deep in Z (so the outer half of the wall is removed at the joint).
    """
    return box(NOTCH_DEPTH, H, T / 2.0)


def _half_lap_notch_short():
    """Notch box for the end of a short wall. 3" wide along Z, full height,
    0.75" deep in X."""
    return box(T / 2.0, H, NOTCH_DEPTH)


def make_bed_long_wall(doc, side="north", name=None):
    """Create a long bed wall (96" along X) on the north or south edge.

    side: "north" (z = -22.3, -Z) or "south" (z = +22.3, +Z)
    Returns the FreeCAD Part::Feature.
    """
    if name is None:
        name = f"BedLongWall_{side}"

    if side == "north":
        z_outer = -BED_W / 2.0    # low z corner of the box (= -22.3)
        z_box = z_outer            # box starts here, extends +Z
    elif side == "south":
        z_outer = +BED_W / 2.0    # high z face (= +22.3)
        z_box = z_outer - T       # low z corner of the box (= +20.8)
    else:
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    # Wall box: 96" long (X), 11.25" tall (Y), 1.5" thick (Z).
    # Placed with the LOW-z corner at z_box, bottom at y=SKID_H.
    # For north: z_box = -22.3, extends to z=-20.8.  Wall at z in [-22.3, -20.8].
    # For south: z_box = +20.8, extends to z=+22.3.  Wall at z in [+20.8, +22.3].
    wall = box(BED_L, H, T,
               x=-BED_L / 2.0,
               y=SKID_H,
               z=z_box)

    # Cut half-lap notches at both ends. The notch removes the OUTER half of
    # the wall (T/2 = 0.75"). Notch box has its low z corner at:
    #   - north: z_outer = -22.3 (removes [-22.3, -20.8] of outer half)
    #   - south: z_box   = +20.8 (removes [+20.8, +22.3] of outer half)
    for sign in (-1, +1):
        notch_x = sign * (BED_L / 2.0 - NOTCH_DEPTH)
        notch_z = z_box if side == "north" else z_box
        notch = box(NOTCH_DEPTH, H, T / 2.0,
                    x=notch_x, y=SKID_H, z=z_box)
        wall = wall.cut(notch)

    return add_feature(doc, name, wall)


def make_bed_short_wall(doc, side="west", name=None):
    """Create a short bed wall (41.6" along Z) on the west or east edge.

    side: "west" (x = -22.3) or "east" (x = +22.3)
    """
    if name is None:
        name = f"BedShortWall_{side}"

    if side == "west":
        x_outer = -BED_W / 2.0    # low x corner of the box (= -22.3)
        x_box = x_outer            # box starts here, extends +X
    elif side == "east":
        x_outer = +BED_W / 2.0    # high x face (= +22.3)
        x_box = x_outer - T       # low x corner of the box (= +20.8)
    else:
        raise ValueError(f"side must be 'west' or 'east', got {side!r}")

    # Short wall length: BED_W - 2*T (fits between the long walls)
    short_L = BED_W - 2.0 * T

    # Wall box: 1.5" wide (X), 11.25" tall (Y), 41.6" long (Z).
    # Placed with the LOW-x corner at x_box, bottom at y=SKID_H.
    # For west: x_box = -22.3, extends to x=-20.8.  Wall at x in [-22.3, -20.8].
    # For east: x_box = +20.8, extends to x=+22.3.  Wall at x in [+20.8, +22.3].
    wall = box(T, H, short_L,
               x=x_box,
               y=SKID_H,
               z=-short_L / 2.0)

    # Half-lap notches at both Z ends. Notch removes the OUTER half (T/2).
    # Notch box has its low x corner at the outer face.
    for sign in (-1, +1):
        notch_z = sign * (short_L / 2.0 - NOTCH_DEPTH)
        notch = box(T / 2.0, H, NOTCH_DEPTH,
                    x=x_box, y=SKID_H, z=notch_z)
        wall = wall.cut(notch)

    return add_feature(doc, name, wall)


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
    print(f"  Total wood volume: {sum(o.Shape.Volume for o in (n,s,w,e)):.1f} in^3")
