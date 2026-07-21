"""
Wattplot v2 — Parametric 3D model
Ballasted by soil-filled planter box, no ground anchors.

Coordinate system:
    +X = east (long axis of bed, 8 ft)
    +Y = up
    +Z = south (wind direction in worst-case load)

Outputs:
    models/wattplot_v2.step  - parametric CAD (open in Fusion 360 / FreeCAD)
    models/wattplot_v2.stl   - mesh for slicing / visualization
    renders/wattplot_v2_*.png - 3D renders at multiple angles

PARAMETERS come from wattplot_params.py (single source of truth).
Change a value there and re-run wattplot.py to update everything.
"""

import os
import sys
import math
import cadquery as cq
from cadquery import exporters

# Allow this file to find wattplot_params when run directly
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from wattplot_params import BED, STRUCTURE, PANEL, SOIL

# ----------------------------------------------------------------------------
# Backwards-compatible P dict (legacy code may import P['bed_outer_L'] etc.)
# ----------------------------------------------------------------------------
P = {
    'bed_outer_L':       BED['outer_L_in'],
    'bed_outer_W':       BED['outer_W_in'],
    'bed_soil_depth':    BED['wall_h_in'],
    'bed_wall_thk':      BED['wall_thk_in'],
    'bed_floor_thk':     0.0,
    'bed_wall_height':   BED['wall_h_in'],
    'post_side':         STRUCTURE['post_side_in'],
    'post_height':       STRUCTURE['post_height_in'],
    'post_inset_from_end': STRUCTURE['post_inset_in'],
    'beam_side':         STRUCTURE['beam_side_in'],
    'beam_length':       STRUCTURE['beam_length_in'],
    'beam_attach_h':     STRUCTURE['beam_attach_h_in'],
    'beam_above_panel':  4.0,
    'panel_L':           PANEL['L_in'],
    'panel_W':           PANEL['W_in'],
    'panel_t':           PANEL['thickness_in'],
    'panel_tilt_deg':    PANEL['panel_tilt_deg'],
    'pin_radius':        0.5,
    'soil_depth':        BED['wall_h_in'],
    'soil_color':        (0.40, 0.25, 0.10, 0.55),
    'skid_side':         BED['skid_side_in'],
    'skid_height':       BED['skid_h_in'],
    'hinge_bar_d':       STRUCTURE['hinge_d_in'],
}

# ----------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------
def deg2rad(d): return d * math.pi / 180.0

def make_bed():
    """Bottomless planter box with 4 walls and base skids."""
    boL, boW = P['bed_outer_L'], P['bed_outer_W']
    wt = P['bed_wall_thk']
    wh = P['bed_wall_height']
    skid_h = P['skid_height']
    skid_s = P['skid_side']

    walls = (
        cq.Workplane("XY")
        .box(boL, wh, wt, centered=(True, False, False))  # north wall (long)
        .translate((0, wh/2, -(boW/2 - wt/2)))
    )
    walls = walls.union(
        cq.Workplane("XY")
        .box(boL, wh, wt, centered=(True, False, False))
        .translate((0, wh/2, (boW/2 - wt/2)))
    )
    walls = walls.union(
        cq.Workplane("XY")
        .box(wt, wh, boW - 2*wt, centered=(False, False, True))
        .translate((-(boL/2 - wt/2), wh/2, 0))
    )
    walls = walls.union(
        cq.Workplane("XY")
        .box(wt, wh, boW - 2*wt, centered=(False, False, True))
        .translate(((boL/2 - wt/2), wh/2, 0))
    )

    # Skids
    skids = (
        cq.Workplane("XY")
        .box(boL, skid_s, skid_s, centered=(True, True, True))
        .translate((0, skid_h/2 - skid_s/2, 0))
    )
    skids = skids.union(
        cq.Workplane("XY")
        .box(boL, skid_s, skid_s, centered=(True, True, True))
        .translate((0, skid_h/2 - skid_s/2, boW/2 - skid_s))
    )

    return walls.union(skids)

def make_soil():
    """Soil volume inside the bed (for render visualization)."""
    boL, boW = P['bed_outer_L'], P['bed_outer_W']
    wt = P['bed_wall_thk']
    sd = P['soil_depth']
    soil = (
        cq.Workplane("XY")
        .box(boL - 2*wt, sd, boW - 2*wt, centered=(True, False, True))
        .translate((0, sd/2, 0))
    )
    return soil

def make_posts():
    """Two posts on the high (north, -Z) side of the bed."""
    ps = P['post_side']
    ph = P['post_height']
    inset = P['post_inset_from_end']
    halfL = P['bed_outer_L']/2

    # Posts sit on top of the bed wall, on the north side
    z_pos = -(P['bed_outer_W']/2) + P['bed_wall_thk']/2
    base_y = P['bed_wall_height']

    post1 = (
        cq.Workplane("XY")
        .box(ps, ph, ps, centered=(True, False, True))
        .translate((-(halfL - inset), base_y + ph/2, z_pos))
    )
    post2 = (
        cq.Workplane("XY")
        .box(ps, ph, ps, centered=(True, False, True))
        .translate(((halfL - inset), base_y + ph/2, z_pos))
    )
    return post1.union(post2)

def make_beam():
    """Horizontal beam between the two posts (at the top)."""
    bs = P['beam_side']
    bl = P['beam_length']
    halfL = P['bed_outer_L']/2
    inset = P['post_inset_from_end']
    base_y = P['bed_wall_height']
    bh = P['beam_attach_h']
    z_pos = -(P['bed_outer_W']/2) + P['bed_wall_thk']/2

    return (
        cq.Workplane("XY")
        .box(bl, bs, bs, centered=(True, False, True))
        .translate((0, base_y + bh, z_pos))
    )

