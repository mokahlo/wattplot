"""
Mini v2.2 bed skids - 2 x 1x2 PT running the length of the bed.
Smaller than the v2.1 2x2 skids (which were 1.5" tall). For the small
4" deep bed, 1x2 skids keep the center of gravity low.
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

SKID_S = MINI["skid_side_in"]   # 0.75 (1x2 actual)
BED_L = MINI["bed_outer_L_in"]  # 18
BED_W = MINI["bed_outer_W_in"]  # 14


def make_skids(doc, name="Mini_BedSkids"):
    z_offset = BED_W / 2.0 - SKID_S / 2.0
    skids = []
    for sign in (-1, +1):
        skid = box(BED_L, SKID_S, SKID_S,
                    x=-BED_L / 2.0, y=0,
                    z=sign * z_offset - SKID_S / 2.0)
        skids.append(skid)
    compound = Part.makeCompound(skids)
    return add_feature(doc, name, compound)
