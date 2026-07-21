"""
Wattplot v2 — 3D visualization (matplotlib)
Renders the model from multiple angles as PNGs for the report.
"""

import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# ----------------------------------------------------------------------------
# Geometry (must match wattplot_v2_model.py)
# ----------------------------------------------------------------------------
P = dict(
    bed_outer_L   = 96.0,
    bed_outer_W   = 44.6,
    bed_wall_thk  = 1.5,
    bed_wall_h    = 12.0,
    skid_h        = 3.0,
    skid_side     = 3.5,
    soil_depth    = 12.0,
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


def box_faces(cx, cy, cz, sx, sy, sz, color, alpha=1.0):
    """Return 6 face polygons of a box (centered at cx,cy,cz, size sx,sy,sz)."""
    x0, x1 = cx - sx/2, cx + sx/2
    y0, y1 = cy - sy/2, cy + sy/2
    z0, z1 = cz - sz/2, cz + sz/2
    faces = [
        # +X
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], color),
        # -X
        ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], color),
        # +Y
        ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], color),
        # -Y
        ([(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)], color),
        # +Z
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], color),
        # -Z
        ([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], color),
    ]
    return faces


def add_box(ax, cx, cy, cz, sx, sy, sz, color, alpha=1.0):
    for poly, col in box_faces(cx, cy, cz, sx, sy, sz, color, alpha):
        coll = Poly3DCollection([poly], facecolors=[col], edgecolors='black',
                                linewidths=0.4, alpha=alpha)
        ax.add_collection3d(coll)


