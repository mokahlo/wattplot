"""
Solar panel — visualization only (the real panel is bought, not modeled).
A thin glass+aluminum sandwich box, 97" × 44.6" × 1.4".
Sits inside the frame, slightly raised above the rails.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED, PANEL
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


PANEL_L = PANEL["L_in"]            # 97
PANEL_W = PANEL["W_in"]            # 44.6
PANEL_T = PANEL["thickness_in"]    # 1.4

WALL_H = LUMBER["2x12"]["actual_h"]
SKID_H = BED["skid_h_in"]
RAIL_H = LUMBER["2x6"]["actual_h"]

# Panel sits inside the frame, on top of the rails. The frame interior is
# 94" × 41.6", but the panel is 97" × 44.6" — so the panel extends over the
# rails on all four sides. Panel bottom sits 0.5" above the rail bottom.
PANEL_Y_BOTTOM = SKID_H + WALL_H + 0.5  # 14.75


def make_panel(doc, name="Panel"):
    """Solar panel as a thin box. Centered at frame center, Y=14.75 bottom."""
    panel = box(PANEL_L, PANEL_T, PANEL_W,
                x=-PANEL_L / 2.0,
                y=PANEL_Y_BOTTOM,
                z=-PANEL_W / 2.0)
    return add_feature(doc, name, panel)


if __name__ == "__main__":
    doc = App.newDocument("test_panel")
    p = make_panel(doc)
    doc.recompute()
    bb = p.Shape.BoundBox
    print(f"  Panel: vol={p.Shape.Volume:.1f} in^3, "
          f"dim={bb.XLength:.1f}×{bb.YLength:.1f}×{bb.ZLength:.1f}, "
          f"mass={p.Shape.Volume * 0.098 / 1728:.1f} lb "
          f"(using glass-aluminum density 0.098 lb/in^3)")
