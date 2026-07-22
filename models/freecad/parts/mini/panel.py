"""
Mini v2 panel — Newpowa 100W 12V Bifacial, 38.58" x 20.87" x 1.18".

The panel is BIGGER than the frame interior (37" x 19"), so it sits ON TOP
of the frame and overhangs the rails on all four sides (~0.79" on the
long sides, ~0.94" on the short sides). This is the same overhang pattern
as the full-size build (see ../panel.py).

The panel's aluminum frame is gripped by mid-clamps (not modeled here)
which wrap the panel frame and bolt through the rails. 6 clamps total
(2 per long rail + 1 per cross rail) per the FRAME design rules.

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


PANEL_L = MINI["panel_L_in"]    # 38.58
PANEL_W = MINI["panel_W_in"]    # 20.87
PANEL_T = MINI["panel_t_in"]    # 1.18

# Bed/frame Y positions (matches frame.py)
WALL_H = MINI["bed_wall_h_in"]   # 3.5
SKID_H = MINI["skid_h_in"]       # 1.5

FRAME_Y_BOTTOM = SKID_H + WALL_H              # 5.0
PANEL_Y_BOTTOM = FRAME_Y_BOTTOM + 0.5         # 5.5, 0.5" above rail bottom
PANEL_Y_TOP = PANEL_Y_BOTTOM + PANEL_T        # 6.68


def make_panel(doc, name="Mini_Panel"):
    panel = box(PANEL_L, PANEL_T, PANEL_W,
                x=-PANEL_L / 2.0, y=PANEL_Y_BOTTOM, z=-PANEL_W / 2.0)
    return add_feature(doc, name, panel)
