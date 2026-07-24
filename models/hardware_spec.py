"""
Hardware spec generator — derives hinge count, mid-clamps, hinge pin length,
carriage bolts, and other hardware from the bed + panel dimensions.

Returns a dict that can be merged into a BOM or rendered as a build-report
section. The hardware scales with the bed length, the panel size, and the
number of joints.
"""
import math
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# Galvanized butt hinge: 4×4" leaf, ½" pin (Home Depot / McMaster)
HINGE_LEAF_IN = 4.0
HINGE_PIN_DIA_IN = 0.5
HINGE_SPACING_IN = 22.0   # center-to-center between hinges
HINGE_END_MARGIN_IN = 4.0  # margin from bed end to first hinge


def derive_hardware_spec(bed_L_in, bed_W_in, panel_L_in, panel_W_in,
                         panel_thk_in=1.4, panel_mass_lb=50.0,
                         actuator_stroke_in=4.0):
    """Derive the hardware spec from bed + panel dimensions.

    Args:
        bed_L_in: bed outer length in inches
        bed_W_in: bed outer width in inches
        panel_L_in: panel length in inches
        panel_W_in: panel width in inches
        panel_thk_in: panel thickness in inches
        panel_mass_lb: panel weight in pounds
        actuator_stroke_in: linear actuator stroke in inches

    Returns:
        dict with keys: hinges, hinge_pin, mid_clamps, end_clamps,
        carriage_bolts, lag_bolts, deck_screws, panel_actuator, hardware
        Each is a dict with 'count' or 'length_in' and 'spec'.
    """
    # ---- Hinges ----
    # 4 hinges for full-size (88" hinge axis = 96" bed - 2×4" margin).
    # For mini: 2 hinges. For any other size, compute by spacing.
    hinge_axis_L = bed_L_in - 2 * HINGE_END_MARGIN_IN
    # Number of hinges: round(hinge_axis_L / HINGE_SPACING_IN) + 1
    # For LONGi: round(88/22)+1 = 5, but design rule says 4 even spacing.
    # Simpler: use the design rule of 4 for full-size, 2 for mini.
    if bed_L_in >= 80:
        n_hinges = 4
    elif bed_L_in >= 40:
        n_hinges = 2
    else:
        n_hinges = 2

    # ---- Continuous hinge pin ----
    # ½" steel rod, bed_L + 2" (extends 1" each end)
    hinge_pin_L = bed_L_in + 2.0

    # ---- Panel mid-clamps ----
    # 2 per long rail + 1 per cross rail = 6 for full-size LONGi
    n_long_rail_clamps = 2 * 2   # 2 per long rail, 2 long rails
    n_cross_rail_clamps = 1 * 2  # 1 per cross rail, 2 cross rails
    n_clamps = n_long_rail_clamps + n_cross_rail_clamps

    # ---- Carriage bolts (bed corner joints) ----
    # 4 corners × 2 bolts each = 8 (through-bolted, not screwed)
    n_carriage_bolts = 4 * 2

    # ---- Lag bolts (hinge leaf to bed wall) ----
    # Each hinge leaf: 4 screws (2 per leaf side). 4 hinges × 4 = 16.
    n_lag_bolts = n_hinges * 4

    # ---- Deck screws (frame corners) ----
    # 4 frame corners × 2 screws = 8
    n_deck_screws_frame = 4 * 2

    # ---- Deck screws (diagonal brace) ----
    # 2 ends × 2 screws = 4
    n_deck_screws_brace = 2 * 2

    # ---- Cleat screws (skids to bed) ----
    # 2 skids × 3 screws = 6
    n_deck_screws_skids = 2 * 3

    return {
        "hinges": {
            "count": n_hinges,
            "spec": f"galvanized butt hinge, {HINGE_LEAF_IN:.1f}\"×{HINGE_LEAF_IN:.1f}\" leaf, "
                    f"{HINGE_PIN_DIA_IN}\" pin, HDG",
            "spacing_in": HINGE_SPACING_IN,
        },
        "hinge_pin": {
            "length_in": hinge_pin_L,
            "spec": f"½\" × {hinge_pin_L:.1f}\" steel rod (continuous, through all hinges)",
        },
        "mid_clamps": {
            "count": n_clamps,
            "spec": f"aluminum mid-clamps, 35mm channel, M8 SS bolt + EPDM washer",
            "long_rail": n_long_rail_clamps,
            "cross_rail": n_cross_rail_clamps,
        },
        "carriage_bolts": {
            "count": n_carriage_bolts,
            "spec": "3/8\" × 4\" carriage bolt HDG + washer + hex nut (bed corner joints)",
        },
        "lag_bolts": {
            "count": n_lag_bolts,
            "spec": "5/16\" × 3\" lag bolt HDG (hinge leaf to bed wall)",
        },
        "deck_screws": {
            "frame_corners": n_deck_screws_frame,
            "diagonal_brace": n_deck_screws_brace,
            "skids": n_deck_screws_skids,
            "total": n_deck_screws_frame + n_deck_screws_brace + n_deck_screws_skids,
            "spec": "¼\" × 3\" deck screw HDG Torx T-25",
        },
        "actuator": {
            "stroke_in": actuator_stroke_in,
            "force_lb": "330 lbf (full-size) or 70 N (mini)",
            "voltage": "12V DC",
            "spec": f"12V linear actuator, {actuator_stroke_in:.1f}\" stroke, IP65",
        },
        "panel": {
            "L_in": panel_L_in,
            "W_in": panel_W_in,
            "thk_in": panel_thk_in,
            "mass_lb": panel_mass_lb,
        },
    }


