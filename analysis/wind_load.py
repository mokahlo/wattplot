"""
Wattplot v2 — Wind load analysis (ASCE 7-22, Risk Cat II, 700-yr MRI)
Site: Phoenix, AZ (Maricopa County) — V_ult = 115 mph 3-second gust
Exposure C, open suburban / flat land.
Structure is ballasted by the soil-filled planter (no ground anchors).

Parameters come from wattplot_params.py.

Outputs:
    analysis/wind_load_report.md   - human-readable summary
    renders/wind_load_summary.png  - force / safety-factor plots
    renders/wind_load_forces.png   - force vectors on the structure
"""

import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from wattplot_params import LOCATION, BED, PANEL, SOIL

# ----------------------------------------------------------------------------
# INPUTS (loaded from wattplot_params.py — single source of truth)
# ----------------------------------------------------------------------------
SITE = dict(
    name             = f"{LOCATION['name']} (Maricopa County)",
    V_ult_mph        = LOCATION['design_wind_speed_mph'],
    V_ult_ms         = round(LOCATION['design_wind_speed_mph'] * 0.447, 1),
    exposure         = LOCATION['design_wind_exposure'],
    Kzt              = 1.0,      # flat terrain
    Kd               = 0.85,     # directionality factor for solar panels
)

PANEL_WIND = dict(
    L_ft             = PANEL['L_in'] / 12.0,
    W_ft             = PANEL['W_in'] / 12.0,
    t_in             = PANEL['thickness_in'],
    mass_lb          = PANEL['mass_lb'],
    area_sqft        = (PANEL['L_in'] * PANEL['W_in']) / 144.0,
)

BED_WIND = dict(
    outer_L_ft       = BED['outer_L_in'] / 12.0,
    outer_W_ft       = BED['outer_W_in'] / 12.0,
    soil_depth_in    = BED['wall_h_in'],
    wall_thk_in      = BED['wall_thk_in'],
    floor_thk_in     = 0.0,
    wall_height_in   = BED['wall_h_in'],
)

SOIL_WIND = dict(
    dry_density_pcf  = SOIL['density_pcf'],
    saturation_factor= SOIL['saturation_factor'],
)

# Wood (rough lumber volume estimates, computed from the structure params)
_post_side_ft = 5.5 / 12.0  # STRUCTURE['post_side_in'] = 5.5
_post_height_ft = 120.0 / 12.0
_beam_side_ft = 5.5 / 12.0
_beam_length_ft = 84.0 / 12.0
WOOD = dict(
    density_pcf      = 30.0,
    post_vol_cuft    = _post_side_ft ** 2 * _post_height_ft * 2,
    beam_vol_cuft    = _beam_side_ft ** 2 * _beam_length_ft,
    wall_vol_cuft    = (2 * (BED_WIND['outer_L_ft'] + BED_WIND['outer_W_ft'])) * (BED_WIND['wall_height_in']/12) * (BED_WIND['wall_thk_in']/12),
)

FRICTION_MU = SOIL['friction_mu']
CF = 1.5
TILTS_DEG = [0, 15, 25, 35, 45, 50, 75, 90]
SF_TARGET = dict(uplift=1.5, sliding=1.5, overturning=2.0)


# ----------------------------------------------------------------------------
# ASCE 7-22 helpers
# ----------------------------------------------------------------------------
def Kz_ExpC(z_ft: float) -> float:
    """Velocity pressure exposure coefficient, Exposure C, ASCE 7-22 Table 26.10-1."""
    # Tabulated values + interpolation
    table = [
        (0,    0.85),  # 0 to <=15 ft
        (15,   0.85),
        (20,   0.90),
        (25,   0.94),
        (30,   0.98),
        (40,   1.04),
        (50,   1.09),
    ]
    if z_ft <= 15:
        return table[0][1]
    for i in range(len(table)-1):
        z0, k0 = table[i]
        z1, k1 = table[i+1]
        if z0 <= z_ft <= z1:
            return k0 + (k1 - k0) * (z_ft - z0) / (z1 - z0)
    return table[-1][1]


def qz_psf(V_mph: float, Kz: float, Kzt: float, Kd: float) -> float:
    """Velocity pressure qz in psf, ASCE 7-22 Eq. 26.10-1."""
    return 0.00256 * Kz * Kzt * Kd * V_mph ** 2


