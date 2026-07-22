"""
Mini v2 actuator mount — 2x2 clevis on north rail of the frame + 2x2 wall
block on the bed's north wall. ½" steel pin through both.

Visualization only — the actual actuator (24" stroke 12V 330 lbf) is bought
hardware, not modeled in detail. The real-world actuator geometry requires
a bracket/extension to span the 20"+ distance between the two anchor points
at 0° tilt (24" stroke + ~6" clevis-to-clevis offset).

Design rules (enforced):
  1. NO MITER CUTS — blocks are simple rectangles.
  2. ALL HARDWARE OFF THE SHELF — 2x2 PT DF, ½" steel pin.
  3. SIMPLE COMMON DIMENSIONS — 1.5" blocks match the 2x2 frame.
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


# Bed/frame Y positions (matches frame.py)
WALL_T = MINI["bed_wall_thk_in"]                # 0.75
WALL_H = MINI["bed_wall_h_in"]                  # 3.5
SKID_H = MINI["skid_h_in"]                      # 1.5 (2x2)
RAIL_T = MINI["long_rail_thk_in"]               # 1.5 (2x2)
RAIL_H = MINI["long_rail_h_in"]                 # 1.5 (2x2)

PANEL_W = MINI["panel_W_in"]                    # 20.87
BED_W = MINI["bed_outer_W_in"]                  # 22

FRAME_Y_BOTTOM = SKID_H + WALL_H                # 5.0
FRAME_Y_TOP = FRAME_Y_BOTTOM + RAIL_H           # 6.5

# North rail's outer face is at z = -BED_W/2 = -11
NORTH_RAIL_Z = -BED_W / 2.0

# 2x2 block: 1.5" x 1.5" x 1.5"
BLOCK_T = RAIL_T     # 1.5 (Z thickness)
BLOCK_H = RAIL_H     # 1.5 (Y height)
BLOCK_L = 4.0        # X length (slightly wider than 2x2 for pin stability)


def make_actuator_mount(doc, name="Mini_ActuatorMount"):
    """Clevis on north rail + wall block on bed's north wall + pin."""
    # Clevis: on top of the frame's north rail
    clevis = box(BLOCK_L, BLOCK_H, BLOCK_T,
                 x=-BLOCK_L / 2.0,
                 y=FRAME_Y_TOP,
                 z=NORTH_RAIL_Z)

    # Wall block: on top of the bed's north wall, slightly further out (in -Z)
    # for pin accessibility (matches the full-size mount pattern).
    wall_block = box(BLOCK_L, BLOCK_H, BLOCK_T,
                     x=-BLOCK_L / 2.0,
                     y=SKID_H + WALL_H,
                     z=NORTH_RAIL_Z - BLOCK_T)  # 1.5" further north

    # Pin: cylinder along Z, through both blocks (when frame is at 0°)
    pin = cylinder(BLOCK_T / 4.0, 3.0 * BLOCK_T,   # ~⅜" diameter, 4.5" long
                   x=0, y=FRAME_Y_TOP + BLOCK_H / 2.0,
                   z=NORTH_RAIL_Z,
                   axis="Z")

    compound = Part.makeCompound([clevis, wall_block, pin])
    return add_feature(doc, name, compound)
