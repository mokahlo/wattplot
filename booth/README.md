# Wattplot, Maker Faire Bay Area 2026, Booth Package

> **Show:** Sept 25–27, 2026 (Fri–Sun), 47 days from today (2026-08-09).
> **Venue:** Historic Mare Island Naval Shipyard, Vallejo CA.
> **Booth:** 10×10 ft (typical BA Faire Maker space).
> **Demo shape:** Working Mini v2.4 on a table, 24" live-sim screen next to it,
>   printed poster, take-home cut-list cards.
>
> **Project week: W3 of 9.** Mini is built and on the bench. Calibrating
> IMU + running closed-loop tilt tests this week. Collateral (poster,
> cards) prints W4. Dry runs W5–W7. Travel/pack W8. Final fixes W9.

## Why this booth

- **The story is optimization.** Two outputs — tomatoes and kilowatt-hours
  — from the same square foot. The panel canopy is what the frame would
  have been lumber for anyway, so the bed is doing more work, not the
  panel displacing the garden. (Sustainability angle: ~10M tons of solar
  panel waste by 2050, and a Wattplot gives any decommissioned panel a
  job. Strong hook for the Maker Faire audience without being the lead.)
- **Mini v2.4 fits the 10×10 footprint** (it's 18×14×12 inches on a table).
- **It's fully functional**, not a render: real panel, real MPPT, real
  actuator, real sensors, real soil. The "wow" moment is a kid pressing a
  button and the panel tilting to follow the sun.
- **Fits any panel up to 8×5 ft**, bring your own 60-cell, 72-cell,
  commercial 96-cell, or new bifacial. Five validated presets, with
  custom-panel support. See `docs/upcycling.md`.
- **Open-source, code-first**, every part of the build is in the repo.
  This is the "ask" for a Maker Faire audience.

## What's in this directory

| File | What it is |
|---|---|
| `PARTS_STATUS.md` | What's already on hand vs. what to order this week. **Order ASAP, build before the faire.** |
| `DEMO_SCRIPT.md` | The 30-second, 2-minute, and 5-minute booth script. What to say, what to point at, what to press. |
| `FAQ.md` | Anticipated questions from faire visitors + crisp answers. |
| `ONE_PAGER.md` | The 8.5×11 take-home (markdown source, prints to PDF). |
| `CUT_LIST_CARD.md` | The 4×6 take-home, the 7 cut lengths on one card. |
| `POSTER.md` | The 24×36 poster concept (text + layout, ready for design pass). |
| `viewer.html` | Interactive 3D viewer (booth-friendly, with auto-rotate + tilt slider). |
| `sim_dashboard.html` | Live-sim dashboard: kWh, DLI, tilt, soil, wind, battery. Stand-alone, no ESP required. |

## Timeline (working backward from Sept 25)

| Week | Dates | Goal |
|---|---|---|
| W1 | Jul 23 – Jul 29 | **Order remaining parts.** Booth package foundation (this dir). |
| W2 | Jul 30 – Aug 5  | **Build the Mini v2.4** (~3-4 hrs). First flash of ESPHome. |
| W3 | Aug 6 – Aug 12  | Calibrate IMU. Closed-loop test. Fill `renders/build_photos/`. |
| W4 | Aug 13 – Aug 19 | Booth collateral: poster printed, cards printed, viewer polished. |
| W5 | Aug 20 – Aug 26 | Dry runs. Practice the demo script. Make a "backup mini" if time allows. |
| W6 | Aug 27 – Sep 2  | Rehearsals. Tighten the demo. Write the speaker notes. |
| W7 | Sep 3 – Sep 9   | Rehearse for friends. Watch for things that confuse people. |
| W8 | Sep 10 – Sep 16 | Pack list. Travel plan. Final hardware burn-in (run for 48 hrs straight). |
| W9 | Sep 17 – Sep 24 | Travel setup. Final fixes. |
| Faire | Sep 25 – 27 | **Mare Island, Vallejo.** Setup Fri 8am, open 10am. |

## Booth layout (10×10)

```
        ┌────────────────────────── 10 ft ──────────────────────────┐
        │                                                            │
        │  ┌────────────┐   ┌──────────────────────┐                 │
        │  │  POSTER    │   │  24" SCREEN          │                 │
        │  │  24×36     │   │  sim_dashboard.html  │                 │
        │  │  vertical  │   │                      │                 │
        │  └────────────┘   └──────────────────────┘                 │
        │                                                            │
        │        ┌──────────────────────────────────┐                │
        │        │  TABLE (30" deep, 6 ft wide)     │                │
        │        │  [ MINI v2.4 + sun lamp ]        │                │
        │        │  [ push-button → panel tilts ]   │                │
        │        └──────────────────────────────────┘                │
        │                                                            │
        │  [ 3D viewer on laptop, 14" ]                              │
        │  [ take-home cards stacked ]                               │
        │  [ 1-2 stools for visitors ]                               │
        │                                                            │
        └────────────────────────────────────────────────────────────┘
```

Two operators minimum (so one can always be at the table when the other
is at the poster or in the restroom). Bring a printed run-of-show with
contact numbers.

## Budget

| Item | Cost |
|---|---|
| Remaining Mini v2.4 parts (~$150 from `PARTS_STATUS.md`) | $150 |
| 24" portable monitor (used, refurbished OK) | $120 |
| Poster print, 24×36, foam-core mounted (FedEx Kinko's) | $40 |
| Take-home cards, 4×6, 500 ct (Vistaprint) | $35 |
| Sun lamp (clamp-on, for the indoor demo) | $20 |
| Pushbutton + wire (for hand-on interaction) | $5 |
| Travel + lodging (3 nights, Vallejo/SF) | $700 |
| Booth fee (already paid via `make.co`) | $0 |
| **Total** | **~$1,070** |

> If the 24" monitor is already in hand, drop that line. If a friend has
> a spare, ask. Maker Faire is the wrong place to discover your monitor
> is dead.

## Constraints (from the venue + the project)

- **No open flames, no propane, no welding.** Wood + 12V only. Easy.
- **10×10 max booth footprint.** No roof, no walls, just canopies allowed
  in some areas, check the faire rules.
- **WiFi is unreliable at Mare Island.** The sim_dashboard is a
  stand-alone HTML page that runs offline. No cloud, no streaming, no
  surprises.
- **The Mini v2.4 runs on its own battery** (12V 7Ah LiFePO4). It can
  demo for ~6 hours without a charge. The sun lamp is for the
  "indoor demo" only, outdoors the sun does the work.

## How to run the booth

1. **Arrive 2 hours before doors open.** Setup is faster than you think.
2. **Test the demo at the booth before the first visitor walks up.**
3. **30-second version** is for the casual walk-by. **5-minute version**
   is for the curious maker who wants to see the firmware.
4. **Hand every visitor a take-home card.** "Scan the QR, the build
   guide is free." This is the most important booth action.
5. **Trade contact info** with the people who say "I'm going to build
   one." Email them after the faire with the repo link and offer to
   answer questions.

See `DEMO_SCRIPT.md` for the actual talk track.

---

## Running the booth

The two HTML pages (`viewer.html`, `sim_dashboard.html`) load STL /
SVG files via `fetch()`. Chrome blocks `fetch()` over `file://`, so
serve the `booth/` directory over HTTP at the booth.

```bash
# On the booth laptop, in a terminal:
cd booth
python -m http.server 8000

# Then open:
#   http://localhost:8000/viewer.html         (3D viewer)
#   http://localhost:8000/sim_dashboard.html  (live sim)
```

> **Pre-fair checklist:** run this on the booth laptop the night
> before, take a screenshot of each, and verify they render. WiFi
> at Mare Island is unreliable, but `localhost` is local and
> always works. Do not depend on a hosted CDN at the faire
> (the 3D viewer uses `unpkg.com` for Three.js, cache the
> assets offline before you go).

### Offline-ready Three.js (recommended)

If you want to be 100% offline at the booth:

```bash
# Once, on a network connection:
mkdir -p booth/vendor/three
curl -L https://unpkg.com/three@0.160.0/build/three.module.js \
  -o booth/vendor/three/three.module.js
# (recreate the subfolders: controls/, loaders/, and copy the
#  needed .js files; ~30 small files total)

# Then edit viewer.html to use ./vendor/three/ instead of
# https://unpkg.com/three@0.160.0/
```

> Easier alternative: bring a personal hotspot. The unpkg CDN is
> small and only loads once.
