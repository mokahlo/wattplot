"""
Wattplot Mini v2 — 3D iso + top renders (matplotlib).
Reads from MINI dict + LUMBER.
"""
import os
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
SKID_S = 1.5                          # 2x2 actual
RAIL_T = MINI["long_rail_thk_in"]    # 1.5 (2x2)
RAIL_H = MINI["long_rail_h_in"]      # 1.5 (2x2)
BRACE_L = MINI["diagonal_brace_length_in"]   # 42

# Bed/frame dimensions from MINI v2
BED_L = MINI["bed_outer_L_in"]        # 40
BED_W = MINI["bed_outer_W_in"]        # 22
SKID_H = MINI["skid_h_in"]            # 1.5
PANEL_L = MINI["panel_L_in"]          # 38.58
PANEL_W = MINI["panel_W_in"]          # 20.87
PANEL_T = MINI["panel_t_in"]          # 1.18

WALL_Y_BOTTOM = SKID_H                # 1.5
WALL_Y_TOP = SKID_H + WALL_H          # 5.0
FRAME_Y_BOTTOM = WALL_Y_TOP
FRAME_Y_TOP = FRAME_Y_BOTTOM + RAIL_H  # 6.5
# Panel sits ON TOP of the frame (overhangs), 0.5" above the rail bottom
PANEL_Y_BOTTOM = FRAME_Y_BOTTOM + 0.5
PANEL_Y_TOP = PANEL_Y_BOTTOM + PANEL_T

HINGE_LEAF = MINI["hinge_leaf_in"]     # 4.0
HINGE_Z = BED_W / 2.0                 # 11 (outer face of south wall)

# Colors
COL_BED    = (0.42, 0.27, 0.13)
COL_FRAME  = (0.85, 0.65, 0.40)
COL_PANEL  = (0.10, 0.15, 0.45)
COL_HINGE  = (0.45, 0.45, 0.50)
COL_SOIL   = (0.30, 0.18, 0.08)


