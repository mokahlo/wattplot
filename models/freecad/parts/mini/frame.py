"""
Mini v2.2 frame - 1x2 PT perimeter around the panel + 2x4 diagonal brace.

Sized to fit the ECO-WORTHY 10W panel (13.3" x 8.1") on an 18" x 14" bed.

Geometry convention (matches bed_wall.py):
  - X is the bed's long axis
  - Z is the bed's short axis
  - Long rails: along X, at z = +/-(BED_W/2 - RAIL_T), length = BED_L
  - Cross rails: along Z, at x = +/-(BED_L/2 - RAIL_T), length = BED_W - 2*RAIL_T
  - Panel sits inside the frame, gripped by mid-clamps (clamps not modeled here)

Design rules (enforced):
  1. NO MITER CUTS - every cut is 90 deg square. Brace square-ends into rails.
  2. ALL HARDWARE OFF THE SHELF - 1x2 PT DF (0.75" x 1.5"), 2x4 for brace.
  3. SIMPLE COMMON DIMENSIONS - 18" / 12.5" / 21" cuts from 8ft stock.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import MINI
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


# Frame dimensions from MINI v2.2
LONG_RAIL_L = MINI["long_rail_length_in"]        # 18
CROSS_RAIL_L = MINI["cross_rail_length_in"]      # 12.5
RAIL_T = MINI["long_rail_thk_in"]                # 0.75 (1x2)
RAIL_H = MINI["long_rail_h_in"]                  # 1.5
BRACE_L = MINI["diagonal_brace_length_in"]       # 21

PANEL_L = MINI["panel_L_in"]                     # 13.3
PANEL_W = MINI["panel_W_in"]                     # 8.1
PANEL_T = MINI["panel_t_in"]                     # 0.7

# Bed dims
BED_L = MINI["bed_outer_L_in"]                   # 18
BED_W = MINI["bed_outer_W_in"]                   # 14
WALL_T = MINI["bed_wall_thk_in"]                 # 0.75
WALL_H = MINI["bed_wall_h_in"]                   # 3.5
SKID_H = MINI["skid_h_in"]                       # 0.75

# Y positions: skid (0..SKID_H) + wall (SKID_H..SKID_H+WALL_H) + rail
FRAME_Y_BOTTOM = SKID_H + WALL_H                 # 4.25
FRAME_Y_TOP = FRAME_Y_BOTTOM + RAIL_H            # 5.75

# Frame interior dimensions (between inside faces of the long rails)
INTERIOR_L = BED_L - 2 * RAIL_T                  # 16.5
INTERIOR_W = BED_W - 2 * RAIL_T                  # 12.5
ANGLE_RAD = math.atan2(INTERIOR_W, INTERIOR_L)   # ~37 deg


def make_frame_long_rail(doc, side="south", name=None):
    """Long rail at the bed's long-side (z = +/-(BED_W/2 - RAIL_T))."""
    if name is None:
        name = f"Mini_FrameLongRail_{side}"
    if side == "south":
        z_box = BED_W / 2.0 - RAIL_T              # inner face = wall inner face
    elif side == "north":
        z_box = -BED_W / 2.0                     # outer face = wall outer face
    else:
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    rail = box(LONG_RAIL_L, RAIL_H, RAIL_T,
               x=-LONG_RAIL_L / 2.0, y=FRAME_Y_BOTTOM, z=z_box)
    return add_feature(doc, name, rail)


def make_frame_cross_rail(doc, side="east", name=None):
    """Cross rail at the bed's short end (x = +/-(BED_L/2 - RAIL_T))."""
    if name is None:
        name = f"Mini_FrameCrossRail_{side}"
    if side == "east":
        x_box = BED_L / 2.0 - RAIL_T
    elif side == "west":
        x_box = -BED_L / 2.0
    else:
        raise ValueError(f"side must be 'east' or 'west', got {side!r}")

    rail = box(RAIL_T, RAIL_H, CROSS_RAIL_L,
               x=x_box, y=FRAME_Y_BOTTOM, z=-CROSS_RAIL_L / 2.0)
    return add_feature(doc, name, rail)


def make_diagonal_brace(doc, name="Mini_DiagonalBrace"):
    """2x4 PT diagonal brace, square ends butt into the long rails.

    Spans the FRAME interior (corner to corner). For v2.2:
      interior = 16.5 x 12.5, brace length = sqrt(16.5^2 + 12.5^2) ~ 20.7"
      Use 21" from 2x4x8ft stock (75" waste).
    """
    brace = box(BRACE_L, RAIL_T, RAIL_H,
                x=-BRACE_L / 2.0, y=0, z=-RAIL_H / 2.0)
    brace = brace.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0),
                         math.degrees(ANGLE_RAD))
    brace_y = FRAME_Y_BOTTOM + 0.25
    brace = brace.translate(App.Vector(0, brace_y, 0))
    return add_feature(doc, name, brace)


def make_frame_assembly(doc, name="Mini_FrameAssembly"):
    south = make_frame_long_rail(doc, "south")
    north = make_frame_long_rail(doc, "north")
    east = make_frame_cross_rail(doc, "east")
    west = make_frame_cross_rail(doc, "west")
    brace = make_diagonal_brace(doc)
    compound = Part.makeCompound([south.Shape, north.Shape,
                                  east.Shape, west.Shape, brace.Shape])
    obj = add_feature(doc, name, compound)
    return obj, [south, north, east, west, brace]
