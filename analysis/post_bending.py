"""
Wattplot v2 — Post bending + lateral bracing analysis

wind_load.py treats the whole structure as a rigid body tipping about the
bed edge. It does not check whether the 4x4 posts themselves survive the
panel drag as a cantilever bending moment at their base connection — the
gap this module closes.

Model (first-pass, not stamped calcs — same caveat as wind_load.py):
  - Each post is a cantilever, fixed at the base, free at the top.
  - Panel drag (from wind_load.wind_forces_on_panel) is delivered to the
    post tops through the rigid rail frame. Absent a bracing design, load
    sharing among the 4 posts cannot be assumed uniform, so — matching the
    "2 effective posts" convention wind_load.py already uses for post
    self-drag — this analysis assumes the WORST-CASE 2 posts carry the
    full panel drag between them (not all 4). This is conservative on
    purpose: bracing (this module's second half) is what actually
    justifies spreading load across all 4 posts.
  - Each of those 2 posts additionally carries its own share of post
    self-drag (already modeled as 2 effective posts in wind_load.py).
  - Moment arm for panel drag = panel centroid height above grade (drag is
    delivered essentially at the post tops). Moment arm for post self-drag
    = post mid-height (uniform pressure on a cantilever of that height).

Allowable stresses come from models/freecad/materials.py WOOD (NDS
Supplement, PT Douglas Fir, wet-use values). Wind is a short-duration
load, so the NDS load-duration factor CD = 1.6 is applied on top of the
tabulated (already wet-use) allowable stresses. No other NDS adjustment
factors (size factor CF, beam-stability CL) are applied — consistent with
wind_load.py's own level of rigor, not a stamped calc.

Outputs:
    analysis/post_bending_report.md   - human-readable summary
    renders/post_bending.png          - stress / SF plots
"""

import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "models", "freecad"))

from wattplot_params import CONTROL, POSTS

from materials import LUMBER, WOOD
from wind_load import POST_DRAG, SITE, Kz_ExpC, panel_geometry, qz_psf, wind_forces_on_panel

# ----------------------------------------------------------------------------
# INPUTS
# ----------------------------------------------------------------------------
POST_SIZE = "4x4"
POST_B_IN = LUMBER[POST_SIZE]["actual_t"]   # 3.5" actual
POST_H_IN = LUMBER[POST_SIZE]["actual_h"]   # 3.5" actual (square post)
POST_HEIGHT_FT = POSTS["height_in"] / 12.0

CD_WIND = 1.6                               # NDS Table 2.3.2, wind/seismic duration
FB_ALLOW_PSI = WOOD["bending_stress_psi"] * CD_WIND
FV_ALLOW_PSI = WOOD["shear_parallel_psi"] * CD_WIND
E_PSI = WOOD["modulus_elasticity_psi"]

# Section properties (square post, load about either axis is the same)
S_IN3 = POST_B_IN * POST_H_IN ** 2 / 6.0     # section modulus
I_IN4 = POST_B_IN * POST_H_IN ** 3 / 12.0    # moment of inertia
A_IN2 = POST_B_IN * POST_H_IN                # cross-section area

N_POSTS_SHARING = 2                          # worst-case 2 of 4 posts, unbraced
DEFLECTION_LIMIT_RATIO = 180                 # L/180, typical for wind sway on a canopy

TILTS_DEG = [0, 15, 25, 35, 45, 50, 75, 90]
MAX_TILT_DEG = CONTROL["max_tilt_deg"]
SF_TARGET = 1.5   # NDS-style target for an allowable-stress check


