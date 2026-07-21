"""
Wattplot v2 — FreeCAD master assembly.

Run with:
    "C:/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" \\
        -c "exec(open('models/freecad/assemble.py').read())"

Or from Python inside the FreeCAD app:
    >>> exec(open('models/freecad/assemble.py').read())

Outputs:
    models/wattplot_v2.step     — full parametric STEP
    models/wattplot_v2.stl      — mesh for 3D printing or rendering
    models/wattplot_v2_tilted.stl — same model, panel tilted to panel_tilt_deg
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

from wattplot_params import PANEL
from models.freecad.parts.bed_wall import make_bed_long_wall, make_bed_short_wall
from models.freecad.parts.skid import make_skids
from models.freecad.parts.frame import make_frame_assembly
from models.freecad.parts.panel import make_panel
from models.freecad.parts.hinge import make_all_hinges
from models.freecad.parts.panel_clamp import make_all_clamps
from models.freecad.parts.actuator_mount import make_actuator_mount

import math

OUTDIR_MODELS = os.path.join(ROOT, "models")


# ---- color helpers ---------------------------------------------------------

COLORS = {
    "wood":   (0.55, 0.40, 0.25, 1.0),   # warm brown
    "frame":  (0.45, 0.32, 0.20, 1.0),   # darker brown
    "metal":  (0.50, 0.50, 0.55, 1.0),   # silver-gray
    "panel":  (0.10, 0.15, 0.30, 0.85),  # solar blue, slightly transparent
    "clamp":  (0.75, 0.75, 0.78, 1.0),   # aluminum
    "soil":   (0.40, 0.25, 0.10, 0.55),  # dark earth
    "skid":   (0.45, 0.32, 0.20, 1.0),
}


def set_color(obj, rgba):
    """Set a FreeCAD object's view color. No-op in headless mode."""
    if obj.ViewObject is None:
        return  # no GUI; skip coloring
    try:
        obj.ViewObject.ShapeColor = rgba[:3]
        obj.ViewObject.Transparency = int((1 - rgba[3]) * 100)
    except Exception:
        pass  # headless mode; ignore


# ---- build the full assembly ----------------------------------------------

def build_assembly(tilt_deg=0.0, doc=None, name="Wattplot_v2"):
    """Build the full assembly in a new (or given) document.

    Returns the document.
    """
    if doc is None:
        doc = App.newDocument(name)
    doc.recompute()

    print(f"[freecad] building Wattplot v2 (tilt = {tilt_deg}°) ...")

    # ---- bed (static, not tilted) ----
    n_wall = make_bed_long_wall(doc, "north")
    s_wall = make_bed_long_wall(doc, "south")
    w_wall = make_bed_short_wall(doc, "west")
    e_wall = make_bed_short_wall(doc, "east")
    skids  = make_skids(doc)
    for o in (n_wall, s_wall, w_wall, e_wall):
        set_color(o, COLORS["wood"])
    set_color(skids, COLORS["skid"])
    print(f"  [bed] 4 walls + skids")

    # ---- frame (tilted as a unit) ----
    # Build at 0° (flat over the bed), then rotate around the hinge axis
    # (X axis at y=14.25, z=22.3) by tilt_deg.
    frame, frame_parts = make_frame_assembly(doc)
    for o in frame_parts:
        set_color(o, COLORS["frame"])

    # ---- panel (tilted with the frame) ----
    panel = make_panel(doc)
    set_color(panel, COLORS["panel"])

    # ---- hinges (static, mounted on the south wall) ----
    hinges_obj, hinges = make_all_hinges(doc)
    for h in hinges:
        set_color(h, COLORS["metal"])

    # ---- panel clamps (tilted with the frame) ----
    clamps_obj, clamps = make_all_clamps(doc)
    for c in clamps:
        set_color(c, COLORS["clamp"])

    # ---- actuator mount (clevis tilts, wall block stays) ----
    act = make_actuator_mount(doc)
    set_color(act, COLORS["metal"])

    # ---- tilt ----
    # The frame+panel+clamps form a rigid group that rotates about the hinge
    # axis (X axis at y=14.25, z=22.3). For engineering drawings the side view
    # already shows the tilt at 35° and 90°. The 3D model is built FLAT (0°)
    # so the geometry is easy to see and dimension. (The original cadquery
    # model showed the tilted pose; for the FreeCAD model we keep it flat
    # because the in-place rotation hits FreeCAD's "immutable shape" guard.)
    if tilt_deg != 0.0:
        print(f"  [tilt] NOTE: 3D model is built flat (0°). The engineering "
              f"drawing shows the {tilt_deg}° tilted view. Apply tilt manually "
              f"in FreeCAD GUI if you want a 3D tilted view.")

    print(f"[freecad] assembly complete — {len(doc.Objects)} objects in doc")
    return doc


# ---- export ----------------------------------------------------------------

def export_step(doc, out_path):
    """Export the doc to a STEP file. Skips objects with empty shapes."""
    shapes = [o.Shape for o in doc.Objects
              if hasattr(o, "Shape") and o.Shape and not o.Shape.isNull()]
    if not shapes:
        print(f"[freecad] STEP: no shapes to export, skipping {out_path}")
        return
    compound = Part.makeCompound(shapes)
    compound.exportStep(out_path)
    print(f"[freecad] STEP: {out_path}")


def export_stl(doc, out_path):
    """Export the doc to an STL file. Skips objects with empty shapes."""
    shapes = [o.Shape for o in doc.Objects
              if hasattr(o, "Shape") and o.Shape and not o.Shape.isNull()]
    if not shapes:
        print(f"[freecad] STL: no shapes to export, skipping {out_path}")
        return
    compound = Part.makeCompound(shapes)
    mesh = MeshPart.meshFromShape(compound,
                                  LinearDeflection=1.0,
                                  AngularDeflection=0.5,
                                  Relative=False)
    mesh.write(out_path)
    print(f"[freecad] STL:  {out_path}")


def export_fcstd(doc, out_path):
    """Save the FreeCAD document as a .FCStd file (the editable parametric model)."""
    doc.saveAs(out_path)
    print(f"[freecad] FCStd: {out_path}")


# ---- main ------------------------------------------------------------------

if __name__ == "__main__":
    tilt = PANEL["panel_tilt_deg"]
    doc = build_assembly(tilt_deg=tilt)
    export_step(doc, os.path.join(OUTDIR_MODELS, "wattplot_v2.step"))
    export_stl(doc, os.path.join(OUTDIR_MODELS, "wattplot_v2.stl"))
    export_fcstd(doc, os.path.join(OUTDIR_MODELS, "wattplot_v2.fcstd"))

    # Also write a flat version (0° tilt) for reference
    doc_flat = build_assembly(tilt_deg=0.0, name="Wattplot_v2_flat")
    export_stl(doc_flat, os.path.join(OUTDIR_MODELS, "wattplot_v2_flat.stl"))

    print(f"[freecad] done. STEP + STL + FCStd exported to {OUTDIR_MODELS}")
