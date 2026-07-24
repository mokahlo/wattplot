"""
Bed skids — 2 × 4x4 PT running the length of the bed, under the long walls.
4x4 actual: 3.5" × 3.5". Length = bed length (auto-derived).

Refactored to use `lumber.make_lumber()`. Bed length is read from
`wattplot_params.BED` and updates automatically with the upcycling pivot.
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED
from models.freecad.materials import LUMBER
from models.freecad.parts.lumber import make_lumber
from models.freecad.parts._helpers import add_feature

import FreeCAD as App
import Part


# 4x4 actual dimensions
SKID_THK = LUMBER["4x4"]["actual_t"]   # 3.5

# Bed dimensions (derived from wattplot_params)
BED_L = BED["outer_L_in"]             # 96 for default, 65 for 60-cell, etc.
BED_W = BED["outer_W_in"]


def make_skids(doc, name="BedSkids"):
    """Two 4x4 skids, running along X at z=±(BED_W/2 - SKID_THK/2).

    The outer face of each skid is flush with the outer face of the long
    wall (z=±bed_W/2). The skids extend along the full bed length.
    """
    z_offset = BED_W / 2.0 - SKID_THK / 2.0  # = bed_W/2 - 1.75

    skids = []
    for sign in (-1, +1):
        # Skid sits on the ground (y=0 to y=SKID_THK)
        skid = make_lumber(
            "4x4",
            length=BED_L,
            axis="X",
            origin=(-BED_L / 2.0, 0, sign * z_offset - SKID_THK / 2.0),
        )
        skids.append(skid)

    compound = Part.makeCompound(skids)
    return add_feature(doc, name, compound)


if __name__ == "__main__":
    doc = App.newDocument("test_skids")
    s = make_skids(doc)
    doc.recompute()
    bb = s.Shape.BoundBox
    mass_lb = s.Shape.Volume * 35 / 1728  # 35 pcf (PT DF)
    print(f"  Skids: vol={s.Shape.Volume:.1f} in^3, "
          f"dim={bb.XLength:.1f}×{bb.YLength:.1f}×{bb.ZLength:.1f}, "
          f"mass={mass_lb:.1f} lb")
