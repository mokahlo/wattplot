# Wattplot v2

A DIY, open-source planter (up to 8 ft × 5 ft) with a tilting solar canopy
on top. Grow tomatoes underneath; make power above. A parametric,
code-first design: 3D model, sun simulation, wind-load analysis, cut
lists, and firmware all generated from one params file.

> **Status:** pre-prototype. The mechanical / structural / aerodynamic design is validated by 3D model + ASCE 7-22 wind calc + geometric shadow raycaster. The smart controller (ESP32-based) and custom PCB are next steps.

## Two builds, one frame

Same bed, same frame, same hinges and clamps — pick your tilt mechanism:

| | **Basic** | **Smart** |
|---|---|---|
| Tilt | Fixed, pinned prop strut (0/15/25/35/45°) | Motorized, 0–45°, linear actuator |
| Electronics | None | ESP32 controller + sensors + PCB |
| Storm response | Manual stow: pull pin, lay flat (2 min) | Auto-fold on wind, plus manual stow |
| Panel | Salvaged/upcycled panel ideal | New 620 W bifacial (or any preset) |
| Cost | **~$250–450** (salvage panel) | ~$1,400 |
| Time | A weekend | 10–15 hr + electronics |
| Guide | [`docs/build_basic.md`](docs/build_basic.md) | [`docs/build_guide.md`](docs/build_guide.md) |

**Start with Basic.** It's the whole idea in its cheapest form: a raised
bed that shades its crop and pays you back in watts, built with a drill
and a saw. Smart is the flagship upgrade — every Basic build has the
strut holes and hinge line to accept the actuator later.

## Design rules (enforced)

Three constraints guide every part of the design:

1. **No miter cuts.** Every cut is a 90° square cut. Joints are butt, half-lap, or
   lap. The diagonal brace has square ends that butt into the long rails - no
   angled cuts at the corners. (You don't need a miter saw.)
2. **All hardware off the shelf.** Hinges, panel clamps, bolts, screws, rod, and
   pins are standard sizes from Home Depot, McMaster, or solar-mounting
   suppliers (IronRidge / Unirac / Quick Mount). No custom metal parts.
3. **Simple, common dimensions.** All lumber from standard stock lengths (8 ft,
   10 ft, 12 ft) with reasonable waste (≤ 18" per board). No fractional-inch
   stock lengths. The frame: 96" long rails (2x6x8ft, no waste), 42" cross
   rails (cut from 2x6x8ft, 6" waste), 102" diagonal brace (from 2x4x10ft,
   18" waste).

## Interactive 3D model

[**Open the 3D viewer**](https://mokahlo.github.io/wattplot/) - drag to orbit, scroll to zoom. Loads the live STEP-derived STL.

---

## See it at Maker Faire Bay Area 2026

**Sept 25-27, 2026 · Mare Island Naval Shipyard, Vallejo CA.**

A working Mini v2.4 on the table, 24" live-sim dashboard next to it,
printed poster, take-home cut-list cards. The booth package
(booth plan, demo script, FAQ, parts list, interactive viewer, sim
dashboard) lives in [`booth/`](booth/).

If you're at the faire, come by. If you want to exhibit your own
agrivoltaic / solar / smart-garden project, the booth package
documents what worked (and what to skip) for next time.

---

## Fits any panel up to 8×5 ft: bring your own

A single Wattplot planter is bounded by **8-ft lumber stock**: 8 ft
long, 5 ft wide. The bed is sized to the panel (with up to 0.5"
overhang per side), and the cut list is derived from the bed.

The primary use case is **upcycling decommissioned panels that
would otherwise be landfilled**. A 12-year-old 250 W residential
panel is still a 235 W panel, perfect for shade + some power, and
you delay recycling by 10-20 years.

Five validated panel presets are in `wattplot_params.py`:

| Preset | L × W (in) | New W | Derated W |
|---|---|---|---|
| `longi_620W` (new bifacial) | 97.0 × 44.6 | 620 W | 620 W |
| `residential_60cell` | 65.0 × 39.0 | 250 W | 235 W (12 yr) |
| `residential_72cell` | 77.0 × 39.0 | 300 W | 288 W (8 yr) |
| `commercial_96cell` | 65.0 × 41.0 | 400 W | 388 W (6 yr) |
| `large_format_1m65` | 65.0 × 41.0 | 400 W | 392 W (4 yr) |

```python
import wattplot_params as P
P.apply_panel_preset('residential_60cell')  # bed resizes automatically
```

For custom panels, set `PANEL['L_in']`, `PANEL['W_in']`, `wattage`,
`panel_age_years`, `panel_bifacial`, and the bed + derated wattage
are computed for you. See [`docs/upcycling.md`](docs/upcycling.md)
for the full guide (lumber math, MPPT sizing, when a salvage
panel is *not* a good fit).

---

## Build photos

_(No physical build yet - placeholder for v1 prototype photos. Once you have a build, drop the images in `renders/build_photos/` and update this section.)_

**Build the entire apparatus:** see [`docs/build_guide.md`](docs/build_guide.md) for
the step-by-step assembly guide (8 phases, ~10-15 hours).

**Test & validation:** see [`docs/test_checklist.md`](docs/test_checklist.md) for
per-component and per-system tests, with a final sign-off checklist.

**Photo template** (for the build log):

| # | Subject | Angle | Notes |
|---|---|---|---|
| 1 | Overview of completed build | Iso from southeast, 20° elevation | Frame at 35° tilt, full bed |
| 2 | Bed close-up | Front (south wall) | Show half-lap corners, 4× butt hinges on south wall |
| 3 | Frame close-up | Iso from north | Show 2x6 PT perimeter + 2x4 diagonal brace |
| 4 | Hinge detail | Side, 12" away | One hinge in close-up, show leaf + knuckle + 1⁄2" pin |
| 5 | Actuator mount | Side | 2x6 PT clevis on north rail, 2x6 wall block, 1⁄2" pin |
| 6 | Panel mounting | Above, looking down | 6× aluminum mid-clamps on the rails |
| 7 | IMU on frame | Underside of north rail | BMI160 breakout screwed to the rail |
| 8 | PCB in enclosure | Above, enclosure open | All JST-XH connectors, ESP32, IMU/INA219 visible |
| 9 | Wiring close-up | Side, 6" away | Cable carrier with motor + IMU cables |
| 10 | Soil sensors | Soil cross-section | DS18B20 + soil moisture in the bed |
| 11 | Soil filled + planted | Front | 4 tomato seedlings, 11.25" soil depth |
| 12 | Dashboard on phone | Phone in hand | HA dashboard showing tilt, DLI, current draw |
| 13 | Frame at 90° (vertical) | Iso from east | BEDSUN mode, full sun on the bed |
| 14 | Frame flat (storm) | Iso from east | FOLDING mode, canopy down |

Add your photos to `renders/build_photos/` and link them in this section.

---

---

## What's in the box

```
wattplot.py                            ← top-level pipeline:  python wattplot.py
wattplot_params.py                     ← single source of truth for ALL parameters
models/
  freecad/                             ← FreeCAD parametric 3D model
    materials.py                       ← wood species, fasteners, hardware
    parts/                             ← one file per part (bed_wall, frame,
      _helpers.py, bed_wall.py,        ←   hinge, panel_clamp, actuator_mount,
      frame.py, panel.py, hinge.py,    ←   skids, diagonal_brace, ...)
      panel_clamp.py, skid.py,
      actuator_mount.py
    assemble.py                         ← imports all parts, exports STEP+STL+FCStd
    _run.py                             ← freecadcmd entry point
  legacy_cadquery/                     ← old cadquery model (archived)
  shadow_raycaster.py                  ← geometric bed-shadow from 3D panel
  render_3d_views.py, render_svg_views.py
analysis/
  sun_simulator.py                     ← annual kWh, bed DLI, tomato yield
  wind_load.py                         ← ASCE 7-22 force + safety factors
  engineering_drawing.py               ← side-view engineering drawings
  pcb_schematic.py                     ← PCB block-diagram generator
renders/                               ← generated PNGs (mostly gitignored)
firmware/                              ← ESPHome firmware for the controller
docs/                                  ← design + build + test docs (see below)
  index.html                           ← GitHub Pages 3D viewer
  control_law.md                       ← firmware spec (state machine, PI loop)
  pcb_design.md                        ← custom PCB spec (KiCad-ready)
  wiring.md                            ← pin-by-pin wiring from PCB to apparatus
  sensor_placement.md                  ← where each sensor mounts + why
  build_basic.md                       ← Basic tier: fixed pinned tilt, no electronics
  build_guide.md                       ← step-by-step build (8 phases, ~10-15 hours)
  test_checklist.md                    ← per-component + integration tests
```

**All design rules, the build, the wiring, and the tests are documented.**
`wattplot_params.py` is the single source of truth - change a value there
and the whole pipeline (3D model, shadow, sun sim, wind sim) updates in
~10 seconds.

---

## The design (one paragraph)

An 8 ft × 3.7 ft planter with 22" walls (25" rim height — wheelchair-
accessible seated-gardening range, with access from both long sides)
holding 20" of soil, with a solar panel
**surrounded by an all-wood frame** (2x6 PT Douglas Fir perimeter +
2x4 PT diagonal brace). The frame is hinged on the south wall by four
galvanized butt hinges. The bed is the **ballast** - no ground anchors.
In the **Basic** build the north rail rests on a pinned 2x4 prop strut
(fixed tilt, set by hand). In the **Smart** build the north rail is
pushed by a 4" stroke linear actuator (0-45°; storm fold = flat), and
the controller uses a PI loop on motor current to reduce tilt under
wind load, then back to the commanded angle when wind drops. **45° is
the structural max**: above it the wind calc fails overturning at the
design wind (SF 0.95-0.98 at 75-90°), so the old 90° "sun-on-bed /
wring-out" modes are calm-weather-only and off by default.

**Frame material:** all lumber for sustainability (FSC Douglas Fir where
available). Hardware (hinges, panel clamps) is metal where the load demands.

## Power architecture - only two sources

```
            ┌─────────────────┐
            │ 620W bifacial   │
            │ main panel      │  ← the only solar source
            └────┬────────────┘
                 │  DC bus (30-40V, 0-18A)
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
  ┌──────────┐      ┌───────────────────┐
  │ Micro-   │      │ MPPT (Victron     │
  │ inverter │      │  100/30 or EPEver  │
  │ (AC out) │      │  Tracer 4210AN)   │
  └────┬─────┘      └────────┬──────────┘
       │                     │
       ▼                     ▼
   [240V AC]            ┌──────────┐
                        │ 12V      │  ← the only battery
                      │ LiFePO4  │
                      └────┬─────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  ESP32 +     │
                    │  DRV8871     ├──► Linear actuator (panel tilt)
                    │  BMI160 IMU  │     ↑ closed-loop position
                    │  INA219      │     │ actual tilt
                    │  DS18B20     │     │
                    │  soil sensor │
                    └──────────────┘
```

**Only two energy sources: the main 620W panel and the 12V battery.** No separate trickle panel. The main panel feeds both the microinverter (for AC) and a real hardware MPPT (Victron SmartSolar 100/30 or EPEver Tracer 4210AN) for 12V battery charging - both from the same panel via a Y-splitter on the MC4 leads. The 620W panel produces 50-100× more energy than the controller needs, so it's a non-issue.

> **Earlier revisions (v2.0-2.3) used a DPS5005 programmable buck + UART-MPPT pattern** for the full-size build. That was retired: the DPS5005 was a hack (using a bench PSU as a charge controller) and was also undersized for the 620W panel (5A max output would have thrown away ~90% of the panel's potential). The mini build (v2.4) uses a standalone **Sunapex 10A** MPPT - no host connection, IP67 waterproof, LiFePO4-aware out of the box. The full-size build needs the larger Victron/EPEver above. See `docs/build_guide.md` §7.

## Key design numbers (Phoenix, AZ, Cat II 700-yr, Exp C)

- **Wind:** 115 mph 3-sec gust design. At 20" soil fill (~3,900 lb dead load
  in the 22"-wall accessible bed), the structure passes safety factor ≥ 2.0
  from 0-45° tilt — 45° is the max operating angle. Stowed flat (0°) the
  panel carries ~zero wind load; stow is the storm answer for both tiers
  (manual pin on Basic, auto-fold on Smart). Rated deployed wind: ~125 mph
  at 45°, ~165 mph at 35°.
- **Power (azimuth tracking 35° tilt, Phoenix 2025):** 2,240 kWh/year.
- **Tomato yield (35° tilt):** ~124 kg/year from 4 plants. Vertical (90°)
  gives full bed sun but ~50% less power and more heat stress.
- **Best balance:** static 35° or azimuth tracking 35°, depending on whether
  you value simplicity or kWh.

See `analysis/wind_load_report.md` and `analysis/sun_simulator.py` for the
underlying calculations.

## The smart controller (target design)

```
priority  source                              sets θ_desired / lights
─────────────────────────────────────────────────────────────────
   1      user override                       arbitrary
   2      hard current limit                  θ = 0 (safety)
   3      NWS rain forecast + dry soil        θ = 0 (capture rain)
   4      NWS wind forecast > 50 mph          θ = 15 (preemptive)
   5      wind > 50% of safe limit            pause tracking
   6      soil wet 72h+ → wring out           θ = 90
   7      soil dry 48h+ + no rain → conserve  θ = 35
   8      time-of-day + tracking mode         θ = 0-90 (azimuth track)
   9      time-of-day + power mode            θ = 35
   10     time-of-day + bed-sun mode          θ = 90
   L1     battery SOC < 50%                  lights off
   L2     natural DLI > target               lights off
   L3     DLI deficit > 0 (need light)       lights on (pre/post-dawn)
   L4     hard constraint                    8 hr dark minimum
```

Goal: **keep motor current below I_safe, while maximizing commanded tilt for sun exposure.**

## How to run

```bash
# Full pipeline (3D model export + sun sim + wind sim)
python wattplot.py

# Just the simulation (skip the 3D export)
python wattplot.py --skip-model

# Just one analysis
python analysis/sun_simulator.py
python analysis/wind_load.py

# Override a parameter at the command line
python wattplot.py --tilt 50

# View the 3D model in a browser
open renders/viewer.html
```

### Dependencies

- Python 3.10+
- `numpy`, `pandas`, `matplotlib`, `pvlib`, `shapely`, `scipy` (for analysis)
- **FreeCAD 1.0+** (for the 3D model - `freecadcmd` is auto-detected on
  Windows in `C:\Program Files\FreeCAD *\bin\`)
- `ruff` (for lint)

```bash
pip install numpy pandas matplotlib pvlib shapely scipy ruff
```

The 3D model is built by FreeCAD. On Windows with FreeCAD 1.0+ installed
in the default location, the orchestrator finds it automatically. To
override, set `$FREECADCMD` to the path of `freecadcmd.exe`.

## Hardware reference — Smart tier (target spec, not yet built)

This is the full flagship BOM. **Basic tier** deletes the actuator,
MPPT-for-controller, LiFePO4, ESP32/PCB, and grow light rows, and swaps
the new 620W panel for a salvaged one — see
[`docs/build_basic.md`](docs/build_basic.md).

| Component | Spec | ~$ |
|---|---|---|
| Bed walls | 1x6 cedar skin (4 courses, 22" tall) + 2x4 PT cleats + 2x6 PT caps; 25" accessible rim | 150 |
| Frame rails | 2x6 PT DF, 2 × 8 ft long + 2 × 8 ft cross | 60 |
| Diagonal brace | 2x4 PT DF, 1 × 10 ft | 15 |
| Skids | 4x4 PT DF, 2 × 8 ft | 30 |
| Hinges | 4 × galvanized butt hinges 4"×4", 1⁄2" pin, +96" 1⁄2" rod | 35 |
| Panel clamps | 6 × aluminum mid-clamps, 35mm channel | 18 |
| Linear actuator | 12V, 4" stroke, IP65, 330 lb | 60 |
| **MPPT charge controller (full-size)** | Victron SmartSolar 100/30 (30A, 100V) or EPEver Tracer 4210AN (40A, 100V) | 200 |
| Panel | 620W bifacial (LONGi Hi-MO X10 or similar) | 200 |
| Microinverter | Enphase IQ7+ or APsystems DS3, 240V, UL 1741 | 150 |
| 12V 100Ah LiFePO4 | LiTime or similar | 230 |
| ESP32 + custom PCB | w/ DRV8871, INA219, BMI160, sensors | 120 |
| 200W LED grow light | full spectrum, IP65 (v2) | 130 |
| Misc (screws, bolts, wire, irrigation) | | 50 |
| **Total parts** | | **~$1,400** |

All structural lumber is FSC Douglas Fir where available. No welding. No
concrete. See `bom.md` for sourcing notes.

The MPPT is a real hardware charge controller (Victron or EPEver) sized
for the 620W panel - no firmware-side MPPT loop, no UART setpoint
commands. ESP32 reads MPPT telemetry (panel V/I, battery V, charge
state) over VE.Direct / RS-485 for energy monitoring and Home
Assistant visibility. The same panel also feeds the microinverter for
AC output via a Y-splitter. No separate trickle panel needed.

## Project status

- [x] Parametric 3D model (FreeCAD) with STEP / STL / FCStd export, one
      file per part (`models/freecad/parts/`)
- [x] All-wood perimeter frame design (2x6 rails + 2x4 brace, half-lap bed corners)
- [x] ASCE 7-22 wind load analysis, Phoenix, Exp C, Cat II 700-yr
- [x] Geometric shadow raycaster (uses actual 3D panel)
- [x] Annual sun + yield simulator (5 tilt schedules, Phoenix weather)
- [x] Engineering side-view drawings (with frame + actuator + hinge detail)
- [x] PCB spec (KiCad-ready) - `docs/pcb_design.md`
- [x] Wiring diagram (pin-by-pin) - `docs/wiring.md`
- [x] Sensor placement plan - `docs/sensor_placement.md`
- [x] Build guide (8 phases, ~10-15 hours) - `docs/build_guide.md`
- [x] Test & validation checklist - `docs/test_checklist.md`
- [x] ESPHome firmware (PI controller, NWS polling, fold logic) - `firmware/`
- [ ] Order custom PCB from JLCPCB
- [ ] Real-world deployment validation

## Prior art & acknowledgments

Wattplot builds on the work of many open-source projects. If you find their work useful, please support them.

### Agrivoltaic simulation
- **[NREL/bifacial_radiance](https://github.com/NREL/bifacial_radiance)** - gold-standard bifacial PV ray-tracer. Our 2D `shadow_raycaster.py` is a simplified version of what bifacial_radiance does in 3D.
- **[NREL/InSPIRE](https://github.com/NREL/InSPIRE)** - agrivoltaic tutorials, scripts, and research workflows.
- **[DailyAgrivoltaicOperation (astuhlmacher)](https://github.com/astuhlmacher/DailyAgrivoltaicOperation)** - dual-axis panel optimization under crop constraints, the academic version of what Wattplot does in firmware.
- **[PASE 1.0](https://gitlab.uliege.be/pase/pase_1.0)** - Python Agrivoltaic Simulation Environment, energy + crop dual-objective.

### Solar tracker controllers
- **[Helioduino (NachtRaveVL)](https://github.com/NachtRaveVL/Simple-SolarTracker-Arduino)** - mature LDR-based sun tracker for Arduino. The reference for "professional grade" tracker control.
- **[SolarArduino (HDwayne)](https://github.com/HDwayne/SolarArduino)** - ESP32 sun tracker with **wind safety using an anemometer** (folds to safety position for 15 min if wind > 5 m/s). The pattern for our wind-safety state machine in `docs/control_law.md` comes from here.
- **[Sunchronizer (Nerdiyde)](https://github.com/Nerdiyde/Sunchronizer)** - ESP32 + 6000N linear actuator + **BMI160 IMU for closed-loop position feedback**. We adopted the IMU approach for the same reason (drift-free actual tilt angle).
- **[f2knpw/ESP32_Solar_Tracker](https://github.com/f2knpw/ESP32_Solar_Tracker)** - Lite ESP32 solar tracker with sun-position calc, sleep mode, OTA.

### Smart solar chargers (MPPT pattern)
- **Earlier revisions of Wattplot (v2.0-2.3) used a DPS5005-as-MPPT pattern** (similar to OSPController and fugu-mppt-firmware below). This was retired in v2.4 because the DPS5005 was both a hack (using a bench PSU as a charge controller) and undersized for the 620W panel. The current build uses off-the-shelf hardware MPPTs (Sunapex HC-SM10A on the mini, Victron/EPEver on the full-size) - the firmware no longer commands a charge controller, it only reads telemetry.
- **[OSPController (Open Solar Project)](https://github.com/opensolarproject/OSPController)** - ESP32 controls a commercial DPS5005 buck via UART for MPPT. Good reference if you want to revive the UART-MPPT pattern (e.g., to add telemetry from a Victron VE.Direct port to a custom control loop).
- **[fugu-mppt-firmware (fl4p)](https://github.com/fl4p/fugu-mppt-firmware)** - ESP32 MPPT firmware, 95% efficient synchronous buck. Reference for designing a custom MPPT from scratch (we deliberately chose not to).
- **[akgang ESP32 MPPT](https://github.com/akgang-rgb/ESP32-Smart-Solar-Controller-MPPT-Firmware-Web-Dashboard)** - single-file Arduino ESP32 MPPT with INA226, web dashboard, NASA POWER + OWM forecasts. Reference for the MPPT loop algorithm (perturb-and-observe with dither) if we ever need to bring back a firmware-side MPPT step.

### Weather + solar (IoT pattern)
- **[SolarWS (BeardedTinker)](https://github.com/BeardedTinker/SolarWS)** - ESPHome weather station, deep sleep at night, OTA.
- **[solar_weather (squidpickles)](https://github.com/squidpickles/solar_weather)** - ESPHome config for solar weather station.
- **[Home Assistant Forecast.Solar integration](https://www.home-assistant.io/integrations/forecast_solar/)** - built-in solar production forecast for HA. A drop-in alternative to our NWS-based forecast.

### DIY raised bed + solar
- **[POSCAS](https://www.appropedia.org/Parametric_Open_Source_Cold-Frame_Agrivoltaic_Systems)** - Parametric Open Source Cold-Frame Agrivoltaic System. **The closest analog to Wattplot** in philosophy (open-source, parametric, agrivoltaic) but for a cold frame. Worth studying.
- **[Vege Garden Automation (Rototron)](https://www.rototron.info/projects/micropython-vegetable-garden-automation-tutorial/)** - solar-powered soil sensors + MQTT + HA on a raised bed. **Validates the IoT + raised bed + solar pattern** Wattplot uses.

### Standards
- **[ASCE 7-22](https://www.asce.org/publications-and-news/asce-7)** - wind load provisions. Our `analysis/wind_load.py` uses ASCE 7-22 Table 26.10-1 for velocity pressure exposure coefficients.
- **[pvlib](https://pvlib-python.readthedocs.io/)** - solar position + clear-sky modeling. Industry standard, NREL-developed.
- **[IEC 61215 / UL 61730](https://en.wikipedia.org/wiki/Solar_panel)** - panel safety standards. Our 620W bifacial panel is certified to these.
- **[UL 1741 / IEEE 1547](https://en.wikipedia.org/wiki/UL_1741)** - grid-tie inverter safety. We use a commercial microinverter (Enphase IQ7+, APsystems DS3) that meets these, so the user doesn't have to.

### Plug-and-play solar laws (regulatory)
- **Utah [SB 190](https://le.utah.gov/~2024/bills/sbillint/SB0190.html)** (2024) - first comprehensive balcony solar law, 800W plug-in allowance.
- **California [AB 1076](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202120220AB1076)** (2022) - most generous, 5 kW plug-in allowance.
- **Colorado [HB 22-1015](https://leg.colorado.gov/bills/hb22-1015)** (2022) - 800W plug-in, similar to Utah.

Wattplot's 620W panel is below the 800W threshold in Utah and Colorado, and well within California's 5 kW cap. Design fits the regulatory window for plug-and-play solar in all three states.

### Tools we use
- **[cadquery](https://github.com/CadQuery/cadquery)** - parametric 3D model
- **[shapely](https://shapely.readthedocs.io/)** - 2D geometry for the shadow raycaster
- **[cairosvg](https://cairosvg.org/)** - SVG → PNG rendering
- **[matplotlib](https://matplotlib.org/)** - plots
- **[three.js](https://threejs.org/)** - the interactive 3D viewer in `docs/`

---

## License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE).

You are free to use, modify, and sell products based on this design. Attribution appreciated.

## Contributing

Issues, PRs, and forks welcome. The system is small enough that you should be able to read the whole codebase in an afternoon.

If you build one, send photos.

## Acknowledgments

- `pvlib` (Sandia / pvlib-team) for solar position + clear-sky modeling
- `cadquery` for parametric CAD
- `shapely` for 2D geometry
- ASCE 7-22 for the wind provisions
- The "balcony solar" laws in Utah (SB 190), California (AB 1076), and Colorado (HB22-1015) for inspiring the plug-and-play direction
