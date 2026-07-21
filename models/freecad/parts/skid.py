"""
Bed skids — 2 × 4x4 PT running the length of the bed, under the long walls.
4x4 actual: 3.5" × 3.5". Length: 96" (matches bed length).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


# 4x4 actual
SKID_S = LUMBER["4x4"]["actual_t"]   # 3.5
BED_L = BED["outer_L_in"]             # 96
BED_W = BED["outer_W_in"]             # 44.6
SKID_H = BED["skid_h_in"]             # 3.0


def make_skids(doc, name="BedSkids"):
    """Two 4x4 skids, 96" long, running along X at z=±(BED_W/2 - SKID_S/2)."""
    # Position: center of skid at z=±(BED_W/2 - SKID_S/2) so the OUTER face
    # of the skid is flush with the outer face of the long wall (z=±22.3).
    z_offset = BED_W / 2.0 - SKID_S / 2.0   # = 22.3 - 1.75 = 20.55

    skids = []
    for sign in (-1, +1):
        skid = box(BED_L, SKID_S, SKID_S,
                   x=-BED_L / 2.0,
                   y=0,                # bottom of skid on the ground
                   z=sign * z_offset - SKID_S / 2.0)
        skids.append(skid)

    compound = Part.makeCompound(skids)
    return add_feature(doc, name, compound)


if __name__ == "__main__":
    doc = App.newDocument("test_skids")
    s = make_skids(doc)
    doc.recompute()
    bb = s.Shape.BoundBox
    print(f"  Skids: vol={s.Shape.Volume:.1f} in^3, "
          f"dim={bb.XLength:.1f}×{bb.YLength:.1f}×{bb.ZLength:.1f}, "
          f"mass={s.Shape.Volume*35/1728:.1f} lb")
