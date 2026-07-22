"""
Wattplot Mini - 3D iso + top renders (matplotlib).
Reads from MINI dict + LUMBER. Auto-scales to the current MINI dimensions.
"""
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from wattplot_params import MINI
from models.freecad.materials import LUMBER


# Lumber dimensions
WALL_T = LUMBER["1x4"]["actual_t"]   # 0.75
WALL_H = LUMBER["1x4"]["actual_h"]   # 3.5
SKID_S = MINI["skid_side_in"]         # 0.75 (1x2) or 1.5 (2x2)
RAIL_T = MINI["long_rail_thk_in"]    # 0.75 (1x2) or 1.5 (2x2)
RAIL_H = MINI["long_rail_h_in"]      # 1.5

# Bed/frame dimensions from MINI
BED_L = MINI["bed_outer_L_in"]
BED_W = MINI["bed_outer_W_in"]
SKID_H = MINI["skid_h_in"]
PANEL_L = MINI["panel_L_in"]
PANEL_W = MINI["panel_W_in"]
PANEL_T = MINI["panel_t_in"]
PANEL_WATT = MINI["panel_wattage"]

WALL_Y_BOTTOM = SKID_H
WALL_Y_TOP = SKID_H + WALL_H
FRAME_Y_BOTTOM = WALL_Y_TOP
FRAME_Y_TOP = FRAME_Y_BOTTOM + RAIL_H
PANEL_Y_BOTTOM = FRAME_Y_BOTTOM + 0.5
PANEL_Y_TOP = PANEL_Y_BOTTOM + PANEL_T

HINGE_LEAF = MINI["hinge_leaf_in"]
HINGE_PIN_D = MINI["hinge_pin_d_in"]

# Kickstand geometry (for actuator visualization)
ACT_STROKE = MINI["actuator_stroke_in"]
ACT_BOTTOM_Y = SKID_H + 0.75 / 2  # mid-height of bottom block
ACT_BOTTOM_Z = BED_W / 2 + 0.75 / 2  # outer face of wall + half of block
ACT_TOP_Y = PANEL_Y_BOTTOM
ACT_TOP_Z = BED_W / 2 - MINI["kickstand_top_mount_offset_in"]

# Colors
COL_BED    = (0.42, 0.27, 0.13)
COL_FRAME  = (0.85, 0.65, 0.40)
COL_PANEL  = (0.10, 0.15, 0.45)
COL_HINGE  = (0.45, 0.45, 0.50)
COL_SOIL   = (0.30, 0.18, 0.08)
COL_ACT    = (0.70, 0.70, 0.70)


def box_faces(cx, cy, cz, sx, sy, sz, color):
    x0, x1 = cx - sx/2, cx + sx/2
    y0, y1 = cy - sy/2, cy + sy/2
    z0, z1 = cz - sz/2, cz + sz/2
    return [
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], color),
        ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], color),
        ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], color),
        ([(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)], color),
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], color),
        ([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], color),
    ]


def add_box(ax, cx, cy, cz, sx, sy, sz, color, alpha=1.0):
    for poly, col in box_faces(cx, cy, cz, sx, sy, sz, color):
        coll = Poly3DCollection([poly], facecolors=[col], edgecolors='black',
                                linewidths=0.3, alpha=alpha)
        ax.add_collection3d(coll)


def _make_cyl_between(x1, y1, z1, x2, y2, z2, radius, color):
    """Make a cylinder along the line from (x1,y1,z1) to (x2,y2,z2)."""
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    L = math.sqrt(dx*dx + dy*dy + dz*dz)
    if L < 1e-9:
        return []
    ux, uy, uz = dx / L, dy / L, dz / L
    if abs(ux) < 0.9:
        v1x, v1y, v1z = 1, 0, 0
    else:
        v1x, v1y, v1z = 0, 1, 0
    dot = v1x*ux + v1y*uy + v1z*uz
    v1x, v1y, v1z = v1x - dot*ux, v1y - dot*uy, v1z - dot*uz
    norm = math.sqrt(v1x*v1x + v1y*v1y + v1z*v1z)
    v1x, v1y, v1z = v1x / norm, v1y / norm, v1z / norm
    v2x, v2y, v2z = uy*v1z - uz*v1y, uz*v1x - ux*v1z, ux*v1y - uy*v1x
    N = 16
    faces = []
    base_pts = []
    top_pts = []
    for i in range(N):
        theta = 2 * math.pi * i / N
        cx_off = radius * (math.cos(theta) * v1x + math.sin(theta) * v2x)
        cy_off = radius * (math.cos(theta) * v1y + math.sin(theta) * v2y)
        cz_off = radius * (math.cos(theta) * v1z + math.sin(theta) * v2z)
        base_pts.append((x1 + cx_off, y1 + cy_off, z1 + cz_off))
        top_pts.append((x2 + cx_off, y2 + cy_off, z2 + cz_off))
    for i in range(N):
        j = (i + 1) % N
        face = [base_pts[i], top_pts[i], top_pts[j], base_pts[j]]
        faces.append((face, color))
    faces.append((base_pts, color))
    faces.append((list(reversed(top_pts)), color))
    return faces


