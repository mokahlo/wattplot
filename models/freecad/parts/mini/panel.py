"""
Mini v2.2 panel - ECO-WORTHY 10W 12V (or poly), 13.3" x 8.1" x 0.7", 1.88 lb.

Sits inside the 1x2 frame (which is 18" x 14" outer, 16.5" x 12.5" inner).
The panel's aluminum frame is gripped by mid-clamps (not modeled here)
which wrap the panel frame and bolt through the rails. 4 clamps total
(2 per long rail) per the FRAME design rules.

Y position: panel bottom 0.5" above the rail bottom (so the panel sits
on top of the rails with a small clamp gap below the panel frame).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import MINI
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


PANEL_L = MINI["panel_L_in"]    # 13.3
PANEL_W = MINI["panel_W_in"]    # 8.1
PANEL_T = MINI["panel_t_in"]    # 0.7

# Bed/frame Y positions (matches frame.py)
WALL_H = MINI["bed_wall_h_in"]   # 3.5
SKID_H = MINI["skid_h_in"]       # 0.75

FRAME_Y_BOTTOM = SKID_H + WALL_H              # 4.25
PANEL_Y_BOTTOM = FRAME_Y_BOTTOM + 0.5         # 4.75, 0.5" above rail bottom
PANEL_Y_TOP = PANEL_Y_BOTTOM + PANEL_T        # 5.45


def make_panel(doc, name="Mini_Panel"):
    panel = box(PANEL_L, PANEL_T, PANEL_W,
                x=-PANEL_L / 2.0, y=PANEL_Y_BOTTOM, z=-PANEL_W / 2.0)
    return add_feature(doc, name, panel)