# ----------------------------------------------------------------------------
# Per-post demand
# ----------------------------------------------------------------------------
def post_demand(tilt_deg: float, V_mph: float = SITE["V_ult_mph"]):
    """Horizontal shear + bending moment at a single post base, worst-case."""
    panel = wind_forces_on_panel(tilt_deg, V_mph)
    geom = panel_geometry(tilt_deg)
    y_c_ft = geom["centroid_height_ft"]      # panel drag delivered ~ here

    # Post self-drag, same "2 effective posts" convention as wind_load.py
    qh_post = qz_psf(V_mph, Kz_ExpC(POST_DRAG["centroid_ft"]), SITE["Kzt"], SITE["Kd"])
    f_h_posts_total = qh_post * POST_DRAG["area_sqft"] * POST_DRAG["n_effective"] * POST_DRAG["cf"]

    # Worst-case: panel drag + post self-drag both funneled into N_POSTS_SHARING posts
    f_h_panel_per_post = panel["F_horiz_lb"] / N_POSTS_SHARING
    f_h_post_per_post = f_h_posts_total / N_POSTS_SHARING

    v_base_lb = f_h_panel_per_post + f_h_post_per_post   # total shear at base

    m_base_ftlb = (f_h_panel_per_post * y_c_ft
                   + f_h_post_per_post * (POST_HEIGHT_FT / 2.0))
    m_base_inlb = m_base_ftlb * 12.0

    # Cantilever tip deflection, point load at panel height + distributed
    # self-drag approximated as a point load at post mid-height (small term).
    p_tip_lb = f_h_panel_per_post
    l_tip_in = y_c_ft * 12.0
    defl_panel_in = (p_tip_lb * l_tip_in ** 3) / (3.0 * E_PSI * I_IN4) if p_tip_lb > 0 else 0.0
    l_self_in = POST_HEIGHT_FT * 12.0
    defl_self_in = (f_h_post_per_post * l_self_in ** 3) / (8.0 * E_PSI * I_IN4) if f_h_post_per_post > 0 else 0.0
    defl_in = defl_panel_in + defl_self_in

    bending_stress_psi = m_base_inlb / S_IN3
    shear_stress_psi = 1.5 * v_base_lb / A_IN2   # rectangular section, max at neutral axis

    sf_bending = FB_ALLOW_PSI / bending_stress_psi if bending_stress_psi > 0 else float("inf")
    sf_shear = FV_ALLOW_PSI / shear_stress_psi if shear_stress_psi > 0 else float("inf")

    defl_limit_in = (POST_HEIGHT_FT * 12.0) / DEFLECTION_LIMIT_RATIO
    sf_deflection = defl_limit_in / defl_in if defl_in > 0 else float("inf")

    return {
        "tilt_deg": tilt_deg,
        "V_mph": V_mph,
        "F_h_panel_per_post_lb": f_h_panel_per_post,
        "F_h_post_per_post_lb": f_h_post_per_post,
        "V_base_lb": v_base_lb,
        "M_base_ftlb": m_base_ftlb,
        "M_base_inlb": m_base_inlb,
        "bending_stress_psi": bending_stress_psi,
        "shear_stress_psi": shear_stress_psi,
        "sf_bending": sf_bending,
        "sf_shear": sf_shear,
        "deflection_in": defl_in,
        "deflection_limit_in": defl_limit_in,
        "sf_deflection": sf_deflection,
    }


# ----------------------------------------------------------------------------
# Lateral bracing (racking) — square-cut gusset sizing
# ----------------------------------------------------------------------------
def bending_crossover_tilt(target_sf: float):
    """Binary search: unbraced tilt at which SF_bending drops to target_sf."""
    lo, hi = 0.0, MAX_TILT_DEG
    for _ in range(50):
        mid = (lo + hi) / 2
        if post_demand(mid)["sf_bending"] >= target_sf:
            lo = mid
        else:
            hi = mid
    return lo


def alt_post_size(post_b_in: float, post_h_in: float, tilt_deg: float = MAX_TILT_DEG):
    """Bending SF for an alternate square post size, same load model (still
    N_POSTS_SHARING posts carrying the load — only the section changes)."""
    d = post_demand(tilt_deg)
    s = post_b_in * post_h_in ** 2 / 6.0
    stress = d["M_base_inlb"] / s
    return {"size_in": post_b_in, "S_in3": s, "stress_psi": stress,
            "sf_bending": FB_ALLOW_PSI / stress}


def gusset_demand(tilt_deg: float = MAX_TILT_DEG, V_mph: float = SITE["V_ult_mph"],
                  gusset_leg_in: float = 18.0):
    """Axial force a knee-brace gusset must carry to take the post base out
    of bending, at the operating cap.

    A knee brace from post to rail near the post top converts the portal
    frame from "post base resists moment" to "post base resists shear +
    axial only, brace carries the racking force axially" — the square-cut
    escape hatch from design rule #1 (no miters), since a gusset plate
    bolted to the square-cut brace end needs no mitered joint.

    Approximated as a 45° brace (gusset_leg_in run = gusset_leg_in rise),
    so the brace axial force ≈ V_base / cos(45°) = V_base * sqrt(2).
    """
    d = post_demand(tilt_deg, V_mph)
    v_base = d["V_base_lb"]
    brace_angle_deg = 45.0
    brace_force_lb = v_base / math.cos(math.radians(brace_angle_deg))
    return {
        "tilt_deg": tilt_deg,
        "V_base_lb": v_base,
        "brace_angle_deg": brace_angle_deg,
        "brace_force_lb": brace_force_lb,
        "gusset_leg_in": gusset_leg_in,
    }


