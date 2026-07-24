# Wattplot v2 — Wind Load Analysis

**Site:** Phoenix, AZ (Maricopa County)  
**Standard:** ASCE 7-22, Risk Cat II, 700-yr MRI  
**Basic wind speed V:** 115.0 mph 3-sec gust (51.4 m/s) at 33 ft, Exposure C  
**Exposure:** C (Kzt = 1.0, Kd = 0.85)  
**Force coefficient Cf:** 1.5 (open tilted plate, conservative)

## Geometry

- Panel: 8.083333333333334 ft × 3.716666666666667 ft × 1.4" (30.04 sq ft, ~65.0 lb)
- Bed: 8.0 ft × 3.716666666666667 ft × 22.0" wall
- Wood density assumed: 30.0 pcf (PT pine, conservative)
- Soil density assumed: 75.0 pcf (wet loam/compost, ×1.0 saturation)
- Bed-on-grade friction: μ = 0.4

## Dead load (ballast) at 20.0" soil depth

| Component | Weight |
|---|---|
| Soil (47.14 cu ft) | 3536 lb |
| Lumber (posts + beam + walls) | 251 lb |
| Panel | 65 lb |
| Hardware (hinges/bolts) | 25 lb |
| **Total dead load W** | **3876 lb** |

## Force sweep across tilt angles

| Tilt | qh (psf) | F_vert (uplift, lb) | F_horiz (drag, lb) | SF uplift | SF sliding | SF overturning |
|---|---|---|---|---|---|---|
| 0° | 24.5 | 0 | 0 | inf | inf | inf |
| 15° | 24.5 | 276 | 74 | 14.07 | 21.00 | 44.74 |
| 25° | 24.5 | 422 | 197 | 9.18 | 7.88 | 10.01 |
| 35° | 24.5 | 518 | 363 | 7.48 | 4.28 | 4.20 |
| 45° | 24.5 | 551 | 551 | 7.03 | 2.81 | 2.35 |
| 50° | 24.5 | 543 | 647 | 7.14 | 2.40 | 1.90 |
| 75° | 24.5 | 276 | 1028 | 14.07 | 1.51 | 1.09 |
| 90° | 24.5 | 0 | 1102 | 57427862164769408.00 | 1.41 | 1.11 |

## Verdict at default 20.0" soil depth

At the v1 design tilt of 35° (and V = 115.0 mph):

- Uplift safety factor: **7.48** (target ≥ 1.5) — PASS
- Sliding safety factor: **4.28** (target ≥ 1.5) — PASS
- Overturning safety factor: **4.20** (target ≥ 2.0) — PASS

## Recommended soil depth

Worst-case uplift tilt is **45°** (sin(2θ) is maximum at 45°).
To hit the overturning target SF ≥ 2.0 at 45° tilt and V = 115.0 mph, you need approximately:

### **Soil depth ≥ 16.7"** (1.39 ft)

At that depth:

- Total dead load: 3292 lb
- SF uplift: 5.97, SF sliding: 2.39, SF overturning: 2.00

## Notes & caveats

- **First-pass engineering, not stamped calcs.** If this is a real build in Phoenix city limits, the structure may need a permit and a PE stamp. Maricopa County wind amendments and IRC triggers are real.
- Cf = 1.5 is conservative for an open plate. ASCE 7 doesn't have a dedicated section for a one-panel solar canopy, so we used a free-plate value. A real calc could refine with wind-tunnel data or a CFD check.
- Soil weight is the swing variable. Wet/wet+saturated soil can be 30-50% heavier than dry. We used a wet-loam value (75.0 pcf).
- Friction coefficient μ = 0.4 is a conservative estimate for PT pine on dirt. Wet/muddy ground could be 0.2-0.3; on a gravel pad or concrete, could be 0.5-0.6.
- The big lever here is **soil depth**. Every extra inch of soil is ~190 lb of ballast. If you want a margin, go deeper rather than wider.
