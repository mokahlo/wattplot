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

import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from wattplot_params import BED, CONTROL, LOCATION, PANEL, POSTS, SOIL

# Canopy height: the panel rests on rails across the 72" corner posts.
POST_TOP_Y_IN = POSTS['height_in'] + POSTS['rail_thickness_in']

# ----------------------------------------------------------------------------
# INPUTS (loaded from wattplot_params.py — single source of truth)
# ----------------------------------------------------------------------------
SITE = {
    "name": f"{LOCATION['name']} (Maricopa County)",
    "V_ult_mph": LOCATION['design_wind_speed_mph'],
    "V_ult_ms": round(LOCATION['design_wind_speed_mph'] * 0.447, 1),
    "exposure": LOCATION['design_wind_exposure'],
    "Kzt": 1.0,      # flat terrain
    "Kd": 0.85,     # directionality factor for solar panels
}

PANEL_WIND = {
    "L_ft": PANEL['L_in'] / 12.0,
    "W_ft": PANEL['W_in'] / 12.0,
    "t_in": PANEL['thickness_in'],
    "mass_lb": PANEL['mass_lb'],
    "area_sqft": (PANEL['L_in'] * PANEL['W_in']) / 144.0,
}

BED_WIND = {
    "outer_L_ft": BED['outer_L_in'] / 12.0,
    "outer_W_ft": BED['outer_W_in'] / 12.0,
    # Ballast soil = actual fill depth (freeboard below rim doesn't count),
    # falling back to wall height for configs without an explicit fill.
    "soil_depth_in": BED.get('soil_fill_in', BED['wall_h_in']),
    "wall_thk_in": BED['wall_thk_in'],
    "floor_thk_in": 0.0,
    "wall_height_in": BED['wall_h_in'],
}

SOIL_WIND = {
    "dry_density_pcf": SOIL['density_pcf'],
    "saturation_factor": SOIL['saturation_factor'],
}

# Wood (rough lumber volume estimates, computed from the actual v2 structure:
# 4 × 4x4 corner posts at POSTS['height_in'], 4 panel rails on top, and the
# 1x6-skin bed walls). Cleats/headers/footers/slats are lumped into a flat
# 20% adder on the wall volume rather than modeled board by board.
_post_side_ft   = POSTS['thickness_in'] / 12.0
_post_height_ft = POSTS['height_in'] / 12.0
_rail_t_ft      = POSTS['rail_thickness_in'] / 12.0
_rail_w_ft      = POSTS['rail_width_in'] / 12.0
WOOD = {
    "density_pcf": 30.0,
    "post_vol_cuft": _post_side_ft ** 2 * _post_height_ft * POSTS['count'],
    # 2 rails along the length + 2 across the width
    "beam_vol_cuft": _rail_t_ft * _rail_w_ft * 2 * (BED_WIND['outer_L_ft']
                                                      + BED_WIND['outer_W_ft']),
    "wall_vol_cuft": 1.20 * (2 * (BED_WIND['outer_L_ft'] + BED_WIND['outer_W_ft']))
                       * (BED_WIND['wall_height_in']/12) * (BED_WIND['wall_thk_in']/12),
}

# Corner-post wind drag. The 4 posts are a small but non-trivial extra
# overturning moment (they act at mid-height, ~3 ft, while the panel acts
# at ~6 ft). ASCE Cf ~1.3 for a square section; the two leeward posts are
# shielded by the windward pair, so only 2 posts are counted.
POST_DRAG = {
    "cf": 1.3,
    "n_effective": 2,
    "area_sqft": (POSTS['thickness_in']/12.0) * (POSTS['height_in']/12.0),
    "centroid_ft": POSTS['height_in'] / 12.0 / 2.0,
}

