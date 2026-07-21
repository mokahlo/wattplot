"""
Hinges — 4 × galvanized butt hinges, 4"×4" leaf, ½" pin.

Each hinge has two leaves and a knuckle (the cylindrical pin housing).
In the model, each leaf is a thin box. The pin is a cylinder along X.
4 hinges are spaced evenly along the 88.5" hinge axis.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED, FRAME
from models.freecad.materials import LUMBER, HARDWARE
from models.freecad.parts._helpers import box, cylinder, add_feature

import FreeCAD as App
import Part


# Hinge placement
H = HARDWARE["butt_hinge_4x4"]
LEAF_W = H["leaf_W_in"]    # 4.0 (Z direction, perpendicular to hinge axis)
LEAF_L = H["leaf_L_in"]    # 4.0 (X direction, along hinge axis)
LEAF_T = H["leaf_t_in"]    # 0.075
PIN_D = H["pin_d_in"]      # 0.5

HINGE_COUNT = H["count"]   # 4
HINGE_SPACING = FRAME["hinge"]["spacing_in"]   # 22.0

# Hinge axis runs along X at the top of the south wall.
# Wall top is at y = SKID_H + WALL_H = 14.25
# Hinge center is at the OUTER face of the south wall, z = +22.3
WALL_T = LUMBER["2x12"]["actual_t"]
WALL_H = LUMBER["2x12"]["actual_h"]
SKID_H = BED["skid_h_in"]

HINGE_Y_CENTER = SKID_H + WALL_H   # 14.25 (top of south wall)
HINGE_Z_CENTER = +BED["outer_W_in"] / 2.0  # +22.3 (outer face of south wall)


def make_hinge(doc, x_pos, name=None):
    """Create one butt hinge at the given X position along the hinge axis.

    The hinge has two leaves:
      - Frame leaf: above the wall (attached to the bottom of the frame's
        south long rail)
      - Wall leaf: on the outer face of the south wall (lag-bolted to the wall)
    The knuckle (with the pin) is at the wall's outer face, so the pin sits
    at z=HINGE_Z_CENTER, y=HINGE_Y_CENTER.

    Returns a Compound of (frame_leaf, wall_leaf, pin).
    """
    if name is None:
        name = f"Hinge_{x_pos:.0f}"

    # Frame leaf: just above the wall top, on the +Z side of the rail
    # The rail's bottom is at y=14.25, so the frame leaf sits at y=14.25
    # but slightly into the rail. For visualization, place it on TOP of the wall.
    frame_leaf = box(LEAF_L, LEAF_W, LEAF_T,
                     x=x_pos - LEAF_L / 2.0,
                     y=HINGE_Y_CENTER,
                     z=HINGE_Z_CENTER - LEAF_T)  # leaf thickness extends from z=22.3 to z=22.225

    # Wall leaf: on the outer face of the south wall (z=+22.3 to +22.3+LEAF_T=+22.375)
    # Actually, the wall leaf is attached to the wall's TOP face (y=14.25), with
    # the leaf body extending downward. But the leaf is wider than the wall is tall
    # in the Y direction. So place the wall leaf on the outer face of the wall.
    # Hmm, actually butt hinges go on the EDGE of a door. The "wall" side leaf
    # is mounted on the jamb (the top of the south wall in our case), and the
    # "frame" side leaf is mounted on the door (the bottom of the frame rail).
    # Both leaves wrap around the hinge knuckle.
    #
    # For our purposes, simplify: both leaves are thin (LEAF_T = 0.075)
    # rectangles meeting at the knuckle line. The knuckle is at the OUTER edge
    # of the south wall (z=22.3, y=14.25), and the leaves extend in -Z and -Y.
    # Wall leaf: extends in -Y from the knuckle, sitting flat on the wall top.
    # Frame leaf: extends in -Z from the knuckle, sitting on the south face of the rail.
    #
    # For visualization, just place both leaves as small boxes meeting at the knuckle.
    wall_leaf = box(LEAF_L, LEAF_T, LEAF_W,
                    x=x_pos - LEAF_L / 2.0,
                    y=HINGE_Y_CENTER - LEAF_W,  # leaf extends DOWN from the top
                    z=HINGE_Z_CENTER)            # leaf at the outer face

    # Pin (cylinder along X, with diameter PIN_D)
    pin = cylinder(PIN_D / 2.0, LEAF_L * 0.8,
                   x=x_pos - LEAF_L * 0.4,
                   y=HINGE_Y_CENTER,
                   z=HINGE_Z_CENTER,
                   axis="X")

    compound = Part.makeCompound([frame_leaf, wall_leaf, pin])
    return add_feature(doc, name, compound)


def make_all_hinges(doc, name="HingeSet"):
    """Create all 4 hinges evenly spaced along the hinge axis.

    Hinge axis runs from x=-44 to x=+44 (so the hinges are inside the bed length,
    with some margin). With 4 hinges and 22" spacing, x positions are:
        -33, -11, +11, +33  (centered on the bed)
    """
    # Total hinge axis length: 88" (same as long rail length, FRAME['long_rail']['length_in'])
    axis_len = FRAME["long_rail"]["length_in"]
    # Place hinges at positions: -axis_len/2 + spacing/2, ..., +axis_len/2 - spacing/2
    # For 4 hinges with axis_len=88.5 and spacing=22.0:
    # Total span = 3 * 22.0 = 66", centered on 0, so x in [-33, +33]
    half_span = (HINGE_COUNT - 1) * HINGE_SPACING / 2.0
    x_positions = [-half_span + i * HINGE_SPACING for i in range(HINGE_COUNT)]
    # = [-33, -11, +11, +33]

    hinges = []
    for x in x_positions:
        hinges.append(make_hinge(doc, x))
    compound = Part.makeCompound([h.Shape for h in hinges])
    obj = add_feature(doc, name, compound)
    return obj, hinges


if __name__ == "__main__":
    doc = App.newDocument("test_hinges")
    h, hinges = make_all_hinges(doc)
    doc.recompute()
    print(f"  Hinge set: vol={h.Shape.Volume:.2f} in^3")
    for hi in hinges:
        bb = hi.Shape.BoundBox
        print(f"    {hi.Name}: bbox X=[{bb.XMin:.1f},{bb.XMax:.1f}], Y=[{bb.YMin:.2f},{bb.YMax:.2f}], Z=[{bb.ZMin:.2f},{bb.ZMax:.2f}]")
