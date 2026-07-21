"""
Actuator mount — 2x6 clevis on the north rail of the frame + matching block
on the bed's north wall. ½" steel pin through both.

Visualization only — the actual actuator (ECO-WORTHY 12V 4" stroke) is bought
hardware, not modeled in detail.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED, FRAME, PANEL
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, cylinder, add_feature

import FreeCAD as App
import Part


PANEL_L = PANEL["L_in"]
PANEL_W = PANEL["W_in"]

WALL_T = LUMBER["2x12"]["actual_t"]
WALL_H = LUMBER["2x12"]["actual_h"]
SKID_H = BED["skid_h_in"]
RAIL_T = LUMBER["2x6"]["actual_t"]
RAIL_H = LUMBER["2x6"]["actual_h"]

AM = FRAME["actuator_mount"]
BLOCK_T = AM["block_thickness_in"]   # 1.5
BLOCK_H = AM["block_height_in"]      # 5.5
BLOCK_L = AM["block_length_in"]      # 6.0

# Frame north rail is at y = SKID_H + WALL_H to + WALL_H + RAIL_H = 14.25 to 19.75
# North rail's outer face is at z = -22.3 (north side of bed)
# Block sits on top of the rail, oriented so its 6" length is along X
# and the pin goes through it along Z (toward the actuator).

FRAME_Y_TOP = SKID_H + WALL_H + RAIL_H   # 19.75
NORTH_RAIL_Z = -PANEL_W / 2.0             # -22.3 (outer face of north rail)
# Clevis block: on top of the north rail, centered along X
# Block at z = north_rail_z (extends from z=-22.3 to z=-22.3+1.5=-20.8 in +Z)


def make_actuator_mount(doc, name="ActuatorMount"):
    """Clevis on north rail + wall block on bed's north wall + pin."""
    # Clevis on the north rail — sits on top of the rail
    clevis = box(BLOCK_L, BLOCK_H, BLOCK_T,
                 x=-BLOCK_L / 2.0,
                 y=FRAME_Y_TOP,
                 z=NORTH_RAIL_Z)

    # Wall block — on top of the bed's north wall, directly opposite the clevis
    # when the frame is at 0° tilt. The actuator will span between them.
    # When the frame tilts up, the clevis moves with it. The wall block stays put.
    wall_block = box(BLOCK_L, BLOCK_H, BLOCK_T,
                     x=-BLOCK_L / 2.0,
                     y=SKID_H + WALL_H,
                     z=NORTH_RAIL_Z - 3.0)   # 3" further out (so the pin is accessible)

    # Pin: cylinder along Z, through both blocks (when frame is at 0°)
    pin = cylinder(0.25, 6.0,   # ½" diameter, 6" long
                   x=0, y=FRAME_Y_TOP + BLOCK_H / 2.0,
                   z=NORTH_RAIL_Z,
                   axis="Z")

    compound = Part.makeCompound([clevis, wall_block, pin])
    return add_feature(doc, name, compound)


if __name__ == "__main__":
    doc = App.newDocument("test_actuator")
    a = make_actuator_mount(doc)
    doc.recompute()
    bb = a.Shape.BoundBox
    print(f"  Actuator mount: vol={a.Shape.Volume:.1f} in^3, "
          f"dim={bb.XLength:.1f}×{bb.YLength:.1f}×{bb.ZLength:.1f}")