def assemble_scene(ax):
    """Draw the whole model into a matplotlib 3D axes."""
    boL, boW = P['bed_outer_L'], P['bed_outer_W']
    wt       = P['bed_wall_thk']
    wh       = P['bed_wall_h']
    skid_h   = P['skid_h']
    skid_s   = P['skid_side']
    sd       = P['soil_depth']

    bed_brown   = (0.55, 0.40, 0.25)
    soil_brown  = (0.40, 0.25, 0.10)
    wood_brown  = (0.45, 0.32, 0.20)
    panel_blue  = (0.10, 0.15, 0.30)
    hinge_gray  = (0.50, 0.50, 0.55)

    # 4 walls (perimeter of bed), centered on Y = wh/2
    # North wall (-Z)
    add_box(ax, 0, wh/2, -boW/2 + wt/2, boL, wh, wt, bed_brown)
    # South wall (+Z)
    add_box(ax, 0, wh/2, boW/2 - wt/2, boL, wh, wt, bed_brown)
    # West wall (-X)
    add_box(ax, -boL/2 + wt/2, wh/2, 0, wt, wh, boW - 2*wt, bed_brown)
    # East wall (+X)
    add_box(ax, boL/2 - wt/2, wh/2, 0, wt, wh, boW - 2*wt, bed_brown)

    # Skids (2 under the bed, full length, raised)
    add_box(ax, 0, skid_s/2 - skid_s/2, 0, boL, skid_s, skid_s, wood_brown)
    add_box(ax, 0, skid_s/2 - skid_s/2, boW/2 - skid_s, boL, skid_s, skid_s, wood_brown)

    # Soil volume inside the bed
    add_box(ax, 0, sd/2, 0, boL - 2*wt, sd, boW - 2*wt, soil_brown, alpha=0.65)

    # 2 high-side posts (north end, on the bed wall)
    ps, ph, inset = P['post_side'], P['post_height'], P['post_inset']
    base_y = wh
    z_post = -boW/2 + wt/2
    for x_pos in [-boL/2 + inset, boL/2 - inset]:
        add_box(ax, x_pos, base_y + ph/2, z_post, ps, ph, ps, wood_brown)

    # Horizontal beam (north of posts, at the top)
    bs, bl, bh = P['beam_side'], P['beam_length'], P['beam_attach_h']
    add_box(ax, 0, base_y + bh, z_post, bl, bs, bs, wood_brown)

    # Tilted panel (south side hinge, extending up to the north)
    pL, pW, pt, tilt = P['panel_L'], P['panel_W'], P['panel_t'], math.radians(P['panel_tilt'])
    hinge_y = wh
    hinge_z = boW/2
    # Build panel as a box, then rotate about X axis through the hinge
    # Center of panel in local frame: (0, 0, -pW/2) [hinge at z=0, panel extends -Z]
    # Wait: hinge is on south wall (+Z), panel extends up-north (-Z direction in plan).
    # In local "before translation" frame: hinge at z=0, panel center at z = -pL/2 (since panel length extends north from hinge)
    # Wait, no, pL is along X (east-west), pW is along Z (north-south).
    # Let me re-define: pL=8ft along X, pW=3.72ft along Z.
    # Hinge is at south wall (+Z). Panel extends in -Z direction (north).
    # In local frame: hinge at z=0, panel center at z = -pL/2? But pL is along X.
    # I conflated L and W. Let me redo: in real life, the panel long axis (8ft) is along the bed length (X).
    # Hmm, but I want the panel to tilt with its 8ft edge along X.
    # In a tilted canopy, the panel pivots about its SHORT edge (3.72 ft = panel W), not its long edge.
    # That means the tilt axis is along X (the long axis of the bed), and the panel tilts up toward -Z.
    # The "low" edge is at +Z (south wall), the "high" edge is at -Z (north, near the posts).
    # The 8 ft dimension (pL) is along the tilt axis (X), unchanged.
    # The 3.72 ft dimension (pW) is along the tilt direction (Z), and gets tilted up.
    # So: hinge edge is along X at z=+Z (south wall top, 12" high). Panel extends in -Z.
    # Panel W (3.72ft) is the dimension that gets tilted.

    # In local frame: hinge at z=0, panel extends in -Z direction. After tilt by angle theta about X axis:
    # A point at (x, 0, -z) goes to (x, z*sin(theta), -z*cos(theta))
    # So the panel in world coords has corners at:
    # (x, y, z) for x in [-pL/2, +pL/2], y in [0, pt], z = -W*cos(theta) at the high edge
    # After rotation by theta about X axis (right-hand rule):
    # Point (x, 0, -W) goes to (x, W*sin(theta), -W*cos(theta))
    # So in world coords, panel center is at:
    # x = 0
    # y = wh + (W/2) * sin(theta)
    # z = boW/2 - (W/2) * cos(theta)
    # The panel is a tilted box of size pL x pt x pW (in its local frame), centered at:
    cx, cy, cz = 0, wh + (pW/2) * math.sin(tilt), boW/2 - (pW/2) * math.cos(tilt)
    # The panel needs to be drawn as a tilted box. We'll do it by computing the 8 corners and drawing 6 faces.
    corners_local = np.array([
        [-pL/2, -pt/2, -pW/2],  # 0
        [+pL/2, -pt/2, -pW/2],  # 1
        [+pL/2, +pt/2, -pW/2],  # 2
        [-pL/2, +pt/2, -pW/2],  # 3
        [-pL/2, -pt/2, +pW/2],  # 4
        [+pL/2, -pt/2, +pW/2],  # 5
        [+pL/2, +pt/2, +pW/2],  # 6
        [-pL/2, +pt/2, +pW/2],  # 7
    ])
    # Rotate about X axis by angle -tilt (so that local -Z edge goes up in world +Y)
    # Rotation about X by angle a:
    #   y' = y*cos(a) - z*sin(a)
    #   z' = y*sin(a) + z*cos(a)
    # We want the local -Z direction to become (0, +sin(tilt), -cos(tilt)) in world.
    # i.e., when local (y=0, z=-1) -> world (y=+sin(tilt), z=-cos(tilt))
    #   +sin(tilt) = 0*cos(a) - (-1)*sin(a) = sin(a) -> a = tilt
    #   -cos(tilt) = 0*sin(a) + (-1)*cos(a) = -cos(a) -> a = tilt
    # So a = +tilt. Good.
    cos_t, sin_t = math.cos(tilt), math.sin(tilt)
    R = np.array([
        [1, 0,        0      ],
        [0, cos_t,   -sin_t  ],
        [0, sin_t,    cos_t  ],
    ])
    corners_world = corners_local @ R.T
    # Translate to panel center
    corners_world += np.array([cx, cy, cz])

    faces_def = [
        (0, 1, 2, 3),  # -Z face (which is now tilted up)
        (4, 5, 6, 7),  # +Z face
        (0, 1, 5, 4),  # -Y face
        (3, 2, 6, 7),  # +Y face
        (0, 3, 7, 4),  # -X face
        (1, 2, 6, 5),  # +X face
    ]
    for f in faces_def:
        poly = [corners_world[i] for i in f]
        coll = Poly3DCollection([poly], facecolors=[panel_blue], edgecolors='black',
                                linewidths=0.4, alpha=0.95)
        ax.add_collection3d(coll)

    # Add solar cell grid lines on the top face for visual interest
    n_cells_x = 12   # visual only
    n_cells_z = 6
    for i in range(1, n_cells_x):
        frac = -pL/2 + i * pL / n_cells_x
        p1 = np.array([frac, -pt/2, -pW/2]) @ R.T + np.array([cx, cy, cz])
        p2 = np.array([frac, -pt/2, +pW/2]) @ R.T + np.array([cx, cy, cz])
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                color=(0.6, 0.7, 0.9), linewidth=0.3, alpha=0.6)
    for j in range(1, n_cells_z):
        frac = -pW/2 + j * pW / n_cells_z
        p1 = np.array([-pL/2, -pt/2, frac]) @ R.T + np.array([cx, cy, cz])
        p2 = np.array([+pL/2, -pt/2, frac]) @ R.T + np.array([cx, cy, cz])
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                color=(0.6, 0.7, 0.9), linewidth=0.3, alpha=0.6)

    # Hinge bar (south side, at the wall top)
    hinge_d = 0.5
    add_box(ax, 0, wh - hinge_d, boW/2 + hinge_d/2, boL - 4, hinge_d, hinge_d, hinge_gray)


def setup_axes(ax, elev, azim, title):
    ax.set_xlabel("X (east, in)")
    ax.set_ylabel("Y (up, in)")
    ax.set_zlabel("Z (north, in)")
    ax.set_title(title, fontsize=12)
    ax.view_init(elev=elev, azim=azim)
    # Set equal aspect ratio (rough)
    ax.set_xlim(-60, 60)
    ax.set_ylim(-5, 130)
    ax.set_zlim(-50, 50)
    ax.set_box_aspect((120, 130, 100))
    ax.grid(True, alpha=0.2)


def render(outdir):
    views = [
        ("iso",        25, -50, "Perspective view (from south-east)"),
        ("north_side",  5, -90, "North side view (looking south at the panel)"),
        ("east_side",   5,   0, "East side view (showing tilt)"),
        ("top",        75, -90, "Top-down view (plan)"),
    ]
    for name, elev, azim, title in views:
        fig = plt.figure(figsize=(13, 9))
        ax = fig.add_subplot(111, projection='3d')
        assemble_scene(ax)
        setup_axes(ax, elev, azim, title)
        plt.tight_layout()
        out = os.path.join(outdir, f"wattplot_v2_{name}.png")
        plt.savefig(out, dpi=120)
        plt.close()
        print(f"[render] {out}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "..", "renders")
    os.makedirs(outdir, exist_ok=True)
    render(outdir)
    print("[render] done.")
