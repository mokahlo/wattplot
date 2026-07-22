"""Wrapper to run assemble_mini.py with proper sys.path."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from models.freecad.assemble_mini import (
    build_mini_assembly, export_step, export_stl, export_fcstd
)
doc = build_mini_assembly()
export_step(doc, os.path.join(ROOT, "models", "wattplot_v2_mini.step"))
export_stl(doc, os.path.join(ROOT, "models", "wattplot_v2_mini.stl"))
export_fcstd(doc, os.path.join(ROOT, "models", "wattplot_v2_mini.fcstd"))
print("[freecad] mini done.")
