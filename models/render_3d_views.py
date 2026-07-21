"""
Wattplot v2 — 3D visualization (matplotlib) for the new all-wood frame design.

Reads geometry from wattplot_params.py + models/freecad/materials.py.
Renders 3D iso view + 2D top-down and side views as PNGs.
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from wattplot_params import BED, FRAME, PANEL
from models.freecad.materials import LUMBER

# ----------------------------------------------------------------------------
# Geometry constants
# ----------------------------------------------------------------------------
WALL_T = LUMBER["2x12"]["actual_t"]
WALL_H = LUMBER["2x12"]["actual_h"]
SKID_S = LUMBER["4x4"]["actual_t"]
RAIL_T = LUMBER["2x6"]["actual_t"]
RAIL_H = LUMBER["2x6"]["actual_h"]
BRACE_T = LUMBER["2x4"]["actual_t"]
BRACE_H = LUMBER["2x4"]["actual_h"]

BED_L = BED["outer_L_in"]   # 96
BED_W = BED["outer_W_in"]   # 44.6
SKID_H = BED["skid_h_in"]   # 3.0
PANEL_L = PANEL["L_in"]     # 97
PANEL_W = PANEL["W_in"]     # 44.6
PANEL_T = PANEL["thickness_in"]
PANEL_TILT = PANEL["panel_tilt_deg"]

# Frame dimensions — read from FRAME dict (single source of truth)
LONG_RAIL_L = FRAME["long_rail"]["length_in"]      # 96.0 (8ft stock, no waste)
CROSS_RAIL_L = FRAME["cross_rail"]["length_in"]    # 42.0 (from 2x6x8ft)
BRACE_L = FRAME["diagonal_brace"]["length_in"]     # 102.0 (from 2x4x10ft)
HINGE_COUNT = FRAME["hinge"]["count"]
HINGE_SPACING = FRAME["hinge"]["spacing_in"]

WALL_Y_BOTTOM = SKID_H
WALL_Y_TOP = SKID_H + WALL_H
FRAME_Y_BOTTOM = WALL_Y_TOP
FRAME_Y_TOP = FRAME_Y_BOTTOM + RAIL_H
PANEL_Y_BOTTOM = FRAME_Y_BOTTOM + 0.5
PANEL_Y_TOP = PANEL_Y_BOTTOM + PANEL_T

# Colors (saturated, distinct)
COL_BED    = (0.42, 0.27, 0.13)   # dark wood
COL_SOIL   = (0.30, 0.18, 0.08)   # darker brown
COL_FRAME  = (0.85, 0.65, 0.40)   # cedar (lighter, more visible)
COL_PANEL  = (0.10, 0.15, 0.45)   # solar blue
COL_HINGE  = (0.45, 0.45, 0.50)   # metal gray
COL_CLAMP  = (0.80, 0.80, 0.82)   # aluminum
COL_ACT    = (0.50, 0.45, 0.40)   # wood (for the clevis block)


# ----------------------------------------------------------------------------
# Box helpers
# ----------------------------------------------------------------------------

def box_faces(cx, cy, cz, sx, sy, sz, color):
    """Return 6 face polygons of a box (centered at cx,cy,cz, size sx,sy,sz)."""
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


def rotate_about_x(verts, angle_deg, pivot=(0, 0, 0)):
    """Rotate a list of vertices about the X axis. pivot is (x, y, z)."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    px, py, pz = pivot
    out = []
    for v in verts:
        x, y, z = v
        dy = y - py
        dz = z - pz
        y2 = py + dy * ca - dz * sa
        z2 = pz + dy * sa + dz * ca
        out.append((x, y2, z2))
    return out


# ----------------------------------------------------------------------------
# Build all parts
# ----------------------------------------------------------------------------

