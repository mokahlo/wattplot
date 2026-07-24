"""
Wattplot v2 — Top-level pipeline orchestrator.

Single source of truth (wattplot_params.py) feeds:
  1. The 3D cadquery model — built, exported (STEP / STL / 3MF / VRML)
  2. The shadow raycaster — geometric bed-shadow calculation
  3. The sun simulator — annual kWh, bed DLI, tomato yield per tilt schedule
  4. The wind load analysis — ASCE 7-22 force + safety factor

Change a value in wattplot_params.py and the whole pipeline updates.

Usage:
    python wattplot.py                          # full pipeline (default LONGi 620W)
    python wattplot.py --skip-model             # skip 3D export (faster)
    python wattplot.py --skip-sim               # skip simulation
    python wattplot.py --tilt 50                # override default panel tilt
    python wattplot.py --schedule static35      # run a specific schedule only
    python wattplot.py --panel residential_60cell  # regenerate with a salvage panel
    python wattplot.py --list-panels            # show available panel presets
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


def list_panels():
    """Print all available panel presets and their key dimensions."""
    print()
    print("Available panel presets:")
    print("-" * 80)
    print(f"{'Name':<28} {'Panel LxW (in)':<16} {'New W':<8} {'Derated':<10} {'Age'}")
    print("-" * 80)
    for name, preset in P.PANEL_PRESETS.items():
        L, W = preset["L_in"], preset["W_in"]
        new_W = preset["wattage"]
        age = preset.get("panel_age_years", 0)
        # Apply the same derate formula the function uses
        if age > 0:
            derate = max(0.70, 1.0 - 0.005 * age)
            derated_W = round(new_W * derate, 0)
            derated_str = f"{int(derated_W)} W"
        else:
            derated_str = f"{new_W} W (new)"
        bifacial = "B" if preset.get("panel_bifacial", False) else " "
        print(f"  {bifacial} {name:<25} {L:>4} x {W:<6}  {new_W:<8} {derated_str:<10} {age} yr")
    print()
    print("  B = bifacial. Use --panel <name> to apply.")
    print()


def build_and_export_3d_model(tilt_override=None, output_prefix="wattplot_v2"):
    """Build the FreeCAD 3D model, export to STEP/STL/FCStd.

    The model is built by `models/freecad/assemble.py` (one FreeCAD Part::Feature
    per part), then exported to STEP (parametric CAD), STL (mesh), and saved
    as a .FCStd file (the editable FreeCAD document).

    `output_prefix` controls the basename of the exported files. Default is
    "wattplot_v2" (writes to models/wattplot_v2.{step,stl,fcstd}). When
    `--panel` is used, the prefix is the preset name (e.g.
    "wattplot_v2_residential_60cell") to avoid overwriting the canonical
    files.

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
    # Pass the output prefix and any panel preset via env so _run.py
    # (which runs in a separate FreeCAD process) sees the same state.
    env = os.environ.copy()
    env["WATTPLOT_OUTPUT_PREFIX"] = output_prefix
    # If --panel was used, propagate the preset name so the FreeCAD
    # subprocess applies the same preset before building.
    if hasattr(P, "_active_preset") and P._active_preset:
        env["WATTPLOT_PANEL_PRESET"] = P._active_preset
    cmd = [freecadcmd, runner]
    print(f"  Running: {' '.join(cmd)}")
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
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
    for ext in ("step", "stl", "fcstd"):
        path = os.path.join(models_dir, f"{output_prefix}.{ext}")
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  Exported: {output_prefix}.{ext} ({size_kb:.1f} KB)")
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


