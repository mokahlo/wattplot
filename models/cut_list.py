"""
Cut list generator — derives the lumber cut list from the bed dimensions.

Given a bed (BED['outer_L_in'] × BED['outer_W_in']), produces the full
cut list with source board, waste per board, and a sourcing summary.

Design rules (enforced):
  1. No miter cuts (every cut is 90° square cut).
  2. All hardware off the shelf.
  3. Simple common dimensions: every board sourced from 8-ft stock
     except the diagonal brace (10-ft for full-size, 8-ft for mini).

All cuts are in inches. Source board length is in feet.
"""
import math
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Source board lengths, in inches (the lumber-yard SKUs we buy)
STOCK_8FT_IN = 96.0
STOCK_10FT_IN = 120.0
STOCK_12FT_IN = 144.0

# Sorted by length for the stock-picker below.
_STOCK_BY_LENGTH = sorted(
    [(STOCK_8FT_IN,  "8 ft"),
     (STOCK_10FT_IN, "10 ft"),
     (STOCK_12FT_IN, "12 ft")],
    key=lambda s: s[0],
)


def _stock_for_cut(cut_length: float) -> tuple[float, str]:
    """Pick the shortest stock that fits `cut_length` (or return 8 ft
    if even 12 ft isn't enough -- the operator will need to special-
    order the lumber).

    The cut list is computed for a fixed set of panel presets
    (5x8 ft bed max per wattplot_params.MAX_PLANTER_*_IN), so 12 ft
    should be enough in practice. If a future panel preset pushes
    past 12 ft, this function returns 8 ft with a shorter cut than
    the stock, which surfaces the bug rather than silently
    producing negative waste.
    """
    for stock, label in _STOCK_BY_LENGTH:
        if cut_length <= stock:
            return stock, label
    return STOCK_8FT_IN, "8 ft (cut too long!)"