FRICTION_MU = SOIL['friction_mu']
CF = 1.5
# Sweep through and past the structural cap so the report shows WHY the cap
# is where it is. CONTROL['max_tilt_deg'] is the operating limit.
TILTS_DEG = [0, 15, 25, 35, 45, 50, 75, 90]
MAX_TILT_DEG = CONTROL['max_tilt_deg']
SF_TARGET = {"uplift": 1.5, "sliding": 1.5, "overturning": 2.0}


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
    """Return panel pivot location, centroid, high-edge location in inches.

    CANONICAL v2 GEOMETRY: the panel rides on four 72" corner posts, NOT
    hinged on the bed's south wall. The panel pivots about the rails laid
    across the post tops, so it is centered on the bed in plan (z_c = 0)
    and its centroid sits ~POST_H above grade. This is the dominant term
    in the overturning check - drag on a ~7.5 ft lever arm about the bed
    edge, roughly 3x the old bed-level arrangement.

    The panel WIDTH (short axis) is what tilts about the pivot; the long
    axis runs along the posts. Tilting raises the north edge by
    W*sin(theta)/2 above and drops the south edge equally below.
    """
    post_top_y_in = POST_TOP_Y_IN
    pW_in         = PANEL_WIND['W_ft'] * 12          # short axis tilts
    theta         = math.radians(tilt_deg)

    # Panel pivots about its own centerline on the rails, centered on the bed
    z_c_in    = 0.0
    y_c_in    = post_top_y_in
    z_high_in = -pW_in * math.cos(theta) / 2.0                 # north edge
    y_high_in = post_top_y_in + pW_in * math.sin(theta) / 2.0
    z_low_in  = +pW_in * math.cos(theta) / 2.0                 # south edge
    y_low_in  = post_top_y_in - pW_in * math.sin(theta) / 2.0
    return {
        "pivot": (0, post_top_y_in, 0),
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
def dead_load(soil_depth_in: float | None = None):
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
def check_stability(tilt_deg: float, soil_depth_in: float | None = None,
                    V_mph: float = SITE['V_ult_mph']):
    """Uplift / sliding / overturning vs. dead load + friction.

    Pivot for overturning = windward bed edge in plan (Z = -outer_W/2 if wind from +Z).
    """
    forces = wind_forces_on_panel(tilt_deg, V_mph)
    load   = dead_load(soil_depth_in)

    W = load['total_lb']
    F_v = forces['F_vert_lb']                # uplift (lb)
    F_h = forces['F_horiz_lb']               # drag on the panel (lb)

    # Corner-post drag (acts at post mid-height, independent of tilt)
    qh_post = qz_psf(V_mph, Kz_ExpC(POST_DRAG['centroid_ft']),
                     SITE['Kzt'], SITE['Kd'])
    F_h_posts = (qh_post * POST_DRAG['area_sqft']
                 * POST_DRAG['n_effective'] * POST_DRAG['cf'])
    F_h_total = F_h + F_h_posts

    # 1. UPLIFT (posts add no vertical load)
    sf_uplift = W / F_v if F_v > 0 else float('inf')

    # 2. SLIDING (friction along the bed footprint)
    f_resist = W * FRICTION_MU                # friction resists horizontal motion
    sf_sliding = f_resist / F_h_total if F_h_total > 0 else float('inf')

    # 3. OVERTURNING
    # Pivot is the leeward bed edge in plan:  Z_pivot = -outer_W/2
    # (wind from +Z, structure tips toward -Z)
    z_pivot_in = -BED_WIND['outer_W_ft'] * 12 / 2
    z_c_in     = forces['panel_centroid_z_in']
    y_c_in     = forces['panel_centroid_height_ft'] * 12

    # Dead load acts at the bed's center of mass, Z_cm = 0
    z_cm_in = 0.0

    # Overturning moment about pivot (about the X axis, tipping in -Z direction)
    #  M_OT = F_v * (z_c - z_pivot)  +  F_h * y_c  +  F_h_posts * y_posts
    M_ot_ftlb = (F_v * (z_c_in - z_pivot_in) / 12.0
                 + F_h * (y_c_in / 12.0)
                 + F_h_posts * POST_DRAG['centroid_ft'])
    # Restoring moment: dead load * horizontal arm from pivot to CM
    M_r_ftlb  = W * (z_cm_in - z_pivot_in) / 12.0
    sf_overturning = M_r_ftlb / M_ot_ftlb if M_ot_ftlb > 0 else float('inf')

    return {
        "tilt_deg": tilt_deg,
        "V_mph": V_mph,
        "F_vert_lb": F_v,
        "F_horiz_lb": F_h,
        "F_horiz_posts_lb": F_h_posts,
        "F_horiz_total_lb": F_h_total,
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
    md.append("# Wattplot v2 — Wind Load Analysis\n")
    md.append(f"**Site:** {SITE['name']}  ")
    md.append("**Standard:** ASCE 7-22, Risk Cat II, 700-yr MRI  ")
    md.append(f"**Basic wind speed V:** {SITE['V_ult_mph']} mph 3-sec gust "
              f"({SITE['V_ult_ms']} m/s) at 33 ft, Exposure C  ")
    md.append(f"**Exposure:** {SITE['exposure']} (Kzt = {SITE['Kzt']}, Kd = {SITE['Kd']})  ")
    md.append(f"**Force coefficient Cf:** {CF} (open tilted plate, conservative)\n")

    md.append("## Geometry\n")
    md.append(f"- **Canopy on {POSTS['height_in']:.0f}\" corner posts** — panel centroid "
              f"at {POST_TOP_Y_IN/12:.1f} ft above grade. This long lever arm, not "
              f"uplift, is what governs the design.")
    md.append(f"- **Operating tilt capped at {MAX_TILT_DEG:.0f}°** "
              f"(`CONTROL['max_tilt_deg']`). Rows above it below are shown to "
              f"document why the cap exists — they are NOT operating states.")
    md.append(f"- Panel: {PANEL_WIND['L_ft']} ft × {PANEL_WIND['W_ft']} ft × {PANEL_WIND['t_in']}\" "
              f"({PANEL_WIND['area_sqft']:.2f} sq ft, ~{PANEL_WIND['mass_lb']} lb); "
              f"tilts about its long axis, so the {PANEL_WIND['W_ft']:.2f} ft width rises")
    md.append(f"- Bed: {BED_WIND['outer_L_ft']} ft × {BED_WIND['outer_W_ft']} ft × "
              f"{BED_WIND['wall_height_in']}\" wall, {BED_WIND['soil_depth_in']}\" soil fill")
    md.append(f"- Corner-post drag included: {POST_DRAG['n_effective']} effective posts "
              f"× Cf {POST_DRAG['cf']} acting at {POST_DRAG['centroid_ft']:.1f} ft")
    md.append(f"- Wood density assumed: {WOOD['density_pcf']} pcf (PT pine, conservative)")
    md.append(f"- Soil density assumed: {SOIL_WIND['dry_density_pcf']} pcf "
              f"(wet loam/compost, ×{SOIL_WIND['saturation_factor']} saturation)")
    md.append(f"- Bed-on-grade friction: μ = {FRICTION_MU}\n")

    md.append(f"## Dead load (ballast) at {BED_WIND['soil_depth_in']}\" soil depth\n")
    base = dead_load()
    md.append("| Component | Weight |")
    md.append("|---|---|")
    md.append(f"| Soil ({base['soil_vol_cuft']:.2f} cu ft) | {base['soil_lb']:.0f} lb |")
    md.append(f"| Lumber (posts + beam + walls) | {base['wood_lb']:.0f} lb |")
    md.append(f"| Panel | {base['panel_lb']:.0f} lb |")
    md.append(f"| Hardware (hinges/bolts) | {base['hardware_lb']:.0f} lb |")
    md.append(f"| **Total dead load W** | **{base['total_lb']:.0f} lb** |\n")

    md.append("## Force sweep across tilt angles\n")
    md.append("| Tilt | qh (psf) | F_vert (uplift, lb) | F_horiz (drag, lb) | SF uplift | SF sliding | SF overturning | |")
    md.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        over = r['tilt_deg'] > MAX_TILT_DEG
        flag = "🚫 above cap" if over else ("✅" if r['sf_overturning'] >= SF_TARGET['overturning'] else "⚠️")
        # No uplift at 0° and 90° (plate edge-on / flat), so SF is unbounded
        sfu = "n/a" if r['F_vert_lb'] < 1e-6 else f"{r['sf_uplift']:.2f}"
        md.append(f"| {r['tilt_deg']}° | {wind_forces_on_panel(r['tilt_deg'])['qh_psf']:.1f} | "
                  f"{r['F_vert_lb']:.0f} | {r['F_horiz_total_lb']:.0f} | "
                  f"{sfu} | {r['sf_sliding']:.2f} | {r['sf_overturning']:.2f} | {flag} |")
    md.append("")
    md.append(f"Drag column includes corner-post drag "
              f"({rows[0]['F_horiz_posts_lb']:.0f} lb, constant with tilt).\n")

    md.append(f"## Verdict at the {MAX_TILT_DEG:.0f}° operating cap "
              f"({BED_WIND['soil_depth_in']}\" soil depth)\n")
    r35 = check_stability(MAX_TILT_DEG)
    md.append(f"At the max operating tilt of {MAX_TILT_DEG:.0f}° "
              f"(and V = {SITE['V_ult_mph']} mph):\n")
    md.append(f"- Uplift safety factor: **{r35['sf_uplift']:.2f}** "
              f"(target ≥ {SF_TARGET['uplift']}) — "
              f"{'PASS' if r35['sf_uplift'] >= SF_TARGET['uplift'] else '**FAIL**'}")
    md.append(f"- Sliding safety factor: **{r35['sf_sliding']:.2f}** "
              f"(target ≥ {SF_TARGET['sliding']}) — "
              f"{'PASS' if r35['sf_sliding'] >= SF_TARGET['sliding'] else '**FAIL**'}")
    md.append(f"- Overturning safety factor: **{r35['sf_overturning']:.2f}** "
              f"(target ≥ {SF_TARGET['overturning']}) — "
              f"{'PASS' if r35['sf_overturning'] >= SF_TARGET['overturning'] else '**FAIL**'}\n")

    # Rated wind speed at the operating cap (SF scales with V^2)
    _v_ot = SITE['V_ult_mph'] * math.sqrt(r35['sf_overturning'] / SF_TARGET['overturning'])
    _v_sl = SITE['V_ult_mph'] * math.sqrt(r35['sf_sliding'] / SF_TARGET['sliding'])
    md.append(f"**Rated deployed wind speed at {MAX_TILT_DEG:.0f}°: "
              f"~{min(_v_ot, _v_sl):.0f} mph** (the speed at which the governing "
              f"safety factor reaches its target).\n")
    md.append(f"Stowed flat (0°) the panel contributes no drag or uplift and only the "
              f"posts are loaded — SF overturning {rows[0]['sf_overturning']:.1f}. "
              f"**Stowing is the storm answer for both tiers.**\n")

    md.append("## Recommended soil depth\n")
    md.append(f"Required soil depth is solved at the {MAX_TILT_DEG:.0f}° operating cap "
              f"(above the cap is not an operating state).")
    md.append(f"To hit the overturning target SF ≥ {SF_TARGET['overturning']} at "
              f"{MAX_TILT_DEG:.0f}° tilt and V = {SITE['V_ult_mph']} mph, you need approximately:\n")
    req_depth = required_soil_depth(MAX_TILT_DEG)
    md.append(f"### **Soil depth ≥ {req_depth:.1f}\"** ({(req_depth/12):.2f} ft)\n")
    md.append(f"The build ships {BED_WIND['soil_depth_in']}\" "
              f"({BED['wall_h_in']}\" wall = {BED['wall_h_in']/5.5:.0f} courses of 1x6, "
              f"2\" freeboard). At the required depth:\n")
    r_req = check_stability(MAX_TILT_DEG, soil_depth_in=req_depth)
    md.append(f"- Total dead load: {r_req['W_lb']:.0f} lb")
    md.append(f"- SF uplift: {r_req['sf_uplift']:.2f}, "
              f"SF sliding: {r_req['sf_sliding']:.2f}, "
              f"SF overturning: {r_req['sf_overturning']:.2f}\n")

    md.append("## Notes & caveats\n")
    md.append("- **First-pass engineering, not stamped calcs.** If this is a real build "
              "in Phoenix city limits, the structure may need a permit and a PE stamp. "
              "Maricopa County wind amendments and IRC triggers are real.")
    md.append(f"- Cf = {CF} is conservative for an open plate. ASCE 7 doesn't have a "
              f"dedicated section for a one-panel solar canopy, so we used a free-plate "
              f"value. A real calc could refine with wind-tunnel data or a CFD check.")
    md.append(f"- **Soil weight is the swing variable, and it cuts against us.** We assume "
              f"{SOIL_WIND['dry_density_pcf']} pcf (wet loam). Dry desert soil can be "
              f"55-65 pcf, which drops SF overturning at {MAX_TILT_DEG:.0f}° to ~1.9-2.2. "
              f"This is exactly why the bed is {BED['wall_h_in']:.1f}\" "
              f"({BED['wall_h_in']/5.5:.0f} courses) and not 4 courses — at 4 courses a "
              f"dry bed falls to SF 1.53, below target. Keep the bed watered, or treat "
              f"a bone-dry bed as a reason to stow.")
    md.append(f"- Friction coefficient μ = {FRICTION_MU} is a conservative estimate for "
              f"PT pine on dirt. Wet/muddy ground could be 0.2-0.3; on a gravel pad or "
              f"concrete, could be 0.5-0.6.")
    md.append(f"- **Post drag is modeled crudely.** {POST_DRAG['n_effective']} of "
              f"{POSTS['count']} posts at Cf {POST_DRAG['cf']}, assuming the leeward pair "
              f"is fully shielded. ASCE 7-22 Ch. 29 open-frame provisions would be the "
              f"rigorous route.")
    md.append("- **The posts themselves are checked separately, in "
              "`analysis/post_bending.py` / `post_bending_report.md`.** This analysis "
              "treats the structure as a rigid body tipping about the bed edge; it does "
              "not model the 4x4 posts as cantilevers carrying panel drag at their base "
              "connection. That check exists now — and it **fails** the 4x4 posts, "
              "unbraced, at the 35° operating cap. See the companion report for the two "
              "remedies (upsize to 6x6, or square-cut lateral bracing).")
    md.append("- The big lever here is **soil depth**. Every extra inch of soil is ~190 lb"
              "of ballast. If you want a margin, go deeper rather than wider.\n")

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

    _fig, axes = plt.subplots(1, 2, figsize=(13, 5))

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
    _fig, ax = plt.subplots(figsize=(12, 6))
    bedL = BED_WIND['outer_L_ft']
    bedW = BED_WIND['outer_W_ft']

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
                arrowprops={"arrowstyle": "->", "color": 'red', "lw": 2})
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
                arrowprops={"arrowstyle": "->", "color": '#c0392b'})
    # drag arrow (in plan, +Z direction)
    ax.annotate("", xy=(panel_centroid[0], panel_centroid[1] + 0.4),
                xytext=panel_centroid,
                arrowprops={"arrowstyle": "->", "color": '#2c3e50', "lw": 2})
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
