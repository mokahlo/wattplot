"""Wrapper to run assemble.py with proper sys.path. Use:
  freecadcmd models/freecad/_run.py

The output filename prefix is read from the WATTPLOT_OUTPUT_PREFIX env var
(default "wattplot_v2"). wattplot.py sets this when --panel or --name is used.

If the WATTPLOT_PANEL_PRESET env var is set, the named preset is applied
BEFORE building the model. This is how wattplot.py propagates the
in-memory preset change across the FreeCAD subprocess boundary.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # C:\dev\wattplot
sys.path.insert(0, ROOT)
# Now import and run
from models.freecad.assemble import (
    build_assembly, export_step, export_stl, export_fcstd
)
from wattplot_params import PANEL, BED

# Output prefix: env var set by wattplot.py, or default
prefix = os.environ.get("WATTPLOT_OUTPUT_PREFIX", "wattplot_v2")
# Sanity check on the env var to prevent path traversal
if "/" in prefix or "\\" in prefix or ".." in prefix:
    print(f"[freecad] WARN: invalid WATTPLOT_OUTPUT_PREFIX={prefix!r}, using default")
    prefix = "wattplot_v2"

# Apply a panel preset if requested (propagated from wattplot.py)
preset_name = os.environ.get("WATTPLOT_PANEL_PRESET")
if preset_name:
    import wattplot_params as P_full
    if preset_name in P_full.PANEL_PRESETS:
        P_full.apply_panel_preset(preset_name)
        print(f"[freecad] Applied preset: {preset_name}")
    else:
        print(f"[freecad] WARN: preset {preset_name!r} not found, using default")

tilt = PANEL["panel_tilt_deg"]
print(f"[freecad] Panel: {PANEL['L_in']}\" x {PANEL['W_in']}\" @ {int(PANEL['wattage'])} W, "
      f"tilt = {tilt}°")
print(f"[freecad] Bed:   {BED['outer_L_in']}\" x {BED['outer_W_in']}\"")
print(f"[freecad] Output prefix: {prefix}")

doc = build_assembly(tilt_deg=tilt)
export_step(doc, os.path.join(ROOT, "models", f"{prefix}.step"))
export_stl(doc, os.path.join(ROOT, "models", f"{prefix}.stl"))
export_fcstd(doc, os.path.join(ROOT, "models", f"{prefix}.fcstd"))

doc_flat = build_assembly(tilt_deg=0.0, name="Wattplot_flat")
export_stl(doc_flat, os.path.join(ROOT, "models", f"{prefix}_flat.stl"))
print(f"[freecad] done. {prefix}.{{step,stl,fcstd}} and {prefix}_flat.stl exported.")
