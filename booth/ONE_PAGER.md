# Wattplot, One-Pager (booth handout)

> A single-page, 8.5×11 take-home. Source for this is the markdown
> below; render to PDF for printing (Vistaprint, FedEx Kinko's, or
> `pandoc`).

---

# Wattplot

### Give an old solar panel a second life. Shade + food + power, in one raised bed.

A planter up to 8 ft × 5 ft with a hinged, ballast-mounted solar
canopy. Fits **any panel up to 97" × 61"**, new bifacial from the
manufacturer, or **old salvage from a decommissioned rooftop** that
would otherwise be landfilled. The smart controller tilts the
panel to follow the sun, fold for wind, verticalize for rain, and
shut off the motor before it stalls.

**Full-size build:** up to 8 ft × 5 ft, ~$1,400 in parts (new
bifacial) or ~$800 in parts (with a salvage panel), ~10–15 hours
over a weekend.

**This table:** 18" × 14" mini, ~$193 in parts, ~3–4 hours. Same
firmware, same MPPT, same sensors, same decision stack.

---

## Why upcycle?

~10M tons of solar panel waste globally by 2050 (IRENA). Most
panels are removed because the **racking or inverter** failed, not
the cells. A 12-year-old 250 W panel is still a 235 W panel. For
shade + some power, that's a free 235 W, and you delay
recycling by 10-20 years.

---

## The numbers (full-size, Phoenix, AZ)

| What | Value |
|---|---|
| Power (35° tilt, 235W salvage) | ~850 kWh/yr |
| Power (35° tilt, 620W new bifacial) | ~2,240 kWh/yr |
| Tomato yield (4 plants) | ~124 kg/yr, about 250 lb |
| Wind design | 115 mph 3-sec gust (ASCE 7-22, Cat II 700-yr) |
| Tilt range | 0° (storm) to 90° (full bed sun) |
| Panel | Any up to 97"×61", 30+ year life |
| Battery | 12 V 100 Ah LiFePO4, ~10 yr life |
| Microinverter | Enphase IQ7+ or APsystems DS3, 240 V |
| MPPT | Victron SmartSolar 100/30 (full-size) or Sunapex 10A (salvage) |
| Controller | ESP32 + custom PCB, ~$30 in parts |

---

## Fits any panel up to 97"×61"

| Salvage panel | L × W (in) | New W | Derated W | Bed (in) |
|---|---|---|---|---|
| Residential 60-cell | 65 × 39 | 250 W | 235 W (12 yr) | 65 × 39 |
| Residential 72-cell | 77 × 39 | 300 W | 288 W (8 yr) | 77 × 39 |
| Commercial 96-cell | 65 × 41 | 400 W | 388 W (6 yr) | 65 × 41 |
| Large 1m65 (bifacial) | 65 × 41 | 400 W | 392 W (4 yr) | 65 × 41 |
| LONGi 620 W bifacial (new) | 97 × 44.6 | 620 W | 620 W | 96 × 44.6 |

All five are validated presets in `wattplot_params.py`. Bring your
own panel, measure the aluminum frame dimensions and call
`apply_panel_preset(name)`. The bed resizes automatically. The
cut list is derived from the bed.

See `docs/upcycling.md` for the full guide.

---

## How it works

1. **Sun** hits the panel.
2. **MPPT** charges the 12 V battery *and* feeds the microinverter.
3. **Microinverter** exports 240 V AC to the home or grid.
4. **ESP32 controller** decides panel angle from weather, soil,
   time of day.
5. **Linear actuator** tilts the frame 0–90°.
6. **IMU** measures actual tilt, closed loop on motor current.
7. **Bed below** gets morning and evening sun, midday shade.

```
   NWS weather ─┐
   Soil sensors ─┤
   Time of day ──┼──►  decision stack  ──►  θ_desired
   User override ─┤                          │
                 ─┘                          ▼
                                          ┌────────┐
   INA219 motor I ──►  PI loop ──► actuator  ──►  panel
   BMI160 actual θ ──┘
```

---

## The smart controller, priority-ordered decision stack

| # | Source | Action |
|---|---|---|
| 1 | User override | any |
| 2 | Hard current limit | θ = 0 (safety) |
| 3 | NWS rain + dry soil | θ = 0 (capture rain) |
| 4 | NWS wind > 50 mph | θ = 15 (preemptive) |
| 5 | Wind > 50% safe | pause tracking |
| 6 | Soil wet 72h+ | θ = 90 (wring out) |
| 7 | Soil dry 48h+ | θ = 35 (conserve) |
| 8 | Tracking mode | θ = 0-90 (azimuth) |
| 9 | Power mode | θ = 35 |
| 10 | Bed-sun mode | θ = 90 |

Full spec: `docs/control_law.md`. Implementation:
`firmware/wattplot.yaml` (ESPHome).

---

## The build, what's in the box

- **Bed walls**, 2×12 PT Douglas Fir, sized to your panel
- **Frame rails**, 2×6 PT DF, with 2×4 diagonal brace
- **Skids**, 4×4 PT DF
- **Hinges**, galvanized butt, ½" pin, continuous rod
- **Panel**, your salvage (or new)
- **Hardware**, all off the shelf, no welding, no miter cuts
- **All FSC**, sustainable lumber where available

The full-size is ~$800-1,400 in parts (depending on panel source).
The mini on the table is ~$193.

---

## How to get started

| Step | Time | Cost |
|---|---|---|
| 1. Read `README.md` and `docs/upcycling.md` | 30 min | free |
| 2. Source a salvage panel (Craigslist, salvage yard, your own rooftop) | varies | $0-200 |
| 3. Measure the panel frame, call `apply_panel_preset(...)` or set dims | 30 min | $0 |
| 4. Build the **Mini** first to validate (`docs/build_guide_mini.md`) | 3-4 hr | ~$193 |
| 5. Calibrate the IMU, flash ESPHome | 1 hr | $0 |
| 6. Order the full-size lumber + MPPT (sized to your panel) | 30 min | $300-600 |
| 7. Build the full-size | 10-15 hr | $0 |
| 8. Plant tomatoes, run the dashboard | forever | tomato seeds |

**The single most important thing to do first: build the mini.**
It's the same firmware, the same MPPT, the same sensors. If the mini
works, the full-size works.

---

## Open source

Wattplot is MIT-licensed, open-source, code-first.

- **Repo:** github.com/mokahlo/wattplot
- **3D viewer:** mokahlo.github.io/wattplot
- **Upcycling guide:** docs/upcycling.md
- **License:** MIT (use, modify, sell, attribution appreciated)

If you build one, send photos. If you sell one, attribution. If you
find a bug, open an issue.

---

## Contact

- Project lead: mokah (GitHub)
- Faire booth: Sept 25–27, 2026, Mare Island, Vallejo CA
- Email: see repo Issues

---

*Made in the open. Tested in the sun. Built from old panels.*
