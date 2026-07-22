"""
Mini hinge — 2 × 1.5" butt hinges on the south wall, ⅜" pin.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import MINI
from models.freecad.parts._helpers import box, cylinder, add_feature

import FreeCAD as App
import Part


LEAF = MINI["hinge_leaf_in"]    # 1.5
PIN_D = MINI["hinge_pin_d_in"]  # 0.375
COUNT = MINI["hinge_count"]      # 2
ROD_LEN = MINI["hinge_rod_length_in"]  # 24

WALL_T = 0.75
WALL_H = 3.5
SKID_H = MINI["skid_h_in"]

HINGE_Y = SKID_H + WALL_H    # top of south wall
HINGE_Z = +MINI["bed_outer_W_in"] / 2.0   # outer face of south wall


def make_hinge(doc, x_pos, name=None):
    if name is None:
        name = f"Mini_Hinge_{x_pos:.0f}"
    # Hinge body
    body = box(LEAF, LEAF, LEAF * 0.5,
               x=x_pos - LEAF / 2.0, y=HINGE_Y, z=HINGE_Z)
    # Pin
    pin = cylinder(PIN_D / 2.0, LEAF * 0.8,
                   x=x_pos - LEAF * 0.4, y=HINGE_Y, z=HINGE_Z, axis="X")
    compound = Part.makeCompound([body, pin])
    return add_feature(doc, name, compound)


def make_all_hinges(doc, name="Mini_HingeSet"):
    # 2 hinges, evenly spaced along the 19" hinge axis
    # Total span: 13" centered, leaving 3" margin on each end
    span = 13.0
    x_positions = [-span / 2, +span / 2]
    hinges = [make_hinge(doc, x) for x in x_positions]
    compound = Part.makeCompound([h.Shape for h in hinges])
    return add_feature(doc, name, compound), hinges
