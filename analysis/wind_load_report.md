# Wattplot v2 — Wind Load Analysis

**Site:** Phoenix, AZ (Maricopa County)  
**Standard:** ASCE 7-22, Risk Cat II, 700-yr MRI  
**Basic wind speed V:** 115.0 mph 3-sec gust (51.4 m/s) at 33 ft, Exposure C  
**Exposure:** C (Kzt = 1.0, Kd = 0.85)  
**Force coefficient Cf:** 1.5 (open tilted plate, conservative)

## Geometry

- **Canopy on 72" corner posts** — panel centroid at 6.1 ft above grade. This long lever arm, not uplift, is what governs the design.
- **Operating tilt capped at 35°** (`CONTROL['max_tilt_deg']`). Rows above it below are shown to document why the cap exists — they are NOT operating states.
- Panel: 8.083333333333334 ft × 3.716666666666667 ft × 1.4" (30.04 sq ft, ~65.0 lb); tilts about its long axis, so the 3.72 ft width rises
- Bed: 8.0 ft × 3.716666666666667 ft × 27.5" wall, 25.5" soil fill
- Corner-post drag included: 2 effective posts × Cf 1.3 acting at 3.0 ft
- Wood density assumed: 30.0 pcf (PT pine, conservative)
- Soil density assumed: 75.0 pcf (wet loam/compost, ×1.0 saturation)
- Bed-on-grade friction: μ = 0.4

## Dead load (ballast) at 25.5" soil depth

| Component | Weight |
|---|---|
| Soil (60.10 cu ft) | 4508 lb |
| Lumber (posts + beam + walls) | 222 lb |
| Panel | 65 lb |
| Hardware (hinges/bolts) | 25 lb |
| **Total dead load W** | **4820 lb** |

## Force sweep across tilt angles

| Tilt | qh (psf) | F_vert (uplift, lb) | F_horiz (drag, lb) | SF uplift | SF sliding | SF overturning | |
|---|---|---|---|---|---|---|---|
| 0° | 24.5 | 0 | 111 | n/a | 17.32 | 26.83 | ✅ |
| 15° | 24.5 | 276 | 185 | 17.49 | 10.41 | 6.90 | ✅ |
| 25° | 24.5 | 422 | 308 | 11.42 | 6.26 | 3.85 | ✅ |
| 35° | 24.5 | 518 | 474 | 9.31 | 4.07 | 2.55 | ✅ |
| 45° | 24.5 | 551 | 662 | 8.75 | 2.91 | 1.89 | 🚫 above cap |
| 50° | 24.5 | 543 | 758 | 8.88 | 2.54 | 1.69 | 🚫 above cap |
| 75° | 24.5 | 276 | 1140 | 17.49 | 1.69 | 1.25 | 🚫 above cap |
| 90° | 24.5 | 0 | 1214 | n/a | 1.59 | 1.26 | 🚫 above cap |

Drag column includes corner-post drag (111 lb, constant with tilt).

## Verdict at the 35° operating cap (25.5" soil depth)

At the max operating tilt of 35° (and V = 115.0 mph):

- Uplift safety factor: **9.31** (target ≥ 1.5) — PASS
- Sliding safety factor: **4.07** (target ≥ 1.5) — PASS
- Overturning safety factor: **2.55** (target ≥ 2.0) — PASS

**Rated deployed wind speed at 35°: ~130 mph** (the speed at which the governing safety factor reaches its target).

Stowed flat (0°) the panel contributes no drag or uplift and only the posts are loaded — SF overturning 26.8. **Stowing is the storm answer for both tiers.**

## Recommended soil depth

Required soil depth is solved at the 35° operating cap (above the cap is not an operating state).
To hit the overturning target SF ≥ 2.0 at 35° tilt and V = 115.0 mph, you need approximately:

### **Soil depth ≥ 19.6"** (1.64 ft)

The build ships 25.5" (27.5" wall = 5 courses of 1x6, 2" freeboard). At the required depth:

- Total dead load: 3786 lb
- SF uplift: 7.31, SF sliding: 3.20, SF overturning: 2.00

## Notes & caveats

- **First-pass engineering, not stamped calcs.** If this is a real build in Phoenix city limits, the structure may need a permit and a PE stamp. Maricopa County wind amendments and IRC triggers are real.
- Cf = 1.5 is conservative for an open plate. ASCE 7 doesn't have a dedicated section for a one-panel solar canopy, so we used a free-plate value. A real calc could refine with wind-tunnel data or a CFD check.
- **Soil weight is the swing variable, and it cuts against us.** We assume 75.0 pcf (wet loam). Dry desert soil can be 55-65 pcf, which drops SF overturning at 35° to ~1.9-2.2. This is exactly why the bed is 27.5" (5 courses) and not 4 courses — at 4 courses a dry bed falls to SF 1.53, below target. Keep the bed watered, or treat a bone-dry bed as a reason to stow.
- Friction coefficient μ = 0.4 is a conservative estimate for PT pine on dirt. Wet/muddy ground could be 0.2-0.3; on a gravel pad or concrete, could be 0.5-0.6.
- **Post drag is modeled crudely.** 2 of 4 posts at Cf 1.3, assuming the leeward pair is fully shielded. ASCE 7-22 Ch. 29 open-frame provisions would be the rigorous route.
- **The posts themselves are checked separately, in `analysis/post_bending.py` / `post_bending_report.md`.** This analysis treats the structure as a rigid body tipping about the bed edge; it does not model the 4x4 posts as cantilevers carrying panel drag at their base connection. That check exists now — and it **fails** the 4x4 posts, unbraced, at the 35° operating cap. See the companion report for the two remedies (upsize to 6x6, or square-cut lateral bracing).
- The big lever here is **soil depth**. Every extra inch of soil is ~190 lbof ballast. If you want a margin, go deeper rather than wider.