def panel_geometry(tilt_deg: float):
    """Return panel hinge location, centroid, high-edge location in inches."""
    bed_top_y_in = BED_WIND['wall_height_in']                  # 12"
    hinge_z_in   = BED_WIND['outer_W_ft'] * 12 / 2             # south wall top
    pL_in        = PANEL_WIND['L_ft'] * 12
    theta        = math.radians(tilt_deg)

    z_low_in  = hinge_z_in                                # +Z, hinge on south wall
    y_low_in  = bed_top_y_in
    z_high_in = hinge_z_in - pL_in * math.cos(theta)      # north (-Z)
    y_high_in = bed_top_y_in + pL_in * math.sin(theta)
    z_c_in    = (z_low_in + z_high_in) / 2
    y_c_in    = (y_low_in + y_high_in) / 2
    return {
        "hinge": (0, y_low_in, z_low_in),
        "centroid": (0, y_c_in, z_c_in),
        "high_edge": (0, y_high_in, z_high_in),
        "centroid_height_ft": y_c_in / 12.0,
    }


def wind_forces_on_panel(tilt_deg: float, V_mph: float = SITE['V_ult_mph']):
    """Compute horizontal drag and vertical lift forces on the tilted panel.

    Wind assumed from the south (worst-case uplift + drag for north-hemisphere
    canopies). Plate normal points up-and-south when tilted with high side north.
    """
    geom = panel_geometry(tilt_deg)
    z_c_ft = geom['centroid_height_ft']

    Kz = Kz_ExpC(z_c_ft)
    qh = qz_psf(V_mph, Kz, SITE['Kzt'], SITE['Kd'])  # psf

    A = PANEL_WIND['area_sqft']
    theta = math.radians(tilt_deg)

    # Wind normal force on tilted plate (projected area = A*sin(theta))
    F_N = qh * A * math.sin(theta) * CF          # lb, along plate normal

    # Decompose: normal is (0, cos(theta), sin(theta))  [+Y, +Z = up, toward wind]
    F_vert = F_N * math.cos(theta)               # lb, +Y (uplift on the panel)
    F_horiz = F_N * math.sin(theta)              # lb, +Z (drag toward wind)

    return {
        "tilt_deg": tilt_deg,
        "Kz": Kz,
        "qh_psf": qh,
        "F_normal_lb": F_N,
        "F_vert_lb": F_vert,                     # uplift
        "F_horiz_lb": F_horiz,                   # drag, in +Z
        "panel_centroid_height_ft": z_c_ft,
        "panel_centroid_z_in": geom['centroid'][2],
    }


# ----------------------------------------------------------------------------
# Ballast (dead load) calc
# ----------------------------------------------------------------------------
def dead_load(soil_depth_in: float = None):
    """Total dead load in lb (bed wood + soil + posts + beam + panel + hardware)."""
    if soil_depth_in is None:
        soil_depth_in = BED_WIND['soil_depth_in']

    # Soil (interior volume, accounting for wall thickness)
    interior_L = BED_WIND['outer_L_ft'] - 2 * (BED_WIND['wall_thk_in']/12)
    interior_W = BED_WIND['outer_W_ft'] - 2 * (BED_WIND['wall_thk_in']/12)
    soil_vol_cuft = interior_L * interior_W * (soil_depth_in / 12.0)
    soil_lb = soil_vol_cuft * SOIL_WIND['dry_density_pcf'] * SOIL_WIND['saturation_factor']

    # Wood volume -> weight
    wood_vol = (WOOD['post_vol_cuft'] + WOOD['beam_vol_cuft'] + WOOD['wall_vol_cuft'])
    wood_lb  = wood_vol * WOOD['density_pcf']

    panel_lb = PANEL_WIND['mass_lb']

    # Hardware (hinges, bolts, screws, etc.)
    hardware_lb = 25.0

    total = soil_lb + wood_lb + panel_lb + hardware_lb

    return {
        "soil_depth_in": soil_depth_in,
        "soil_lb": soil_lb,
        "wood_lb": wood_lb,
        "panel_lb": panel_lb,
        "hardware_lb": hardware_lb,
        "total_lb": total,
        "soil_vol_cuft": soil_vol_cuft,
        "interior_L_ft": interior_L,
        "interior_W_ft": interior_W,
    }


