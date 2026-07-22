"""
Mini v2 bed walls — 1x4 PT DF, half-lap corners.
40" x 22" outer, 1x4 walls (0.75 x 3.5 actual) on 2x2 skids.

Geometry convention (matches full-size):
  - X is the bed's long axis (length direction)
  - Z is the bed's short axis (width direction)
  - LONG walls run along X, at z = ±(BED_W/2 - T), length = BED_L
  - SHORT walls run along Z, at x = ±(BED_L/2 - T), length = BED_W - 2*T

Design rules (enforced):
  1. NO MITER CUTS — every cut is 90° square. Half-lap notches at corners.
  2. ALL HARDWARE OFF THE SHELF — 1x4 PT DF, 2x2 PT DF.
  3. SIMPLE COMMON DIMENSIONS — 40" / 20.5" from 1x4x8ft stock.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import MINI
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


NOMINAL = "1x4"        # 0.75 x 3.5 actual
T = LUMBER[NOMINAL]["actual_t"]   # 0.75
H = LUMBER[NOMINAL]["actual_h"]   # 3.5

BED_L = MINI["bed_outer_L_in"]     # 40
BED_W = MINI["bed_outer_W_in"]     # 22
SKID_H = MINI["skid_h_in"]         # 1.5 (2x2)

# Half-lap notch: 1.5" wide x H tall x T/2 deep. Square cut, no miter.
# Sits at the END of the wall, removing the OUTER half of the wall thickness.
NOTCH_DEPTH = 1.5


def make_bed_long_wall(doc, side="north", name=None):
    """Long wall: runs along X (the bed's long axis), at z = ±(BED_W/2 - T)."""
    if name is None:
        name = f"Mini_BedLongWall_{side}"
    if side == "north":
        # North wall: outer face at -BED_W/2, box extends +Z toward center
        z_box = -BED_W / 2.0          # low z corner = outer face
    elif side == "south":
        # South wall: outer face at +BED_W/2, box extends -Z toward center
        z_box = +BED_W / 2.0 - T      # low z corner = inner face
    else:
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    wall = box(BED_L, H, T, x=-BED_L / 2.0, y=SKID_H, z=z_box)
    # Half-lap notches at both ends (X=±(BED_L/2 - NOTCH_DEPTH))
    for sign in (-1, +1):
        notch_x = sign * (BED_L / 2.0 - NOTCH_DEPTH)
        notch = box(NOTCH_DEPTH, H, T / 2.0, x=notch_x, y=SKID_H, z=z_box)
        wall = wall.cut(notch)
    return add_feature(doc, name, wall)


def make_bed_short_wall(doc, side="west", name=None):
    """Short wall: runs along Z (the bed's short axis), at x = ±(BED_L/2 - T).

    Position is on the SHORT END of the bed (x = ±BED_L/2), not at ±BED_W/2.
    Length is the interior bed width: BED_W - 2*T (so it fits between the
    long walls with the half-lap notches interlocking).
    """
    if name is None:
        name = f"Mini_BedShortWall_{side}"
    if side == "west":
        # West wall: outer face at -BED_L/2, box extends +X toward center
        x_box = -BED_L / 2.0          # low x corner = outer face
    elif side == "east":
        # East wall: outer face at +BED_L/2, box extends -X toward center
        x_box = +BED_L / 2.0 - T      # low x corner = inner face
    else:
        raise ValueError(f"side must be 'west' or 'east', got {side!r}")

    short_L = BED_W - 2.0 * T   # 22 - 1.5 = 20.5"
    wall = box(T, H, short_L, x=x_box, y=SKID_H, z=-short_L / 2.0)
    # Half-lap notches at both ends (Z=±(short_L/2 - NOTCH_DEPTH))
    for sign in (-1, +1):
        notch_z = sign * (short_L / 2.0 - NOTCH_DEPTH)
        notch = box(T / 2.0, H, NOTCH_DEPTH, x=x_box, y=SKID_H, z=notch_z)
        wall = wall.cut(notch)
    return add_feature(doc, name, wall)


if __name__ == "__main__":
    doc = App.newDocument("test_mini_bed_v2")
    n = make_bed_long_wall(doc, "north")
    s = make_bed_long_wall(doc, "south")
    w = make_bed_short_wall(doc, "west")
    e = make_bed_short_wall(doc, "east")
    doc.recompute()
    for o in (n, s, w, e):
        bb = o.Shape.BoundBox
        print(f"  {o.Name}: vol={o.Shape.Volume:.2f} in^3, "
              f"X=[{bb.XMin:.1f},{bb.XMax:.1f}], Y=[{bb.YMin:.1f},{bb.YMax:.1f}], Z=[{bb.ZMin:.1f},{bb.ZMax:.1f}]")