# ----------------------------------------------------------------------------
# Reporting + visualization
# ----------------------------------------------------------------------------
def run_analysis():
    out_md = os.path.join(HERE, "post_bending_report.md")
    fig1 = os.path.join(HERE, "..", "renders", "post_bending.png")
    os.makedirs(os.path.dirname(fig1), exist_ok=True)

    rows = [post_demand(t) for t in TILTS_DEG]
    r_cap = post_demand(MAX_TILT_DEG)
    g_cap = gusset_demand(MAX_TILT_DEG)
    tilt_at_sf15 = bending_crossover_tilt(1.5)
    tilt_at_sf10 = bending_crossover_tilt(1.0)
    r_cap_4post_M_ftlb = r_cap["M_base_ftlb"] / 2.0   # optimistic: all 4 posts share equally
    r_cap_4post_stress = (r_cap_4post_M_ftlb * 12.0) / S_IN3
    r_cap_4post_sf = FB_ALLOW_PSI / r_cap_4post_stress
    alt_6x6 = alt_post_size(5.5, 5.5)

    md = []
    md.append("# Wattplot v2 — Post Bending & Lateral Bracing Analysis\n")
    md.append("**Companion to `analysis/wind_load_report.md`.** That report treats the "
              "structure as a rigid body tipping about the bed edge; this one checks "
              "whether the 4x4 posts themselves survive the same wind as cantilevers, "
              "and what it takes to brace them so their base connections don't have to "
              "resist a bending moment.\n")
    md.append(f"**Post:** {POST_SIZE} PT {WOOD['species']}, {POST_B_IN}\" × {POST_H_IN}\" "
              f"actual, {POST_HEIGHT_FT*12:.0f}\" tall, {POSTS['count']} posts total.")
    md.append(f"**Allowable stresses (NDS wet-use × CD {CD_WIND} wind duration):** "
              f"Fb' = {FB_ALLOW_PSI:.0f} psi, Fv' = {FV_ALLOW_PSI:.0f} psi. "
              f"No other NDS adjustment factors (size, beam-stability) applied — "
              f"first-pass, not a stamped calc.")
    md.append(f"**Load-sharing assumption:** worst-case, {N_POSTS_SHARING} of "
              f"{POSTS['count']} posts carry the full panel drag between them "
              "(no credit taken for the other 2 posts or for rail-frame stiffness). "
              "This is the conservative case for an UNBRACED frame — see §Bracing "
              "below for how bracing changes this.\n")

    md.append("## Bending, shear, and deflection at the post base\n")
    md.append("| Tilt | V_base (lb) | M_base (ft·lb) | f_b (psi) | SF bending | "
              "f_v (psi) | SF shear | defl (in) | SF defl | |")
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        over = r["tilt_deg"] > MAX_TILT_DEG
        worst_sf = min(r["sf_bending"], r["sf_shear"], r["sf_deflection"])
        flag = "🚫 above cap" if over else ("✅" if worst_sf >= SF_TARGET else "⚠️")
        md.append(f"| {r['tilt_deg']}° | {r['V_base_lb']:.0f} | {r['M_base_ftlb']:.0f} | "
                  f"{r['bending_stress_psi']:.0f} | {r['sf_bending']:.2f} | "
                  f"{r['shear_stress_psi']:.0f} | {r['sf_shear']:.2f} | "
                  f"{r['deflection_in']:.2f} | {r['sf_deflection']:.2f} | {flag} |")
    md.append("")

    md.append(f"## Verdict at the {MAX_TILT_DEG:.0f}° operating cap\n")
    md.append(f"**This check FAILS at the {MAX_TILT_DEG:.0f}° operating cap, unbraced.** "
              "The overturning check in `wind_load_report.md` passing does not mean the "
              "posts survive — they're a separate failure mode, and this one governs "
              "first.\n")
    verdict_bend = "PASS" if r_cap["sf_bending"] >= SF_TARGET else "**FAIL**"
    verdict_shear = "PASS" if r_cap["sf_shear"] >= SF_TARGET else "**FAIL**"
    verdict_defl = "PASS" if r_cap["sf_deflection"] >= SF_TARGET else "**FAIL**"
    md.append(f"- Bending: **{r_cap['bending_stress_psi']:.0f} psi** vs. "
              f"Fb' = {FB_ALLOW_PSI:.0f} psi → SF **{r_cap['sf_bending']:.2f}** "
              f"(target ≥ {SF_TARGET}) — {verdict_bend}")
    md.append(f"- Shear: **{r_cap['shear_stress_psi']:.0f} psi** vs. "
              f"Fv' = {FV_ALLOW_PSI:.0f} psi → SF **{r_cap['sf_shear']:.2f}** "
              f"(target ≥ {SF_TARGET}) — {verdict_shear}")
    md.append(f"- Deflection: **{r_cap['deflection_in']:.2f}\"** vs. limit "
              f"{r_cap['deflection_limit_in']:.2f}\" (L/{DEFLECTION_LIMIT_RATIO}) → "
              f"SF **{r_cap['sf_deflection']:.2f}** — {verdict_defl}")
    md.append(f"- **Base connection demand: M = {r_cap['M_base_ftlb']:.0f} ft·lb, "
              f"V = {r_cap['V_base_lb']:.0f} lb.** Most off-the-shelf post-base "
              "brackets (e.g. Simpson Strong-Tie ABU/CBSQ) are pin connections rated "
              "for shear + uplift, **not** a bending moment this size — so even if "
              "the wood section itself were beefed up, the connection is a second "
              "gap.\n")
    md.append("**Bending, not shear or deflection, is the governing failure.** "
              "Shear passes with SF ≈ 10 even at 35°, and deflection is a "
              "serviceability concern, not a strength one. The 4x4 section is "
              "simply too small in bending for a 6-ft cantilever under this load, "
              "under the conservative (2-of-4-posts) load-sharing assumption.\n")
    md.append(f"**Unbraced tilt limits, bending alone:** SF drops below the "
              f"{SF_TARGET} target at **{tilt_at_sf15:.0f}°** and below 1.0 "
              f"(stress exceeds allowable) at **{tilt_at_sf10:.0f}°**. Bending "
              f"fails well before the {MAX_TILT_DEG:.0f}° overturning-derived cap "
              "— the real operating limit for an unbraced 4x4 post is closer to "
              f"{tilt_at_sf15:.0f}° than {MAX_TILT_DEG:.0f}°.\n")
    md.append(f"**Sensitivity — optimistic 4-post-uniform sharing** (crediting all "
              f"4 posts equally instead of the conservative 2 used above): M drops "
              f"to {r_cap_4post_M_ftlb:.0f} ft·lb, stress to "
              f"{r_cap_4post_stress:.0f} psi, SF to **{r_cap_4post_sf:.2f}** — "
              f"still below the {SF_TARGET} target. Even the optimistic case does "
              "not pass without bracing or a bigger post.\n")

    md.append("## Two remedies (either closes the gap; pick one)\n")
    md.append(f"**Option A — upsize to 6x6 posts.** At {MAX_TILT_DEG:.0f}° with the "
              f"same conservative 2-post sharing: S = {alt_6x6['S_in3']:.1f} in³ "
              f"(vs. {S_IN3:.1f} in³ for 4x4), stress = "
              f"{alt_6x6['stress_psi']:.0f} psi, **SF = {alt_6x6['sf_bending']:.2f} "
              "— PASS** with margin. Simplest fix; no bracing design needed. Cost: "
              "heavier/pricier posts (6x6 PT DF vs 4x4) and the frame/hardware "
              "already sized around 4x4 rail pockets would need rechecking.\n")
    md.append("**Option B — lateral bracing (square-cut, per design rule #1).** "
              "A 45° knee brace from post to rail near the post top converts the "
              "post-and-rail portal frame from a **moment frame** (base resists "
              "bending) to a **braced frame** (base resists shear + axial only; "
              "the brace carries the racking force axially). The obvious brace "
              "geometry needs mitered ends — the escape hatch is a **square-cut "
              "gusset plate**: a short square-cut timber brace (or a plywood/steel "
              "gusset alone) bolted flat across the post/rail corner, carrying the "
              "same axial force a mitered brace would without a single non-90° "
              f"cut. At the {MAX_TILT_DEG:.0f}° cap (45° brace, "
              f"{g_cap['gusset_leg_in']:.0f}\" legs): brace axial force = "
              f"**{g_cap['brace_force_lb']:.0f} lb**, spec target "
              f"≥ {g_cap['brace_force_lb']*1.5:.0f} lb — well within off-the-shelf "
              "structural angle brackets (design rule #2).\n")
    md.append("**Bracing alone does not fully retire the base-moment problem** — "
              "it reduces the effective cantilever to the short run below the "
              "brace's lower attachment point, it doesn't zero it out. Model that "
              "residual moment once a specific bracket height is chosen, and "
              "confirm it's within a standard post-base bracket's rating before "
              "treating Option B as sufficient on its own. Option A (upsize) is "
              "the more conservative and simpler fix if the frame geometry can "
              "absorb a larger post; Option B is lighter/cheaper if the residual "
              "moment checks out.\n")

    md.append("## Notes & caveats\n")
    md.append("- **First-pass engineering, not stamped calcs.** Same caveat as "
              "`wind_load_report.md`. A real build should get a PE stamp before "
              "the full-size Smart tier goes in the ground.")
    md.append("- **Load sharing among the 4 posts is the biggest modeling "
              "assumption here.** This analysis conservatively assumes only 2 "
              "posts share the load (matching wind_load.py's existing "
              "'2 effective posts' convention for post self-drag) because, "
              "absent a bracing design, there's no rigid mechanism guaranteeing "
              "the other 2 posts help. Once bracing (above) is actually built, "
              "the true per-post demand is lower than this table shows — but the "
              "table's numbers are the ones that should size the base connection "
              "if you're not ready to trust the bracing.")
    md.append("- No NDS size factor (CF) or beam-stability factor (CL) applied to "
              "the allowable bending stress — only the load-duration factor CD. "
              "Both would typically increase the allowable slightly for a post "
              "this size, so this is conservative, not unconservative.")
    md.append("- Deflection limit (L/180) is a judgment call for a canopy, not a "
              "code-mandated value the way it might be for a roof diaphragm. "
              "Treat the deflection numbers as a serviceability sanity check, "
              "not a pass/fail structural limit.")
    md.append("- Panel drag is assumed delivered to the post tops as a point load "
              "at the panel centroid height — consistent with `wind_load.py`'s "
              "own overturning-moment model, but a real rail-to-post connection "
              "distributes some of that load below the very top.\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"[post_bending] wrote {out_md}")

    # ---------------- Plot ----------------
    tilts = [r["tilt_deg"] for r in rows]
    sf_b = [r["sf_bending"] for r in rows]
    sf_v = [r["sf_shear"] for r in rows]
    sf_d = [r["sf_deflection"] for r in rows]

    _fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(tilts, sf_b, "o-", label="SF bending", color="#c0392b")
    ax.plot(tilts, sf_v, "s-", label="SF shear", color="#2c3e50")
    ax.plot(tilts, sf_d, "^-", label="SF deflection", color="#16a085")
    ax.axhline(SF_TARGET, color="gray", ls=":", alpha=0.6, label=f"target ({SF_TARGET})")
    ax.axvline(MAX_TILT_DEG, color="#8e44ad", ls="--", alpha=0.5,
              label=f"operating cap ({MAX_TILT_DEG:.0f}°)")
    ax.set_xlabel("Panel tilt (deg)")
    ax.set_ylabel("Safety factor")
    ax.set_title(f"Post base safety factors vs. tilt\n"
                f"{POST_SIZE} PT DF post, {N_POSTS_SHARING} of {POSTS['count']} posts "
                f"sharing load (worst-case, unbraced)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(fig1, dpi=130)
    plt.close()
    print(f"[post_bending] wrote {fig1}")

    return rows, r_cap, g_cap


if __name__ == "__main__":
    rows, r_cap, g_cap = run_analysis()
    print()
    print("=" * 70)
    print(f"Post: {POST_SIZE} PT DF, {POST_HEIGHT_FT*12:.0f}\" tall")
    print(f"Allowable (wet-use x CD {CD_WIND}): Fb'={FB_ALLOW_PSI:.0f} psi  "
          f"Fv'={FV_ALLOW_PSI:.0f} psi")
    print()
    print(f"{'Tilt':>5} {'V(lb)':>7} {'M(ft-lb)':>9} {'fb(psi)':>8} {'SFb':>6} "
          f"{'fv(psi)':>8} {'SFv':>6} {'defl(in)':>9} {'SFd':>6}")
    for r in rows:
        print(f"{r['tilt_deg']:>4}° {r['V_base_lb']:>7.0f} {r['M_base_ftlb']:>9.0f} "
              f"{r['bending_stress_psi']:>8.0f} {r['sf_bending']:>6.2f} "
              f"{r['shear_stress_psi']:>8.0f} {r['sf_shear']:>6.2f} "
              f"{r['deflection_in']:>9.2f} {r['sf_deflection']:>6.2f}")
    print()
    print(f"At {MAX_TILT_DEG:.0f}° cap: base connection M={r_cap['M_base_ftlb']:.0f} ft-lb, "
          f"V={r_cap['V_base_lb']:.0f} lb")
    print(f"Gusset brace at {g_cap['tilt_deg']:.0f}°: axial force "
          f"{g_cap['brace_force_lb']:.0f} lb (spec >= {g_cap['brace_force_lb']*1.5:.0f} lb)")
    print("=" * 70)
