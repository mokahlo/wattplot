# Wattplot v2

A DIY, open-source 8 ft × 3.7 ft planter with an adjustable-tilt bifacial solar canopy.
A parametric, code-first design that integrates 3D modeling, sun simulation,
wind-load analysis, and a smart-folding controller into a single pipeline.

> **Status:** pre-prototype. The mechanical / structural / aerodynamic design is validated by 3D model + ASCE 7-22 wind calc + geometric shadow raycaster. The smart controller (ESP32-based) and custom PCB are next steps.

## Design rules (enforced)

Three constraints guide every part of the design:

1. **No miter cuts.** Every cut is a 90° square cut. Joints are butt, half-lap, or
   lap. The diagonal brace has square ends that butt into the long rails — no
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

[**Open the 3D viewer**](https://mokahlo.github.io/wattplot/) — drag to orbit, scroll to zoom. Loads the live STEP-derived STL.

---

## Build photos

_(No physical build yet — placeholder for v1 prototype photos. Once you have a build, drop the images in `renders/build_photos/` and update this section.)_

Suggested photo angles for a build log:
- Overview: bed + posts + panel at 35° tilt
- Smart controller PCB installed in its enclosure
- Hinge detail (south wall, panel in flat and tilted positions)
- Actuator mounted on the beam, connected to panel
- Soil fill and tomato planting
- Dashboard on a phone showing tilt, DLI, current draw
- Winter scene at 90° vertical, full sun on the bed

Want a release-blocking photo template? Add an issue with the tag `build-photo`.

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
docs/                                  ← GitHub Pages 3D viewer
```

Change a value in `wattplot_params.py`, run `python wattplot.py`, and the
whole pipeline (3D model, shadow, sun sim, wind sim) updates in ~10 seconds.

---

## The design (one paragraph)

An 8 ft × 3.7 ft × 12" soil-filled planter with a 620 W bifacial solar
panel **surrounded by an all-wood frame** (2x6 PT Douglas Fir perimeter +
2x4 PT diagonal brace). The frame is hinged on the south wall by four
galvanized butt hinges, and the north rail is pushed by a 4" stroke linear
actuator. The panel tilts 0–90° (storm fold → sun-on-bed vertical). The bed
is the **ballast** — no ground anchors. The smart controller uses a PI loop
on motor current to reduce tilt under wind load, then back to the commanded
angle when wind drops.

**Frame material:** all lumber for sustainability (FSC Douglas Fir where
available). Hardware (hinges, panel clamps) is metal where the load demands.

## Power architecture — only two sources

```
            ┌─────────────────┐
            │ 620W bifacial   │
            │ main panel      │  ← the only solar source
            └────┬────────────┘
                 │  DC bus (30-40V, 0-18A)
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
  ┌──────────┐      ┌──────────────┐
  │ Micro-   │      │ DPS5005 MPPT │
  │ inverter │      │ (commercial, │
  │ (AC out) │      │  UART-ctrl)  │
  └────┬─────┘      └──────┬───────┘
       │                   │
       ▼                   ▼
   [240V AC]          ┌──────────┐
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

**Only two energy sources: the main 620W panel and the 12V battery.** No separate trickle panel. The main panel feeds both the microinverter (for AC) and a DPS5005 programmable buck converter (for 12V battery charging) — both from the same panel. The 620W panel produces 50–100× more energy than the controller needs, so it's a non-issue.

## Key design numbers (Phoenix, AZ, Cat II 700-yr, Exp C)

- **Wind:** 115 mph 3-sec gust design. At 12" soil depth, structure passes
  safety factor ≥ 2.0 from 0–35° tilt. 14.6" soil depth covers 0–50°.
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
- **FreeCAD 1.0+** (for the 3D model — `freecadcmd` is auto-detected on
  Windows in `C:\Program Files\FreeCAD *\bin\`)
- `ruff` (for lint)

```bash
pip install numpy pandas matplotlib pvlib shapely scipy ruff
```

The 3D model is built by FreeCAD. On Windows with FreeCAD 1.0+ installed
in the default location, the orchestrator finds it automatically. To
override, set `$FREECADCMD` to the path of `freecadcmd.exe`.

## Hardware reference (target spec, not yet built)

| Component | Spec | ~$ |
|---|---|---|
| Bed walls | 2x12 PT Douglas Fir, 4 × 8 ft + 1 × 8 ft, 11.25" actual depth | 100 |
| Frame rails | 2x6 PT DF, 2 × 8 ft long + 2 × 8 ft cross | 60 |
| Diagonal brace | 2x4 PT DF, 1 × 10 ft | 15 |
| Skids | 4x4 PT DF, 2 × 8 ft | 30 |
| Hinges | 4 × galvanized butt hinges 4"×4", ½" pin, +96" ½" rod | 35 |
| Panel clamps | 6 × aluminum mid-clamps, 35mm channel | 18 |
| Linear actuator | 12V, 4" stroke, IP65, 330 lb | 60 |
| **DPS5005 MPPT** | Ruideng programmable buck, UART-controlled, 50V/5A | 25 |
| Panel | 620W bifacial (LONGi Hi-MO X10 or similar) | 200 |
| Microinverter | Enphase IQ7+ or APsystems DS3, 240V, UL 1741 | 150 |
| 12V 100Ah LiFePO4 | LiTime or similar | 230 |
| ESP32 + custom PCB | w/ DRV8871, INA219, BMI160, sensors | 120 |
| 200W LED grow light | full spectrum, IP65 (v2) | 130 |
| Misc (screws, bolts, wire, irrigation) | | 50 |
| **Total parts** | | **~$1,225** |

All structural lumber is FSC Douglas Fir where available. No welding. No
concrete. See `bom.md` for sourcing notes.

Note: DPS5005 is the MPPT path. The 620W main panel feeds the DPS5005 via UART control from the ESP32 — 95% efficient, no custom magnetics design, hackable. The same panel also feeds the microinverter for AC output. No separate trickle panel needed.

## Project status

- [x] Parametric 3D model (FreeCAD) with STEP / STL / FCStd export, one
      file per part (`models/freecad/parts/`)
- [x] All-wood perimeter frame design (2x6 rails + 2x4 brace, half-lap bed corners)
- [x] ASCE 7-22 wind load analysis, Phoenix, Exp C, Cat II 700-yr
- [x] Geometric shadow raycaster (uses actual 3D panel)
- [x] Annual sun + yield simulator (5 tilt schedules, Phoenix weather)
- [x] Engineering side-view drawings (with frame + actuator + hinge detail)
- [x] PCB block diagram (controller + sensors)
- [x] ESPHome firmware (PI controller, NWS polling, fold logic) — `firmware/`
- [ ] Custom PCB (JLCPCB fab + assembly)
- [ ] Real-world deployment validation

## Prior art & acknowledgments

Wattplot builds on the work of many open-source projects. If you find their work useful, please support them.

### Agrivoltaic simulation
- **[NREL/bifacial_radiance](https://github.com/NREL/bifacial_radiance)** — gold-standard bifacial PV ray-tracer. Our 2D `shadow_raycaster.py` is a simplified version of what bifacial_radiance does in 3D.
- **[NREL/InSPIRE](https://github.com/NREL/InSPIRE)** — agrivoltaic tutorials, scripts, and research workflows.
- **[DailyAgrivoltaicOperation (astuhlmacher)](https://github.com/astuhlmacher/DailyAgrivoltaicOperation)** — dual-axis panel optimization under crop constraints, the academic version of what Wattplot does in firmware.
- **[PASE 1.0](https://gitlab.uliege.be/pase/pase_1.0)** — Python Agrivoltaic Simulation Environment, energy + crop dual-objective.

### Solar tracker controllers
- **[Helioduino (NachtRaveVL)](https://github.com/NachtRaveVL/Simple-SolarTracker-Arduino)** — mature LDR-based sun tracker for Arduino. The reference for "professional grade" tracker control.
- **[SolarArduino (HDwayne)](https://github.com/HDwayne/SolarArduino)** — ESP32 sun tracker with **wind safety using an anemometer** (folds to safety position for 15 min if wind > 5 m/s). The pattern for our wind-safety state machine in `docs/control_law.md` comes from here.
- **[Sunchronizer (Nerdiyde)](https://github.com/Nerdiyde/Sunchronizer)** — ESP32 + 6000N linear actuator + **BMI160 IMU for closed-loop position feedback**. We adopted the IMU approach for the same reason (drift-free actual tilt angle).
- **[f2knpw/ESP32_Solar_Tracker](https://github.com/f2knpw/ESP32_Solar_Tracker)** — Lite ESP32 solar tracker with sun-position calc, sleep mode, OTA.

### Smart solar chargers (MPPT pattern)
- **[OSPController (Open Solar Project)](https://github.com/opensolarproject/OSPController)** — ESP32 controls a commercial DPS5005 buck via UART for MPPT. **We adopted this exact pattern** — the DPS5005 in the Wattplot PCB is the MPPT path, controlled by the ESP32, no custom magnetics.
- **[fugu-mppt-firmware (fl4p)](https://github.com/fl4p/fugu-mppt-firmware)** — ESP32 MPPT firmware, 95% efficient synchronous buck.
- **[akgang ESP32 MPPT](https://github.com/akgang-rgb/ESP32-Smart-Solar-Controller-MPPT-Firmware-Web-Dashboard)** — single-file Arduino ESP32 MPPT with INA226, web dashboard, NASA POWER + OWM forecasts. The "single .ino file" philosophy is what we want for v1 prototype.

### Weather + solar (IoT pattern)
- **[SolarWS (BeardedTinker)](https://github.com/BeardedTinker/SolarWS)** — ESPHome weather station, deep sleep at night, OTA.
- **[solar_weather (squidpickles)](https://github.com/squidpickles/solar_weather)** — ESPHome config for solar weather station.
- **[Home Assistant Forecast.Solar integration](https://www.home-assistant.io/integrations/forecast_solar/)** — built-in solar production forecast for HA. A drop-in alternative to our NWS-based forecast.

### DIY raised bed + solar
- **[POSCAS](https://www.appropedia.org/Parametric_Open_Source_Cold-Frame_Agrivoltaic_Systems)** — Parametric Open Source Cold-Frame Agrivoltaic System. **The closest analog to Wattplot** in philosophy (open-source, parametric, agrivoltaic) but for a cold frame. Worth studying.
- **[Vege Garden Automation (Rototron)](https://www.rototron.info/projects/micropython-vegetable-garden-automation-tutorial/)** — solar-powered soil sensors + MQTT + HA on a raised bed. **Validates the IoT + raised bed + solar pattern** Wattplot uses.

### Standards
- **[ASCE 7-22](https://www.asce.org/publications-and-news/asce-7)** — wind load provisions. Our `analysis/wind_load.py` uses ASCE 7-22 Table 26.10-1 for velocity pressure exposure coefficients.
- **[pvlib](https://pvlib-python.readthedocs.io/)** — solar position + clear-sky modeling. Industry standard, NREL-developed.
- **[IEC 61215 / UL 61730](https://en.wikipedia.org/wiki/Solar_panel)** — panel safety standards. Our 620W bifacial panel is certified to these.
- **[UL 1741 / IEEE 1547](https://en.wikipedia.org/wiki/UL_1741)** — grid-tie inverter safety. We use a commercial microinverter (Enphase IQ7+, APsystems DS3) that meets these, so the user doesn't have to.

### Plug-and-play solar laws (regulatory)
- **Utah [SB 190](https://le.utah.gov/~2024/bills/sbillint/SB0190.html)** (2024) — first comprehensive balcony solar law, 800W plug-in allowance.
- **California [AB 1076](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202120220AB1076)** (2022) — most generous, 5 kW plug-in allowance.
- **Colorado [HB 22-1015](https://leg.colorado.gov/bills/hb22-1015)** (2022) — 800W plug-in, similar to Utah.

Wattplot's 620W panel is below the 800W threshold in Utah and Colorado, and well within California's 5 kW cap. Design fits the regulatory window for plug-and-play solar in all three states.

### Tools we use
- **[cadquery](https://github.com/CadQuery/cadquery)** — parametric 3D model
- **[shapely](https://shapely.readthedocs.io/)** — 2D geometry for the shadow raycaster
- **[cairosvg](https://cairosvg.org/)** — SVG → PNG rendering
- **[matplotlib](https://matplotlib.org/)** — plots
- **[three.js](https://threejs.org/)** — the interactive 3D viewer in `docs/`

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE).

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