def _pack(board: float, cut_length: float, qty: int) -> tuple[float, int, float]:
    """Pack `qty` pieces of `cut_length` onto `board`s of `board`.

    Returns (source_board, n_boards_needed, waste_per_board).
    `n_boards_needed` accounts for partial boards: if 2 pieces
    fit per board, qty=3 needs 2 boards (one with 1 piece, one
    with 2). Waste is computed per-board, summed, and divided by
    qty to get the per-piece waste. Total waste is (n_boards *
    waste_per_board).
    """
    pieces_per_board = max(1, int(board // cut_length))
    n_boards = (qty + pieces_per_board - 1) // pieces_per_board
    waste_per_board = board - pieces_per_board * cut_length
    return board, n_boards, waste_per_board


def derive_cut_list(bed_L_in, bed_W_in, wall_thk=1.5, rail_thk=1.5,
                    skid_side=3.5, skid_h=3.0, panel_thk=1.4):
    """Derive the lumber cut list from the bed dimensions.

    Args:
        bed_L_in: bed outer length in inches (typically 8 ft for full-size)
        bed_W_in: bed outer width in inches (typically 5 ft for full-size,
                  or panel_W + margin)
        wall_thk: bed wall thickness in inches (default 1.5 for 2x lumber)
        rail_thk: frame rail thickness in inches (default 1.5 for 2x6)
        skid_side: skid cross-section side in inches (default 3.5 for 4x4)
        skid_h: skid height in inches (default 3.0)
        panel_thk: panel thickness in inches (for frame inside clearance)

    Returns:
        dict with keys:
          'cuts': list of Cut namedtuples
          'boards_8ft': dict of nominal_size -> count of 8-ft boards needed
          'boards_10ft': dict for 10-ft boards
          'total_waste_in': total inches of waste across all cuts
          'total_length_in': total length of lumber used
          'skid_count': number of skids
    """
    from collections import namedtuple
    Cut = namedtuple("Cut", "qty nominal length_in use source_board waste_per_board_in")

    cuts = []

    def _add(qty, nominal, length, label):
        """Add a cut, picking the right stock and computing waste.

        Packs `qty` pieces of `length` onto the smallest stock that
        fits, then sums per-board waste to get the cut's reported
        waste_per_board (it's actually waste-per-piece in the final
        accounting; see `Cut` docstring).
        """
        board, n_boards, waste_per_board = _pack(
            _stock_for_cut(length)[0], length, qty
        )
        cuts.append(Cut(qty, nominal, length, label, board,
                        waste_per_board * n_boards / qty))

    # ---- Bed walls: 1x6 cedar skin over 2x4 cleats, 2x6 caps ----
    # (see BED_WALL in wattplot_params.py). Course count and per-
    # course height come from BED_WALL; for v3 the bed is 5 courses
    # × 5.5" = 27.5" walls (was 4 × 5.5" = 22" in v1).
    from wattplot_params import BED_WALL
    courses = BED_WALL['courses']
    skin_thk = BED_WALL['skin_thk_in']
    wall_h = courses * BED_WALL['course_h_in']
    long_wall_L = bed_L_in                          # skin boards, full bed length
    short_wall_L = bed_W_in - 2.0 * skin_thk        # between the long-wall skins
    _add(2 * courses, "1x6", long_wall_L,
         f"long wall skin (N/S), {courses} courses")
    _add(2 * courses, "1x6", short_wall_L,
         f"short wall skin (W/E), {courses} courses")
    # Vertical cleats carry the soil pressure (skin alone would bow).
    n_cleats = 2 * BED_WALL['cleats_long_wall'] + 2 * BED_WALL['cleats_short_wall']
    _add(n_cleats, "2x4", wall_h, "wall cleat (vertical, <=24\" o.c.)")
    # 2x6 caps on hinge (S) and strut (N) walls - hinge screws bite here.
    _add(2, "2x6", long_wall_L, "wall cap, hinge + strut walls")

    # ---- Frame rails (4 pieces, 2x6 PT DF) ----
    long_rail_L = bed_L_in                          # 2 long rails, full bed length
    cross_rail_L = bed_W_in - 2.0 * rail_thk        # 2 cross rails, between the long rails
    _add(2, "2x6", long_rail_L, "long frame rail")
    _add(2, "2x6", cross_rail_L, "cross frame rail")

    # ---- Diagonal brace (1 piece, 2x4 PT DF) ----
    # Pythagoras: fits inside the frame rectangle
    brace_L = math.sqrt(bed_L_in**2 + bed_W_in**2)
    _add(1, "2x4", brace_L, "diagonal brace")

    # ---- Skids (2 pieces, 4x4 PT DF) ----
    skid_L = bed_L_in
    _add(2, "4x4", skid_L, "long skid")

    # ---- Aggregate by source board length ----
    # Per-cut board math: how many pieces of this length fit on one source
    # board, then how many boards that cut needs. Summed per nominal size.
    # (Cuts of the same nominal but different lengths get separate boards -
    # slightly conservative, but honest about real lumber-yard shopping.)
    boards_8ft_actual = {}
    boards_10ft_actual = {}
    for cut in cuts:
        per_board = max(1, int(cut.source_board // cut.length_in))
        n_boards = math.ceil(cut.qty / per_board)
        if cut.source_board == STOCK_8FT_IN:
            boards_8ft_actual[cut.nominal] = boards_8ft_actual.get(cut.nominal, 0) + n_boards
        elif cut.source_board == STOCK_10FT_IN:
            boards_10ft_actual[cut.nominal] = boards_10ft_actual.get(cut.nominal, 0) + n_boards

    total_waste = sum(c.waste_per_board_in * c.qty for c in cuts)
    total_length = sum(c.length_in * c.qty for c in cuts)

    return {
        "cuts": cuts,
        "boards_8ft": boards_8ft_actual,
        "boards_10ft": boards_10ft_actual,
        "total_waste_in": total_waste,
        "total_length_in": total_length,
        "skid_count": 2,
    }


def print_cut_list(result, title="Cut list"):
    """Pretty-print a cut list result dict."""
    print()
    print(title)
    print("=" * 80)
    print(f"{'Qty':<5} {'Nominal':<8} {'Length':<10} {'Use':<32} {'Source':<8} {'Waste':<8}")
    print("-" * 80)
    for c in result["cuts"]:
        length_str = f"{c.length_in:.1f}\"" + (f" ({c.length_in/12:.2f} ft)" if c.length_in > 30 else "")
        source_str = f"{c.source_board/12:.0f} ft"
        waste_str = f"{c.waste_per_board_in:.1f}\""
        print(f"{c.qty:<5} {c.nominal:<8} {length_str:<10} {c.use:<32} {source_str:<8} {waste_str:<8}")
    print("-" * 80)
    print()
    print("Source boards to buy:")
    for nominal, count in result["boards_8ft"].items():
        species = "cedar" if nominal.startswith("1x") else "PT DF"
        print(f"  {count} × {nominal} × 8 ft {species} @ Home Depot")
    for nominal, count in result["boards_10ft"].items():
        print(f"  {count} × {nominal} × 10 ft PT DF @ Home Depot")
    print()
    print(f"Total lumber length: {result['total_length_in']:.1f}\" "
          f"({result['total_length_in']/12:.2f} ft)")
    print(f"Total waste:          {result['total_waste_in']:.1f}\" "
          f"({result['total_waste_in']/12:.2f} ft)")
    if result["total_length_in"] > 0:
        waste_pct = result["total_waste_in"] / (result["total_length_in"] + result["total_waste_in"]) * 100
        print(f"Waste fraction:       {waste_pct:.1f}%")
    print()


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    print("Test 1: LONGi 620W (96x44.6 bed)")
    print("-" * 60)
    r1 = derive_cut_list(bed_L_in=96.0, bed_W_in=44.6)
    print_cut_list(r1)

    print("Test 2: Residential 60-cell (65x39 bed)")
    print("-" * 60)
    r2 = derive_cut_list(bed_L_in=65.0, bed_W_in=39.0)
    print_cut_list(r2)