# ----------------------------------------------------------------------------
# Stability checks
# ----------------------------------------------------------------------------
def check_stability(tilt_deg: float, soil_depth_in: float = None,
                    V_mph: float = SITE['V_ult_mph']):
    """Uplift / sliding / overturning vs. dead load + friction.

    Pivot for overturning = windward bed edge in plan (Z = -outer_W/2 if wind from +Z).
    """
    forces = wind_forces_on_panel(tilt_deg, V_mph)
    load   = dead_load(soil_depth_in)

    W = load['total_lb']
    F_v = forces['F_vert_lb']                # uplift (lb)
    F_h = forces['F_horiz_lb']               # drag (lb)

    # 1. UPLIFT
    sf_uplift = W / F_v if F_v > 0 else float('inf')

    # 2. SLIDING (friction along the bed footprint)
    f_resist = W * FRICTION_MU                # friction resists horizontal motion
    sf_sliding = f_resist / F_h if F_h > 0 else float('inf')

    # 3. OVERTURNING
    # Pivot is the leeward bed edge in plan:  Z_pivot = -outer_W/2
    # (wind from +Z, structure tips toward -Z)
    z_pivot_in = -BED_WIND['outer_W_ft'] * 12 / 2
    z_c_in     = forces['panel_centroid_z_in']
    y_c_in     = forces['panel_centroid_height_ft'] * 12

    # Dead load acts at the bed's center of mass, Z_cm = 0
    z_cm_in = 0.0

    # Overturning moment about pivot (about the X axis, tipping in -Z direction)
    #  M_OT = F_v * (z_c - z_pivot)  +  F_h * y_c
    M_ot_ftlb = F_v * (z_c_in - z_pivot_in) / 12.0 + F_h * (y_c_in / 12.0)
    # Restoring moment: dead load * horizontal arm from pivot to CM
    M_r_ftlb  = W * (z_cm_in - z_pivot_in) / 12.0
    sf_overturning = M_r_ftlb / M_ot_ftlb if M_ot_ftlb > 0 else float('inf')

    return {
        "tilt_deg": tilt_deg,
        "V_mph": V_mph,
        "F_vert_lb": F_v,
        "F_horiz_lb": F_h,
        "W_lb": W,
        "friction_resist_lb": f_resist,
        "M_overturning_ftlb": M_ot_ftlb,
        "M_restoring_ftlb": M_r_ftlb,
        "sf_uplift": sf_uplift,
        "sf_sliding": sf_sliding,
        "sf_overturning": sf_overturning,
        "load_breakdown": load,
    }


# ----------------------------------------------------------------------------
# Required soil depth solver
# ----------------------------------------------------------------------------
def required_soil_depth(tilt_deg: float, target_sf: float = SF_TARGET['overturning'],
                        V_mph: float = SITE['V_ult_mph']):
    """Binary search for soil depth that hits the target overturning SF."""
    lo, hi = 1.0, 36.0   # inches
    for _ in range(60):
        mid = (lo + hi) / 2
        r = check_stability(tilt_deg, soil_depth_in=mid, V_mph=V_mph)
        if r['sf_overturning'] < target_sf:
            lo = mid
        else:
            hi = mid
    return hi


