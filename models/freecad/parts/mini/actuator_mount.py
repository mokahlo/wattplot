"""
Mini actuator mount — 1x2 clevis on north rail + 1x2 wall block on bed's north wall.
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


PANEL_W = MINI["panel_W_in"]   # 8.46
BED_W = MINI["bed_outer_W_in"]   # 10
WALL_T = 0.75
WALL_H = 3.5
SKID_H = MINI["skid_h_in"]

FRAME_Y_TOP = SKID_H + WALL_H + 1.5
NORTH_RAIL_Z = -BED_W / 2.0   # outer face of north wall (rail flush with wall)

BLOCK_T = 0.75    # 1x2 actual
BLOCK_H = 1.5
BLOCK_L = 3.0


def make_actuator_mount(doc, name="Mini_ActuatorMount"):
    """Clevis on north rail + wall block on bed's north wall, both flush in Z."""
    # Clevis on north rail: rail is at z = -BED_W/2 to -BED_W/2 + RAIL_T
    # Place clevis on TOP of the rail, extending upward
    clevis = box(BLOCK_L, BLOCK_H, BLOCK_T,
                 x=-BLOCK_L / 2.0, y=FRAME_Y_TOP, z=NORTH_RAIL_Z)
    # Wall block on bed's north wall: z = -BED_W/2 to -BED_W/2 + RAIL_T
    # (flush with the rail in Z, on top of the wall in Y)
    wall_block = box(BLOCK_L, BLOCK_H, BLOCK_T,
                     x=-BLOCK_L / 2.0, y=SKID_H + WALL_H,
                     z=NORTH_RAIL_Z)
    compound = Part.makeCompound([clevis, wall_block])
    return add_feature(doc, name, compound)
