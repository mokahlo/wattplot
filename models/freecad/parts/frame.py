"""
Frame — 2x6 PT DF perimeter around the panel, plus 2x4 diagonal brace.

Geometry at 0° tilt (panel flat over the bed):
  - Frame interior: 97" (X) × 44.6" (Z) — matches the panel outer dims
  - Long rails: 2x6 PT, 97" long, sit on the east and west edges of the panel
  - Cross rails: 2x6 PT, 41.6" long, sit between the long rails at the panel ends
  - Diagonal brace: 2x4 PT, ~103" long, runs corner to corner inside the frame
  - All sit on top of the south wall, hinged at z=22.3
  - Bottom of frame is at y = SKID_H + H_wall = 14.25 (top of south wall)

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


# Constants
PANEL_L = PANEL["L_in"]            # 97
PANEL_W = PANEL["W_in"]            # 44.6
PANEL_T = PANEL["thickness_in"]    # 1.4

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

    Rail is 97" long (X), 1.5" thick (Z), 5.5" tall (Y), bottom at y=14.25.
    The rail's center-line Z position = ±(PANEL_W/2) = ±22.3, so the rail's
    inner face is at z=±(22.3 - 1.5) = ±20.8 and outer face at z=±22.3.
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

    rail = box(PANEL_L, RAIL_H, RAIL_T,
               x=-PANEL_L / 2.0,
               y=FRAME_Y_BOTTOM,
               z=z_box)
    return add_feature(doc, name, rail)


def make_frame_cross_rail(doc, side="east", name=None):
    """Cross rail on the east or west end of the panel.

    side: "east" (x=+48.5) or "west" (x=-48.5)

    Rail is 1.5" thick (X), 5.5" tall (Y), 41.6" long (Z), bottom at y=14.25.
    The rail fits between the long rails: Z extent [-20.8, +20.8] (= 41.6").
    """
    if name is None:
        name = f"FrameCrossRail_{side}"

    if side == "east":
        x_outer = +PANEL_L / 2.0
        x_box = x_outer - RAIL_T    # low-x corner of box = +47
    elif side == "west":
        x_outer = -PANEL_L / 2.0
        x_box = x_outer             # low-x corner of box = -48.5
    else:
        raise ValueError(f"side must be 'east' or 'west', got {side!r}")

    cross_L_z = PANEL_W - 2.0 * RAIL_T   # 41.6
    rail = box(RAIL_T, RAIL_H, cross_L_z,
               x=x_box,
               y=FRAME_Y_BOTTOM,
               z=-cross_L_z / 2.0)
    return add_feature(doc, name, rail)


def make_diagonal_brace(doc, name="DiagonalBrace"):
    """2x4 PT diagonal brace, spanning the frame interior corner to corner.

    Interior is (PANEL_L - 2*RAIL_T) × (PANEL_W - 2*RAIL_T) = 94" × 41.6".
    Diagonal length = sqrt(94^2 + 41.6^2) ≈ 102.8".

    The brace is laid flat in the X-Z plane (in the plane of the frame),
    with its center matching the frame center. Thickness (1.5") is in Y.
    """
    interior_L = PANEL_L - 2 * RAIL_T   # 94
    interior_W = PANEL_W - 2 * RAIL_T   # 41.6
    diagonal = math.sqrt(interior_L ** 2 + interior_W ** 2)  # ~102.8
    # Use 102" (round to even inch)
    brace_L = 102.0

    # Place a 2x4 box of length brace_L along the X axis, then rotate about Y
    # to match the diagonal angle. The angle from the +X axis is:
    angle_rad = math.atan2(interior_W, interior_L)  # = atan2(41.6, 94) ≈ 23.86°
    angle_deg = math.degrees(angle_rad)

    # Build the brace centered at origin, lying along +X
    brace = box(brace_L, BRACE_T, BRACE_H,
                x=-brace_L / 2.0, y=0, z=-BRACE_H / 2.0)

    # Rotate in the X-Z plane (around Y axis) by angle_deg
    brace = brace.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), angle_deg)

    # Place it inside the frame, sitting on top of the south wall (y=14.25),
    # and below the panel so the panel can sit on it. Actually, the brace
    # is a structural member, so put it just above the frame bottom.
    brace_y = FRAME_Y_BOTTOM + RAIL_T   # just above the bottom of the rails (in the 5.5" height)
    # Translate to the center of the frame at this y
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