# ----------------------------------------------------------------------------
# Reporting + visualization
# ----------------------------------------------------------------------------
def run_analysis():
    here = os.path.dirname(os.path.abspath(__file__))
    out_md = os.path.join(here, "wind_load_report.md")
    fig1   = os.path.join(here, "..", "renders", "wind_load_summary.png")
    fig2   = os.path.join(here, "..", "renders", "wind_load_forces.png")
    os.makedirs(os.path.dirname(fig1), exist_ok=True)

    # Sweep tilts
    rows = []
    for t in TILTS_DEG:
        r = check_stability(t)
        rows.append(r)

    # Solve for required soil depth at worst-case tilt
    worst_tilt = max(TILTS_DEG, key=lambda t: check_stability(t)['F_vert_lb'])
    req_depth = required_soil_depth(worst_tilt)

    # ---------------- Markdown report ----------------
    md = []
    md.append(f"# Wattplot v2 — Wind Load Analysis\n")
    md.append(f"**Site:** {SITE['name']}  ")
    md.append(f"**Standard:** ASCE 7-22, Risk Cat II, 700-yr MRI  ")
    md.append(f"**Basic wind speed V:** {SITE['V_ult_mph']} mph 3-sec gust "
              f"({SITE['V_ult_ms']} m/s) at 33 ft, Exposure C  ")
    md.append(f"**Exposure:** {SITE['exposure']} (Kzt = {SITE['Kzt']}, Kd = {SITE['Kd']})  ")
    md.append(f"**Force coefficient Cf:** {CF} (open tilted plate, conservative)\n")

    md.append(f"## Geometry\n")
    md.append(f"- Panel: {PANEL_WIND['L_ft']} ft × {PANEL_WIND['W_ft']} ft × {PANEL_WIND['t_in']}\" "
              f"({PANEL_WIND['area_sqft']:.2f} sq ft, ~{PANEL_WIND['mass_lb']} lb)")
    md.append(f"- Bed: {BED_WIND['outer_L_ft']} ft × {BED_WIND['outer_W_ft']} ft × "
              f"{BED_WIND['wall_height_in']}\" wall")
    md.append(f"- Wood density assumed: {WOOD['density_pcf']} pcf (PT pine, conservative)")
    md.append(f"- Soil density assumed: {SOIL_WIND['dry_density_pcf']} pcf "
              f"(wet loam/compost, ×{SOIL_WIND['saturation_factor']} saturation)")
    md.append(f"- Bed-on-grade friction: μ = {FRICTION_MU}\n")

    md.append(f"## Dead load (ballast) at {BED_WIND['soil_depth_in']}\" soil depth\n")
    base = dead_load()
    md.append(f"| Component | Weight |")
    md.append(f"|---|---|")
    md.append(f"| Soil ({base['soil_vol_cuft']:.2f} cu ft) | {base['soil_lb']:.0f} lb |")
    md.append(f"| Lumber (posts + beam + walls) | {base['wood_lb']:.0f} lb |")
    md.append(f"| Panel | {base['panel_lb']:.0f} lb |")
    md.append(f"| Hardware (hinges/bolts) | {base['hardware_lb']:.0f} lb |")
    md.append(f"| **Total dead load W** | **{base['total_lb']:.0f} lb** |\n")

    md.append(f"## Force sweep across tilt angles\n")
    md.append(f"| Tilt | qh (psf) | F_vert (uplift, lb) | F_horiz (drag, lb) | SF uplift | SF sliding | SF overturning |")
    md.append(f"|---|---|---|---|---|---|---|")
    for r in rows:
        md.append(f"| {r['tilt_deg']}° | {wind_forces_on_panel(r['tilt_deg'])['qh_psf']:.1f} | "
                  f"{r['F_vert_lb']:.0f} | {r['F_horiz_lb']:.0f} | "
                  f"{r['sf_uplift']:.2f} | {r['sf_sliding']:.2f} | {r['sf_overturning']:.2f} |")
    md.append("")

    md.append(f"## Verdict at default {BED_WIND['soil_depth_in']}\" soil depth\n")
    r35 = check_stability(35)
    md.append(f"At the v1 design tilt of 35° (and V = {SITE['V_ult_mph']} mph):\n")
    md.append(f"- Uplift safety factor: **{r35['sf_uplift']:.2f}** "
              f"(target ≥ {SF_TARGET['uplift']}) — "
              f"{'PASS' if r35['sf_uplift'] >= SF_TARGET['uplift'] else '**FAIL**'}")
    md.append(f"- Sliding safety factor: **{r35['sf_sliding']:.2f}** "
              f"(target ≥ {SF_TARGET['sliding']}) — "
              f"{'PASS' if r35['sf_sliding'] >= SF_TARGET['sliding'] else '**FAIL**'}")
    md.append(f"- Overturning safety factor: **{r35['sf_overturning']:.2f}** "
              f"(target ≥ {SF_TARGET['overturning']}) — "
              f"{'PASS' if r35['sf_overturning'] >= SF_TARGET['overturning'] else '**FAIL**'}\n")

    md.append(f"## Recommended soil depth\n")
    md.append(f"Worst-case uplift tilt is **{worst_tilt}°** (sin(2θ) is maximum at 45°).")
    md.append(f"To hit the overturning target SF ≥ {SF_TARGET['overturning']} at "
              f"{worst_tilt}° tilt and V = {SITE['V_ult_mph']} mph, you need approximately:\n")
    md.append(f"### **Soil depth ≥ {req_depth:.1f}\"** ({(req_depth/12):.2f} ft)\n")
    md.append(f"At that depth:\n")
    r_req = check_stability(worst_tilt, soil_depth_in=req_depth)
    md.append(f"- Total dead load: {r_req['W_lb']:.0f} lb")
    md.append(f"- SF uplift: {r_req['sf_uplift']:.2f}, "
              f"SF sliding: {r_req['sf_sliding']:.2f}, "
              f"SF overturning: {r_req['sf_overturning']:.2f}\n")

    md.append(f"## Notes & caveats\n")
    md.append(f"- **First-pass engineering, not stamped calcs.** If this is a real build "
              f"in Phoenix city limits, the structure may need a permit and a PE stamp. "
              f"Maricopa County wind amendments and IRC triggers are real.")
    md.append(f"- Cf = {CF} is conservative for an open plate. ASCE 7 doesn't have a "
              f"dedicated section for a one-panel solar canopy, so we used a free-plate "
              f"value. A real calc could refine with wind-tunnel data or a CFD check.")
    md.append(f"- Soil weight is the swing variable. Wet/wet+saturated soil can be "
              f"30-50% heavier than dry. We used a wet-loam value ({SOIL_WIND['dry_density_pcf']} pcf).")
    md.append(f"- Friction coefficient μ = {FRICTION_MU} is a conservative estimate for "
              f"PT pine on dirt. Wet/muddy ground could be 0.2-0.3; on a gravel pad or "
              f"concrete, could be 0.5-0.6.")
    md.append(f"- The big lever here is **soil depth**. Every extra inch of soil is ~190 lb "
              f"of ballast. If you want a margin, go deeper rather than wider.\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"[wind] wrote {out_md}")

    # ---------------- Plots ----------------
    tilts = [r['tilt_deg'] for r in rows]
    Fv    = [r['F_vert_lb'] for r in rows]
    Fh    = [r['F_horiz_lb'] for r in rows]
    SFu   = [r['sf_uplift'] for r in rows]
    SFs   = [r['sf_sliding'] for r in rows]
    SFo   = [r['sf_overturning'] for r in rows]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    ax.plot(tilts, Fv, 'o-', label='Uplift (vertical, lb)', color='#c0392b')
    ax.plot(tilts, Fh, 's-', label='Drag (horizontal, lb)', color='#2c3e50')
    ax.set_xlabel("Panel tilt (deg)")
    ax.set_ylabel("Force on panel (lb)")
    ax.set_title(f"Wind forces vs. tilt\nV = {SITE['V_ult_mph']} mph, Exp C, Cat II 700-yr")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1]
    ax.plot(tilts, SFu, 'o-', label='SF uplift',  color='#c0392b')
    ax.plot(tilts, SFs, 's-', label='SF sliding', color='#16a085')
    ax.plot(tilts, SFo, '^-', label='SF overturning', color='#8e44ad')
    ax.axhline(SF_TARGET['uplift'],     color='#c0392b', ls=':', alpha=0.5, label=f"target uplift ({SF_TARGET['uplift']})")
    ax.axhline(SF_TARGET['sliding'],    color='#16a085', ls=':', alpha=0.5, label=f"target sliding ({SF_TARGET['sliding']})")
    ax.axhline(SF_TARGET['overturning'],color='#8e44ad', ls=':', alpha=0.5, label=f"target overturning ({SF_TARGET['overturning']})")
    ax.set_xlabel("Panel tilt (deg)")
    ax.set_ylabel("Safety factor (dead_load / demand)")
    ax.set_title(f"Safety factors at {BED_WIND['soil_depth_in']}\" soil depth\n"
                 f"Total dead load = {base['total_lb']:.0f} lb")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()
    plt.savefig(fig1, dpi=130)
    plt.close()
    print(f"[wind] wrote {fig1}")

    # Force-vector diagram (side view, 2D)
    fig, ax = plt.subplots(figsize=(12, 6))
    bedL = BED_WIND['outer_L_ft']
    bedW = BED_WIND['outer_W_ft']
    wall_h = BED_WIND['wall_height_in']/12.0

    # Bed (top view rectangle)
    bed_rect = Rectangle((-bedL/2, 0), bedL, bedW, fill=True,
                         facecolor='#8d6e63', edgecolor='black', alpha=0.6, label='Planter footprint')
    ax.add_patch(bed_rect)

    # Pivot for overturning
    pivot = (-bedL/2, 0)  # in plan, leeward bed edge if wind from +Z
    ax.plot(*pivot, 'ko', markersize=8)
    ax.annotate("Overturning\npivot", pivot, textcoords="offset points",
                xytext=(8, -10), fontsize=8)

    # Wind direction arrow
    ax.annotate("", xy=(bedL/2 + 1, bedW/2 + 0.5), xytext=(bedL/2 + 0.2, bedW/2 + 0.5),
                arrowprops=dict(arrowstyle="->", color='red', lw=2))
    ax.text(bedL/2 + 0.5, bedW/2 + 0.7, "Wind from south (+Z)", color='red', fontsize=9)

    # Center of mass
    cm = (0, 0)
    ax.plot(*cm, 'g^', markersize=10)
    ax.annotate("Dead-load CM\n(bed center)", cm, textcoords="offset points",
                xytext=(-50, -25), fontsize=8, color='green')

    # Force vectors on the panel (worst-case tilt = 45°)
    forces_45 = check_stability(45)
    Fv = forces_45['F_vert_lb']
    Fh = forces_45['F_horiz_lb']

    panel_centroid = (0, forces_45['load_breakdown']['interior_W_ft']/2 - 1.0)  # rough z-position
    # Better: actual centroid in Z from earlier
    geom45 = panel_geometry(45)
    panel_centroid = (0, geom45['centroid'][2]/12.0)
    # uplift arrow (up, +Y -> but we're in plan view, so show in 2D as a "tipping" arrow)
    ax.annotate(f"Uplift {Fv:.0f} lb\n(vertical, lifts panel)", panel_centroid,
                textcoords="offset points", xytext=(20, 20), fontsize=9, color='#c0392b',
                arrowprops=dict(arrowstyle="->", color='#c0392b'))
    # drag arrow (in plan, +Z direction)
    ax.annotate("", xy=(panel_centroid[0], panel_centroid[1] + 0.4),
                xytext=panel_centroid,
                arrowprops=dict(arrowstyle="->", color='#2c3e50', lw=2))
    ax.text(panel_centroid[0] + 0.05, panel_centroid[1] + 0.2,
            f"Drag {Fh:.0f} lb", color='#2c3e50', fontsize=9)

    ax.set_xlim(-bedL/2 - 0.5, bedL/2 + 1.5)
    ax.set_ylim(-bedW/2 - 0.5, bedW/2 + 1.5)
    ax.set_aspect('equal')
    ax.set_xlabel("X (east, ft)")
    ax.set_ylabel("Z (south, ft)")
    ax.set_title(f"Force diagram at 45° tilt (worst-case uplift)\n"
                 f"Dead load W = {forces_45['W_lb']:.0f} lb  |  "
                 f"SF overturning = {forces_45['sf_overturning']:.2f}")
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower left')
    plt.tight_layout()
    plt.savefig(fig2, dpi=130)
    plt.close()
    print(f"[wind] wrote {fig2}")

    return rows, req_depth


