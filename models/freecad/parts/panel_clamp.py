"""
Panel clamps — 6 × aluminum mid-clamps, 2"×2"×0.4".

Distribution: 2 per long rail + 1 per cross rail = 6 total.
Mounted on top of the rails, gripping the panel frame.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED, FRAME, PANEL
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


PANEL_L = PANEL["L_in"]
PANEL_W = PANEL["W_in"]
PANEL_T = PANEL["thickness_in"]

WALL_H = LUMBER["2x12"]["actual_h"]
SKID_H = BED["skid_h_in"]
RAIL_H = LUMBER["2x6"]["actual_h"]

C = FRAME["panel_clamp"]
CLAMP_L = C["length_in"]      # 2.0
CLAMP_H = C["height_in"]      # 2.0
CLAMP_T = C["thickness_in"]   # 0.4

# Panel bottom is at y = SKID_H + WALL_H + 0.5 = 14.75
# The clamp grips the panel from above. The clamp body sits on top of the rail,
# which is at y=14.25 to 19.75. The panel is at y=14.75 to 16.15.
# Clamp is mounted above the rail (on top), extending up to clamp the panel.
# Wait — the clamp should hold the panel from the SIDE (the rail's inside face),
# not from above. So the clamp is mounted on top of the rail and extends over
# the panel edge, with a bolt pressing down on the panel frame.
# For visualization, place the clamp as a small block on top of the rail,
# near the panel edge.

PANEL_Y_TOP = SKID_H + WALL_H + 0.5 + PANEL_T   # 16.15
RAIL_Y_TOP = SKID_H + WALL_H + RAIL_H           # 19.75

# Clamp Y: bottom at PANEL_Y_TOP (sits on top of panel frame), height CLAMP_H upward
CLAMP_Y_BOTTOM = PANEL_Y_TOP


def make_clamp(doc, x, y, z, name=None):
    """One clamp as a small box at the given position."""
    if name is None:
        name = f"Clamp_{x:.0f}_{z:.0f}"
    clamp = box(CLAMP_L, CLAMP_H, CLAMP_T,
                x=x - CLAMP_L / 2.0,
                y=y,
                z=z - CLAMP_T / 2.0)
    return add_feature(doc, name, clamp)


def make_all_clamps(doc, name="PanelClampSet"):
    """Create all 6 clamps (2 per long rail, 1 per cross rail)."""
    clamps = []
    # 2 per long rail, evenly spaced along the rail
    per_long = C["per_long_rail"]   # 2
    rail_len = FRAME["long_rail"]["length_in"]   # 88.5
    for sign in (-1, +1):
        z_rail = sign * (PANEL_W / 2.0 - 0)  # outer face of rail (z=±22.3)
        for i in range(per_long):
            # Distribute evenly along the rail, with margin
            x = -rail_len/2 + (rail_len * (i + 0.5) / per_long) * 1.0
            # Actually evenly: for per_long=2, place at rail_len*0.25 and rail_len*0.75
            x = -rail_len/2 + rail_len * (i + 0.5) / per_long
            # Clamp on the inner edge of the rail (where the panel is)
            z = sign * (PANEL_W / 2.0 - 0) - sign * 0  # at the rail center
            # Actually mount on the rail top, near the panel edge. For the south
            # rail, the panel is at z < z_rail, so the clamp is at z slightly < z_rail.
            # For the north rail, the panel is at z > z_rail.
            z_clamp = z_rail - sign * 0.5  # 0.5" inside the rail from the outer face
            clamps.append(make_clamp(doc, x, CLAMP_Y_BOTTOM, z_clamp))

    # 1 per cross rail
    per_cross = C["per_cross_rail"]   # 1
    cross_len = FRAME["cross_rail"]["length_in"]   # 41.6
    for sign in (-1, +1):
        x_rail = sign * (PANEL_L / 2.0)
        z = 0  # center of the cross rail
        clamps.append(make_clamp(doc, x_rail, CLAMP_Y_BOTTOM, z))

    compound = Part.makeCompound([c.Shape for c in clamps])
    obj = add_feature(doc, name, compound)
    return obj, clamps


if __name__ == "__main__":
    doc = App.newDocument("test_clamps")
    obj, clamps = make_all_clamps(doc)
    doc.recompute()
    print(f"  Clamp set: {len(clamps)} clamps, vol={obj.Shape.Volume:.2f} in^3")
    for c in clamps:
        bb = c.Shape.BoundBox
        print(f"    {c.Name}: X=[{bb.XMin:.1f},{bb.XMax:.1f}], Z=[{bb.ZMin:.1f},{bb.ZMax:.1f}]")