def box_faces(cx, cy, cz, sx, sy, sz, color):
    """Return list of (face polygon, color) tuples for a 3D box."""
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
    """Make a cylinder along the line from (x1,y1,z1) to (x2,y2,z2).
    Returns list of (polygon, color) tuples for the cylinder side + caps.
    """
    import math as _math
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    L = _math.sqrt(dx*dx + dy*dy + dz*dz)
    if L < 1e-9:
        return []
    ux, uy, uz = dx / L, dy / L, dz / L
    # Find two perpendicular vectors in the plane perpendicular to (ux,uy,uz)
    if abs(ux) < 0.9:
        v1x, v1y, v1z = 1, 0, 0
    else:
        v1x, v1y, v1z = 0, 1, 0
    # v1 = v1 - (v1.u) * u
    dot = v1x*ux + v1y*uy + v1z*uz
    v1x, v1y, v1z = v1x - dot*ux, v1y - dot*uy, v1z - dot*uz
    norm = _math.sqrt(v1x*v1x + v1y*v1y + v1z*v1z)
    v1x, v1y, v1z = v1x / norm, v1y / norm, v1z / norm
    # v2 = u x v1
    v2x, v2y, v2z = uy*v1z - uz*v1y, uz*v1x - ux*v1z, ux*v1y - uy*v1x
    # Generate side as N-gon
    N = 16
    faces = []
    base_pts = []
    top_pts = []
    for i in range(N):
        theta = 2 * _math.pi * i / N
        cx_off = radius * (_math.cos(theta) * v1x + _math.sin(theta) * v2x)
        cy_off = radius * (_math.cos(theta) * v1y + _math.sin(theta) * v2y)
        cz_off = radius * (_math.cos(theta) * v1z + _math.sin(theta) * v2z)
        base_pts.append((x1 + cx_off, y1 + cy_off, z1 + cz_off))
        top_pts.append((x2 + cx_off, y2 + cy_off, z2 + cz_off))
    # Side faces (rectangles)
    for i in range(N):
        j = (i + 1) % N
        face = [base_pts[i], top_pts[i], top_pts[j], base_pts[j]]
        faces.append((face, color))
    # End caps
    faces.append((base_pts, color))  # base cap (reversed for outward normal)
    faces.append((list(reversed(top_pts)), color))  # top cap
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
                            label='Frame (2x2 PT perimeter)', alpha=0.7)
    ax.add_patch(frame_outer)
    # Panel
    panel = Rectangle((-PANEL_L/2, -PANEL_W/2), PANEL_L, PANEL_W,
                      facecolor=COL_PANEL, edgecolor='black', linewidth=1.0,
                      label=f'Panel (100W Bifacial, {PANEL_L:.1f}"x{PANEL_W:.1f}")')
    ax.add_patch(panel)
    # Hinges on south wall (z = +BED_W/2)
    hinge_span = 26.0  # span of 2 hinges along the 40" south wall
    for x in [-hinge_span/2, +hinge_span/2]:
        hinge = Rectangle((x - HINGE_LEAF/2, BED_W/2 - 0.4), HINGE_LEAF, 0.4,
                          facecolor=COL_HINGE, edgecolor='black', linewidth=0.6,
                          label='Hinge (4" butt, ½" pin)' if x == -hinge_span/2 else None)
        ax.add_patch(hinge)
    # Hinge axis line
    ax.axhline(y=BED_W/2, color='red', linestyle='--', linewidth=1.0, alpha=0.5,
               label='Hinge axis (½" continuous rod)')
    # Diagonal brace (visual hint)
    ax.plot([-BED_L/2 + RAIL_T, BED_L/2 - RAIL_T],
            [-BED_W/2 + RAIL_T, BED_W/2 - RAIL_T],
            color='orange', linestyle=':', linewidth=1.5, alpha=0.6,
            label='Diagonal brace (2x4, 42")')

    ax.set_xlim(-24, 24)
    ax.set_ylim(-15, 15)
    ax.set_aspect('equal')
    ax.set_xlabel("X (east, inches)")
    ax.set_ylabel("Z (north ↓ south, inches)")
    ax.set_title(f"Wattplot Mini v2 — Top view ({BED_L:.0f}\"x{BED_W:.0f}\" bed, 100W bifacial)",
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

    bed_y_center = (WALL_Y_BOTTOM + WALL_Y_TOP) / 2   # 3.25

    # Bed walls (long walls at z = ±(BED_W/2 - WALL_T))
    add_box(ax, 0, bed_y_center, -(BED_W/2 - WALL_T/2), BED_L, WALL_H, WALL_T, COL_BED)
    add_box(ax, 0, bed_y_center, +(BED_W/2 - WALL_T/2), BED_L, WALL_H, WALL_T, COL_BED)
    # Bed walls (short walls at x = ±(BED_L/2 - WALL_T))
    add_box(ax, -(BED_L/2 - WALL_T/2), bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED)
    add_box(ax, +(BED_L/2 - WALL_T/2), bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED)

    # Skids (2x2, at z = ±(BED_W/2 - SKID_S/2))
    for sign in (-1, +1):
        z_skid = sign * (BED_W/2 - SKID_S/2)
        add_box(ax, 0, SKID_S/2, z_skid, BED_L, SKID_S, SKID_S, COL_BED)

    # Frame long rails (at z = ±(BED_W/2 - RAIL_T))
    fy_center = (FRAME_Y_BOTTOM + FRAME_Y_TOP) / 2
    add_box(ax, 0, fy_center, -(BED_W/2 - RAIL_T/2), BED_L, RAIL_H, RAIL_T, COL_FRAME)
    add_box(ax, 0, fy_center, +(BED_W/2 - RAIL_T/2), BED_L, RAIL_H, RAIL_T, COL_FRAME)
    # Frame cross rails (at x = ±(BED_L/2 - RAIL_T))
    add_box(ax, -(BED_L/2 - RAIL_T/2), fy_center, 0, RAIL_T, RAIL_H, BED_W - 2*RAIL_T, COL_FRAME)
    add_box(ax, +(BED_L/2 - RAIL_T/2), fy_center, 0, RAIL_T, RAIL_H, BED_W - 2*RAIL_T, COL_FRAME)

    # Diagonal brace
    brace = box_faces(0, fy_center + 0.5, 0, BRACE_L, RAIL_T, RAIL_H, COL_FRAME)
    import math as _math
    angle_deg = _math.degrees(_math.atan2(BED_W - 2*RAIL_T, BED_L - 2*RAIL_T))
    cos_a, sin_a = _math.cos(_math.radians(angle_deg)), _math.sin(_math.radians(angle_deg))
    # Rotate the brace poly by angle around Y axis
    rotated_faces = []
    for poly, col in brace:
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
    for x in [-13, +13]:
        add_box(ax, x, FRAME_Y_BOTTOM, BED_W/2, HINGE_LEAF, 0.4, 0.5, COL_HINGE, alpha=0.8)

    # Kickstand actuator on south side (low side, 0-35° tilt range)
    # Bottom mount: 2x2 block on bed's south wall, low
    add_box(ax, 0, 0.75, BED_W/2 + 0.75, 4.0, 1.5, 1.5, (0.5, 0.45, 0.4), alpha=0.9)
    # Top mount: 2x2 bracket hanging below the panel
    add_box(ax, 0, 4.75, 5.0 - 0.75, 4.0, 1.5, 1.5, (0.5, 0.45, 0.4), alpha=0.9)
    # Actuator body (cylinder) from bottom pin to top pin
    act_faces = _make_cyl_between(0, 1.5, 12.5, 0, 4.0, 5.0, 0.375, (0.7, 0.7, 0.7))
    if act_faces:
        verts = [poly for poly, _ in act_faces]
        colors = [col for _, col in act_faces]
        coll = Poly3DCollection(verts, facecolors=colors, edgecolors='black',
                                linewidths=0.3, alpha=0.85)
        ax.add_collection3d(coll)

    ax.set_xlim(-25, 25)
    ax.set_ylim(0, 12)
    ax.set_zlim(-18, 18)
    # Camera looking from the south-east (so kickstand is in the foreground)
    ax.view_init(elev=15, azim=145)
    ax.set_xlabel("X (east, in)")
    ax.set_ylabel("Y (up, in)")
    ax.set_zlabel("Z (south, in)")
    ax.set_title(f"Wattplot Mini v2.1 — Iso view ({BED_L:.0f}\"x{BED_W:.0f}\", 100W bifacial, 4\" kickstand actuator, 0-35° tilt)",
                 fontsize=11)
    plt.tight_layout()
    out = os.path.join(outdir, "wattplot_v2_mini_iso.png")
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] mini iso: {out}")


if __name__ == "__main__":
    render_mini()