def build_static_parts():
    """Parts that don't tilt: bed, skids, soil, hinges."""
    parts = []  # list of (verts, color, alpha, label)

    # Bed walls
    bed_y_center = (WALL_Y_BOTTOM + WALL_Y_TOP) / 2
    parts.append((box_faces(0, bed_y_center, -BED_W/2 + WALL_T/2, BED_L, WALL_H, WALL_T, COL_BED), "wall_n"))
    parts.append((box_faces(0, bed_y_center, BED_W/2 - WALL_T/2, BED_L, WALL_H, WALL_T, COL_BED), "wall_s"))
    parts.append((box_faces(-BED_L/2 + WALL_T/2, bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED), "wall_w"))
    parts.append((box_faces(BED_L/2 - WALL_T/2, bed_y_center, 0, WALL_T, WALL_H, BED_W - 2*WALL_T, COL_BED), "wall_e"))
    # Skids
    parts.append((box_faces(0, SKID_S/2, 0, BED_L, SKID_S, SKID_S, COL_BED), "skid_n"))
    parts.append((box_faces(0, SKID_S/2, BED_W/2 - SKID_S, BED_L, SKID_S, SKID_S, COL_BED), "skid_s"))
    # Soil (transparent)
    parts.append((box_faces(0, (WALL_Y_BOTTOM + WALL_Y_TOP)/2, 0, BED_L - 2*WALL_T, WALL_H - 0.5, BED_W - 2*WALL_T, COL_SOIL), "soil"))
    # Hinges (on top of south wall)
    for i in range(HINGE_COUNT):
        x = -((HINGE_COUNT - 1) * HINGE_SPACING) / 2 + i * HINGE_SPACING
        # Hinge body: 4" x 4" x 0.5" box straddling the wall top
        parts.append((box_faces(x, FRAME_Y_BOTTOM + 0.25, BED_W/2 + 0.25, 4.0, 0.5, 4.0, COL_HINGE), "hinge"))

    return parts


def build_tilting_parts(tilt_deg=0.0):
    """Parts that tilt with the frame: 4 rails, brace, panel, clamps, actuator mount.

    Built at 0° (flat over the bed) then rotated about the hinge axis.
    """
    parts = []
    pivot = (0, FRAME_Y_BOTTOM, BED_W/2)   # hinge axis (X) at south wall top

    # South long rail
    parts.append((box_faces(0, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2,
                            BED_W/2 - RAIL_T/2, LONG_RAIL_L, RAIL_H, RAIL_T, COL_FRAME), "rail_s"))
    # North long rail
    parts.append((box_faces(0, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2,
                            -BED_W/2 + RAIL_T/2, LONG_RAIL_L, RAIL_H, RAIL_T, COL_FRAME), "rail_n"))
    # East cross rail
    parts.append((box_faces(BED_L/2 - RAIL_T/2, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2,
                            0, RAIL_T, RAIL_H, CROSS_RAIL_L, COL_FRAME), "rail_e"))
    # West cross rail
    parts.append((box_faces(-BED_L/2 + RAIL_T/2, (FRAME_Y_BOTTOM + FRAME_Y_TOP)/2,
                            0, RAIL_T, RAIL_H, CROSS_RAIL_L, COL_FRAME), "rail_w"))

    # Diagonal brace (in the frame plane, at y = FRAME_Y_BOTTOM + small offset)
    interior_L = PANEL_L - 2*RAIL_T
    interior_W = PANEL_W - 2*RAIL_T
    brace_len = BRACE_L   # 102" from 2x4x10ft
    brace_angle = math.degrees(math.atan2(interior_W, interior_L))
    # Build brace as a 2x4 lying along X
    brace_verts = box_faces(0, 0, 0, brace_len, BRACE_T, BRACE_H, COL_FRAME)
    # Rotate in XZ plane about Y axis, then translate to frame plane
    rotated = []
    a = math.radians(brace_angle)
    ca, sa = math.cos(a), math.sin(a)
    for poly, col in brace_verts:
        new_poly = []
        for v in poly:
            x, y, z = v
            x2 = x * ca - z * sa
            z2 = x * sa + z * ca
            new_poly.append((x2, y + FRAME_Y_BOTTOM + 0.5, z2))
        rotated.append((new_poly, col))
    parts.append((rotated, "brace"))

    # Panel
    parts.append((box_faces(0, (PANEL_Y_BOTTOM + PANEL_Y_TOP)/2, 0,
                            PANEL_L, PANEL_T, PANEL_W, COL_PANEL), "panel"))

    # Panel clamps (6 × aluminum mid-clamps on the rails)
    # 2 per long rail, at 1/4 and 3/4 of rail length
    for sign in (-1, +1):
        z_rail = sign * (BED_W/2 - RAIL_T/2)
        for j in range(2):
            x = -LONG_RAIL_L/2 + LONG_RAIL_L * (j + 0.5) / 2
            z_clamp = z_rail - sign * 0.7
            parts.append((box_faces(x, PANEL_Y_TOP, z_clamp, 2.0, 2.0, 0.4, COL_CLAMP), "clamp"))
    # 1 per cross rail
    for sign in (-1, +1):
        x_rail = sign * (PANEL_L/2 - RAIL_T/2)
        parts.append((box_faces(x_rail, PANEL_Y_TOP, 0, 0.4, 2.0, 2.0, COL_CLAMP), "clamp"))

    # Actuator mount: clevis on north rail + wall block on north wall
    parts.append((box_faces(0, FRAME_Y_TOP + RAIL_H/2, -BED_W/2 + RAIL_T/2,
                            6.0, RAIL_H, RAIL_T, COL_ACT), "act_clevis"))
    parts.append((box_faces(0, FRAME_Y_BOTTOM + RAIL_H/2, -BED_W/2 - 3.0,
                            6.0, RAIL_H, RAIL_T, COL_ACT), "act_wall"))

    # Apply tilt to all
    tilted_parts = []
    for verts, label in parts:
        tilted_verts = [(rotate_about_x(poly, tilt_deg, pivot=pivot), col)
                        for poly, col in verts]
        tilted_parts.append((tilted_verts, label))
    return tilted_parts


