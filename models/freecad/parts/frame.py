"""
Frame — 2x6 PT DF perimeter around the panel, plus 2x4 diagonal brace.

Design rules (enforced):
  1. NO MITER CUTS — all joints butt. Diagonal brace has square ends.
  2. ALL HARDWARE OFF THE SHELF — standard sizes, see materials.py.
  3. SIMPLE COMMON DIMENSIONS — long rails 96" (2x6x8ft, no waste),
     cross rails 42" (cut from 2x6x8ft, 6" waste per board), diagonal brace
     102" (cut from 2x4x10ft, 18" waste).

Geometry at 0° tilt (panel flat over the bed):
  - Frame exterior: 96" (X) × 45.6" (Z) — long rails are 96", cross rails are 42"
  - Frame interior: 93" (X) × 42" (Z) — between the long rails (93" between
    the inside faces of the cross rails)
  - Long rails at z=±22.3 (each 1.5" thick, 5.5" tall, 96" long)
  - Cross rails at x=±48.5 (each 1.5" thick in X, 5.5" tall, 42" long)
  - Diagonal brace: 2x4 PT, 102" long, runs corner to corner inside the frame
  - All sit on top of the south wall, hinged at z=22.3
  - Bottom of frame is at y = SKID_H + H_wall = 14.25

At any tilt angle θ (around the hinge axis along X), the entire frame is
rotated by θ. The frame module builds it flat; assemble.py applies the tilt.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED, FRAME, PANEL
from models.freecad.materials import LUMBER
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


# Constants — read from wattplot_params.py (single source of truth)
PANEL_L = PANEL["L_in"]            # 97
PANEL_W = PANEL["W_in"]            # 44.6
PANEL_T = PANEL["thickness_in"]    # 1.4

# Frame dimensions — read from FRAME dict
LONG_RAIL_L = FRAME["long_rail"]["length_in"]     # 96.0 (8ft, no waste)
CROSS_RAIL_L = FRAME["cross_rail"]["length_in"]   # 42.0 (cut from 8ft)
BRACE_L = FRAME["diagonal_brace"]["length_in"]    # 102.0 (from 2x4x10ft)

WALL_T = LUMBER["2x12"]["actual_t"]   # 1.5
WALL_H = LUMBER["2x12"]["actual_h"]   # 11.25
SKID_H = BED["skid_h_in"]             # 3.0

# Top of the south wall = bottom of the frame when at 0° tilt
FRAME_Y_BOTTOM = SKID_H + WALL_H   # 14.25

# 2x6 actual dims
RAIL_T = LUMBER["2x6"]["actual_t"]  # 1.5
RAIL_H = LUMBER["2x6"]["actual_h"]  # 5.5

# 2x4 actual dims
BRACE_T = LUMBER["2x4"]["actual_t"]  # 1.5
BRACE_H = LUMBER["2x4"]["actual_h"]  # 3.5


def make_frame_long_rail(doc, side="south", name=None):
    """Long rail on the south or north edge of the panel.

    side: "south" (z=+22.3, hinged side) or "north" (z=-22.3, actuator side)

    Rail is LONG_RAIL_L=96" (X, 8ft stock no waste), 1.5" thick (Z), 5.5" tall
    (Y), bottom at y=14.25. The 97" panel overhangs 0.5" each end; clamps
    grip the panel frame at the ends.
    """
    if name is None:
        name = f"FrameLongRail_{side}"

    if side == "south":
        z_outer = +PANEL_W / 2.0    # +22.3
        z_box = z_outer - RAIL_T    # low-z corner of box = +20.8
    elif side == "north":
        z_outer = -PANEL_W / 2.0    # -22.3
        z_box = z_outer             # low-z corner of box = -22.3
    else:
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    rail = box(LONG_RAIL_L, RAIL_H, RAIL_T,
               x=-LONG_RAIL_L / 2.0,
               y=FRAME_Y_BOTTOM,
               z=z_box)
    return add_feature(doc, name, rail)


def make_frame_cross_rail(doc, side="east", name=None):
    """Cross rail on the east or west end of the panel.

    side: "east" (x=+48.5) or "west" (x=-48.5)

    Rail is 1.5" thick (X), 5.5" tall (Y), CROSS_RAIL_L=42" long (Z),
    bottom at y=14.25. Butt-jointed at both ends to the inside faces of
    the long rails (no miter).
    """
    if name is None:
        name = f"FrameCrossRail_{side}"

    if side == "east":
        # x_outer = +PANEL_L/2 (panel east edge)
        x_box = (PANEL_L / 2.0) - RAIL_T   # low-x corner of box = +47
    elif side == "west":
        # x_outer = -PANEL_L/2
        x_box = -(PANEL_L / 2.0)            # low-x corner of box = -48.5
    else:
        raise ValueError(f"side must be 'east' or 'west', got {side!r}")

    rail = box(RAIL_T, RAIL_H, CROSS_RAIL_L,
               x=x_box,
               y=FRAME_Y_BOTTOM,
               z=-CROSS_RAIL_L / 2.0)
    return add_feature(doc, name, rail)


def make_diagonal_brace(doc, name="DiagonalBrace"):
    """2x4 PT diagonal brace, 102" long, runs corner to corner inside the frame.

    Square ends butt into the inside faces of the long rails (no miter cut).

    Interior dimensions:
      - X extent (between cross rails):  PANEL_L - 2*RAIL_T = 97 - 3 = 94"
      - Z extent (between long rails):   PANEL_W - 2*RAIL_T = 44.6 - 3 = 41.6"
    Diagonal = sqrt(94^2 + 41.6^2) = sqrt(8836 + 1730.6) = sqrt(10566.6) ≈ 102.8"

    We use the stock length 102" (from 2x4x10ft). The brace end sits ~0.4"
    short of the inside corner (where the long rail meets the cross rail),
    but the square butt joint lands cleanly on the inside face of the long rail.
    """
    interior_L = PANEL_L - 2 * RAIL_T   # 94
    interior_W = PANEL_W - 2 * RAIL_T   # 41.6
    angle_rad = math.atan2(interior_W, interior_L)  # ~23.86°

    # Build the brace centered at origin, lying along +X
    brace = box(BRACE_L, BRACE_T, BRACE_H,
                x=-BRACE_L / 2.0, y=0, z=-BRACE_H / 2.0)

    # Rotate in the X-Z plane (around Y axis) by angle
    brace = brace.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0),
                          math.degrees(angle_rad))

    # Place the brace in the frame plane (just above the rail bottoms)
    brace_y = FRAME_Y_BOTTOM + 0.5   # 0.5" above the bottom of the rails
    brace = brace.translate(App.Vector(0, brace_y, 0))

    return add_feature(doc, name, brace)


# ---- combined: frame as a single compound ---------------------------------

def make_frame_assembly(doc, name="FrameAssembly"):
    """Build the whole frame (4 rails + brace) as a single Part::Feature
    using a Compound. Useful for the assembly rotation step.
    """
    south = make_frame_long_rail(doc, "south")
    north = make_frame_long_rail(doc, "north")
    east = make_frame_cross_rail(doc, "east")
    west = make_frame_cross_rail(doc, "west")
    brace = make_diagonal_brace(doc)

    # Combine all into a compound
    compound = Part.makeCompound([south.Shape, north.Shape,
                                  east.Shape, west.Shape, brace.Shape])
    obj = add_feature(doc, name, compound)
    return obj, [south, north, east, west, brace]


# ---- quick test -----------------------------------------------------------

if __name__ == "__main__":
    doc = App.newDocument("test_frame")
    f, parts = make_frame_assembly(doc)
    doc.recompute()
    print(f"  Frame compound volume: {f.Shape.Volume:.1f} in^3")
    print(f"  Frame compound bbox:")
    bb = f.Shape.BoundBox
    print(f"    X: [{bb.XMin:.2f}, {bb.XMax:.2f}]  (length {bb.XLength:.2f})")
    print(f"    Y: [{bb.YMin:.2f}, {bb.YMax:.2f}]  (height {bb.YLength:.2f})")
    print(f"    Z: [{bb.ZMin:.2f}, {bb.ZMax:.2f}]  (width  {bb.ZLength:.2f})")
    print(f"  Individual parts:")
    for p in parts:
        bb = p.Shape.BoundBox
        print(f"    {p.Name}: vol={p.Shape.Volume:.1f}, "
              f"bbox=({bb.XLength:.1f}×{bb.YLength:.1f}×{bb.ZLength:.1f})")
