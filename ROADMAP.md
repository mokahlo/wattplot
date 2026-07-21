# Wattplot v2 — Roadmap

This is the working list of milestones, in order. Each has a corresponding
GitHub issue for tracking. Edit this file as priorities shift.

## Phase 1 — Validate the design (current)

- [x] Parametric 3D model with STEP / STL / 3MF / VRML export
- [x] ASCE 7-22 wind load analysis (Phoenix, Exp C, Cat II 700-yr)
- [x] Geometric shadow raycaster using actual 3D panel geometry
- [x] Annual sun simulator with 5 tilt schedules + tomato yield model
- [x] Engineering side-view drawings
- [x] PCB block diagram
- [x] Single source of truth (wattplot_params.py)
- [x] Public repo on GitHub
- [x] CI: pipeline runs on every PR (smoke tests + sim + wind + raycaster)
- [x] GitHub Pages: interactive 3D viewer

## Phase 2 — Prototype the controller

- [ ] ESP32 dev-board prototype: PI loop on motor current
- [ ] Wire up: ESP32 + H-bridge + actuator + INA219 + DS18B20 + soil sensor
- [ ] Bench test: actuator moves, current reads accurately, fold triggers correctly
- [ ] Simulated-wind test mode in firmware (verify algorithm with a box fan)
- [ ] First outdoor deployment, manual control, 1 week
- [ ] Enable auto-fold, watch for false triggers, 2-4 weeks
- [ ] Calibrate setpoint current and deadband from real-world data

## Phase 3 — Custom PCB

- [ ] Finalize schematic (SKiDL → netlist → KiCad layout)
- [ ] Order 5 prototype boards from JLCPCB (~$100)
- [ ] SMT assembly, hand-solder any through-hole parts
- [ ] Port firmware from breadboard to PCB
- [ ] Validate in same outdoor test as Phase 2

## Phase 4 — Sun + soil optimization in firmware

- [ ] Implement the full decision stack (NWS, soil, rain, wind, user)
- [ ] Add the "DLI top-up" mode for grow lights
- [ ] Add panel-mist evaporative cooling trigger (panel temp > 50°C)
- [ ] Validate the controller against a year of replayed Phoenix weather

## Phase 5 — First physical build

- [ ] Source lumber (cedar or PT pine), hardware, panel
- [ ] Build the bed (8 ft × 3.7 ft × 12" deep, 2×6 stacked walls)
- [ ] Install hinges, posts, beam, actuator
- [ ] Mount panel, run wiring
- [ ] Fill with soil, plant tomatoes
- [ ] Document the build (photos, time, cost, gotchas)

## Phase 6 — Documentation + community

- [ ] Build photos in README
- [ ] Bill of materials v2 (post-pivot: single 620W panel, hinged, ballasted)
- [ ] Assembly guide with photos
- [ ] Calibration guide for the smart controller
- [ ] "I built one" — collect feedback from early builders
- [ ] YouTube build video? (optional)

## Phase 7 — Product path (if it goes there)

- [ ] Validate the design against multiple US states' plug-and-play solar laws
- [ ] Decide grid-tie (microinverter) vs off-grid (battery + inverter)
- [ ] Cost-down pass on the BOM
- [ ] Cert-friendly electrical design (if going commercial)
- [ ] Field-test 3-5 units in different climates

---

_This is a living document. Update as the project evolves._