def draw_scene(ax, tilt_deg=0.0, show_soil=True, soil_alpha=0.4):
    """Draw the full scene into a 3D matplotlib axes."""
    static_parts = build_static_parts()
    tilting_parts = build_tilting_parts(tilt_deg=tilt_deg)
    for verts, label in static_parts:
        if label == "soil":
            if show_soil:
                add_box_from_verts(ax, verts, COL_SOIL, alpha=soil_alpha)
        else:
            add_box_from_verts(ax, verts, COL_BED if "skid" in label or "wall" in label
                              else COL_HINGE)
    for verts, label in tilting_parts:
        if "rail" in label or "brace" in label:
            add_box_from_verts(ax, verts, COL_FRAME)
        elif "panel" in label:
            add_box_from_verts(ax, verts, COL_PANEL)
        elif "clamp" in label:
            add_box_from_verts(ax, verts, COL_CLAMP)
        elif "act" in label:
            add_box_from_verts(ax, verts, COL_ACT)


def add_box_from_verts(ax, verts, color, alpha=1.0):
    """Add polygons from box_faces output."""
    for poly, col in verts:
        coll = Poly3DCollection([poly], facecolors=[col], edgecolors='black',
                                linewidths=0.3, alpha=alpha)
        ax.add_collection3d(coll)


# ----------------------------------------------------------------------------
# Render views
# ----------------------------------------------------------------------------

def render_iso(outpath, tilt_deg=35.0):
    """Render an iso 3D view of the model."""
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    draw_scene(ax, tilt_deg=tilt_deg, show_soil=True, soil_alpha=0.35)

    # View limits
    ax.set_xlim(-55, 55)
    ax.set_ylim(-5, 45)
    ax.set_zlim(-30, 30)
    # Standard iso: 25° elevation, looking from southeast
    ax.view_init(elev=22, azim=-50)
    ax.set_xlabel("X (east, in)")
    ax.set_ylabel("Y (up, in)")
    ax.set_zlabel("Z (south, in)")
    ax.set_title(f"Wattplot v2 — Iso view (frame at {tilt_deg:.0f}° tilt)\n"
                 f"All-wood frame: 2x6 perimeter + 2x4 diagonal brace, 2x12 bed walls",
                 fontsize=11)
    plt.tight_layout()
    plt.savefig(outpath, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] iso: {outpath}")


