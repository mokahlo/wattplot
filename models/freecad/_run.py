"""Wrapper to run assemble.py with proper sys.path. Use:
  freecadcmd models/freecad/_run.py
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # C:\dev\wattplot
sys.path.insert(0, ROOT)
# Now import and run
from models.freecad.assemble import (
    build_assembly, export_step, export_stl, export_fcstd
)
from wattplot_params import PANEL

tilt = PANEL["panel_tilt_deg"]
doc = build_assembly(tilt_deg=tilt)
export_step(doc, os.path.join(ROOT, "models", "wattplot_v2.step"))
export_stl(doc, os.path.join(ROOT, "models", "wattplot_v2.stl"))
export_fcstd(doc, os.path.join(ROOT, "models", "wattplot_v2.fcstd"))

doc_flat = build_assembly(tilt_deg=0.0, name="Wattplot_v2_flat")
export_stl(doc_flat, os.path.join(ROOT, "models", "wattplot_v2_flat.stl"))
print(f"[freecad] done. STEP + STL + FCStd exported.")
