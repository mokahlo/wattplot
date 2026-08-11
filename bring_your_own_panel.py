"""
Bring your own panel — the upcycling front door.

Takes a panel spec (any dimensions, any age, any wattage) and produces
a complete build report: bed size, lumber cut list, hardware spec,
MPPT recommendation, model output, and a one-page "build it" summary.

Usage:
    python bring_your_own_panel.py --L 66 --W 39 --wattage 250 --age 12
    python bring_your_own_panel.py --L 97 --W 44.6 --wattage 620 --bifacial
    python bring_your_own_panel.py --list-presets

The default --L 97 --W 44.6 --wattage 620 matches the LONGi 620W preset.
Use this as a "drop in your real panel" command before you go to Home Depot.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "models"))
sys.path.insert(0, os.path.join(HERE, "analysis"))

import wattplot_params as P
from models.cut_list import derive_cut_list, print_cut_list
from models.hardware_spec import derive_hardware_spec, print_hardware_spec


def banner(text, char="=", width=80):
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)


def recommend_mppt(panel_W, panel_Imp=None, age_years=0):
    """Pick an MPPT charge controller sized to the panel.

    Args:
        panel_W: panel nameplate wattage
        panel_Imp: panel current at max power (amps). Estimated if not given.
        age_years: panel age (for derate)

    Returns:
        dict with 'model', 'p_v_max', 'i_max', 'cost_estimate', 'rationale'
    """
    # Estimate Imp if not given (typical: 8A for 250W panel, 10A for 400W)
    if panel_Imp is None:
        # Rough rule: ~6A per 200W for 12V panels
        panel_Imp = max(6.0, panel_W / 30.0)
    if age_years > 0:
        derate = max(0.70, 1.0 - 0.005 * age_years)
        panel_W_actual = panel_W * derate
    else:
        panel_W_actual = panel_W

    if panel_W_actual <= 50:
        return {
            "model": "Sunapex 10A MPPT (HC-SM10A)",
            "p_v_max": 45.0,
            "i_max": 10.0,
            "cost_estimate": "$25",
            "rationale": f"10A MPPT is enough for {panel_W_actual:.0f}W panel "
                          f"(estimated Imp = {panel_Imp:.1f}A)",
        }
    elif panel_W_actual <= 200:
        return {
            "model": "Victron SmartSolar 100/20 or EPEver Tracer 2210AN",
            "p_v_max": 100.0,
            "i_max": 20.0,
            "cost_estimate": "$100-150",
            "rationale": f"20A MPPT sized for {panel_W_actual:.0f}W panel "
                          f"(estimated Imp = {panel_Imp:.1f}A)",
        }
    elif panel_W_actual <= 400:
        return {
            "model": "Victron SmartSolar 100/30 or EPEver Tracer 3210AN",
            "p_v_max": 100.0,
            "i_max": 30.0,
            "cost_estimate": "$150-200",
            "rationale": f"30A MPPT sized for {panel_W_actual:.0f}W panel "
                          f"(estimated Imp = {panel_Imp:.1f}A)",
        }
    else:  # 400+
        return {
            "model": "Victron SmartSolar 100/50 or EPEver Tracer 4210AN",
            "p_v_max": 100.0,
            "i_max": 50.0,
            "cost_estimate": "$200-300",
            "rationale": f"50A MPPT sized for {panel_W_actual:.0f}W panel "
                          f"(estimated Imp = {panel_Imp:.1f}A)",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Bring your own panel — generate a complete build report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python bring_your_own_panel.py --L 66 --W 39 --wattage 250 --age 12
      (12-year-old 60-cell residential, 235W derated)

  python bring_your_own_panel.py --L 97 --W 44.6 --wattage 620
      (LONGi 620W bifacial, no derate)

  python bring_your_own_panel.py --list-presets
      (show the named presets for easy copy-paste)
""",
    )
    parser.add_argument("--L", type=float, help="Panel length in inches (with frame)")
    parser.add_argument("--W", type=float, help="Panel width in inches (with frame)")
    parser.add_argument("--wattage", type=float, help="Panel nameplate wattage (new)")
    parser.add_argument("--age", type=float, default=0, help="Panel age in years (default 0 = new)")
    parser.add_argument("--bifacial", action="store_true", help="Panel is bifacial (default: monofacial)")
    parser.add_argument("--mass", type=float, default=None, help="Panel mass in lb (estimated from wattage if not given)")
    parser.add_argument("--thickness", type=float, default=1.4, help="Panel thickness in inches (default 1.4)")
    parser.add_argument("--name", type=str, default="custom", help="Name for this panel (used in output files)")
    parser.add_argument("--list-presets", action="store_true", help="List named panel presets")
    parser.add_argument("--preset", type=str, help="Use a named preset (overrides --L/--W/etc.)")
    args = parser.parse_args()

    if args.list_presets:
        banner("Named panel presets (drop in for --L/--W/--wattage/--age)")
        for name, p in P.PANEL_PRESETS.items():
            label = p.get("label", name)
            print(f"  {name}")
            print(f"    {label}")
            print(f"    {p['L_in']}\" × {p['W_in']}\" ({p['L_in']/12:.2f} × {p['W_in']/12:.2f} ft), "
                  f"{p['wattage']}W nameplate, {p.get('panel_age_years', 0)} yr old, "
                  f"{'bifacial' if p.get('panel_bifacial', False) else 'monofacial'}")
            print()
        return

    # Apply preset if given
    if args.preset:
        if args.preset not in P.PANEL_PRESETS:
            print(f"Unknown preset: {args.preset!r}. Use --list-presets.")
            sys.exit(1)
        P.apply_panel_preset(args.preset)
        panel_L = P.PANEL["L_in"]
        panel_W = P.PANEL["W_in"]
        panel_wattage = P.PANEL["wattage"]
        panel_age = P.PANEL.get("panel_age_years", 0)
        panel_bifacial = P.PANEL.get("panel_bifacial", False)
        panel_mass = P.PANEL.get("mass_lb", 50.0)
        panel_thk = P.PANEL.get("thickness_in", 1.4)
        name = args.preset
    else:
        # Require at least L, W, wattage
        if not (args.L and args.W and args.wattage):
            print("Error: --L, --W, --wattage are required (or use --preset / --list-presets)")
            parser.print_help()
            sys.exit(1)
        panel_L = args.L
        panel_W = args.W
        panel_wattage = args.wattage
        panel_age = args.age
        panel_bifacial = args.bifacial
        panel_mass = args.mass if args.mass else max(20, panel_wattage * 0.1)
        panel_thk = args.thickness
        name = args.name
        # Apply to wattplot_params
        P.PANEL["L_in"] = panel_L
        P.PANEL["W_in"] = panel_W
        P.PANEL["wattage"] = panel_wattage
        P.PANEL["thickness_in"] = panel_thk
        P.PANEL["mass_lb"] = panel_mass
        P.PANEL["panel_age_years"] = int(panel_age)
        P.PANEL["panel_bifacial"] = panel_bifacial
        # Derate
        if panel_age > 0:
            derate = max(0.70, 1.0 - 0.005 * panel_age)
            P.PANEL["wattage"] = round(panel_wattage * derate, 0)
        # Resize bed
        P.BED["outer_L_in"] = min(panel_L + 1.0, P.MAX_PLANTER_L_IN)
        P.BED["outer_W_in"] = min(panel_W + 1.0, P.MAX_PLANTER_W_IN)

    bed_L = P.BED["outer_L_in"]
    bed_W = P.BED["outer_W_in"]
    final_wattage = int(P.PANEL["wattage"])

    # ---- Over-cap check ----
    # Panel can overhang bed by 0.5" per side (1" total). So a 97" panel
    # fits a 96" bed, but 98" doesn't.
    max_panel_L = P.MAX_PLANTER_L_IN + 1.0
    max_panel_W = P.MAX_PLANTER_W_IN + 1.0
    if panel_L > max_panel_L or panel_W > max_panel_W:
        banner(f"*** PANEL TOO BIG: {panel_L}\"×{panel_W}\" exceeds "
               f"max {max_panel_L}\"×{max_panel_W}\" (8×5 ft + 1\" overhang) ***")
        print(f"  Panel:  {panel_L:.1f}\" × {panel_W:.1f}\"")
        print(f"  Max:    {max_panel_L:.1f}\" × {max_panel_W:.1f}\"")
        print("  Options:")
        print("    1. Build TWO planters in a row (each takes half the panel)")
        print("    2. Scale up the lumber (10-ft or 12-ft stock, $) and rebuild")
        print("    3. Use a smaller panel")
        print()
        return

    # ---- Header ----
    banner(f"Build report: {name} panel")
    print(f"  Panel:        {panel_L:.1f}\" × {panel_W:.1f}\" × {panel_thk:.1f}\" "
          f"({panel_L/12:.2f} × {panel_W/12:.2f} ft)")
    print(f"  Mass:         {panel_mass:.1f} lb")
    print(f"  Wattage:      {final_wattage} W "
          f"(nameplate {panel_wattage:.0f} W, {int(panel_age)} yr old, "
          f"{'bifacial' if panel_bifacial else 'monofacial'})")
    print(f"  Bed (auto):   {bed_L:.1f}\" × {bed_W:.1f}\" "
          f"({bed_L/12:.2f} × {bed_W/12:.2f} ft)")

    # ---- Cut list ----
    cuts = derive_cut_list(bed_L_in=bed_L, bed_W_in=bed_W)
    print_cut_list(cuts, title="Lumber cut list (from bed dimensions)")

    # ---- Hardware spec ----
    hardware = derive_hardware_spec(
        bed_L_in=bed_L, bed_W_in=bed_W,
        panel_L_in=panel_L, panel_W_in=panel_W,
        panel_thk_in=panel_thk, panel_mass_lb=panel_mass,
        actuator_stroke_in=4.0,
    )
    print_hardware_spec(hardware, title="Hardware spec (from bed + panel)")

    # ---- MPPT recommendation ----
    mppt = recommend_mppt(panel_wattage, age_years=int(panel_age))
    print("MPPT charge controller (from panel wattage)")
    print("=" * 80)
    print(f"  Model:     {mppt['model']}")
    print(f"  Cost:      ~{mppt['cost_estimate']}")
    print(f"  Voc max:   {mppt['p_v_max']} V")
    print(f"  I max:     {mppt['i_max']} A")
    print(f"  Rationale: {mppt['rationale']}")
    print()

