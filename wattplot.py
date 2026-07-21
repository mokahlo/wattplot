"""
Wattplot v2 — Top-level pipeline orchestrator.

Single source of truth (wattplot_params.py) feeds:
  1. The 3D cadquery model — built, exported (STEP / STL / 3MF / VRML)
  2. The shadow raycaster — geometric bed-shadow calculation
  3. The sun simulator — annual kWh, bed DLI, tomato yield per tilt schedule
  4. The wind load analysis — ASCE 7-22 force + safety factor

Change a value in wattplot_params.py and the whole pipeline updates.

Usage:
    python wattplot.py                     # full pipeline
    python wattplot.py --skip-model        # skip 3D export (faster)
    python wattplot.py --skip-sim          # skip simulation
    python wattplot.py --tilt 50          # override default panel tilt
    python wattplot.py --schedule static35 # run a specific schedule only
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "models"))
sys.path.insert(0, os.path.join(HERE, "analysis"))

import wattplot_params as P  # noqa: E402


def banner(text):
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)


def build_and_export_3d_model(tilt_override=None):
    """Build the cadquery 3D model, export to STEP/STL/3MF/VRML."""
    banner("STEP 1/3 — Build & export 3D model")
    if tilt_override is not None:
        P.PANEL['panel_tilt_deg'] = tilt_override
        print(f"  Override: panel tilt = {tilt_override}°")

    from export_3d import build_model
    from cadquery import exporters

    model = build_model().val()
    models_dir = os.path.join(HERE, "models")
    os.makedirs(models_dir, exist_ok=True)

    for ext in ["STEP", "STL", "3MF", "VRML"]:
        out = os.path.join(models_dir, f"wattplot_v2.{ext.lower()}")
        if ext == "STL":
            exporters.export(model, out, exportType=ext, tolerance=0.5)
        else:
            exporters.export(model, out, exportType=ext)
        size_kb = os.path.getsize(out) / 1024
        print(f"  Exported {ext:5s}: {os.path.basename(out)} ({size_kb:.1f} KB)")
    print(f"  Current panel tilt (from shared params): {P.PANEL['panel_tilt_deg']}°")


def run_simulation():
    """Run the sun simulator and produce plots + comparison table."""
    banner("STEP 2/3 — Sun + tilt simulation")
    from sun_simulator import run_simulation, print_comparison, plot_results
    results, df = run_simulation()
    print_comparison(results)
    renders_dir = os.path.join(HERE, "renders")
    plot_results(results, df, renders_dir)
    return results


def run_wind_load():
    """Run the wind load analysis at the current panel tilt."""
    banner("STEP 3/3 — Wind load analysis (ASCE 7-22)")
    from wind_load import run_analysis
    runs = run_analysis()
    out_md = os.path.join(HERE, "analysis", "wind_load_report.md")
    print(f"  Report: {out_md}")
    return runs


def main():
    parser = argparse.ArgumentParser(description="Wattplot v2 pipeline orchestrator")
    parser.add_argument("--skip-model", action="store_true", help="Skip 3D model export")
    parser.add_argument("--skip-sim", action="store_true", help="Skip simulation")
    parser.add_argument("--skip-wind", action="store_true", help="Skip wind load")
    parser.add_argument("--tilt", type=float, help="Override panel tilt (degrees)")
    parser.add_argument("--schedule", type=str, help="Specific schedule name to simulate")
    args = parser.parse_args()

    t0 = time.time()
    print()
    print(f"Wattplot v2 pipeline — {P.LOCATION['name']}")
    print(f"   lat {P.LOCATION['latitude']}, lon {P.LOCATION['longitude']}, "
          f"wind {P.LOCATION['design_wind_speed_mph']} mph @ {P.LOCATION['design_wind_exposure']} exposure")
    print(f"   bed {P.BED['outer_L_in']/12:.1f} x {P.BED['outer_W_in']/12:.2f} ft, "
          f"panel {P.PANEL['L_in']/12:.2f} x {P.PANEL['W_in']/12:.2f} ft @ "
          f"{P.PANEL['wattage']}W")
    print()

    if not args.skip_model:
        build_and_export_3d_model(args.tilt)

    if not args.skip_sim:
        run_simulation()

    if not args.skip_wind:
        run_wind_load()

    elapsed = time.time() - t0
    print()
    print("=" * 70)
    print(f"  Pipeline complete in {elapsed:.1f}s")
    print("  Output: models/, renders/, analysis/")
    print("=" * 70)


if __name__ == "__main__":
    main()
