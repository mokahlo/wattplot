# ADR-001: 35° operating-tilt cap

**Status:** Accepted (v3.0, 2026-08-05; reaffirmed in `analysis/wind_load_report.md`)
**Deciders:** mokah (project owner)
**Consulted:** ASCE 7-22 wind calc, NDS post bending, FreeCAD 3D model

## Context

The wattplot tilts a 620 W panel on 72" corner posts. The tilt
schedule decides both annual kWh (sun simulator) and the worst-case
wind moment on the structure (wind load analysis). Three regimes:

- **0° (flat, stowed):** minimal wind drag. SF overturning ~26.8.
- **35° (power position):** annual kWh peaks near 35° in Phoenix
  (sun simulator).
- **45° – 90°:** no kWh gain, much more drag. The wind calc shows
  SF overturning drops below 2.0 at ≥ 45° tilt.

## Decision

**35° is the structural cap.** Hard-enforced in firmware as
`commanded_tilt.max_value: 35` (see `firmware/wattplot.yaml` line 1053).
No 90° "bed sun" or "wring out" modes. To dry the bed, stow flat at 0°
instead.

## Rationale

1. **Sun simulator:** static 35° = 1539 kWh/yr; seasonal 90/35° =
   1411 kWh/yr; azimuth tracking 35° = 2240 kWh/yr. Going past 35°
   adds zero kWh (the panel is past the sun's average annual
   elevation) and costs wind margin.
2. **Wind load (ASCE 7-22, Phoenix Cat II, 700-yr, Exp C):**
   - 35°: SF 2.55 — passes target SF 2.0 with margin.
   - 45°: SF 1.89 — fails.
   - 50°: SF 1.69 — fails worse.
   - 90°: SF 1.26 — fails worst.
3. **Post bending (`analysis/post_bending.py`):** even with the
   bed-sized soil ballast (60 cu ft, 4,500 lb), the 4×4 posts fail
   at 35° unbraced (SF 0.65 vs target 1.5). Higher tilt = larger
   lever arm = worse. The 35° cap keeps the bending moment bounded;
   6×6 posts or lateral bracing are required to actually reach 35°
   safely.

## Consequences

- **BedSun mode retired in v3.1.** Removed `controller_mode`
  option; `select.controller_mode` is now `Power` only.
- **Firmware clamps commanded tilt to [0, 35°].** `controller_state`
  options are unchanged (`Normal` / `Monitoring` / `Folding` /
  `Locked`) but the PI loop cannot command > 35° from any state.
- **Documentation refresh.** README §"Design", `analysis/wind_load.py`
  caveat, `analysis/post_bending_report.md`, `docs/control_law.md`
  all updated. `docs/control_law.md` §"Goal (verbatim)" is
  aspirational; deployed behavior is in `firmware/README.md`.
- **Calibration threshold.** `endstop_current_threshold` default
  0.90 A is calibrated against the IPROPI spike when the panel
  hits the physical strut at the top of its travel. With no 90°
  travel, calibration should stay at 35° max — `commanded_tilt.max_value`
  enforces this for normal operation, but the `Calibrate Actuator`
  button can briefly command 35° during discovery.

## When to revisit

- If a PE review validates a 6×6-post design with lateral bracing,
  the cap can rise to ~45° (where wind SF is 1.89 — still fails
  without an additional structural margin).
- If the bed depth grows (more soil ballast), the wind SF improves
  slightly at every tilt but the cap is governed by the post
  bending, not the bed.
- If we move to a wind-shielded site (not Exp C), the cap can rise.

## Alternatives considered

- **90° cap (the v1 / v2.4 design):** rejected. The wind calc at
  design wind gives SF 1.26, which is below every reasonable
  target. The "bed sun" / "wring out" use cases can be served by
  stowing flat (the panel casts no shadow, the bed dries).
- **No cap (open up to 90°):** rejected. Would require either
  much heavier posts + bracing or a much heavier bed.
- **60° cap:** considered. SF at 60° not explicitly computed in the
  wind table (the table is at 0/15/25/35/45/50/75/90°), so
  interpolation suggests SF ~1.5 at 60° — still below target.