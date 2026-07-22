"""
Mini panel — Newpowa 10W 12V Mono, 17.32" × 8.46" × 0.71".
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


PANEL_L = MINI["panel_L_in"]
PANEL_W = MINI["panel_W_in"]
PANEL_T = MINI["panel_t_in"]

WALL_T = LUMBER["1x4"]["actual_t"]
WALL_H = LUMBER["1x4"]["actual_h"]
SKID_H = MINI["skid_h_in"]
RAIL_T = MINI["long_rail_thk_in"]

PANEL_Y_BOTTOM = SKID_H + WALL_H + 0.25   # 0.25" above rail bottom


def make_panel(doc, name="Mini_Panel"):
    panel = box(PANEL_L, PANEL_T, PANEL_W,
                x=-PANEL_L / 2.0, y=PANEL_Y_BOTTOM, z=-PANEL_W / 2.0)
    return add_feature(doc, name, panel)
