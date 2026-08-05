# Wattplot Basic — fixed-tilt build (no electronics)

The Basic tier is the same bed, frame, hinges, and panel clamps as the
Smart build — but the tilt is set by hand with a pinned prop strut
instead of a linear actuator. No ESP32, no PCB, no wiring beyond the
panel leads to your charge controller. This is the weekend build and
the natural home for a salvaged panel (see [`upcycling.md`](upcycling.md)).

**What you skip vs. the Smart build:** actuator, actuator mount blocks,
ESP32/PCB, IMU, INA219, soil sensor, all firmware. Everything else in
[`build_guide.md`](build_guide.md) applies — follow it and substitute
Phase "actuator install" with the strut below.

## The pinned strut

Two 2x4 struts (one per cross-rail end, both cut from a single
2x4x8ft board — square cuts only, per the design rules) prop the
frame's north rail:

- **Top end:** square cut, butts under the north rail against a 2x4
  stop block screwed to the rail.
- **Bottom end:** sits in a 2x4 shoe screwed to the bed's north wall.
- **Lock:** a ½" steel pin (same rod stock as the hinge pin) through
  the shoe and strut. One hole per tilt angle.

Tilt stops: **0° (stowed flat), 15°, 25°, 35° (max)** — matching
the tilt schedule presets in the sun simulator, so the annual-yield
numbers in the sim apply directly. 35° is the structural ceiling: with
the panel up on 72" posts, the wind calc passes SF ≥ 2.0 only to 35° at
the design wind. Set it seasonally: steeper in winter, shallower
in summer, or just leave it at 25° year-round and lose only a few
percent annually.

## Storm stow (do this — it's your wind safety)

The Basic build has no auto-fold. **You are the fold controller.**

Before any forecast of sustained winds above ~40 mph or gusts above
~55 mph:

1. Pull both strut pins.
2. Lower the frame flat onto the bed walls (0° stop).
3. Re-pin both struts in the 0° holes so the frame can't be lifted by
   gusts.

At 0° the panel carries essentially zero uplift and drag (see
[`../analysis/wind_load_report.md`](../analysis/wind_load_report.md) —
the 0° row is the whole story). Deployed, the structure is engineered
for the ASCE 7-22 design wind (115 mph, Exposure C) with SF ≥ 2 up to
35° tilt (~130 mph rated at 35°, 25.5" soil fill) —
but stowing is free, takes two minutes, and turns a marginal night
into a non-event. If a named storm is coming, stow.

## Cost

The delta vs. the Smart BOM: subtract the actuator (~$40), electronics
(~$40–80), and PCB. With a salvaged residential panel (often free to
$50 on Craigslist), the Basic build lands in the **$400–650** range
depending on lumber choice (PT pine vs. cedar). See [`../bom.md`](../bom.md).

## Upgrade path

Drill the strut holes even if you plan to go Smart later — a Smart
build with strut holes degrades gracefully to a pinned Basic build if
the electronics come off, and the struts double as a mechanical backup
prop while you're bench-testing the actuator.