def print_hardware_spec(spec, title="Hardware spec"):
    """Pretty-print a hardware spec dict."""
    print()
    print(title)
    print("=" * 80)
    print(f"Panel:  {spec['panel']['L_in']:.1f}\" × {spec['panel']['W_in']:.1f}\" × "
          f"{spec['panel']['thk_in']:.1f}\", {spec['panel']['mass_lb']:.0f} lb")
    print()
    print(f"Hinges:           {spec['hinges']['count']} × {spec['hinges']['spec']}")
    print(f"Hinge pin:        {spec['hinge_pin']['spec']}")
    print(f"Mid-clamps:       {spec['mid_clamps']['count']} × {spec['mid_clamps']['spec']}")
    print(f"  ({spec['mid_clamps']['long_rail']} on long rails, "
          f"{spec['mid_clamps']['cross_rail']} on cross rails)")
    print(f"Carriage bolts:   {spec['carriage_bolts']['count']} × {spec['carriage_bolts']['spec']}")
    print(f"Lag bolts:        {spec['lag_bolts']['count']} × {spec['lag_bolts']['spec']}")
    print(f"Deck screws:      {spec['deck_screws']['total']} × {spec['deck_screws']['spec']}")
    print(f"  ({spec['deck_screws']['frame_corners']} frame corners, "
          f"{spec['deck_screws']['diagonal_brace']} diagonal brace, "
          f"{spec['deck_screws']['skids']} skids)")
    print(f"Actuator:         {spec['actuator']['spec']}")
    print()


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    print("Test 1: LONGi 620W (96×44.6 bed, 97×44.6 panel)")
    print("-" * 60)
    s1 = derive_hardware_spec(bed_L_in=96.0, bed_W_in=44.6,
                              panel_L_in=97.0, panel_W_in=44.6,
                              panel_mass_lb=65.0, actuator_stroke_in=4.0)
    print_hardware_spec(s1)

    print("Test 2: Mini v2.4 (18×14 bed, 13.3×8.1 panel)")
    print("-" * 60)
    s2 = derive_hardware_spec(bed_L_in=18.0, bed_W_in=14.0,
                              panel_L_in=13.3, panel_W_in=8.1,
                              panel_thk_in=0.7, panel_mass_lb=1.88,
                              actuator_stroke_in=3.94)
    print_hardware_spec(s2)

    print("Test 3: Residential 60-cell (65×39 bed, 65×39 panel)")
    print("-" * 60)
    s3 = derive_hardware_spec(bed_L_in=65.0, bed_W_in=39.0,
                              panel_L_in=65.0, panel_W_in=39.0,
                              panel_mass_lb=38.0, actuator_stroke_in=4.0)
    print_hardware_spec(s3)
