"""
Wattplot Mini — 3D iso + top + east renders (matplotlib).
Reads from MINI dict + LUMBER. Scaled-down version of render_3d_views.py.
"""
import os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from wattplot_params import MINI
from models.freecad.materials import LUMBER


# Constants
WALL_T = LUMBER["1x4"]["actual_t"]   # 0.75
WALL_H = LUMBER["1x4"]["actual_h"]   # 3.5
SKID_S = 1.5                          # 2x2 actual
RAIL_T = LUMBER["1x2"]["actual_t"]   # 0.75
RAIL_H = LUMBER["1x2"]["actual_h"]   # 1.5

BED_L = MINI["bed_outer_L_in"]        # 19
BED_W = MINI["bed_outer_W_in"]        # 10
SKID_H = MINI["skid_h_in"]            # 0.75
PANEL_L = MINI["panel_L_in"]          # 17.32
PANEL_W = MINI["panel_W_in"]          # 8.46
PANEL_T = MINI["panel_t_in"]          # 0.71

WALL_Y_BOTTOM = SKID_H                # 0.75
WALL_Y_TOP = SKID_H + WALL_H          # 4.25
FRAME_Y_BOTTOM = WALL_Y_TOP
FRAME_Y_TOP = FRAME_Y_BOTTOM + RAIL_H
PANEL_Y_BOTTOM = FRAME_Y_BOTTOM + 0.25
PANEL_Y_TOP = PANEL_Y_BOTTOM + PANEL_T

COL_BED    = (0.42, 0.27, 0.13)
COL_FRAME  = (0.85, 0.65, 0.40)
COL_PANEL  = (0.10, 0.15, 0.45)
COL_HINGE  = (0.45, 0.45, 0.50)


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


def render_mini(outdir=None):
    if outdir is None:
        outdir = os.path.join(HERE, "..", "renders")
    os.makedirs(outdir, exist_ok=True)

    # Top view (always flat)
    fig, ax = plt.subplots(figsize=(12, 6))
    # Bed
    bed = Rectangle((-BED_L/2, -BED_W/2), BED_L, BED_W,
                    facecolor=COL_BED, edgecolor='black', linewidth=1.5,
                    label='Bed (19"x10", 1x4 PT)')
    ax.add_patch(bed)
    # Frame
    frame_outer = Rectangle((-PANEL_L/2 - RAIL_T/2, -PANEL_W/2 - RAIL_T/2),
                            PANEL_L + RAIL_T, PANEL_W + RAIL_T,
                            facecolor=COL_FRAME, edgecolor='black', linewidth=1.5,
                            label='Frame (1x2 PT perimeter)')
    ax.add_patch(frame_outer)
    # Panel
    panel = Rectangle((-PANEL_L/2, -PANEL_W/2), PANEL_L, PANEL_W,
                      facecolor=COL_PANEL, edgecolor='black', linewidth=1.0,
                      label=f'Panel (10W 12V, {PANEL_L}x{PANEL_W}")')
    ax.add_patch(panel)
    # Hinges (south wall)
    for x in [-6.5, 6.5]:
        hinge = Rectangle((x - 0.75, BED_W/2 - 0.4), 1.5, 0.4,
                          facecolor=COL_HINGE, edgecolor='black', linewidth=0.6)
        ax.add_patch(hinge)
    # Hinge axis line
    ax.axhline(y=BED_W/2, color='red', linestyle='--', linewidth=1.0, alpha=0.5,
               label='Hinge axis')
    ax.set_xlim(-12, 12)
    ax.set_ylim(-7, 7)
    ax.set_aspect('equal')
    ax.set_xlabel("X (east, inches)")
    ax.set_ylabel("Z (north ↑ south, inches)")
    ax.set_title("Wattplot Mini — Top view (1/5 scale, ~19\"x10\")", fontsize=11)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, linestyle=':')
    plt.tight_layout()
    out = os.path.join(outdir, "wattplot_v2_mini_top.png")
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] mini top: {out}")

    # Iso view
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Bed walls
    bed_y_center = (WALL_Y_BOTTOM + WALL_Y_TOP) / 2
    add_box(ax, 0, bed_y_center, -BED_W/2 + WALL_T/2, BED_L, WALL_H, WALL_T, COL_BED)
    add_box(ax, 0, bed_y_center, BED_W/2 - WALL_T/2, BED_L, WALL_H, WALL_T, COL_BED)
    add_box(ax, -BED_L/2 + WALL_T/2, bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED)
    add_box(ax, BED_L/2 - WALL_T/2, bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED)
    # Skids
    for sign in (-1, +1):
        z_skid = sign * (BED_W/2 - SKID_S/2)
        add_box(ax, 0, SKID_S/2, z_skid, BED_L, SKID_S, SKID_S, COL_BED)
    # Frame
    add_box(ax, 0, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2, BED_W/2 - RAIL_T/2, BED_L, RAIL_H, RAIL_T, COL_FRAME)
    add_box(ax, 0, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2, -BED_W/2 + RAIL_T/2, BED_L, RAIL_H, RAIL_T, COL_FRAME)
    add_box(ax, PANEL_L/2 - RAIL_T/2, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2, 0, RAIL_T, RAIL_H, PANEL_W - 2*RAIL_T, COL_FRAME)
    add_box(ax, -PANEL_L/2 + RAIL_T/2, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2, 0, RAIL_T, RAIL_H, PANEL_W - 2*RAIL_T, COL_FRAME)
    # Panel
    add_box(ax, 0, (PANEL_Y_BOTTOM + PANEL_Y_TOP)/2, 0, PANEL_L, PANEL_T, PANEL_W, COL_PANEL)

    ax.set_xlim(-13, 13)
    ax.set_ylim(0, 8)
    ax.set_zlim(-8, 8)
    ax.view_init(elev=25, azim=-50)
    ax.set_xlabel("X (east, in)")
    ax.set_ylabel("Y (up, in)")
    ax.set_zlabel("Z (south, in)")
    ax.set_title("Wattplot Mini — Iso view (1/5 scale)", fontsize=11)
    plt.tight_layout()
    out = os.path.join(outdir, "wattplot_v2_mini_iso.png")
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] mini iso: {out}")


if __name__ == "__main__":
    render_mini()
