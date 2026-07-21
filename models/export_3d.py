"""
Wattplot v2 — Export a 3MF file and a simple HTML viewer wrapping the STEP.
3MF is a modern 3D format supported by Windows 3D Viewer and most browsers.

Parameters come from wattplot_params.py.
"""

import os
import sys
import math
import cadquery as cq
from cadquery import exporters

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from wattplot_params import BED, STRUCTURE, PANEL

# Local aliases for clarity
P = {
    'bed_outer_L':   BED['outer_L_in'],
    'bed_outer_W':   BED['outer_W_in'],
    'bed_wall_thk':  BED['wall_thk_in'],
    'bed_wall_h':    BED['wall_h_in'],
    'skid_h':        BED['skid_h_in'],
    'skid_side':     BED['skid_side_in'],
    'post_side':     STRUCTURE['post_side_in'],
    'post_height':   STRUCTURE['post_height_in'],
    'post_inset':    STRUCTURE['post_inset_in'],
    'beam_side':     STRUCTURE['beam_side_in'],
    'beam_length':   STRUCTURE['beam_length_in'],
    'beam_attach_h': STRUCTURE['beam_attach_h_in'],
    'panel_L':       PANEL['L_in'],
    'panel_W':       PANEL['W_in'],
    'panel_t':       PANEL['thickness_in'],
    'panel_tilt':    PANEL['panel_tilt_deg'],
}


def build_model():
    boL, boW = P['bed_outer_L'], P['bed_outer_W']
    wt       = P['bed_wall_thk']
    wh       = P['bed_wall_h']
    skid_h   = P['skid_h']
    skid_s   = P['skid_side']

    # Bed
    n_wall = cq.Workplane("XY").box(boL, wh, wt, centered=(True, False, False)).translate((0, wh/2, -boW/2 + wt/2))
    s_wall = cq.Workplane("XY").box(boL, wh, wt, centered=(True, False, False)).translate((0, wh/2,  boW/2 - wt/2))
    w_wall = cq.Workplane("XY").box(wt, wh, boW - 2*wt, centered=(False, False, True)).translate((-boL/2 + wt/2, wh/2, 0))
    e_wall = cq.Workplane("XY").box(wt, wh, boW - 2*wt, centered=(False, False, True)).translate(( boL/2 - wt/2, wh/2, 0))
    bed = n_wall.union(s_wall).union(w_wall).union(e_wall)
    skid1 = cq.Workplane("XY").box(boL, skid_s, skid_s, centered=(True, True, True)).translate((0, skid_h/2 - skid_s/2, 0))
    skid2 = cq.Workplane("XY").box(boL, skid_s, skid_s, centered=(True, True, True)).translate((0, skid_h/2 - skid_s/2, boW/2 - skid_s))
    bed = bed.union(skid1).union(skid2)

    # Posts
    ps, ph, inset = P['post_side'], P['post_height'], P['post_inset']
    base_y = wh
    z_post = -boW/2 + wt/2
    post1 = cq.Workplane("XY").box(ps, ph, ps, centered=(True, False, True)).translate((-boL/2 + inset, base_y + ph/2, z_post))
    post2 = cq.Workplane("XY").box(ps, ph, ps, centered=(True, False, True)).translate(( boL/2 - inset, base_y + ph/2, z_post))
    posts = post1.union(post2)

    # Beam
    bs, bl, bh = P['beam_side'], P['beam_length'], P['beam_attach_h']
    beam = cq.Workplane("XY").box(bl, bs, bs, centered=(True, False, True)).translate((0, base_y + bh, z_post))

    # Panel
    pL, pW, pt, tilt = P['panel_L'], P['panel_W'], P['panel_t'], P['panel_tilt']
    hinge_y = wh
    hinge_z = boW/2
    panel = cq.Workplane("XZ").rect(pL, pW, centered=(True, True)).extrude(pt)
    panel = panel.rotate((0, 0, 0), (1, 0, 0), math.degrees(tilt))
    panel = panel.translate((0, hinge_y + pW/2 * math.sin(tilt), hinge_z - pW/2 * math.cos(tilt)))

    # Hinge
    hinge_d = 0.5
    hinge = cq.Workplane("XZ").rect(boL - 4, hinge_d, centered=(True, False)).extrude(hinge_d*2).translate((0, hinge_y - hinge_d, hinge_z - hinge_d/2))

    return bed.union(posts).union(beam).union(panel).union(hinge)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(here, "..", "models")
    renders_dir = os.path.join(here, "..", "renders")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(renders_dir, exist_ok=True)

    model = build_model()
    model = model.val()  # Workplane -> Shape

    # Export 3MF, STEP, STL, VRML
    exporters.export(model, os.path.join(models_dir, "wattplot_v2.3mf"), exportType="3MF")
    print("[export] 3MF ->", os.path.join(models_dir, "wattplot_v2.3mf"))

    exporters.export(model, os.path.join(models_dir, "wattplot_v2.step"), exportType="STEP")
    print("[export] STEP ->", os.path.join(models_dir, "wattplot_v2.step"))

    exporters.export(model, os.path.join(models_dir, "wattplot_v2.stl"), exportType="STL", tolerance=0.5)
    print("[export] STL  ->", os.path.join(models_dir, "wattplot_v2.stl"))

    exporters.export(model, os.path.join(models_dir, "wattplot_v2.wrl"), exportType="VRML")
    print("[export] VRML ->", os.path.join(models_dir, "wattplot_v2.wrl"))


if __name__ == "__main__":
    main()
