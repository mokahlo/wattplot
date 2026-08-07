"""
Frame geometry calculator — derives the frame rail and brace dimensions
from the bed + panel dimensions. This is the single source of truth for
the wood frame sizing.

The wood frame sits on top of the bed's south wall. The frame is a
rectangle that:
  - Has 2 long rails parallel to the bed length (north and south sides)
  - Has 2 cross rails perpendicular, between the long rails
  - Has 1 diagonal brace inside the frame, square ends butting into the
    inside faces of the long rails

The cross rail length is set to fit between the long rails cleanly with
a small overlap. The brace length is the diagonal of the inside rectangle.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.freecad.materials import LUMBER


def compute_frame_dimensions(bed_L_in, bed_W_in, wall_thk_in=1.5, rail_thk_in=1.5):
    """Derive the frame rail and brace dimensions from the bed size.

    Args:
        bed_L_in: bed outer length in inches
        bed_W_in: bed outer width in inches
        wall_thk_in: bed wall thickness in inches (default 1.5 for 2x lumber)
        rail_thk_in: frame rail thickness in inches (default 1.5 for 2x6)

    Returns:
        dict with:
            'long_rail_L': length of the long rails (X direction)
            'long_rail_thk': rail thickness in Z direction
            'long_rail_height': rail height in Y direction
            'cross_rail_L': length of the cross rails (Z direction)
            'cross_rail_thk': rail thickness in X direction
            'cross_rail_height': rail height in Y direction
            'brace_L': length of the diagonal brace
            'frame_outer_L': frame outer length (= bed_L)
            'frame_outer_W': frame outer width (= bed_W)
            'frame_interior_L': inside length (= bed_L - 2*rail_thk)
            'frame_interior_W': inside width (= bed_W - 2*rail_thk)
            'frame_z_offset': Z position of long rails (signed)
            'frame_x_offset': X position of cross rails (signed)
    """
    # Long rails: full bed length (run along X, parallel to bed length)
    long_rail_L = bed_L_in
    long_rail_thk = rail_thk_in
    long_rail_height = LUMBER["2x6"]["actual_h"]  # 5.5"

    # Cross rails: fit between the long rails. The cross rail sits ON TOP
    # of the long rail, with the long rail inner faces at z = ±(bed_W/2 - rail_thk).
    # The cross rail extends from z = -bed_W/2 to z = +bed_W/2 (full bed width,
    # so it caps the end of the bed). Length = bed_W.
    cross_rail_L = bed_W_in
    cross_rail_thk = rail_thk_in
    cross_rail_height = LUMBER["2x6"]["actual_h"]  # 5.5"

    # Diagonal brace: from corner to corner of the frame's interior
    interior_L = bed_L_in - 2 * rail_thk_in
    interior_W = bed_W_in - 2 * rail_thk_in
    brace_L = math.sqrt(interior_L**2 + interior_W**2)

    return {
        "long_rail_L": long_rail_L,
        "long_rail_thk": long_rail_thk,
        "long_rail_height": long_rail_height,
        "cross_rail_L": cross_rail_L,
        "cross_rail_thk": cross_rail_thk,
        "cross_rail_height": cross_rail_height,
        "brace_L": brace_L,
        "frame_outer_L": bed_L_in,
        "frame_outer_W": bed_W_in,
        "frame_interior_L": interior_L,
        "frame_interior_W": interior_W,
        "frame_z_offset": bed_W_in / 2.0,
        "frame_x_offset": bed_L_in / 2.0,
    }


def compute_bed_dimensions(bed_L_in, bed_W_in, wall_thk_in=1.5,
                            skid_h_in=3.0, post_t_in=3.5,
                            wall_h_in=27.5, cap_t_in=1.5):
    """Derive the bed (planter) wall and skid dimensions.

    The bed is built as: 4 corner posts (4x4) at the outside corners,
    walls fitting between the posts, and 2 skids under the long walls.
    So the wall length is bed_outer - 2*post_t (walls fit between posts).

    Args:
        bed_L_in: bed outer length in inches
        bed_W_in: bed outer width in inches
        wall_thk_in: bed wall thickness in inches
        skid_h_in: skid height in inches (bed sits on top of skids)
        post_t_in: corner post thickness in inches (4x4 actual = 3.5)
        wall_h_in: wall height in inches (1x6 cedar, 5 courses = 27.5
                    for the full-size build; was 4 courses = 22.0 in v1)
        cap_t_in: 2x6 cap thickness in inches (1.5)

    Returns:
        dict with long_wall_L, short_wall_L, skid_L, post_top_y, etc.
    """
    return {
        "long_wall_L": bed_L_in - 2 * post_t_in,    # between posts
        "short_wall_L": bed_W_in - 2 * post_t_in,   # between posts
        "skid_L": bed_L_in,                          # full bed length
        "skid_thk": LUMBER["4x4"]["actual_t"],      # 3.5
        "skid_h": skid_h_in,
        "wall_thk": wall_thk_in,
        "wall_h": wall_h_in,
        "cap_t": cap_t_in,
        "post_t": post_t_in,
        "post_top_y": skid_h_in + wall_h_in + cap_t_in + 0.5,  # panel support
        "frame_y_bottom": skid_h_in + wall_h_in,
    }


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    test_beds = [
        ("LONGi 620W", 96.0, 44.6),
        ("60-cell", 65.0, 39.0),
        ("72-cell", 77.0, 39.0),
        ("96-cell", 65.0, 41.0),
        ("Custom 70x42", 71.0, 43.0),
    ]

    for name, L, W in test_beds:
        print(f"\n{name} (bed {L}\" x {W}\")")
        print("-" * 50)
        bed = compute_bed_dimensions(L, W)
        frame = compute_frame_dimensions(L, W)
        print(f"  Bed:")
        print(f"    long wall L:   {bed['long_wall_L']:.1f}\"")
        print(f"    short wall L:  {bed['short_wall_L']:.1f}\"")
        print(f"    skid L:        {bed['skid_L']:.1f}\"")
        print(f"    frame y_bot:   {bed['frame_y_bottom']:.2f}\"")
        print(f"  Frame:")
        print(f"    long rail L:   {frame['long_rail_L']:.1f}\"")
        print(f"    cross rail L:  {frame['cross_rail_L']:.1f}\"")
        print(f"    brace L:       {frame['brace_L']:.2f}\" "
              f"(from {L-3:.1f} x {W-3:.1f} interior)")
        # Source board check
        if frame['long_rail_L'] <= 96:
            print(f"    long rail fits in 8-ft stock, "
                  f"waste {96 - frame['long_rail_L']:.1f}\"")
        else:
            print(f"    long rail needs 10-ft stock")
        if frame['cross_rail_L'] <= 48:
            cuts_per_8ft = 96 / frame['cross_rail_L']
            print(f"    cross rail: {cuts_per_8ft:.1f} per 8-ft board")
        if frame['brace_L'] <= 96:
            print(f"    brace fits in 8-ft stock, waste {96 - frame['brace_L']:.1f}\"")
        elif frame['brace_L'] <= 120:
            print(f"    brace needs 10-ft stock, waste {120 - frame['brace_L']:.1f}\"")
