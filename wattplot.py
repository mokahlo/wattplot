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
    """Build the FreeCAD 3D model, export to STEP/STL/FCStd.

    The model is built by `models/freecad/assemble.py` (one FreeCAD Part::Feature
    per part), then exported to STEP (parametric CAD), STL (mesh), and saved
    as a .FCStd file (the editable FreeCAD document).

    Requires FreeCAD 1.0+. The script auto-detects `freecadcmd` in the
    standard install locations, or uses $FREECADCMD if set.
    """
    banner("STEP 1/3 — Build & export 3D model (FreeCAD)")
    if tilt_override is not None:
        P.PANEL['panel_tilt_deg'] = tilt_override
        print(f"  Override: panel tilt = {tilt_override}°")

    freecadcmd = _find_freecadcmd()
    if freecadcmd is None:
        print("  [model] FreeCAD not found — skipping 3D model export.")
        print("         Install FreeCAD 1.0+ from https://www.freecad.org/")
        print("         or set $FREECADCMD to your FreeCADCmd.exe path.")
        return

    print(f"  Using: {freecadcmd}")
    runner = os.path.join(HERE, "models", "freecad", "_run.py")
    cmd = [freecadcmd, runner]
    print(f"  Running: {' '.join(cmd)}")
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    # Print only the lines after the FreeCAD banner so we see our [freecad] log
    for line in result.stdout.splitlines():
        if line.startswith("[freecad]"):
            print(f"  {line}")
    if result.returncode != 0:
        print(f"  [model] FreeCAD exited with code {result.returncode}")
        if result.stderr:
            print("  stderr (last 10 lines):")
            for line in result.stderr.splitlines()[-10:]:
                print(f"    {line}")
        return

    # Show the exported files
    models_dir = os.path.join(HERE, "models")
    for fname in ("wattplot_v2.step", "wattplot_v2.stl", "wattplot_v2.fcstd"):
        path = os.path.join(models_dir, fname)
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  Exported: {fname} ({size_kb:.1f} KB)")
    print(f"  Current panel tilt (from shared params): {P.PANEL['panel_tilt_deg']}°")


def _find_freecadcmd():
    """Find the freecadcmd executable. Checks (in order):
      1. $FREECADCMD environment variable
      2. C:\\Program Files\\FreeCAD *\\bin\\freecadcmd.exe
      3. freecadcmd on PATH
    Returns the full path, or None if not found.
    """
    import shutil
    import glob

    env = os.environ.get("FREECADCMD")
    if env and os.path.isfile(env):
        return env

    # Windows default locations
    for pattern in [
        r"C:\Program Files\FreeCAD *\bin\freecadcmd.exe",
        r"C:\Program Files (x86)\FreeCAD *\bin\freecadcmd.exe",
    ]:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

    # Linux/macOS fallback
    found = shutil.which("freecadcmd")
    if found:
        return found

    return None


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