def render_mini(outdir=None):
    if outdir is None:
        outdir = os.path.join(HERE, "..", "renders")
    os.makedirs(outdir, exist_ok=True)

    # ============= Top view (flat) =============
    fig, ax = plt.subplots(figsize=(14, 8))
    # Bed
    bed = Rectangle((-BED_L/2, -BED_W/2), BED_L, BED_W,
                    facecolor=COL_BED, edgecolor='black', linewidth=1.5,
                    label=f'Bed ({BED_L:.0f}"x{BED_W:.0f}", 1x4 PT)')
    ax.add_patch(bed)
    # Frame
    frame_outer = Rectangle((-BED_L/2, -BED_W/2), BED_L, BED_W,
                            facecolor=COL_FRAME, edgecolor='black', linewidth=1.5,
                            label=f'Frame ({int(RAIL_T*4)/4}"x{int(RAIL_H*4)/4}" PT perimeter)', alpha=0.7)
    ax.add_patch(frame_outer)
    # Panel
    panel = Rectangle((-PANEL_L/2, -PANEL_W/2), PANEL_L, PANEL_W,
                      facecolor=COL_PANEL, edgecolor='black', linewidth=1.0,
                      label=f'Panel ({PANEL_WATT}W, {PANEL_L:.1f}"x{PANEL_W:.1f}")')
    ax.add_patch(panel)
    # Hinges on south wall
    hinge_span = BED_L - 5  # 2.5" margin each end on the bed
    for x in [-hinge_span/2, +hinge_span/2]:
        hinge = Rectangle((x - HINGE_LEAF/2, BED_W/2 - 0.3), HINGE_LEAF, 0.3,
                          facecolor=COL_HINGE, edgecolor='black', linewidth=0.6,
                          label=f'Hinge ({HINGE_LEAF:.1f}" butt, {HINGE_PIN_D}" pin)' if x == -hinge_span/2 else None)
        ax.add_patch(hinge)
    # Hinge axis line
    ax.axhline(y=BED_W/2, color='red', linestyle='--', linewidth=1.0, alpha=0.5,
               label=f'Hinge axis ({HINGE_PIN_D}" continuous rod)')
    # Diagonal brace (visual hint)
    brace_label = f'Diagonal brace ({int(RAIL_T*4)/4}"x{int(RAIL_H*4)/4}", {MINI["diagonal_brace_length_in"]:.0f}")'
    ax.plot([-BED_L/2 + RAIL_T, BED_L/2 - RAIL_T],
            [-BED_W/2 + RAIL_T, BED_W/2 - RAIL_T],
            color='orange', linestyle=':', linewidth=1.5, alpha=0.6,
            label=brace_label)
    # Kickstand actuator (visual hint, dashed line from bed to panel)
    ax.plot([0, 0], [ACT_BOTTOM_Z, ACT_TOP_Z],
            color='gray', linestyle='--', linewidth=1.5, alpha=0.6,
            label=f'Kickstand actuator ({ACT_STROKE:.2f}" stroke)')

    margin = max(BED_L, BED_W) * 0.3
    ax.set_xlim(-BED_L/2 - margin, BED_L/2 + margin)
    ax.set_ylim(-BED_W/2 - margin, BED_W/2 + margin)
    ax.set_aspect('equal')
    ax.set_xlabel("X (east, inches)")
    ax.set_ylabel("Z (north ↓ south, inches)")
    ax.set_title(f"Wattplot Mini v2.2 — Top view ({BED_L:.0f}\"x{BED_W:.0f}\" bed, {PANEL_WATT}W panel, {ACT_STROKE:.2f}\" kickstand)",
                 fontsize=11)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, linestyle=':')
    plt.tight_layout()
    out = os.path.join(outdir, "wattplot_v2_mini_top.png")
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] mini top: {out}")

    # ============= Iso view =============
    fig = plt.figure(figsize=(14, 9))
    ax = fig.add_subplot(111, projection='3d')

    bed_y_center = (WALL_Y_BOTTOM + WALL_Y_TOP) / 2

    # Bed walls (long walls at z = ±(BED_W/2 - WALL_T))
    add_box(ax, 0, bed_y_center, -(BED_W/2 - WALL_T/2), BED_L, WALL_H, WALL_T, COL_BED)
    add_box(ax, 0, bed_y_center, +(BED_W/2 - WALL_T/2), BED_L, WALL_H, WALL_T, COL_BED)
    # Bed walls (short walls at x = ±(BED_L/2 - WALL_T))
    add_box(ax, -(BED_L/2 - WALL_T/2), bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED)
    add_box(ax, +(BED_L/2 - WALL_T/2), bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED)

    # Skids (at z = ±(BED_W/2 - SKID_S/2))
    for sign in (-1, +1):
        z_skid = sign * (BED_W/2 - SKID_S/2)
        add_box(ax, 0, SKID_S/2, z_skid, BED_L, SKID_S, SKID_S, COL_BED)

    # Frame long rails
    fy_center = (FRAME_Y_BOTTOM + FRAME_Y_TOP) / 2
    add_box(ax, 0, fy_center, -(BED_W/2 - RAIL_T/2), BED_L, RAIL_H, RAIL_T, COL_FRAME)
    add_box(ax, 0, fy_center, +(BED_W/2 - RAIL_T/2), BED_L, RAIL_H, RAIL_T, COL_FRAME)
    # Frame cross rails
    add_box(ax, -(BED_L/2 - RAIL_T/2), fy_center, 0, RAIL_T, RAIL_H, BED_W - 2*RAIL_T, COL_FRAME)
    add_box(ax, +(BED_L/2 - RAIL_T/2), fy_center, 0, RAIL_T, RAIL_H, BED_W - 2*RAIL_T, COL_FRAME)

    # Diagonal brace
    angle_deg = math.degrees(math.atan2(BED_W - 2*RAIL_T, BED_L - 2*RAIL_T))
    brace_faces = box_faces(0, fy_center + 0.5, 0,
                            MINI["diagonal_brace_length_in"], RAIL_T, RAIL_H,
                            COL_FRAME)
    cos_a, sin_a = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    rotated_faces = []
    for poly, col in brace_faces:
        new_poly = []
        for (x, y, z) in poly:
            xr = x * cos_a + z * sin_a
            zr = -x * sin_a + z * cos_a
            new_poly.append((xr, y, zr))
        rotated_faces.append((new_poly, col))
    for poly, col in rotated_faces:
        coll = Poly3DCollection([poly], facecolors=[col], edgecolors='black',
                                linewidths=0.3, alpha=1.0)
        ax.add_collection3d(coll)

    # Panel
    add_box(ax, 0, (PANEL_Y_BOTTOM + PANEL_Y_TOP)/2, 0,
            PANEL_L, PANEL_T, PANEL_W, COL_PANEL)

    # Hinges (visual blocks on south wall)
    for x in [-hinge_span/2, +hinge_span/2]:
        add_box(ax, x, FRAME_Y_BOTTOM, BED_W/2, HINGE_LEAF, 0.3, 0.4, COL_HINGE, alpha=0.8)

    # Kickstand actuator mount blocks
    add_box(ax, 0, ACT_BOTTOM_Y, BED_W/2 + 0.375, 3.0, 0.75, 0.75, COL_ACT, alpha=0.9)
    add_box(ax, 0, ACT_TOP_Y - 0.375, ACT_TOP_Z, 3.0, 0.75, 0.75, COL_ACT, alpha=0.9)
    # Actuator body (cylinder) from bottom pin to top pin
    act_faces = _make_cyl_between(0, ACT_BOTTOM_Y, BED_W/2 + 0.75,
                                   0, ACT_TOP_Y, ACT_TOP_Z,
                                   0.375, COL_ACT)
    if act_faces:
        verts = [poly for poly, _ in act_faces]
        colors = [col for _, col in act_faces]
        coll = Poly3DCollection(verts, facecolors=colors, edgecolors='black',
                                linewidths=0.3, alpha=0.85)
        ax.add_collection3d(coll)

    ax.set_xlim(-BED_L, BED_L)
    ax.set_ylim(0, 12)
    ax.set_zlim(-BED_W - 4, BED_W + 4)
    # Camera looking from the south-east (so kickstand is in the foreground)
    ax.view_init(elev=25, azim=145)
    ax.set_xlabel("X (east, in)")
    ax.set_ylabel("Y (up, in)")
    ax.set_zlabel("Z (south, in)")
    ax.set_title(f"Wattplot Mini v2.2 — Iso view ({BED_L:.0f}\"x{BED_W:.0f}\" bed, {PANEL_WATT}W panel, {ACT_STROKE:.2f}\" kickstand)",
                 fontsize=11)
    plt.tight_layout()
    out = os.path.join(outdir, "wattplot_v2_mini_iso.png")
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] mini iso: {out}")


if __name__ == "__main__":
    render_mini()
