"""
Mini frame — 1x2 PT perimeter around the panel + 1x2 diagonal brace.
Scaled-down from the full-size frame.py.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import MINI
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


# Frame dims
LONG_RAIL_L = MINI["long_rail_length_in"]   # 19
CROSS_RAIL_L = MINI["cross_rail_length_in"]  # 9.5
RAIL_T = MINI["long_rail_thk_in"]          # 0.75
RAIL_H = MINI["long_rail_h_in"]            # 1.5
BRACE_L = MINI["diagonal_brace_length_in"]  # 20

PANEL_L = MINI["panel_L_in"]    # 17.32
PANEL_W = MINI["panel_W_in"]    # 8.46
PANEL_T = MINI["panel_t_in"]    # 0.71

# Bed dims (for placing frame on top)
BED_L = MINI["bed_outer_L_in"]             # 19
BED_W = MINI["bed_outer_W_in"]             # 10
WALL_T = LUMBER["1x4"]["actual_t"]    # 0.75
WALL_H = LUMBER["1x4"]["actual_h"]    # 3.5
SKID_H = MINI["skid_h_in"]             # 0.75

FRAME_Y_BOTTOM = SKID_H + WALL_H
FRAME_Y_TOP = FRAME_Y_BOTTOM + RAIL_H


def make_frame_long_rail(doc, side="south", name=None):
    """Long rail flush with the bed's outer face in Z (sits on top of the wall).

    For the south rail: z extent = (bed_outer_W/2 - RAIL_T) to (bed_outer_W/2)
    = wall's inner face to wall's outer face. The panel (at z = ±panel_W/2)
    fits inside the bed, with the rail's inner face just outside the panel.
    """
    if name is None:
        name = f"Mini_FrameLongRail_{side}"
    if side == "south":
        # South rail: z_box (low z) = wall inner face, z extent to wall outer face
        z_box = BED_W / 2.0 - RAIL_T
    elif side == "north":
        z_box = -BED_W / 2.0
    else:
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    rail = box(LONG_RAIL_L, RAIL_H, RAIL_T,
               x=-LONG_RAIL_L / 2.0, y=FRAME_Y_BOTTOM, z=z_box)
    return add_feature(doc, name, rail)


def make_frame_cross_rail(doc, side="east", name=None):
    if name is None:
        name = f"Mini_FrameCrossRail_{side}"
    if side == "east":
        x_box = +PANEL_L / 2.0 - RAIL_T
    elif side == "west":
        x_box = -PANEL_L / 2.0
    else:
        raise ValueError(f"side must be 'east' or 'west', got {side!r}")

    rail = box(RAIL_T, RAIL_H, CROSS_RAIL_L,
               x=x_box, y=FRAME_Y_BOTTOM, z=-CROSS_RAIL_L / 2.0)
    return add_feature(doc, name, rail)


def make_diagonal_brace(doc, name="Mini_DiagonalBrace"):
    """1x2 PT diagonal brace, square ends butt into long rails (no miter)."""
    interior_L = PANEL_L - 2 * RAIL_T
    interior_W = PANEL_W - 2 * RAIL_T
    angle_rad = math.atan2(interior_W, interior_L)

    brace = box(BRACE_L, RAIL_T, RAIL_H,
                x=-BRACE_L / 2.0, y=0, z=-RAIL_H / 2.0)
    brace = brace.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0),
                          math.degrees(angle_rad))
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
