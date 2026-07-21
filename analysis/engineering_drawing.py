"""
Wattplot v2 — 2D engineering side view.
Shows the structure in profile with dimensions, tilt angle, and wind forces.

Design (v2 — all-wood frame):
  - Bed: 2x12 PT lumber, half-lap corners, on 4x4 skids, bottomless
  - Frame: 2x6 PT perimeter around the panel, 2x4 PT diagonal brace
  - Hinge: 4 × galvanized butt hinges, ½" pin, on the bed's south wall
  - Panel clamp: 6 × aluminum mid-clamps on the rails
  - Actuator mount: 2x6 clevis on the north rail, 2x6 block on north wall
  - No posts, no beam — the wood frame is the structure
"""
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, Polygon

# ----------------------------------------------------------------------------
# Geometry (matches wattplot_params.py + models/freecad/parts/*.py)
# ----------------------------------------------------------------------------
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from wattplot_params import BED, PANEL
from models.freecad.materials import LUMBER

P = dict(
    bed_outer_L   = BED['outer_L_in'],
    bed_outer_W   = BED['outer_W_in'],
    bed_wall_thk  = LUMBER['2x12']['actual_t'],   # 1.5
    bed_wall_h    = LUMBER['2x12']['actual_h'],   # 11.25 (actual 2x12, not nominal 12)
    skid_h        = BED['skid_h_in'],
    panel_L       = PANEL['L_in'],
    panel_W       = PANEL['W_in'],
    panel_t       = PANEL['thickness_in'],
    panel_tilt    = PANEL['panel_tilt_deg'],
    # Frame members
    rail_W        = LUMBER['2x6']['actual_t'],   # 1.5
    rail_H        = LUMBER['2x6']['actual_h'],   # 5.5
    brace_W       = LUMBER['2x4']['actual_t'],   # 1.5
    brace_H       = LUMBER['2x4']['actual_h'],   # 3.5
)