def apply_panel(panel_name):
    """Apply a panel preset to wattplot_params, print the change.

    Returns the output prefix to use for the FreeCAD export, or None if
    the panel name is invalid.
    """
    if panel_name not in P.PANEL_PRESETS:
        print(f"  [panel] Unknown preset: {panel_name!r}")
        print(f"           Use --list-panels to see available presets.")
        return None
    preset = P.PANEL_PRESETS[panel_name]
    P.apply_panel_preset(panel_name)
    # Tag the active preset so the FreeCAD subprocess can re-apply it
    # (subprocesses re-import wattplot_params and don't see in-memory changes).
    P._active_preset = panel_name
    print(f"  [panel] Applied preset: {preset.get('label', panel_name)}")
    print(f"           Panel: {P.PANEL['L_in']}\" x {P.PANEL['W_in']}\" "
          f"({P.PANEL['L_in']/12:.2f} x {P.PANEL['W_in']/12:.2f} ft)")
    print(f"           Bed:   {P.BED['outer_L_in']}\" x {P.BED['outer_W_in']}\" "
          f"({P.BED['outer_L_in']/12:.2f} x {P.BED['outer_W_in']/12:.2f} ft)")
    print(f"           Wattage: {int(P.PANEL['wattage'])} W "
          f"(age {P.PANEL.get('panel_age_years', 0)} yr, "
          f"{'bifacial' if P.PANEL.get('panel_bifacial', False) else 'monofacial'})")
    return f"wattplot_v2_{panel_name}"


def main():
    parser = argparse.ArgumentParser(
        description="Wattplot v2 pipeline orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python wattplot.py                            # full pipeline (LONGi 620W)\n"
               "  python wattplot.py --list-panels              # show panel presets\n"
               "  python wattplot.py --panel residential_60cell # regenerate with salvage panel\n"
               "  python wattplot.py --skip-model --skip-wind   # sun sim only\n",
    )
    parser.add_argument("--skip-model", action="store_true", help="Skip 3D model export")
    parser.add_argument("--skip-sim", action="store_true", help="Skip simulation")
    parser.add_argument("--skip-wind", action="store_true", help="Skip wind load")
    parser.add_argument("--tilt", type=float, help="Override panel tilt (degrees)")
    parser.add_argument("--schedule", type=str, help="Specific schedule name to simulate")
    parser.add_argument("--panel", type=str, help="Apply a panel preset (see --list-panels)")
    parser.add_argument("--list-panels", action="store_true", help="List available panel presets and exit")
    parser.add_argument("--name", type=str, default=None,
                        help="Custom output prefix for the model files (default = 'wattplot_v2' or 'wattplot_v2_<panel>')")
    args = parser.parse_args()

    if args.list_panels:
        list_panels()
        return

    t0 = time.time()
    print()
    print(f"Wattplot v2 pipeline — {P.LOCATION['name']}")

    # Apply panel preset if requested
    output_prefix = "wattplot_v2"
    if args.panel:
        result = apply_panel(args.panel)
        if result is None:
            sys.exit(1)
        output_prefix = args.name if args.name else result

    print(f"   lat {P.LOCATION['latitude']}, lon {P.LOCATION['longitude']}, "
          f"wind {P.LOCATION['design_wind_speed_mph']} mph @ {P.LOCATION['design_wind_exposure']} exposure")
    print(f"   bed {P.BED['outer_L_in']/12:.2f} x {P.BED['outer_W_in']/12:.2f} ft, "
          f"panel {P.PANEL['L_in']/12:.2f} x {P.PANEL['W_in']/12:.2f} ft @ "
          f"{int(P.PANEL['wattage'])}W")
    print()

    if not args.skip_model:
        build_and_export_3d_model(args.tilt, output_prefix=output_prefix)

    if not args.skip_sim:
        run_simulation()

    if not args.skip_wind:
        run_wind_load()

    elapsed = time.time() - t0
    print()
    print("=" * 70)
    print(f"  Pipeline complete in {elapsed:.1f}s")
    print(f"  Output: models/{output_prefix}.{{step,stl,fcstd}}, renders/, analysis/")
    print("=" * 70)


if __name__ == "__main__":
    main()
