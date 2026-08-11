# Wattplot v2 — Post Bending & Lateral Bracing Analysis

**Companion to `analysis/wind_load_report.md`.** That report treats the structure as a rigid body tipping about the bed edge; this one checks whether the 4x4 posts themselves survive the same wind as cantilevers, and what it takes to brace them so their base connections don't have to resist a bending moment.

**Post:** 4x4 PT Douglas Fir (Pressure Treated), 3.5" × 3.5" actual, 72" tall, 4 posts total.
**Allowable stresses (NDS wet-use × CD 1.6 wind duration):** Fb' = 1400 psi, Fv' = 288 psi. No other NDS adjustment factors (size, beam-stability) applied — first-pass, not a stamped calc.
**Load-sharing assumption:** worst-case, 2 of 4 posts carry the full panel drag between them (no credit taken for the other 2 posts or for rail-frame stiffness). This is the conservative case for an UNBRACED frame — see §Bracing below for how bracing changes this.

## Bending, shear, and deflection at the post base

| Tilt | V_base (lb) | M_base (ft·lb) | f_b (psi) | SF bending | f_v (psi) | SF shear | defl (in) | SF defl | |
|---|---|---|---|---|---|---|---|---|---|
| 0° | 56 | 167 | 280 | 4.99 | 7 | 42.27 | 0.15 | 2.70 | ✅ |
| 15° | 93 | 393 | 660 | 2.12 | 11 | 25.41 | 0.43 | 0.94 | ⚠️ |
| 25° | 154 | 770 | 1293 | 1.08 | 19 | 15.26 | 0.89 | 0.45 | ⚠️ |
| 35° | 237 | 1278 | 2145 | 0.65 | 29 | 9.93 | 1.52 | 0.26 | ⚠️ |
| 45° | 331 | 1855 | 3115 | 0.45 | 41 | 7.10 | 2.23 | 0.18 | 🚫 above cap |
| 50° | 379 | 2148 | 3607 | 0.39 | 46 | 6.20 | 2.59 | 0.15 | 🚫 above cap |
| 75° | 570 | 3317 | 5570 | 0.25 | 70 | 4.13 | 4.04 | 0.10 | 🚫 above cap |
| 90° | 607 | 3543 | 5949 | 0.24 | 74 | 3.88 | 4.32 | 0.09 | 🚫 above cap |

## Verdict at the 35° operating cap

**This check FAILS at the 35° operating cap, unbraced.** The overturning check in `wind_load_report.md` passing does not mean the posts survive — they're a separate failure mode, and this one governs first.

- Bending: **2145 psi** vs. Fb' = 1400 psi → SF **0.65** (target ≥ 1.5) — **FAIL**
- Shear: **29 psi** vs. Fv' = 288 psi → SF **9.93** (target ≥ 1.5) — PASS
- Deflection: **1.52"** vs. limit 0.40" (L/180) → SF **0.26** — **FAIL**
- **Base connection demand: M = 1278 ft·lb, V = 237 lb.** Most off-the-shelf post-base brackets (e.g. Simpson Strong-Tie ABU/CBSQ) are pin connections rated for shear + uplift, **not** a bending moment this size — so even if the wood section itself were beefed up, the connection is a second gap.

**Bending, not shear or deflection, is the governing failure.** Shear passes with SF ≈ 10 even at 35°, and deflection is a serviceability concern, not a strength one. The 4x4 section is simply too small in bending for a 6-ft cantilever under this load, under the conservative (2-of-4-posts) load-sharing assumption.

**Unbraced tilt limits, bending alone:** SF drops below the 1.5 target at **20°** and below 1.0 (stress exceeds allowable) at **26°**. Bending fails well before the 35° overturning-derived cap — the real operating limit for an unbraced 4x4 post is closer to 20° than 35°.

**Sensitivity — optimistic 4-post-uniform sharing** (crediting all 4 posts equally instead of the conservative 2 used above): M drops to 639 ft·lb, stress to 1073 psi, SF to **1.31** — still below the 1.5 target. Even the optimistic case does not pass without bracing or a bigger post.

## Two remedies (either closes the gap; pick one)

**Option A — upsize to 6x6 posts.** At 35° with the same conservative 2-post sharing: S = 27.7 in³ (vs. 7.1 in³ for 4x4), stress = 553 psi, **SF = 2.53 — PASS** with margin. Simplest fix; no bracing design needed. Cost: heavier/pricier posts (6x6 PT DF vs 4x4) and the frame/hardware already sized around 4x4 rail pockets would need rechecking.

**Option B — lateral bracing (square-cut, per design rule #1).** A 45° knee brace from post to rail near the post top converts the post-and-rail portal frame from a **moment frame** (base resists bending) to a **braced frame** (base resists shear + axial only; the brace carries the racking force axially). The obvious brace geometry needs mitered ends — the escape hatch is a **square-cut gusset plate**: a short square-cut timber brace (or a plywood/steel gusset alone) bolted flat across the post/rail corner, carrying the same axial force a mitered brace would without a single non-90° cut. At the 35° cap (45° brace, 18" legs): brace axial force = **335 lb**, spec target ≥ 503 lb — well within off-the-shelf structural angle brackets (design rule #2).

**Bracing alone does not fully retire the base-moment problem** — it reduces the effective cantilever to the short run below the brace's lower attachment point, it doesn't zero it out. Model that residual moment once a specific bracket height is chosen, and confirm it's within a standard post-base bracket's rating before treating Option B as sufficient on its own. Option A (upsize) is the more conservative and simpler fix if the frame geometry can absorb a larger post; Option B is lighter/cheaper if the residual moment checks out.

## Notes & caveats

- **First-pass engineering, not stamped calcs.** Same caveat as `wind_load_report.md`. A real build should get a PE stamp before the full-size Smart tier goes in the ground.
- **Load sharing among the 4 posts is the biggest modeling assumption here.** This analysis conservatively assumes only 2 posts share the load (matching wind_load.py's existing '2 effective posts' convention for post self-drag) because, absent a bracing design, there's no rigid mechanism guaranteeing the other 2 posts help. Once bracing (above) is actually built, the true per-post demand is lower than this table shows — but the table's numbers are the ones that should size the base connection if you're not ready to trust the bracing.
- No NDS size factor (CF) or beam-stability factor (CL) applied to the allowable bending stress — only the load-duration factor CD. Both would typically increase the allowable slightly for a post this size, so this is conservative, not unconservative.
- Deflection limit (L/180) is a judgment call for a canopy, not a code-mandated value the way it might be for a roof diaphragm. Treat the deflection numbers as a serviceability sanity check, not a pass/fail structural limit.
- Panel drag is assumed delivered to the post tops as a point load at the panel centroid height — consistent with `wind_load.py`'s own overturning-moment model, but a real rail-to-post connection distributes some of that load below the very top.
