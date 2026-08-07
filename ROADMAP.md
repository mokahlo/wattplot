# Wattplot — Status & roadmap

> Source of truth for project status is the README's **Status & roadmap**
> table (kept in sync with this file). This file tracks **what's still on
> the queue**, not what's been done.

## Status snapshot

Mirror of the README table — keep these in sync.

| Layer | State | Notes |
|---|---|---|
| 3D model | Validated | FreeCAD assembly, STEP+STL+FCStd export. 5 panel presets. |
| Sun simulation | Validated | `analysis/sun_simulator.py` — annual kWh, daily DLI, tomato yield. |
| Wind load | Validated | ASCE 7-22, Cat II 700-yr, Exp C, Phoenix. |
| Cut lists | Validated | `models/cut_list.py` — every board, every cut. |
| Post-bending check | Validated (caveat) | `analysis/post_bending.py` — 4×4 unbraced fails at 35°; 6×6 or gussets are the fix. |
| Mini v2.4 (electronics) | Built & running on bench | 18×14″, 10 W panel, kickstand actuator, ESPHome firmware. |
| Full-size structural (Basic) | Designed | 8×5 ft bed, no electronics. Weekend build. |
| Full-size Smart (electronics) | Firmware ready, chip wedged | Schematic rev B + firmware v3.2 compiled; needs physical BOOT+RESET. |
| Custom PCB | Designed | Schematic + PCB layout. JLCPCB-ready. |
| GitHub Pages site | Live | Dark theme, 10+ pages, 3D viewer, data dashboard, gallery, diagrams. |
| Booth materials | Mid-refresh | One-pager + FAQ + poster + sim ready; needs new symbiosis framing. |
| Trademark (WattPlot name) | Coexistence request drafted | `docs/_internal/COEXISTENCE_REQUEST.md`. Awaiting Andrew Welch's reply. |

## Open structural questions

Two checks are still on the queue, called out explicitly in the README.
**Do not build the full-size Smart tier at 35° tilt with 4×4 unbraced
posts** until one of the remedies is locked in:

1. **Post bending.** `analysis/post_bending.py` shows 4×4 unbraced posts
   fail at 35° (SF 0.65 vs target 1.5, worst case). Remedies: upsize to
   6×6 (SF 2.53), or add lateral bracing and confirm the base moment.
2. **Lateral bracing.** Conventional knee brace needs miters, which
   collides with the no-miter design rule. Square-cut gusset plates
   are the answer; sized in `analysis/post_bending.py` §Bracing.

Both items are first-pass calcs, not stamped — get a PE review before
anything goes in the ground.

## Next up (priority order)

- [ ] **Recover the wedged ESP32-S3** and flash firmware v3.2 to the
  Mini v2.4 board. Procedure: `docs/_internal/esp32-s3.md` §8.
  (Owns: the chip. Blocker for: bench-side power / tilt validation.)
- [ ] **Apply the Cloudflare Access policy** on the `/api/*` control
  paths (see `docs/_internal/remote-access.md` §8). Until that's done,
  the control panel is effectively public.
- [ ] **Stamp the build guides.** `docs/build_guide.md`,
  `docs/wiring.md`, `docs/pcb_design.md`, `docs/sensor_placement.md`,
  `docs/watering.md`, `docs/test_checklist.md`, `docs/control_law.md`
  are flagged stale (v1/v2.4 architecture) — stamp them as design
  intent and cross-reference `firmware/wattplot.yaml` and
  `docs/pinmap.html` for the current truth. (Pending: a future pass
  to fully regenerate.)
- [ ] **Resolve the post-bending + bracing.** Pick 6×6 vs gussets and
  update `analysis/wind_load.py` (which currently assumes 4×4
  unbraced).
- [ ] **Order a JLCPCB prototype run** of the rev B PCB so the Mini
  moves off breadboard.
- [ ] **Trademark follow-up.** If Andrew Welch doesn't reply within
  2–3 weeks, follow up once, then decide whether to execute
  `docs/_internal/RENAME_PLAN.md`.

## Completed (historical)

Captured so the chronology isn't lost — but this list is not the
status source (that's the table above).

- [x] Parametric 3D model with STEP / STL / FCStd export, one file
      per part (`models/freecad/parts/`)
- [x] All-wood perimeter frame design (2×6 rails + 2×4 brace,
      half-lap bed corners)
- [x] ASCE 7-22 wind load analysis (Phoenix, Exp C, Cat II 700-yr)
- [x] Geometric shadow raycaster (uses actual 3D panel)
- [x] Annual sun + yield simulator (5 tilt schedules, Phoenix weather)
- [x] Engineering side-view drawings (frame + actuator + hinge detail)
- [x] PCB block diagram (`docs/pcb_design.md` block diagram, plus
      `docs/schematic.html` rev B)
- [x] Wiring diagram (pin-by-pin) — `docs/wiring.md` (stale; see Next up)
- [x] Sensor placement plan — `docs/sensor_placement.md` (stale; see Next up)
- [x] Build guide (8 phases, ~10–15 hr) — `docs/build_guide.md`
      (stale; see Next up)
- [x] Test & validation checklist — `docs/test_checklist.md` (stale)
- [x] ESPHome firmware v3.2 (PI controller, NWS polling, fold logic,
      IPROPI endstops, dual DRV8871 for actuator + solenoid)
- [x] GitHub Pages site (dark theme, 3D viewer, data dashboard,
      gallery, diagrams, live control link)
- [x] Coexistence request drafted (`docs/_internal/COEXISTENCE_REQUEST.md`)

---

_Living document. The status table at the top mirrors the README; the
priority list below is the queue. Edit as priorities shift._