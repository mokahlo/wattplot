# Wattplot, Poster Concept (24×36 vertical)

> **STALE — references the retired `BedSun` (90°) "sun" mode and the
> BMI160 IMU. Both are gone in v3.2.** Update the mode list before
> printing; the rest of the framing is fine. See `firmware/README.md`
> for current behavior.

> This is the **text and layout** for the booth poster. Send to a
> designer (Fiverr, local student) for visual execution. Print at
> FedEx Kinko's on foam core, ~$40.

## Headline (re-framed for upcycling)

Old solar panels are a growing waste stream. Wattplot gives them a
second life: shade + food + some power, in a planter you build from
8-ft lumber stock. Bring your own panel, 8×5 ft fits any
residential.

## Layout

```
┌────────────────────────── 24" ──────────────────────────┐
│  ┌──────────────────────────────────────────────────┐   │
│  │  WATTPLOT                                          │   │
│  │  Give an old panel a second life.                  │   │
│  │  Shade + food + power, in one raised bed.          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                            │
│  ┌──────────────────────────┐  ┌────────────────────┐    │
│  │                          │  │  WHAT IT IS        │    │
│  │  [ LARGE RENDER:         │  │                    │    │
│  │    iso view of full-size │  │  Up to 8 ft × 5 ft │    │
│  │    with old salvage      │  │  raised bed with   │    │
│  │    panel, tomato plants, │  │  a hinged solar    │    │
│  │    full sun ]            │  │  canopy.           │    │
│  │                          │  │                    │    │
│  │  Use: wattplot_v2_iso.png│  │  Fits any panel    │    │
│  │                          │  │  up to 97"×61".    │    │
│  │  Caption: "Old 250W      │  │  Bring your own.   │    │
│  │   panel, 12 years        │  │                    │    │
│  │   retired from a         │  │  5 panel presets:  │    │
│  │   rooftop. Now grows     │  │  60-cell, 72-cell, │    │
│  │   tomatoes in Phoenix."  │  │  96-cell, 1m65,    │    │
│  │                          │  │  new bifacial.     │    │
│  └──────────────────────────┘  └────────────────────┘    │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  HOW IT WORKS (one-line summary)                  │  │
│  │  sun → panel → MPPT → battery + microinverter     │  │
│  │  controller: rain / wind / soil / sun → tilt       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────┐  │
│  │  [ render:       │  │  [ render:       │  │  $193  │  │
│  │    flat (storm)  │  │    35° (power)   │  │  mini  │  │
│  │    at 0° ]       │  │    at 35° ]      │  │  on    │  │
│  │                  │  │                  │  │  the   │  │
│  │  STORM FOLD      │  │  POWER MODE      │  │  table │  │
│  │  high wind       │  │  tilt for max    │  │        │  │
│  │  → flat          │  │  annual kWh      │  │  $1400 │  │
│  │                  │  │                  │  │  full- │  │
│  │  wattplot_v2_    │  │  wattplot_v2_    │  │  size  │  │
│  │  flat_iso.png    │  │  iso.png         │  │        │  │
│  └──────────────────┘  └──────────────────┘  └────────┘  │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  WHY UPCYCLE?                                     │  │
│  │  ~10M tons of panel waste by 2050 (IRENA).         │  │
│  │  Most panels are removed because the racking       │  │
│  │  or inverter failed, not the cells.                │  │
│  │  A 12-year-old 250W panel is still 235W.           │  │
│  │  Wattplot: a second life that delays recycling     │  │
│  │  by 10-20 years and recovers 50-90% of original.   │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  THE SMART CONTROLLER (decision stack)            │  │
│  │  1. user override  2. safety  3. NWS rain         │  │
│  │  4. NWS wind  5. soil wet  6. soil dry           │  │
│  │  7. time-of-day  8. mode (power / sun / track)   │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │  GITHUB          │  │  OPEN SOURCE · MIT ·         │  │
│  │  [QR code →      │  │  parametric · code-first     │  │
│  │  repo]           │  │  5 panel presets ·           │  │
│  │                  │  │  sun sim · wind sim · IMU    │  │
│  │                  │  │                              │  │
│  │                  │  │  github.com/mokahlo/wattplot │  │
│  └──────────────────┘  └──────────────────────────────┘  │
│                                                            │
└────────────────────── 36" ───────────────────────────────┘
```

## Color & type

- **Background:** off-white (#F8F4E9) or matte black (#1A1A1A).
  Off-white reads better in daylight. Matte black pops under spotlights.
- **Title font:** 96pt, sans-serif bold, dark.
- **Body font:** 24-32pt, sans-serif regular.
- **Numbers ($193, 2,240 kWh, 84 kg):** 64pt, bold, accent color.
- **QR code:** 4"×4" minimum, high-contrast, in the bottom corner.

## Source files

- **Renders used:** `renders/wattplot_v2_iso.png`, `renders/wattplot_v2_flat_iso.png`,
  `renders/wattplot_v2_east.png`, `renders/wattplot_v2_top.png`,
  `renders/sun_simulator_monthly_dli.png` (if you want a data viz),
  `renders/wind_load_forces.png` (optional).
- **QR code:** generate from the GitHub repo URL using
  <https://www.qrcode-monkey.com/>. 4-color (black on white) is fine.

## Designer hand-off

Send this `POSTER.md` plus the renders to a designer. Ask for:
- 24"×36" vertical, 300 DPI print-ready PDF
- Editable source (Figma, Illustrator, or InDesign)
- Two rounds of revision

**Budget:** $100-200 on Fiverr for a clean technical poster. Or
ask a local design student; this is a portfolio piece for them.

## Print

- **FedEx Kinko's:** 24×36 poster, $20-40 depending on paper
  (matte vs. glossy). Mount on foam core, +$10.
- **Vistaprint:** Same size, similar price, longer lead time.
- **Local print shop:** Often the cheapest, ask.

Order 2-3 weeks before the faire.
