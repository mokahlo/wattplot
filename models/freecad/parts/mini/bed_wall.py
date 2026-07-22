"""
Mini bed walls — 1x4 PT DF, half-lap corners.
Scaled-down from the full-size bed_wall.py.
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


NOMINAL = "1x4"        # 0.75 × 3.5 actual
T = LUMBER[NOMINAL]["actual_t"]   # 0.75
H = LUMBER[NOMINAL]["actual_h"]   # 3.5

BED_L = MINI["bed_outer_L_in"]     # 19
BED_W = MINI["bed_outer_W_in"]     # 11
SKID_H = MINI["skid_h_in"]          # 0.75

NOTCH_DEPTH = 1.5    # half-lap notch, 3/4 the wall thickness (T/2 = 0.375, but 1.5 is 2x T for visual clarity)


def make_bed_long_wall(doc, side="north", name=None):
    if name is None:
        name = f"Mini_BedLongWall_{side}"
    if side == "north":
        # North wall: outer face at -BED_W/2, box extends +Z toward center
        z_outer = -BED_W / 2.0
        z_box = z_outer          # low z corner = outer face
    elif side == "south":
        # South wall: outer face at +BED_W/2, box extends +Z away from center
        z_outer = +BED_W / 2.0
        z_box = z_outer - T      # low z corner = inner face
    else:
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    wall = box(BED_L, H, T, x=-BED_L / 2.0, y=SKID_H, z=z_box)
    # Half-lap notches at both ends
    for sign in (-1, +1):
        notch_x = sign * (BED_L / 2.0 - NOTCH_DEPTH)
        notch = box(NOTCH_DEPTH, H, T / 2.0, x=notch_x, y=SKID_H, z=z_box)
        wall = wall.cut(notch)
    return add_feature(doc, name, wall)


def make_bed_short_wall(doc, side="west", name=None):
    if name is None:
        name = f"Mini_BedShortWall_{side}"
    if side == "west":
        # West wall: outer face at -BED_W/2, box extends +X toward center
        x_outer = -BED_W / 2.0
        x_box = x_outer          # low x corner = outer face
    elif side == "east":
        # East wall: outer face at +BED_W/2, box extends +X away from center
        x_outer = +BED_W / 2.0
        x_box = x_outer - T      # low x corner = inner face
    else:
        raise ValueError(f"side must be 'west' or 'east', got {side!r}")

    short_L = BED_W - 2.0 * T
    wall = box(T, H, short_L, x=x_box, y=SKID_H, z=-short_L / 2.0)
    for sign in (-1, +1):
        notch_z = sign * (short_L / 2.0 - NOTCH_DEPTH)
        notch = box(T / 2.0, H, NOTCH_DEPTH, x=x_box, y=SKID_H, z=notch_z)
        wall = wall.cut(notch)
    return add_feature(doc, name, wall)


if __name__ == "__main__":
    doc = App.newDocument("test_mini_bed")
    n = make_bed_long_wall(doc, "north")
    s = make_bed_long_wall(doc, "south")
    w = make_bed_short_wall(doc, "west")
    e = make_bed_short_wall(doc, "east")
    doc.recompute()
    for o in (n, s, w, e):
        bb = o.Shape.BoundBox
        print(f"  {o.Name}: vol={o.Shape.Volume:.2f} in^3, "
              f"X=[{bb.XMin:.1f},{bb.XMax:.1f}], Y=[{bb.YMin:.1f},{bb.YMax:.1f}], Z=[{bb.ZMin:.1f},{bb.ZMax:.1f}]")