def render_top_view(outpath, tilt_deg=0.0):
    """Render a 2D top-down view that shows the wood frame rectangle."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Bed walls (top view = bed outline)
    bed = Rectangle((-BED_L/2, -BED_W/2), BED_L, BED_W,
                    facecolor=COL_BED, edgecolor='black', linewidth=1.5,
                    label='Bed walls (2x12 PT, half-lap corners)')
    ax.add_patch(bed)
    # Soil area (inside the walls)
    soil = Rectangle((-BED_L/2 + WALL_T, -BED_W/2 + WALL_T),
                     BED_L - 2*WALL_T, BED_W - 2*WALL_T,
                     facecolor=COL_SOIL, edgecolor='none', alpha=0.5,
                     label='Soil (planting area)')
    ax.add_patch(soil)
    # Frame outline (4 rails around the panel)
    frame_outer = Rectangle((-PANEL_L/2 - RAIL_T/2, -PANEL_W/2 - RAIL_T/2),
                            PANEL_L + RAIL_T, PANEL_W + RAIL_T,
                            facecolor=COL_FRAME, edgecolor='black', linewidth=1.5,
                            label='Wood frame (2x6 PT perimeter)')
    ax.add_patch(frame_outer)
    # Frame interior (where the panel sits)
    frame_inner = Rectangle((-PANEL_L/2 + RAIL_T/2, -PANEL_W/2 + RAIL_T/2),
                            PANEL_L - RAIL_T, PANEL_W - RAIL_T,
                            facecolor='#f5e6d3', edgecolor='none')
    ax.add_patch(frame_inner)
    # Panel (sits inside the frame, tilted at tilt_deg but we show it flat here)
    panel = Rectangle((-PANEL_L/2, -PANEL_W/2), PANEL_L, PANEL_W,
                      facecolor=COL_PANEL, edgecolor='black', linewidth=1.0,
                      label='Panel (97"x44.6", 620W bifacial)',
                      alpha=0.95)
    ax.add_patch(panel)
    # Diagonal brace (across the interior)
    interior_L = PANEL_L - 2*RAIL_T
    interior_W = PANEL_W - 2*RAIL_T
    brace = Polygon(
        [[-interior_L/2, -interior_W/2],
         [interior_L/2, -interior_W/2 + interior_W*0.2],
         [interior_L/2 - interior_L*0.2, interior_W/2],
         [-interior_L/2 + interior_L*0.0, interior_W/2 - interior_W*0.2]],
        closed=True, facecolor=COL_FRAME, edgecolor='black', linewidth=0.8, alpha=0.7,
        label='Diagonal brace (2x4 PT, ~102" long)'
    )
    # Hinges (on south wall, 4 of them)
    for i in range(HINGE_COUNT):
        x = -((HINGE_COUNT - 1) * HINGE_SPACING) / 2 + i * HINGE_SPACING
        hinge = Rectangle((x - 2, BED_W/2 - WALL_T/2 - 0.4), 4, 0.4,
                          facecolor=COL_HINGE, edgecolor='black', linewidth=0.6)
        ax.add_patch(hinge)
    # Panel clamps
    for sign in (-1, +1):
        z_rail = sign * (BED_W/2 - RAIL_T/2)
        for j in range(2):
            x = -LONG_RAIL_L/2 + LONG_RAIL_L * (j + 0.5) / 2
            clamp = Rectangle((x - 1, z_rail - sign * 1.0), 2, 0.4,
                              facecolor=COL_CLAMP, edgecolor='black', linewidth=0.4)
            ax.add_patch(clamp)
    # Actuator mount on north rail
    act = Rectangle((-3, -BED_W/2 - 3.0), 6, 6,
                    facecolor=COL_ACT, edgecolor='black', linewidth=0.6,
                    label='Actuator mount (2x6 PT clevis + wall block)')
    ax.add_patch(act)
    # Hinge axis line
    ax.axhline(y=BED_W/2, color='red', linestyle='--', linewidth=1.0, alpha=0.5,
               label='Hinge axis (X direction)')

    # Skids (visible as dark lines under the bed)
    for sign in (-1, +1):
        skid = Rectangle((-BED_L/2, sign * (BED_W/2 - SKID_S) - SKID_S/2),
                         BED_L, SKID_S,
                         facecolor=COL_BED, edgecolor='black', linewidth=0.6, alpha=0.7)
        ax.add_patch(skid)

    ax.set_xlim(-55, 55)
    ax.set_ylim(-30, 30)
    ax.set_aspect('equal')
    ax.set_xlabel("X (east, inches)")
    ax.set_ylabel("Z (north ↑ south, inches)")
    ax.set_title("Wattplot v2 — Top view (looking down)\n"
                 "Wood frame visible as the cedar-colored rectangle around the panel",
                 fontsize=11)
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=':')
    plt.tight_layout()
    plt.savefig(outpath, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] top: {outpath}")


def render_east_view(outpath, tilt_deg=35.0):
    """Render a 2D east side view (matches engineering_drawing.py style)."""
    fig, ax = plt.subplots(figsize=(14, 9))

    # Bed (cross-section visible)
    bed = Rectangle((-BED_W/2, 0), BED_W, WALL_H,
                    facecolor=COL_BED, edgecolor='black', linewidth=1.2,
                    label='Planter bed (2x12 PT, 11.25" walls)')
    ax.add_patch(bed)
    # Soil
    sd = WALL_H
    soil = Rectangle((-BED_W/2 + WALL_T, 0), BED_W - 2*WALL_T, sd,
                     facecolor=COL_SOIL, edgecolor='none', alpha=0.4,
                     label='Soil ballast')
    ax.add_patch(soil)
    # Skids
    for sign in (-1, +1):
        skid = Rectangle((sign * (BED_W/2 - SKID_S) - SKID_S/2, -SKID_S),
                         SKID_S, SKID_S,
                         facecolor=COL_BED, edgecolor='black', linewidth=0.8)
        ax.add_patch(skid)

    # Hinges (on south wall)
    for i in range(HINGE_COUNT):
        x = -((HINGE_COUNT - 1) * HINGE_SPACING) / 2 + i * HINGE_SPACING
        hinge = Rectangle((x - 2, FRAME_Y_BOTTOM - 0.1), 4, 0.6,
                          facecolor=COL_HINGE, edgecolor='black', linewidth=0.6)
        ax.add_patch(hinge)

    # Frame long rails (south + north)
    south_rail = Rectangle((BED_W/2 - RAIL_T, FRAME_Y_BOTTOM), RAIL_T, RAIL_H,
                           facecolor=COL_FRAME, edgecolor='black', linewidth=1.0,
                           label='2x6 PT long rail')
    ax.add_patch(south_rail)
    north_rail = Rectangle((-BED_W/2, FRAME_Y_BOTTOM), RAIL_T, RAIL_H,
                          facecolor=COL_FRAME, edgecolor='black', linewidth=1.0)
    ax.add_patch(north_rail)

    # Panel + tilted north rail
    tilt = math.radians(tilt_deg)
    high_y = FRAME_Y_BOTTOM + PANEL_W * math.sin(tilt)
    high_z = BED_W/2 - PANEL_W * math.cos(tilt)
    panel = Polygon(
        [(BED_W/2, FRAME_Y_BOTTOM), (high_z, high_y),
         (high_z, high_y + PANEL_T), (BED_W/2, FRAME_Y_BOTTOM + PANEL_T)],
        facecolor=COL_PANEL, edgecolor='black', linewidth=1.0,
        label=f'Panel (620W @ {tilt_deg:.0f}°)'
    )
    ax.add_patch(panel)
    # Tilted north rail
    north_rail_tilted = Polygon(
        [(-BED_W/2, FRAME_Y_BOTTOM + RAIL_H),
         (high_z - RAIL_T * math.cos(tilt), high_y + RAIL_H * math.cos(tilt) + PANEL_T),
         (high_z, high_y + PANEL_T + RAIL_H),
         (BED_W/2, FRAME_Y_BOTTOM + RAIL_H)],
        facecolor=COL_FRAME, edgecolor='black', linewidth=0.8
    )
    ax.add_patch(north_rail_tilted)

    # Actuator
    act = Polygon(
        [(-BED_W/2, FRAME_Y_BOTTOM), (-BED_W/2 + 0.5, FRAME_Y_BOTTOM),
         (high_z + 0.5, high_y + PANEL_T), (high_z, high_y + PANEL_T)],
        facecolor=COL_ACT, edgecolor='black', linewidth=0.6,
        label='Linear actuator (4" stroke)'
    )
    ax.add_patch(act)

    # Tilt angle arc
    arc = plt.matplotlib.patches.Arc(
        (BED_W/2, FRAME_Y_BOTTOM), 24, 24, angle=0,
        theta1=180 - tilt_deg, theta2=180,
        color='red', linewidth=1.5
    )
    ax.add_patch(arc)
    ax.text(BED_W/2 - 14, FRAME_Y_BOTTOM + 2,
            f"{tilt_deg:.0f}° tilt", color='red', fontsize=11, weight='bold')

    # Annotations
    ax.annotate("", xy=(-BED_W/2 - 4, 0), xytext=(-BED_W/2 - 4, FRAME_Y_BOTTOM + RAIL_H),
                arrowprops=dict(arrowstyle='<->', color='blue', lw=1.0))
    ax.text(-BED_W/2 - 6, (FRAME_Y_BOTTOM + RAIL_H)/2, f"{RAIL_H:.1f}\"\n2x6 rail",
            color='blue', fontsize=9, va='center')
    ax.annotate("", xy=(high_z + 3, FRAME_Y_BOTTOM), xytext=(high_z + 3, high_y),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1.0))
    ax.text(high_z + 5, (FRAME_Y_BOTTOM + high_y)/2,
            f"high\n{((high_y-FRAME_Y_BOTTOM)/12):.1f} ft", color='green', fontsize=8, va='center')
    ax.annotate("", xy=(-BED_W/2, -SKID_S - 5), xytext=(BED_W/2, -SKID_S - 5),
                arrowprops=dict(arrowstyle='<->', color='black', lw=0.8))
    ax.text(0, -SKID_S - 9, f'Bed: {BED_W/12:.2f} ft wide', ha='center', fontsize=9)
    ax.text(0, sd/2, 'Soil\nballast', ha='center', va='center', color='white', fontsize=10, weight='bold')

    ax.set_xlim(-30, 30)
    ax.set_ylim(-15, 50)
    ax.set_aspect('equal')
    ax.set_xlabel("Z (north ←  → south, inches)")
    ax.set_ylabel("Y (up, inches)")
    ax.set_title(f"Wattplot v2 — East side view (frame at {tilt_deg:.0f}°)\n"
                 f"2x6 PT long rails on top of 2x12 PT bed walls, ½\" pin hinge on south wall",
                 fontsize=11)
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(outpath, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"[render] east: {outpath}")


def render_all(outdir=None):
    """Render iso + top + east views at default tilt."""
    if outdir is None:
        outdir = os.path.join(HERE, "..", "renders")
    os.makedirs(outdir, exist_ok=True)
    # ISO at 35° tilt
    render_iso(os.path.join(outdir, "wattplot_v2_iso.png"), tilt_deg=35.0)
    # Top-down (always flat for clarity)
    render_top_view(os.path.join(outdir, "wattplot_v2_top.png"), tilt_deg=0.0)
    # East side view at 35° tilt
    render_east_view(os.path.join(outdir, "wattplot_v2_east_side.png"), tilt_deg=35.0)
    # Also flat iso (0°) for reference
    render_iso(os.path.join(outdir, "wattplot_v2_flat_iso.png"), tilt_deg=0.0)


if __name__ == "__main__":
    render_all()