# ---- Estimated power output ----
    # Phoenix, 35° tilt, system_derate, bifacial bonus. Prefer the
    # actual sun_simulator result (pvlib + TMY weather) when available;
    # fall back to the heuristic if the simulator can't run.
    if final_wattage <= 0:
        print("ERROR: final_wattage is 0")
        sys.exit(1)
    annual_kwh = None
    annual_kwh_schedule = None
    try:
        from sun_simulator import run_simulation
        results, _df = run_simulation()      # (dict, dataframe)
        annual_kwh_schedule = {
            "static_35":   results.get("Static 35° (max power)", {}).get("annual_kwh"),
            "seasonal":    results.get("Seasonal 90/35°",        {}).get("annual_kwh"),
            "az_tracking": results.get("Azimuth tracking 35°",   {}).get("annual_kwh"),
        }
        annual_kwh = annual_kwh_schedule["static_35"]
    except (ImportError, OSError, RuntimeError, ValueError, KeyError, AttributeError) as exc:
        # pvlib / TMY data not available (offline install, etc.)
        # Fall back to the heuristic: 2.5 kWh/W/yr at static 35° tilt in
        # Phoenix. Calibrated against sun_simulator for the LONGi 620W
        # preset (1539 / 620 = 2.48). +10% for bifacial.
        annual_kwh = final_wattage * 2.5 * (1.10 if panel_bifacial else 1.0)
        annual_kwh_schedule = None
        sim_warning = f"  (sun_simulator unavailable: {exc}; using heuristic)"

    print("Estimated annual power (Phoenix, 35° tilt, pvlib + TMY)")
    print("=" * 80)
    print(f"  {final_wattage} W panel -> ~{annual_kwh:.0f} kWh/yr at static 35° "
          f"(${int(annual_kwh * 0.13)}/yr at AZ rates)")
    if annual_kwh_schedule:
        for label, key in (("Static 35° (max power)",  "static_35"),
                           ("Seasonal 90/35°",        "seasonal"),
                           ("Azimuth tracking 35°",   "az_tracking")):
            v = annual_kwh_schedule.get(key)
            if v is not None:
                print(f"    {label:<28} {v:>6.0f} kWh/yr")
    if 'sim_warning' in locals():
        print(sim_warning)
    print()

    # ---- Total cost estimate ----
    lumber_cost = sum(
        19 if cut.nominal == "2x12" else
        12 if cut.nominal == "2x6" else
        7 if cut.nominal == "2x4" else
        14 if cut.nominal == "4x4" else
        5 if cut.nominal == "1x4" else
        4 if cut.nominal == "1x2" else 5
        for cut in cuts["cuts"]
        for _ in range(cuts["boards_8ft"].get(cut.nominal, cuts["boards_10ft"].get(cut.nominal, 1)))
    )
    # Actually count distinct board purchases
    n_boards_8 = sum(cuts["boards_8ft"].values())
    n_boards_10 = sum(cuts["boards_10ft"].values())
    lumber_cost = n_boards_8 * 10 + n_boards_10 * 14  # rough avg per board
    hardware_cost = (
        hardware["hinges"]["count"] * 8 +         # $8 per butt hinge
        1 * (hardware["hinge_pin"]["length_in"]/12 * 5) +  # ~$5 per ft of rod
        hardware["mid_clamps"]["count"] * 3 +    # $3 per clamp
        hardware["carriage_bolts"]["count"] * 0.50 +
        hardware["lag_bolts"]["count"] * 0.30 +
        hardware["deck_screws"]["total"] * 0.10
    )
    panel_cost = 0 if panel_age > 0 else final_wattage * 0.40  # new ~$0.40/W, salvage free
    mppt_cost = int(mppt["cost_estimate"].replace("$", "").split("-")[0])
    battery_cost = 230  # 12V 100Ah LiFePO4
    microinverter_cost = 150  # Enphase IQ7+
    controller_cost = 120  # ESP32 + custom PCB
    misc_cost = 50
    total_cost = (
        lumber_cost + hardware_cost + panel_cost + mppt_cost +
        battery_cost + microinverter_cost + controller_cost + misc_cost
    )

    print("Cost estimate (rough, in USD)")
    print("=" * 80)
    print(f"  Lumber ({n_boards_8 + n_boards_10} boards):        ${lumber_cost:.0f}")
    print(f"  Hardware (hinges, clamps, bolts, screws): ${hardware_cost:.0f}")
    if panel_cost > 0:
        print(f"  Panel (new, est ${panel_wattage * 0.40:.0f}):          ${panel_cost:.0f}")
    else:
        print("  Panel (salvage):                  $0 (you bring your own)")
    print(f"  MPPT ({mppt['model'][:30]}): ${mppt_cost}")
    print(f"  Battery (12V 100Ah LiFePO4):    ${battery_cost}")
    print(f"  Microinverter (Enphase IQ7+):    ${microinverter_cost}")
    print(f"  Controller (ESP32 + PCB):        ${controller_cost}")
    print(f"  Misc (wire, irrigation, etc.):   ${misc_cost}")
    print(f"  {'-' * 60}")
    print(f"  TOTAL:                           ${total_cost:.0f}")
    if panel_age > 0:
        print(f"  (with salvage panel)             ${total_cost - (panel_wattage * 0.40):.0f}")
    print()

    # ---- Next steps ----
    print("Next steps")
    print("=" * 80)
    print(f"  1. Take the cut list to Home Depot: {n_boards_8 + n_boards_10} boards, "
          f"~{lumber_cost * 0.7:.0f} min")
    print("  2. Have them pre-cut (or use a circular saw + chisel for the half-laps)")
    print("  3. Order the hardware on the list above (Amazon / McMaster / IronRidge)")
    print("  4. Generate the build guide: see below")
    print(f"  5. Regenerate the 3D model: python wattplot.py --name wattplot_{name} --skip-sim --skip-wind")
    print()

    # ---- Generate the build guide ----
    try:
        from models.build_guide import generate_build_guide, write_build_guide
        guide = generate_build_guide(panel_name=name)
        guide_path = f"docs/build_{name}.md"
        write_build_guide(guide, guide_path)
        print(f"Build guide written: {guide_path} ({len(guide)} bytes)")
    except Exception as e:  # noqa: BLE001
        print(f"Build guide generation failed: {e}")
    print()


if __name__ == "__main__":
    main()