if __name__ == "__main__":
    rows, req_depth = run_analysis()
    print()
    print("=" * 60)
    print(f"Site: {SITE['name']}, V_ult = {SITE['V_ult_mph']} mph")
    print(f"Panel: {PANEL_WIND['L_ft']} x {PANEL_WIND['W_ft']} ft ({PANEL_WIND['area_sqft']:.2f} sq ft)")
    print(f"Default soil depth: {BED_WIND['soil_depth_in']}\"")
    print()
    print(f"{'Tilt':>5} {'qh(psf)':>9} {'Fvert':>7} {'Fhoriz':>7} {'SFu':>6} {'SFs':>6} {'SFo':>6}")
    for r in rows:
        qh = wind_forces_on_panel(r['tilt_deg'])['qh_psf']
        print(f"{r['tilt_deg']:>4}° {qh:>9.1f} {r['F_vert_lb']:>7.0f} "
              f"{r['F_horiz_lb']:>7.0f} {r['sf_uplift']:>6.2f} "
              f"{r['sf_sliding']:>6.2f} {r['sf_overturning']:>6.2f}")
    print()
    print(f"Recommended soil depth for SF_overturning >= {SF_TARGET['overturning']}: "
          f"{req_depth:.1f}\" ({(req_depth/12):.2f} ft)")
    print("=" * 60)
