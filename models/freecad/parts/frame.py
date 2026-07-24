"""
Frame — 2x6 PT DF perimeter around the panel, plus 2x4 diagonal brace.

Design rules (enforced):
  1. NO MITER CUTS — all joints butt. Diagonal brace has square ends.
  2. ALL HARDWARE OFF THE SHELF — standard sizes, see materials.py.
  3. SIMPLE COMMON DIMENSIONS — long rails fit in 8-ft stock (no waste
     when bed is 8 ft), cross rails cut from 8-ft stock, diagonal brace
     from 2x4x10ft for full-size or 2x4x8ft for smaller builds.

Refactored: all rail dimensions are derived from the bed via
`models.frame_geometry.compute_frame_dimensions()`. This means the
frame adapts automatically when the panel preset changes (upcycling
workflow).

Geometry at 0° tilt (panel flat over the bed):
  - Frame exterior: bed_L (X) x bed_W (Z)
  - Frame interior: (bed_L - 2*rail_thk) x (bed_W - 2*rail_thk)
  - Long rails at z = +/- bed_W/2 (each 1.5" thick in Z, 5.5" tall in Y)
  - Cross rails at x = +/- bed_L/2 (each 1.5" thick in X, 5.5" tall in Y)
  - Diagonal brace: 2x4 PT, runs corner to corner inside the frame

The frame module builds it flat. assemble.py applies the tilt.
"""
import sys
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import BED
from models.freecad.materials import LUMBER
from models.freecad.parts.lumber import make_lumber
from models.frame_geometry import compute_frame_dimensions, compute_bed_dimensions
from models.freecad.parts._helpers import add_feature

import FreeCAD as App
import Part


# Bed dimensions (derived from wattplot_params)
BED_L = BED["outer_L_in"]
BED_W = BED["outer_W_in"]
from wattplot_params import BED_WALL
WALL_T = BED["wall_thk_in"]                            # 0.75 (1x6 skin)
_CAP_T = LUMBER[BED_WALL["cap_nominal"]]["actual_t"]   # 1.5 (2x6 flat cap)
WALL_H = BED["wall_h_in"] + _CAP_T                     # 23.5 (to cap top)

# Frame dimensions (derived from bed via frame_geometry)
_FRAME = compute_frame_dimensions(BED_L, BED_W, wall_thk_in=WALL_T)
_BED = compute_bed_dimensions(BED_L, BED_W, wall_thk_in=WALL_T,
                                skid_h_in=BED["skid_h_in"])

# Bottom of frame = top of bed's south wall = SKID_H + WALL_H
FRAME_Y_BOTTOM = _BED["frame_y_bottom"]


def make_frame_long_rail(doc, side="south", name=None):
    """Long rail on the south or north edge of the panel.

    side: "south" (z=+bed_W/2, hinged side) or "north" (z=-bed_W/2, actuator side)

    Rail is _FRAME['long_rail_L'] long (X), 1.5" thick (Z), 5.5" tall (Y),
    bottom at y=FRAME_Y_BOTTOM. The 2x6 is from 8-ft stock, no waste when
    bed_L = 96", otherwise wastes a bit of stock.
    """
    if name is None:
        name = f"FrameLongRail_{side}"
    if side not in ("south", "north"):
        raise ValueError(f"side must be 'north' or 'south', got {side!r}")

    z_outer = +BED_W / 2.0 if side == "south" else -BED_W / 2.0
    z_box = z_outer - _FRAME["long_rail_thk"] if side == "south" else z_outer

    rail = make_lumber(
        "2x6",
        length=_FRAME["long_rail_L"],
        axis="X",
        origin=(-_FRAME["long_rail_L"] / 2.0, FRAME_Y_BOTTOM, z_box),
    )
    return add_feature(doc, name, rail)


def make_frame_cross_rail(doc, side="east", name=None):
    """Cross rail on the east or west end of the panel.

    side: "east" (x=+bed_L/2) or "west" (x=-bed_L/2)

    Rail is 1.5" thick (X), 5.5" tall (Y), _FRAME['cross_rail_L'] long (Z),
    bottom at y=FRAME_Y_BOTTOM. Butt-jointed at both ends against the
    outside faces of the long rails (no miter).
    """
    if name is None:
        name = f"FrameCrossRail_{side}"
    if side not in ("east", "west"):
        raise ValueError(f"side must be 'east' or 'west', got {side!r}")

    x_box = (BED_L / 2.0) - _FRAME["cross_rail_thk"] if side == "east" else -BED_L / 2.0

    rail = make_lumber(
        "2x6",
        length=_FRAME["cross_rail_L"],
        axis="Z",
        origin=(x_box, FRAME_Y_BOTTOM, -_FRAME["cross_rail_L"] / 2.0),
    )
    return add_feature(doc, name, rail)


def make_diagonal_brace(doc, name="DiagonalBrace"):
    """2x4 PT diagonal brace, runs corner to corner inside the frame.

    Square ends butt into the inside faces of the long rails (no miter cut).
    Length is the diagonal of the frame's interior rectangle, computed by
    `compute_frame_dimensions()`.

    Interior dimensions:
      - X extent (between cross rails):  bed_L - 2*rail_thk
      - Z extent (between long rails):   bed_W - 2*rail_thk
    """
    interior_L = _FRAME["frame_interior_L"]
    interior_W = _FRAME["frame_interior_W"]
    brace_L = _FRAME["brace_L"]
    angle_rad = math.atan2(interior_W, interior_L)  # ~23.86° for LONGi

    # Build the brace centered at origin, lying along +X
    brace = make_lumber(
        "2x4",
        length=brace_L,
        axis="X",
        origin=(-brace_L / 2.0, FRAME_Y_BOTTOM + 0.5, -LUMBER["2x4"]["actual_h"] / 2.0),
    )
    # Rotate in the X-Z plane (around Y axis) by angle
    brace = brace.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0),
                          math.degrees(angle_rad))
    return add_feature(doc, name, brace)


# ---- combined: frame as a single compound ---------------------------------

def make_frame_assembly(doc, name="FrameAssembly"):
    """Build the whole frame (4 rails + brace) as a single Part::Feature
    using a Compound. Returns (compound, [parts]).
    """
    south = make_frame_long_rail(doc, "south")
    north = make_frame_long_rail(doc, "north")
    east = make_frame_cross_rail(doc, "east")
    west = make_frame_cross_rail(doc, "west")
    brace = make_diagonal_brace(doc)

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
    bb = f.Shape.BoundBox
    print(f"  Frame bbox: X[{bb.XMin:.1f}, {bb.XMax:.1f}] "
          f"Y[{bb.YMin:.1f}, {bb.YMax:.1f}] Z[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")
    print(f"  Individual parts:")
    for p in parts:
        bb = p.Shape.BoundBox
        print(f"    {p.Name}: {bb.XLength:.1f}×{bb.YLength:.1f}×{bb.ZLength:.1f}")