def make_panel():
    """Tilted panel, hinged on the low (south, +Z) side, resting on the beam.

    The panel pivots around the south wall top edge.
    Tilt angle is measured from horizontal.
    """
    pL = P['panel_L']
    pW = P['panel_W']
    pt = P['panel_t']
    tilt = deg2rad(P['panel_tilt_deg'])

    base_y = P['bed_wall_height']
    hinge_z = P['bed_outer_W']/2  # south wall top, +Z

    # Build panel in local frame: long axis along +X, pivoting around X axis at origin
    panel = (
        cq.Workplane("XZ")
        .rect(pL, pW, centered=(True, False))
        .extrude(pt)
    )
    # Place the panel so that its hinge edge is at z=hinge_z, y=base_y
    # Local panel: hinge edge along +X at z=0, panel extends in +Z. We want hinge
    # at z=hinge_z, panel extending in -Z (toward the posts).
    # So translate to (-pL/2, ?, hinge_z) in the XZ plane, then rotate about X axis
    # by +tilt (lifts the -Z end up).
    panel = panel.translate((0, 0, pW/2))  # shift so hinge is at z=0
    panel = panel.rotate((0, 0, 0), (1, 0, 0), -math.degrees(tilt))  # negative tilt
    # After rotation, hinge edge stays at z=0, free end goes up (-Z stays same,
    # but we want it going UP not just rotated). Redo:
    panel = (
        cq.Workplane("XZ")
        .rect(pL, pW, centered=(True, False))
        .extrude(pt)
    )
    panel = panel.translate((0, 0, pW/2))  # hinge edge at z=0
    # Rotate about X axis: positive angle lifts +Z end UP. We want the -Z end UP.
    # So negative angle (about X axis using right-hand rule).
    panel = panel.rotate((0, 0, 0), (1, 0, 0), math.degrees(tilt))

    # Now translate to world: hinge at (0, base_y, hinge_z)
    panel = panel.translate((0, base_y, hinge_z))
    return panel

def make_hinge():
    """Continuous hinge on the south (low) side of the bed wall."""
    boL = P['bed_outer_L']
    hinge_z = P['bed_outer_W']/2
    base_y = P['bed_wall_height']
    d = P['hinge_bar_d']

    return (
        cq.Workplane("XZ")
        .rect(boL - 4, d, centered=(True, False))
        .extrude(d*2)
        .translate((0, base_y - d, hinge_z - d/2))
    )

def assemble():
    bed   = make_bed()
    soil  = make_soil()
    posts = make_posts()
    beam  = make_beam()
    panel = make_panel()
    hinge = make_hinge()
    return bed, soil, posts, beam, panel, hinge

# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------
def render_views(parts, outdir):
    """Use cadquery's built-in VTK-based renderer to produce PNGs."""
    from cadquery import exporters
    bed, soil, posts, beam, panel, hinge = parts

    # Color assignment
    bed_c   = cq.Color(0.55, 0.40, 0.25, 1.0)   # wood brown
    soil_c  = cq.Color(*P['soil_color'])
    posts_c = cq.Color(0.45, 0.32, 0.20, 1.0)
    beam_c  = cq.Color(0.45, 0.32, 0.20, 1.0)
    panel_c = cq.Color(0.10, 0.15, 0.30, 1.0)   # solar blue
    hinge_c = cq.Color(0.50, 0.50, 0.55, 1.0)

    assembly = (
        cq.Assembly(name="wattplot_v2")
        .add(bed,   name="bed",   color=bed_c)
        .add(soil,  name="soil",  color=soil_c)
        .add(posts, name="posts", color=posts_c)
        .add(beam,  name="beam",  color=beam_c)
        .add(panel, name="panel", color=panel_c)
        .add(hinge, name="hinge", color=hinge_c)
    )

    # Save STEP and STL
    exporters.export(assembly.toCompound(), os.path.join(outdir, "..", "models", "wattplot_v2.step"))
    exporters.export(assembly.toCompound(), os.path.join(outdir, "..", "models", "wattplot_v2.stl"))

    # Views: top-down, side (north), perspective
    views = [
        ("top",   (-90, 0, 0),  (0, 0, 0)),
        ("side",  (0, -90, 0),  (0, 0, 0)),
        ("front", (0,   0, 0),  (0, 0, 0)),
        ("iso",   (-30, -30, 0),(0, 0, 0)),
    ]
    for name, rot, _ in views:
        try:
            exporters.export(
                assembly.toCompound(),
                os.path.join(outdir, f"wattplot_v2_{name}.png"),
                exportType="PNG",
                opt={
                    "width": 1600, "height": 1200,
                    "marginLeft": 20, "marginTop": 20,
                    "showAxes": False, "showGrid": False,
                    "projectionDir": (rot[0], rot[1], rot[2]),
                },
            )
        except Exception as e:
            print(f"[render] {name} failed: {e}")

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(here, "..", "models")
    renders_dir = os.path.join(here, "..", "renders")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(renders_dir, exist_ok=True)

    print("[model] building parts ...")
    parts = assemble()
    print("[model] exporting STEP and STL ...")
    render_views(parts, renders_dir)
    print("[model] done.")
    print(f"[model] STEP: {os.path.join(models_dir, 'wattplot_v2.step')}")
    print(f"[model] STL : {os.path.join(models_dir, 'wattplot_v2.stl')}")
    print(f"[model] PNG : {renders_dir}\\wattplot_v2_*.png")
