---
name: Hardware
about: PCB, wiring, BOM, panel choices, or physical build issue
title: "[hw] "
labels: hardware
---

**Component**

- [ ] Schematic (rev B, 2026-08-03)
- [ ] PCB (JLCPCB layout)
- [ ] Wiring (ESP32 → sensors / DRV8871 / INA219 / DS18B20 / IPROPI)
- [ ] BOM (specific part)
- [ ] Panel preset (new panel to add to wattplot_params.PANEL_PRESETS)
- [ ] Mechanical (bed, posts, hinges, actuator mount, panel clamps)

**What's the issue?**

Clear and concise description.

**What I expected**

What the design should do (cite the docs section if possible).

**What actually happens**

Photos, measurements, multimeter readings, oscilloscope traces welcome.

**Datasheets / part numbers**

If this is a new part: link to the datasheet + vendor page. The
schematic rev B board has these headers:
- Pin map: `docs/pinmap.html`
- Schematic: `docs/schematic.html`
- Wiring: `docs/wiring.md` (note: stale, written for v1/v2.4 — pin
  numbers below may be wrong; cross-check against `firmware/wattplot.yaml`)

**Have you run a PE review?**

Wattplot's full-size Smart tier is **first-pass calcs, not stamped**.
The README and ROADMAP both call this out. PE review is required
before any full-size build goes in the ground.

- [ ] Yes — please attach
- [ ] No — still in design phase
- [ ] N/A — bench / mini only