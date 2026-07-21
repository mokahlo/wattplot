"""
Wattplot v2 — 2D engineering side view.
Shows the structure in profile with dimensions, tilt angle, and wind forces.
"""

import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Polygon

# ----------------------------------------------------------------------------
# Geometry (matches wattplot_v2_model.py)
# ----------------------------------------------------------------------------
P = dict(
    bed_outer_L   = 96.0,    # in
    bed_outer_W   = 44.6,
    bed_wall_thk  = 1.5,
    bed_wall_h    = 12.0,
    post_side     = 5.5,
    post_height   = 120.0,
    post_inset    = 6.0,
    beam_side     = 5.5,
    beam_attach_h = 108.0,
    beam_length   = 84.0,
    panel_L       = 97.0,
    panel_W       = 44.6,
    panel_t       = 1.4,
    panel_tilt    = 35.0,
)


def draw_tilt(tilt_deg):
    P['panel_tilt'] = float(tilt_deg)
    fig, ax = plt.subplots(figsize=(13, 9))

    # World coords: X (east) horizontal, Y (up) vertical
    # Bed is at the origin, with X spanning 0..bed_outer_L, Y from 0..bed_wall_h
    bedW = P['bed_outer_W']
    wh   = P['bed_wall_h']
    wt   = P['bed_wall_thk']

    # The "side view" shows the cross-section. We pick a Z slice (z = boW/2 = max width).
    # Actually, the side view shows the YZ plane (looking from +X).
    # In the side view, we show the bed (Y from 0 to wh, Z from -bedW/2 to +bedW/2).

    # Use a 2D coord system where horizontal is Z (south=north) and vertical is Y.
    # So: x_2d = Z, y_2d = Y.

    bed_z0 = -bedW/2
    bed_z1 =  bedW/2

    # ---- Bed (rectangle) ----
    bed = Rectangle((bed_z0, 0), bedW, wh, facecolor='#8d6e63',
                    edgecolor='black', linewidth=1.2, zorder=2, label='Planter bed (8×3.7 ft, 12" walls)')
    ax.add_patch(bed)

    # Soil
    sd = 12.0
    soil = Rectangle((bed_z0 + wt, 0), bedW - 2*wt, sd, facecolor='#5d4037',
                     edgecolor='none', alpha=0.7, zorder=1, label='Soil ballast (~2000 lb wet)')
    ax.add_patch(soil)

    # Skid
    skid_h = 3.0
    skid = Rectangle((bed_z0, -skid_h), bedW, skid_h, facecolor='#5d4037',
                     edgecolor='black', linewidth=0.8, zorder=1.5)
    ax.add_patch(skid)

    # ---- Posts (north side, at z = -bedW/2 + wt/2, on top of north wall) ----
    z_post = -bedW/2 + wt/2
    ps = P['post_side']
    ph = P['post_height']
    post = Rectangle((z_post - ps/2, wh), ps, ph, facecolor='#6d4c41',
                     edgecolor='black', linewidth=1.0, zorder=2.5,
                     label='6×6 post (10 ft, hinged at bed wall)')
    ax.add_patch(post)

    # ---- Beam (horizontal, between posts at high side) ----
    bs = P['beam_side']
    bl = P['beam_length']
    bh = P['beam_attach_h']
    beam = Rectangle((z_post - bl/2, wh + bh - bs/2), bl, bs, facecolor='#6d4c41',
                     edgecolor='black', linewidth=1.0, zorder=2.5)
    ax.add_patch(beam)

    # ---- Panel ----
    pL = P['panel_L']
    pW = P['panel_W']
    pt = P['panel_t']
    tilt = math.radians(P['panel_tilt'])
    hinge_z = bedW/2  # south wall top
    hinge_y = wh

    # Build panel as a rectangle, rotate about hinge, place
    # In local frame: rectangle from (-pL/2, -pt/2) to (pL/2, pt/2)
    # But in side view we see the panel as a 2D shape (its YZ projection).
    # The panel is 3.72 ft in Z (the tilted direction) and 1.4" in Y (thickness).
    # After rotation by tilt about the X axis (the long axis of the panel),
    # the YZ projection of the panel is a tilted rectangle.

    # The panel "tilted" face: from hinge (z=hinge_z, y=hinge_y) extending in direction
    # (cos(tilt+90°), sin(tilt+90°)) in YZ? Actually:
    # Panel normal is (0, cos(tilt), -sin(tilt)) [up and toward south = +Z]
    # Panel extends from hinge in direction (-Z, +Y) = (-cos(tilt), +sin(tilt)) in YZ
    # Wait, let me think. The panel long axis is X, the tilt direction is YZ.
    # Tilt angle is from horizontal. Un-rotated panel: lies in XZ plane, normal in +Y.
    # Rotated by tilt about X axis: panel long axis still along X, but the panel
    # itself is tilted up. The "tilt direction" is in the YZ plane.
    # From hinge, the panel extends in direction (-sin(tilt), -cos(tilt)) in (Y, Z)?
    # Let's just compute the high edge in (Y, Z):
    # The panel width direction is from hinge to high edge: this direction in (Y, Z) is
    # (sin(tilt), -cos(tilt))? Let's check at tilt=0: panel lies flat, direction is (0, -1)
    # in (Y, Z) — extends in -Z (north). At tilt=90: panel vertical, direction is (1, 0) in
    # (Y, Z) — extends in +Y (up). At tilt=35: direction is (sin(35), -cos(35)) = (0.574, -0.819).
    # So high edge relative to hinge: (Y, Z) = hinge + pW * (sin(tilt), -cos(tilt))
    # = (hinge_y + pW*sin(tilt), hinge_z - pW*cos(tilt))

    high_y = hinge_y + pW * math.sin(tilt)
    high_z = hinge_z - pW * math.cos(tilt)

    # Panel as polygon (top face only, visible from south):
    # 4 corners in (z, y) since the side view shows YZ plane:
    #   hinge-low:  (hinge_z, hinge_y)
    #   hinge-high: (hinge_z, hinge_y + pt) -- but in YZ this is a thin strip
    #   high-low:   (high_z, high_y)
    #   high-high:  (high_z, high_y + pt)
    # For the side view, just show the bottom face (top is parallel, very close).

    panel_low = Polygon(
        [(hinge_z, hinge_y), (high_z, high_y),
         (high_z, high_y + pt), (hinge_z, hinge_y + pt)],
        facecolor='#1a237e', edgecolor='black', linewidth=1.0, zorder=3,
        label=f'Panel (8.08×3.72 ft, ~620W bifacial @ {P["panel_tilt"]:.0f}°)'
    )
    ax.add_patch(panel_low)

    # Hinge line
    ax.plot([hinge_z, hinge_z], [hinge_y - 0.5, hinge_y + 1.5], 'k-', linewidth=2, zorder=4)

    # ---- Annotations ----
    # Tilt angle arc
    arc_center = (hinge_z, hinge_y)
    arc_r = 14
    angle_start = 180  # pointing west (-Z) in the side view
    angle_end = 180 - math.degrees(tilt)
    arc = mpatches.Arc(arc_center, 2*arc_r, 2*arc_r, angle=0,
                       theta1=angle_end, theta2=angle_start,
                       color='red', linewidth=1.5, zorder=5)
    ax.add_patch(arc)
    ax.text(hinge_z - arc_r*1.4, hinge_y + 2,
            f"{P['panel_tilt']:.0f}° tilt", color='red', fontsize=11, weight='bold')

    # Height dimension
    ax.annotate("", xy=(bedW/2 + 4, 0), xytext=(bedW/2 + 4, wh + bh + bs),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=1.2))
    ax.text(bedW/2 + 6, (wh + bh + bs)/2, f"{((wh + bh + bs)/12):.1f} ft\ncanopy height",
            color='blue', fontsize=10, va='center')

    # Panel length dimension
    ax.annotate("", xy=(hinge_z, hinge_y - 4), xytext=(high_z, high_y - 4),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1.0))
    mid_z = (hinge_z + high_z) / 2
    mid_y = (hinge_y + high_y) / 2 - 4
    ax.text(mid_z, mid_y - 4, f'Panel {pW/12:.2f} ft\n(tilted direction)',
            color='green', fontsize=9, ha='center')

    # Bed width
    ax.annotate("", xy=(bed_z0, -skid_h - 5), xytext=(bed_z1, -skid_h - 5),
                arrowprops=dict(arrowstyle='<->', color='black', lw=0.8))
    ax.text(0, -skid_h - 9, f'Bed: {bedW/12:.2f} ft wide',
            ha='center', fontsize=9)

    # Soil label
    ax.text(0, sd/2, 'Soil\nballast', ha='center', va='center',
            color='white', fontsize=10, weight='bold')

    # Wind arrow (south, hitting the panel)
    wind_z = -bedW/2 - 8
    wind_y = high_y - 10
    ax.annotate("", xy=(wind_z, wind_y), xytext=(wind_z - 18, wind_y),
                arrowprops=dict(arrowstyle='->', color='red', lw=2.0))
    ax.text(wind_z - 22, wind_y + 2, "Wind 115 mph\n(from south)", color='red', fontsize=10, ha='right', weight='bold')

    # Force vectors on panel (decomposed) -- computed for this tilt
    tilt_rad = math.radians(tilt_deg)
    fv = round(24.5 * (P['panel_L']/12) * (P['panel_W']/12) * 1.5 * math.sin(tilt_rad) * math.cos(tilt_rad))  # uplift
    fh = round(24.5 * (P['panel_L']/12) * (P['panel_W']/12) * 1.5 * math.sin(tilt_rad) * math.sin(tilt_rad))  # drag
    centroid_y = (hinge_y + high_y) / 2
    centroid_z = (hinge_z + high_z) / 2
    ax.annotate("", xy=(centroid_z, centroid_y + 12), xytext=(centroid_z, centroid_y),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.5))
    ax.text(centroid_z + 1, centroid_y + 14, f"↑ {fv} lb\nuplift", color='#c0392b', fontsize=8)
    ax.annotate("", xy=(centroid_z - 12, centroid_y), xytext=(centroid_z, centroid_y),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5))
    ax.text(centroid_z - 14, centroid_y + 2, f"{fh} lb →\ndrag", color='#2c3e50', fontsize=8, ha='right')

    # Bed pivot label
    pivot = (-bedW/2, 0)
    ax.plot(*pivot, 'ko', markersize=6, zorder=5)
    ax.annotate("Pivot for\noverturning", pivot, textcoords="offset points",
                xytext=(-90, -10), fontsize=8, color='black')

    # ---- Layout ----
    ax.set_xlim(-bedW - 30, bedW + 30)
    ax.set_ylim(-15, wh + bh + bs + 20)
    ax.set_aspect('equal')
    ax.set_xlabel("Z (south ←  → north, inches)")
    ax.set_ylabel("Y (up, inches)")
    ax.set_title("Wattplot v2 — Side view (looking from east)\n"
                 f"8×3.7 ft bed, 6×6 posts, {pL/12:.1f}×{pW/12:.2f} ft panel @ {P['panel_tilt']:.0f}° tilt, "
                 f"hinge on south wall, ballasted by soil")
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(__file__), "..", "renders", f"wattplot_v2_side_view_{tilt_deg:03d}.png")
    plt.savefig(out, dpi=140)
    plt.close()
    print(f"[drawing] wrote {out}")


if __name__ == "__main__":
    for tilt_to_draw in (35, 90):
        draw_tilt(tilt_to_draw)
