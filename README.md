# Wattplot v2

A DIY, open-source 8 ft × 3.7 ft planter with an adjustable-tilt bifacial solar canopy.
A parametric, code-first design that integrates 3D modeling, sun simulation,
wind-load analysis, and a smart-folding controller into a single pipeline.

> **Status:** pre-prototype. The mechanical / structural / aerodynamic design is validated by 3D model + ASCE 7-22 wind calc + geometric shadow raycaster. The smart controller (ESP32-based) and custom PCB are next steps.

---

## What's in the box

```
wattplot.py                       ← top-level pipeline:  python wattplot.py
wattplot_params.py                 ← single source of truth for ALL parameters
models/
  wattplot_v2_model.py             ← cadquery 3D model (parametric)
  shadow_raycaster.py              ← geometric bed-shadow from 3D panel
  export_3d.py                     ← exports STEP / STL / 3MF / VRML
  render_3d_views.py               ← matplotlib 3D previews
  render_svg_views.py              ← cadquery orthographic SVGs
analysis/
  sun_simulator.py                 ← annual kWh, bed DLI, tomato yield
  wind_load.py                     ← ASCE 7-22 force + safety factors
  engineering_drawing.py           ← side-view engineering drawings
  pcb_schematic.py                 ← PCB block-diagram generator
renders/                           ← generated PNGs (gitignored or committed)
```

Change a value in `wattplot_params.py`, run `python wattplot.py`, and the
whole pipeline (3D model, shadow, sun sim, wind sim) updates in ~8 seconds.

---

## The design (one paragraph)

An 8 ft × 3.7 ft × 12" soil-filled cedar planter with a 620 W bifacial solar
panel hinged on the south wall. Two 6×6×10 ft posts on the north side support
a horizontal beam. The panel tilts 0–90° (storm fold → sun-on-bed vertical).
The bed is the **ballast** — no ground anchors. The smart controller uses a
PI loop on motor current to reduce tilt under wind load, then back to the
commanded angle when wind drops.

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
- `numpy`, `pandas`, `matplotlib`, `pvlib`, `cadquery`, `shapely`, `cairosvg`, `scipy`

```bash
pip install numpy pandas matplotlib pvlib cadquery shapely cairosvg scipy
```

## Hardware reference (target spec, not yet built)

| Component | Spec | ~$ |
|---|---|---|
| Bed walls | 2x6 PT pine stacked, 8×3.7 ft, 12" deep | 250 |
| Posts | 6×6×10 ft PT pine, 2 ea | 100 |
| Beam | 6×6×7 ft PT pine | 50 |
| Skids | 4×4 PT pine, 8 ft, 2 ea | 30 |
| Hinge | 1/2" × 6 ft continuous hinge, SS | 50 |
| Panel | 620W bifacial (LONGi Hi-MO X10 or similar) | 200 |
| Linear actuator | 12V, 4" stroke, IP65, 330 lb | 60 |
| ESP32 + custom PCB | w/ MPPT, INA219, sensors, comms | 120 |
| 12V 100Ah LiFePO4 | LiTime or similar | 230 |
| 200W LED grow light | full spectrum, IP65 | 130 |
| Misc (screws, bolts, wire, irrigation) | | 150 |
| **Total parts** | | **~$1,370** |

## Project status

- [x] Parametric 3D model (cadquery) with STEP / STL / 3MF / VRML export
- [x] ASCE 7-22 wind load analysis, Phoenix, Exp C, Cat II 700-yr
- [x] Geometric shadow raycaster (uses actual 3D panel)
- [x] Annual sun + yield simulator (5 tilt schedules, Phoenix weather)
- [x] Engineering side-view drawings
- [x] PCB block diagram (controller + sensors)
- [ ] ESP32 prototype + firmware (PI controller, NWS polling, fold logic)
- [ ] Custom PCB (JLCPCB fab + assembly)
- [ ] Real-world deployment validation

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
