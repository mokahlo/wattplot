"""
Wattplot v2 — Render the cadquery model as clean orthographic SVGs.
getSVG handles z-ordering properly, so the panel is visible.
"""

import os
import math
import cadquery as cq
from cadquery import exporters

# Geometry (matches wattplot_v2_model.py)
P = dict(
    bed_outer_L   = 96.0,
    bed_outer_W   = 44.6,
    bed_wall_thk  = 1.5,
    bed_wall_h    = 12.0,
    skid_h        = 3.0,
    skid_side     = 3.5,
    post_side     = 5.5,
    post_height   = 120.0,
    post_inset    = 6.0,
    beam_side     = 5.5,
    beam_length   = 84.0,
    beam_attach_h = 108.0,
    panel_L       = 97.0,
    panel_W       = 44.6,
    panel_t       = 1.4,
    panel_tilt    = 35.0,
)


def build_model():
    """Build the full assembly as a single compound."""
    boL, boW = P['bed_outer_L'], P['bed_outer_W']
    wt       = P['bed_wall_thk']
    wh       = P['bed_wall_h']
    skid_h   = P['skid_h']
    skid_s   = P['skid_side']

    # 4 walls
    n_wall = cq.Workplane("XY").box(boL, wh, wt, centered=(True, False, False)).translate((0, wh/2, -boW/2 + wt/2))
    s_wall = cq.Workplane("XY").box(boL, wh, wt, centered=(True, False, False)).translate((0, wh/2,  boW/2 - wt/2))
    w_wall = cq.Workplane("XY").box(wt, wh, boW - 2*wt, centered=(False, False, True)).translate((-boL/2 + wt/2, wh/2, 0))
    e_wall = cq.Workplane("XY").box(wt, wh, boW - 2*wt, centered=(False, False, True)).translate(( boL/2 - wt/2, wh/2, 0))
    bed = n_wall.union(s_wall).union(w_wall).union(e_wall)

    # Skids
    skid1 = cq.Workplane("XY").box(boL, skid_s, skid_s, centered=(True, True, True)).translate((0, skid_h/2 - skid_s/2, 0))
    skid2 = cq.Workplane("XY").box(boL, skid_s, skid_s, centered=(True, True, True)).translate((0, skid_h/2 - skid_s/2, boW/2 - skid_s))
    bed = bed.union(skid1).union(skid2)

    # Posts (high side, -Z)
    ps, ph, inset = P['post_side'], P['post_height'], P['post_inset']
    base_y = wh
    z_post = -boW/2 + wt/2
    post1 = cq.Workplane("XY").box(ps, ph, ps, centered=(True, False, True)).translate((-boL/2 + inset, base_y + ph/2, z_post))
    post2 = cq.Workplane("XY").box(ps, ph, ps, centered=(True, False, True)).translate(( boL/2 - inset, base_y + ph/2, z_post))
    posts = post1.union(post2)

    # Beam
    bs, bl, bh = P['beam_side'], P['beam_length'], P['beam_attach_h']
    beam = cq.Workplane("XY").box(bl, bs, bs, centered=(True, False, True)).translate((0, base_y + bh, z_post))

    # Panel — build in local frame, rotate about X axis through hinge, translate
    pL, pW, pt, tilt = P['panel_L'], P['panel_W'], P['panel_t'], P['panel_tilt']
    hinge_y = wh
    hinge_z = boW/2

    # Local panel: center at origin, extents -pL/2..pL/2 (X), -pt/2..pt/2 (Y), -pW/2..pW/2 (Z)
    panel = cq.Workplane("XZ").rect(pL, pW, centered=(True, True)).extrude(pt)
    # Center in Z, then rotate
    panel = panel.rotate((0, 0, 0), (1, 0, 0), math.degrees(tilt))
    # Translate so that the +Z edge (after rotation) is at the hinge
    # The +Z edge in local at z=+pW/2 rotates to: y'=-pW/2*sin(tilt), z'=+pW/2*cos(tilt)
    # To put it at world (0, hinge_y, hinge_z), translate by:
    tx, ty, tz = 0, hinge_y - (-pW/2 * math.sin(tilt)), hinge_z - (pW/2 * math.cos(tilt))
    # But the panel was rotated about origin; the +Z edge in world after rotation is at (0, -pW/2*sin(tilt), +pW/2*cos(tilt)).
    # To put this at (0, hinge_y, hinge_z), translation = (0, hinge_y - (-pW/2*sin), hinge_z - pW/2*cos)
    #                                            = (0, hinge_y + pW/2*sin, hinge_z - pW/2*cos)
    panel = panel.translate((0, hinge_y + pW/2 * math.sin(tilt), hinge_z - pW/2 * math.cos(tilt)))

    # Hinge bar
    hinge_d = 0.5
    hinge = cq.Workplane("XZ").rect(boL - 4, hinge_d, centered=(True, False)).extrude(hinge_d*2).translate((0, hinge_y - hinge_d, hinge_z - hinge_d/2))

    return bed.union(posts).union(beam).union(panel).union(hinge)


def render_views(outdir):
    model = build_model().val()  # convert Workplane to Shape

    # CadQuery getSVG uses a projection direction (camera direction).
    # In CadQuery's convention: projectionDir is the direction the camera looks
    # (from the camera into the scene). For a TOP view, look down -Y: projectionDir=(0, -1, 0)
    # For a NORTH side view (looking south), camera is at -Z looking +Z: projectionDir=(0, 0, 1)
    # For an EAST side view (looking west), camera is at +X looking -X: projectionDir=(-1, 0, 0)
    # For an ISO view, projectionDir=(1, 1, 1) or similar.
    views = [
        ("iso",        ( 1,  0.6,  1)),
        ("top",        ( 0, -1,    0)),
        ("north_side", ( 0,  0,    1)),    # looking south
        ("east_side",  (-1,  0,    0)),    # looking west
    ]
    for name, proj in views:
        svg = exporters.getSVG(
            model,
            opts={
                "width": 1600,
                "height": 1100,
                "marginLeft": 20,
                "marginTop": 20,
                "projectionDir": proj,
                "strokeWidth": 2.5,           # was 0.6 — too thin after scale
                "strokeColor": (0, 0, 0),
                "hiddenColor": (160, 160, 160),
                "showHidden": False,
            }
        )
        svg_path = os.path.join(outdir, f"wattplot_v2_{name}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"[svg] wrote {svg_path}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "..", "renders")
    os.makedirs(outdir, exist_ok=True)
    render_views(outdir)
    print("[svg] done.")
