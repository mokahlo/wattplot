"""
Wattplot Mini — FreeCAD master assembly.
1/5-scale, fully functional, design validation prototype.

Run with:
    "C:/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" \\
        -c "exec(open('models/freecad/assemble_mini.py').read())"

Or use the _run_mini.py wrapper.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import FreeCAD as App
import Part
import Mesh
import MeshPart

from wattplot_params import MINI
from models.freecad.parts.mini.bed_wall import make_bed_long_wall, make_bed_short_wall
from models.freecad.parts.mini.skid import make_skids
from models.freecad.parts.mini.frame import make_frame_assembly
from models.freecad.parts.mini.panel import make_panel
from models.freecad.parts.mini.hinge import make_all_hinges
from models.freecad.parts.mini.actuator_mount import make_actuator_mount

OUTDIR_MODELS = os.path.join(ROOT, "models")


# Colors
COL_BED    = (0.42, 0.27, 0.13)
COL_SOIL   = (0.30, 0.18, 0.08)
COL_FRAME  = (0.85, 0.65, 0.40)
COL_PANEL  = (0.10, 0.15, 0.45)
COL_HINGE  = (0.45, 0.45, 0.50)
COL_CLAMP  = (0.80, 0.80, 0.82)
COL_ACT    = (0.50, 0.45, 0.40)


def set_color(obj, rgba):
    if obj.ViewObject is None:
        return
    try:
        obj.ViewObject.ShapeColor = rgba[:3]
        obj.ViewObject.Transparency = int((1 - rgba[3]) * 100)
    except Exception:
        pass


def build_mini_assembly(doc=None, name="Wattplot_Mini"):
    """Build the mini assembly (flat, 0° tilt)."""
    if doc is None:
        doc = App.newDocument(name)
    doc.recompute()

    print(f"[freecad] building Wattplot Mini (1/5 scale) ...")

    # Bed
    n_wall = make_bed_long_wall(doc, "north")
    s_wall = make_bed_long_wall(doc, "south")
    w_wall = make_bed_short_wall(doc, "west")
    e_wall = make_bed_short_wall(doc, "east")
    skids = make_skids(doc)
    for o in (n_wall, s_wall, w_wall, e_wall):
        set_color(o, COL_BED)
    set_color(skids, COL_BED)
    print(f"  [bed] 4 walls + skids")

    # Frame + panel + actuator mount
    frame, frame_parts = make_frame_assembly(doc)
    panel = make_panel(doc)
    hinges_obj, hinges = make_all_hinges(doc)
    act, act_parts = make_actuator_mount(doc)
    for o in frame_parts:
        set_color(o, COL_FRAME)
    set_color(panel, COL_PANEL)
    for h in hinges:
        set_color(h, COL_HINGE)
    set_color(act, COL_ACT)

    # Smart planter: watering system (v2.4)
    try:
        from models.freecad.parts.mini.watering import (
            make_watering_assembly
        )
        watering, watering_parts = make_watering_assembly(doc)
        set_color(watering, COL_ACT)  # reuse actuator color
        for part in watering_parts:
            set_color(part, COL_ACT)
        print(f"  [watering] solenoid + regulator + drip line + relay")
    except ImportError:
        print(f"  [watering] skipped (module not found)")

    print(f"[freecad] mini assembly complete — {len(doc.Objects)} objects in doc")
    return doc


def export_step(doc, out_path):
    shapes = [o.Shape for o in doc.Objects
              if hasattr(o, "Shape") and o.Shape and not o.Shape.isNull()]
    if not shapes:
        return
    compound = Part.makeCompound(shapes)
    compound.exportStep(out_path)
    print(f"[freecad] STEP: {out_path}")


def export_stl(doc, out_path):
    shapes = [o.Shape for o in doc.Objects
              if hasattr(o, "Shape") and o.Shape and not o.Shape.isNull()]
    if not shapes:
        return
    compound = Part.makeCompound(shapes)
    mesh = MeshPart.meshFromShape(compound,
                                  LinearDeflection=0.5, AngularDeflection=0.5,
                                  Relative=False)
    mesh.write(out_path)
    print(f"[freecad] STL:  {out_path}")


def export_fcstd(doc, out_path):
    doc.saveAs(out_path)
    print(f"[freecad] FCStd: {out_path}")


if __name__ == "__main__":
    doc = build_mini_assembly()
    export_step(doc, os.path.join(OUTDIR_MODELS, "wattplot_v2_mini.step"))
    export_stl(doc, os.path.join(OUTDIR_MODELS, "wattplot_v2_mini.stl"))
    export_fcstd(doc, os.path.join(OUTDIR_MODELS, "wattplot_v2_mini.fcstd"))
    print(f"[freecad] mini done. STEP + STL + FCStd exported to {OUTDIR_MODELS}")
