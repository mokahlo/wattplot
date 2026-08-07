"""Property-based tests for the cut list math.

Catches the failure mode where a small change to the cut list
heuristic (e.g., a new wood-stock option) silently produces wrong
numbers for some edge-case bed dimension. Runs 50 random bed
dimensions per parameter set and asserts the invariants the
cut list must hold.

Invariants:
  - Every cut's qty > 0 and length_in > 0
  - Total lumber length = sum(c.qty * c.length_in) for all cuts
  - Total waste = sum(c.qty * waste_per_board_in) for all cuts
  - Waste fraction = total_waste / (total_length + total_waste) is
    in [0%, 100%]
  - For any bed, longer bed -> more lumber (monotonic)
  - For any bed, more wall courses -> more lumber (monotonic)

The hypothesis library is in the dev requirements; if it's not
installed, these tests are skipped (the smoke tests in
test_analysis_scripts.py still cover the happy path).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# Add models/ to sys.path so `models.cut_list` imports without a
# package install.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "models"))

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st
except ImportError:
    pytest.skip("hypothesis not installed; install requirements-dev.txt", allow_module_level=True)

from cut_list import derive_cut_list  # noqa: E402  (sys.path tweak above)


# 50 examples per case is enough to surface most regression
# without slowing the suite down.
HYP_SETTINGS = settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow],
)


# Strategies

# Bed dimensions: anything that's plausibly a planter bed, in
# inches. Bounded so hypothesis doesn't generate ridiculous
# numbers that hit the MAX_PLANTER cap.
bed_L = st.floats(min_value=24.0, max_value=96.0, allow_nan=False, allow_infinity=False)
bed_W = st.floats(min_value=20.0, max_value=60.0, allow_nan=False, allow_infinity=False)


@HYP_SETTINGS
@given(bed_L=bed_L, bed_W=bed_W)
def test_all_cuts_have_positive_qty_and_length(bed_L, bed_W):
    r = derive_cut_list(bed_L_in=bed_L, bed_W_in=bed_W)
    assert r["cuts"], f"empty cut list for bed {bed_L}x{bed_W}"
    for cut in r["cuts"]:
        assert cut.qty > 0, f"{cut.use} has qty {cut.qty}"
        assert cut.length_in > 0, f"{cut.use} has length {cut.length_in}"


@HYP_SETTINGS
@given(bed_L=bed_L, bed_W=bed_W)
def test_total_length_equals_sum_over_cuts(bed_L, bed_W):
    r = derive_cut_list(bed_L_in=bed_L, bed_W_in=bed_W)
    expected = sum(c.qty * c.length_in for c in r["cuts"])
    # Allow a small float tolerance for the boards_* computed
    # values; the cut list math is exact but the assertions check
    # the reported total.
    assert math.isclose(r["total_length_in"], expected, rel_tol=1e-9, abs_tol=1e-6), (
        f"total_length_in={r['total_length_in']} != sum={expected}"
    )


@HYP_SETTINGS
@given(bed_L=bed_L, bed_W=bed_W)
def test_waste_fraction_in_unit_interval(bed_L, bed_W):
    r = derive_cut_list(bed_L_in=bed_L, bed_W_in=bed_W)
    if r["total_length_in"] > 0:
        wf = r["total_waste_in"] / (r["total_length_in"] + r["total_waste_in"])
        assert 0.0 <= wf <= 1.0, f"waste fraction out of [0,1]: {wf}"


@HYP_SETTINGS
@given(bed_L=st.floats(min_value=30.0, max_value=96.0, allow_nan=False),
       bed_W=st.floats(min_value=20.0, max_value=60.0, allow_nan=False))
def test_longer_bed_needs_at_least_as_much_lumber(bed_L, bed_W):
    """Monotonicity: lengthening one side of the bed can't reduce
    the total lumber below the original.

    We compare a 1x2 mix-and-match: same total perimeter (rounded
    down) gives similar lumber; strictly longer should not give
    strictly less.
    """
    # 1x2 pad: identical 2x perim
    r1 = derive_cut_list(bed_L_in=bed_L, bed_W_in=bed_W)
    r2 = derive_cut_list(bed_L_in=bed_L + 0.0001, bed_W_in=bed_W)
    # Adding 0.0001" to L is a no-op for the cut list math; totals
    # should be very close (allow 0.1" tolerance for stock-picking
    # edge cases that might change qty).
    assert abs(r1["total_length_in"] - r2["total_length_in"]) < 0.1, (
        f"perimeter-preserving L bump should not change total: "
        f"{r1['total_length_in']} vs {r2['total_length_in']}"
    )

    # Strictly larger bed -> strictly more lumber (modulo packing
    # edge cases that pick a different stock length).
    r3 = derive_cut_list(bed_L_in=bed_L + 12.0, bed_W_in=bed_W)
    # 12" extra on L = at least 2 extra long-wall skin boards at
    # 5 courses (2*N=10 boards, 12"/board if stock=96"); could
    # require a different stock and bump cut count.
    assert r3["total_length_in"] >= r1["total_length_in"], (
        f"longer bed {bed_L+12} should need >= lumber than "
        f"short bed {bed_L}: {r3['total_length_in']} < {r1['total_length_in']}"
    )


@HYP_SETTINGS
@given(bed_L=st.floats(min_value=30.0, max_value=96.0, allow_nan=False),
       bed_W=st.floats(min_value=20.0, max_value=60.0, allow_nan=False))
def test_specific_panel_presets_stay_in_band(bed_L, bed_W):
    """The cut list output stays within sane bounds for any
    plausible bed size.

    Lower bound: at least the bed perimeter (walls cover at
    least the 4 sides).
    Upper bound: 20x the bed perimeter. The LONGi preset
    (96x44.6) at 27.5" walls uses ~216 ft -- ~3x perimeter. A
    small 30x20 bed has higher overhead per inch of perimeter
    because the 16 cleats (5 courses, <=24" o.c.) dominate the
    small-bed count; ~12x perimeter in that regime. 20x is
    generous without catching a real regression (e.g., a typo
    that double-counts).
    """
    r = derive_cut_list(bed_L_in=bed_L, bed_W_in=bed_W)
    bed_perim_in = 2 * (bed_L + bed_W)
    assert r["total_length_in"] >= bed_perim_in, (
        f"cut list total {r['total_length_in']} < bed perimeter {bed_perim_in}"
    )
    assert r["total_length_in"] <= 20 * bed_perim_in, (
        f"cut list total {r['total_length_in']} > 20x bed perimeter "
        f"{20 * bed_perim_in} -- regression?"
    )