def draw_tilt(tilt_deg):
    P['panel_tilt'] = float(tilt_deg)
    fig, ax = plt.subplots(figsize=(14, 10))

    # World coords (side view = YZ plane looking from +X east).
    # In 2D: x_2d = Z (south=north), y_2d = Y (up).
    # +Z = south, -Z = north.
    bedW = P['bed_outer_W']
    wh   = P['bed_wall_h']
    wt   = P['bed_wall_thk']
    skid_h = P['skid_h']

    bed_z0 = -bedW/2   # north outer face
    bed_z1 =  bedW/2   # south outer face

    # ---- Bed walls (south + north visible in side view) ----
    bed = Rectangle((bed_z0, 0), bedW, wh,
                    facecolor='#8d6e63', edgecolor='black',
                    linewidth=1.2, zorder=2,
                    label='Planter bed (8×3.7 ft, 2x12 PT walls, 11.25" soil depth)')
    ax.add_patch(bed)

    # Soil
    sd = wh
    soil = Rectangle((bed_z0 + wt, 0), bedW - 2*wt, sd,
                     facecolor='#5d4037', edgecolor='none', alpha=0.7, zorder=1,
                     label='Soil ballast (~2000 lb wet)')
    ax.add_patch(soil)

    # Skid
    skid = Rectangle((bed_z0, -skid_h), bedW, skid_h,
                     facecolor='#5d4037', edgecolor='black',
                     linewidth=0.8, zorder=1.5)
    ax.add_patch(skid)

    # ---- Frame (long rails — south + north — sit on top of the bed walls) ----
    rail_t = P['rail_W']    # 1.5
    rail_h = P['rail_H']    # 5.5
    frame_y = wh            # bottom of frame at top of bed wall
    # South long rail (hinged)
    south_rail = Rectangle((bedW/2 - rail_t, frame_y), rail_t, rail_h,
                           facecolor='#a1887f', edgecolor='black',
                           linewidth=1.0, zorder=2.5,
                           label='Frame long rail (2x6 PT)')
    ax.add_patch(south_rail)
    # North long rail (actuator side)
    north_rail = Rectangle((-bedW/2, frame_y), rail_t, rail_h,
                           facecolor='#a1887f', edgecolor='black',
                           linewidth=1.0, zorder=2.5)
    ax.add_patch(north_rail)

    # ---- Hinge (on top of south wall, between wall and frame) ----
    hinge_y = frame_y
    hinge_z = bedW/2
    # Hinge pin (small cylinder, drawn as a black bar)
    hinge = Rectangle((hinge_z - 0.25, hinge_y - 1.0), 0.5, 2.0,
                      facecolor='#37474f', edgecolor='black', linewidth=0.8, zorder=4,
                      label='4× butt hinge, ½" pin')
    ax.add_patch(hinge)
    # Hinge leaves
    wall_leaf = Rectangle((hinge_z - 2, hinge_y - 0.1), 4, 0.1,
                          facecolor='#90a4ae', edgecolor='black', linewidth=0.5, zorder=3.5)
    rail_leaf = Rectangle((hinge_z - rail_t, hinge_y + 0.0), rail_t, 0.1,
                          facecolor='#90a4ae', edgecolor='black', linewidth=0.5, zorder=3.5)
    ax.add_patch(wall_leaf)
    ax.add_patch(rail_leaf)

    # ---- Panel + tilted frame north rail ----
    pW = P['panel_W']
    pt = P['panel_t']
    tilt = math.radians(P['panel_tilt'])

    # Panel hinge at the top of the south wall, at z=bedW/2, y=wh
    # When tilted by angle θ, the north end of the panel rises:
    # high edge in (Y, Z): (wh + pW*sin(tilt), bedW/2 - pW*cos(tilt))
    high_y = wh + pW * math.sin(tilt)
    high_z = bedW/2 - pW * math.cos(tilt)

    # Panel as a thin polygon
    panel = Polygon(
        [(bedW/2, wh), (high_z, high_y),
         (high_z, high_y + pt), (bedW/2, wh + pt)],
        facecolor='#1a237e', edgecolor='black', linewidth=1.0, zorder=3,
        label=f'Panel (8.08×3.72 ft, ~620W bifacial @ {P["panel_tilt"]:.0f}°)'
    )
    ax.add_patch(panel)

    # Tilted north rail — sits on top of the panel's north edge.
    # At tilt, the rail's hinge side stays at (bedW/2 - rail_t, wh+rail_h)
    # and the free end follows the panel tilt. The 4 corners of the top face
    # are computed by rotating the rail's cross-section about the south hinge.
    rail_north_top = Polygon(
        [(bedW/2 - rail_t, wh + rail_h),
         (high_z - rail_t * math.cos(tilt), high_y + rail_h * math.cos(tilt) + pt),
         (high_z, high_y + pt + rail_h),
         (bedW/2, wh + rail_h)],
        facecolor='#a1887f', edgecolor='black', linewidth=0.8, zorder=2.5
    )
    ax.add_patch(rail_north_top)

    # Diagonal brace (visible in side view as a tilted line inside the frame).
    # Note: we don't draw the brace in the side view — it's a 2x4 in the
    # frame's plane, parallel to the panel face. It would appear edge-on in
    # this view as a thin line, which doesn't add information.

    # ---- Actuator (between bed's north wall block and the frame's north rail) ----
    # The actuator is a 4" stroke linear actuator. At any tilt, it spans
    # between the bed's north wall (fixed block) and the frame's north rail
    # (which moves with the tilt). The actuator is drawn as a thick line
    # with a motor body and a rod.
    actuator_mount_n = (-bedW/2, wh)              # on top of north wall
    # Frame north rail top: at tilt, the rail top edge has moved up.
    # Use the tilted north rail's top inside corner as the actuator attach point.
    actuator_mount_f = (high_z, high_y + pt)      # bottom of tilted north rail (frame side)
    # Draw the actuator body + rod
    act = Polygon(
        [actuator_mount_n, (actuator_mount_n[0] + 0.5, actuator_mount_n[1]),
         (actuator_mount_f[0] + 0.5, actuator_mount_f[1]), actuator_mount_f],
        facecolor='#455a64', edgecolor='black', linewidth=0.6, zorder=2.7,
        label='Linear actuator (4" stroke, 330 lbf)'
    )
    ax.add_patch(act)

    # ---- Tilt angle arc ----
    arc_center = (hinge_z, hinge_y)
    arc_r = 14
    # At 0° tilt, the panel lies in the XZ plane (in side view, it's a horizontal line at y=wh).
    # The arc goes from "flat" (angle 0, pointing -Z) to "tilted" (angle = tilt, pointing up-left).
    # The horizontal line in side view is the -Z direction. The tilt direction is up-and-to-the-left.
    # The angle arc goes from -Z (180° in screen coords where +X is 0°) to the panel direction.
    # Panel direction from hinge in 2D = (high_z - hinge_z, high_y - hinge_y) = (-pW*cos(tilt), pW*sin(tilt))
    # Angle of this vector from +X axis = atan2(pW*sin(tilt), -pW*cos(tilt)) = pi - tilt
    # In screen coords (y goes down), atan2 gives... let's just draw the arc from "south" (0°)
    # to the panel direction (which is up-and-to-the-left, so a negative angle in matplotlib's
    # standard convention).
    arc = mpatches.Arc(arc_center, 2*arc_r, 2*arc_r, angle=0,
                       theta1=180 - math.degrees(tilt), theta2=180,
                       color='red', linewidth=1.5, zorder=5)
    ax.add_patch(arc)
    ax.text(hinge_z - arc_r*1.4, hinge_y + 2,
            f"{P['panel_tilt']:.0f}° tilt", color='red', fontsize=11, weight='bold')

    # ---- Dimension annotations ----
    # Bed width
    ax.annotate("", xy=(bed_z0, -skid_h - 5), xytext=(bed_z1, -skid_h - 5),
                arrowprops=dict(arrowstyle='<->', color='black', lw=0.8))
    ax.text(0, -skid_h - 9, f'Bed: {bedW/12:.2f} ft wide',
            ha='center', fontsize=9)

    # Frame height (rail height above the wall)
    ax.annotate("", xy=(bedW/2 + 4, wh), xytext=(bedW/2 + 4, wh + rail_h),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=1.0))
    ax.text(bedW/2 + 6, wh + rail_h/2, f"{rail_h:.1f}\"\n2x6 rail",
            color='blue', fontsize=9, va='center')

    # Panel high Y dimension (when tilted)
    ax.annotate("", xy=(high_z + 2, wh), xytext=(high_z + 2, high_y),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1.0))
    ax.text(high_z + 4, (wh + high_y)/2, f"high\n{((high_y-wh)/12):.1f} ft",
            color='green', fontsize=8, va='center')

    # Soil label
    ax.text(0, sd/2, 'Soil\nballast', ha='center', va='center',
            color='white', fontsize=10, weight='bold')

    # Wind arrow (from south, hitting the panel)
    wind_y = high_y - 8
    ax.annotate("", xy=(bedW/2 + 4, wind_y), xytext=(bedW/2 + 20, wind_y),
                arrowprops=dict(arrowstyle='->', color='red', lw=2.0))
    ax.text(bedW/2 + 22, wind_y + 2, "Wind 115 mph\n(from south)", color='red', fontsize=10, ha='left', weight='bold')

    # Force vectors on panel (decomposed)
    tilt_rad = math.radians(tilt_deg)
    fv = round(24.5 * (P['panel_L']/12) * (P['panel_W']/12) * 1.5 * math.sin(tilt_rad) * math.cos(tilt_rad))
    fh = round(24.5 * (P['panel_L']/12) * (P['panel_W']/12) * 1.5 * math.sin(tilt_rad) * math.sin(tilt_rad))
    centroid_y = (wh + high_y) / 2
    centroid_z = (bedW/2 + high_z) / 2
    ax.annotate("", xy=(centroid_z, centroid_y + 10), xytext=(centroid_z, centroid_y),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.5))
    ax.text(centroid_z + 1, centroid_y + 12, f"↑ {fv} lb\nuplift", color='#c0392b', fontsize=8)
    ax.annotate("", xy=(centroid_z - 10, centroid_y), xytext=(centroid_z, centroid_y),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5))
    ax.text(centroid_z - 12, centroid_y + 2, f"{fh} lb →\ndrag", color='#2c3e50', fontsize=8, ha='right')

    # Pivot for overturning (north-bottom corner)
    pivot = (-bedW/2, 0)
    ax.plot(*pivot, 'ko', markersize=6, zorder=5)
    ax.annotate("Pivot for\noverturning", pivot, textcoords="offset points",
                xytext=(-90, -10), fontsize=8, color='black')

    # ---- Layout ----
    ax.set_xlim(-bedW - 5, bedW + 35)
    ax.set_ylim(-15, max(wh + rail_h + 5, high_y + 10))
    ax.set_aspect('equal')
    ax.set_xlabel("Z (north ←  → south, inches)")
    ax.set_ylabel("Y (up, inches)")
    ax.set_title(f"Wattplot v2 — Side view (looking from east)\n"
                 f"8×3.7 ft bed, 2x6 PT frame around panel, "
                 f"620W bifacial @ {P['panel_tilt']:.0f}° tilt, hinged on south wall")
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(__file__), "..", "renders",
                       f"wattplot_v2_side_view_{tilt_deg:03d}.png")
    plt.savefig(out, dpi=140)
    plt.close()
    print(f"[drawing] wrote {out}")


if __name__ == "__main__":
    for tilt_to_draw in (35, 90):
        draw_tilt(tilt_to_draw)
