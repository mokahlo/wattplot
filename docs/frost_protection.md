# Frost Protection

Wattplot v3.3 adds a frost-prevention feature that drives **either** a
resistive heating mat **or** a USB grow light (or both) when soil
and/or canopy air temperature drops below a user-set threshold.

The feature is opt-in: by default the `Frost Mode` select is set to
`Off` and nothing happens. The user picks what to wire up and how to
control it.

## What it does

Every 60 seconds the `frost_tick` interval in `wattplot.yaml`:

1. Reads `Soil Temperature` and `Canopy Air Temperature` (DS18B20
   1-Wire sensors).
2. Reads `Battery SOC` (LiFePO4 voltage lookup).
3. Checks `Frost Mode`:
   - `Off` → both switches forced off, no automation.
   - `Heater` → only the heater relay responds to the temp logic.
   - `Grow Light` → only the grow light relay responds.
   - `Both` → both respond, independently.
4. For each enabled output, applies:

   | State | Condition |
   |---|---|
   | **ON** | `soil < soil_threshold` **OR** `canopy < canopy_threshold` |
   | **OFF** | `soil > warm_above` **AND** `canopy > warm_above` |
   | hold | anything in the deadband (between threshold and warm_above) |

5. Applies a **watchdog** that force-off after
   `frost_max_runtime_min` (default 30 min) — catches a stuck relay
   before it can drain the pack overnight.
6. Applies a **battery floor**: if SOC drops below
   `frost_min_battery_soc` (default 50%), force off. We'd rather
   lose a few plants than brick the LiFePO4 pack.
7. Applies a **sensor-error latch**: if BOTH temperatures are NaN
   at the same tick, the tick disables both switches and reports
   `Sensor error` in the `Frost State` text sensor. The latch
   clears on the next tick that has at least one valid reading.

## Hysteresis

The two thresholds and the `warm_above` parameter form a
**deadband**:

```
        soil/canopy temp
   ^
   |   warm (off)
   |   ─────────────── warm_above (e.g. 6°C)
   |   ░░░░░░░░░░░░░░░░ deadband
   |   ──────────────── threshold (e.g. 4°C)
   |   cold (on)
   v
```

The relay turns ON when either sensor drops **below** its
threshold. It turns OFF only when **both** sensors are **above**
`warm_above`. This deadband prevents relay chatter at the
threshold edge — without it, a sensor reading right at 4.000°C
would oscillate every tick.

The deadband is asymmetric (4°C threshold, 6°C warm_above) so the
load has hysteresis even on slow temperature trends.

## Forecast preheat (NWS)

The `nws_poll` script runs every 15 min and pulls the NWS
forecast for the wattplot's gridpoint (Phoenix
PSR/153,87). The frost tick consumes the forecast and engages
the load **before** the sensors say cold — saves the heater's
first hour of warmup.

### How it works

Every 60 s, the tick computes:

```
forecast_preheat = (
    NWS poll is fresh (< 4 h old)
    AND forecast_min_tonight < frost_forecast_threshold_c
)
```

If `forecast_preheat` is true:

- **Engage**: turn ON the load, even if current sensors are warm.
- **Hold**: keep the load ON overnight, even when the afternoon
  hysteresis arm would release. The forecast committed us to a
  cold night, so we don't release just because it's 7°C at 6 pm.
- **Subject to**: Mode select (off when `Frost Mode = Off`),
  battery floor, watchdog. Forecast does NOT bypass the
  battery floor — a wrong forecast shouldn't kill the pack.

### Why the hysteresis arm is suppressed

A typical scenario: it's 6 pm, the soil is 7°C (above
`warm_above = 6°C`), and the forecast says 0°C tonight. Without
the forecast arm, the hysteresis would release the heater (both
temps > 6°C). Then when temps drop to 4°C at 1 am, the sensor
arm engages, but the heater takes 30+ minutes to warm up the
bed. Plants are already cold by then.

With the forecast arm, the heater stays on from 6 pm through
morning, holding the bed at a warmer temperature. The preheat is
the entire point of consuming the forecast.

### Stale-forecast handling

NWS updates forecasts roughly every 6 hours. A poll that's
older than 4 hours is considered stale and ignored. This
prevents the preheat from running on day-old data (the
forecast was for yesterday's overnight, not tonight's).

A failing NWS poll leaves the previous forecast value intact
(rather than clearing it). Better to act on stale data than
on no data.

### Sensors broken? Forecast still works.

If both DS18B20s return NaN, the sensor-error path normally
force-off. **But** if the forecast is preheating, the tick
drives the load on the forecast alone. The weather outside
doesn't care about our wiring — and the user is more likely
to be troubleshooting the sensors in the morning than in a
cold snap, so the forecast keeps things running until they
can fix the sensor.

### Disable forecast preheat

Set `Frost Forecast Threshold (°C)` to -100. The comparison
`forecast < threshold` is then always false, and the preheat
arm never fires. The tick falls back to sensor-only logic.

## Two watchdog limits

The frost protection has TWO watchdog limits, one per arm:

| Knob | Default | Used when |
|---|---|---|
| `Frost Max Runtime (min)` | 30 | Sensor arm (sensors say cold) |
| `Frost Preheat Max Runtime (min)` | 480 | Forecast arm (NWS says cold) |

The tick picks the right one based on which arm is keeping the
load on:

```cpp
int effective_max_runtime_ms = forecast_preheat
    ? preheat_max_runtime_ms    // 8h default
    : max_runtime_ms;            // 30 min default
```

### Why two limits?

The **sensor arm** limit (30 min) is the safety net for a stuck
relay during an active cold snap. A 30 W heater at 12 V pulls
2.5 A; a 10 Ah LiFePO4 pack dies in 4 hours if the relay is
stuck. The 30 min cap means a stuck relay costs at most 0.8 Ah
before the watchdog trips — leaves plenty of margin for a real
fault.

The **forecast arm** limit (8 h) is for overnight preheat. The
whole point of preheat is to run the heater *for the whole
cold night*, not for 30 minutes. With a 30 min cap, the
preheat would trip at 6:30 am and the bed would freeze by 7.
With an 8 h cap, the preheat can run from 6 pm to 2 am — when
the sun starts to warm the bed again.

### When the limit flips

- **Forecast is cold (preheat)**: uses the preheat cap (8h).
  The overnight preheat can run uninterrupted.
- **Forecast clears (morning)**: switches to the sensor cap
  (30 min) for any subsequent heating. The hysteresis should
  release the load when temps recover, so the watchdog
  rarely fires in this path.
- **Sensor says cold, forecast also says cold**: the load is
  on; the tick uses the LARGER cap (preheat = 8h). This
  keeps the load on overnight even though the sensor arm
  was the trigger.

### Power budget at the limits

For the wattplot mini (10 W panel, 12 V 10 Ah LiFePO4 pack):

| Load | Power | 8h runtime | Pack drain |
|---|---|---|---|
| 30 W heating mat | 30 W | 240 Wh | 200% of pack — pack dies |
| 10 W USB grow light | 10 W | 80 Wh | 67% of pack — pack survives |
| 5 W LED panel | 5 W | 40 Wh | 33% of pack — pack comfortable |

A 30 W heater at the default 8 h preheat will deplete the
battery. **For overnight preheat, use a 5-10 W load (USB grow
light or low-power LED panel)**, not a 30 W mat. The battery
floor (`Frost Min Battery SOC (%)`, default 50%) trips first
for a heater that draws more than the pack can supply
overnight.

For the full-size build (larger battery, 620 W panel), the
battery floor and the watchdog are both fine. The 30 W mat
can run a full night if the pack is sized accordingly.

## Hardware

The firmware does NOT include the relay or the load. The ESP32
just drives a logic-level GPIO; you wire your own relay.

### Pin assignments

| GPIO | Output ID | Switch | Use |
|---|---|---|---|
| 39 | `frost_heater_out` | `Frost Heater` | Heater relay (default) |
| 40 | `frost_grow_light_out` | `Frost Grow Light` | Grow light relay |

Both are pulled LOW by default. Drive HIGH to energize the load
through your external relay.

### Wiring the heater (12V resistive mat)

A 30W heating mat at 12V draws ~2.5A. The wattplot's
Sunapex 10A MPPT has plenty of headroom, but the relay MUST
switch the 12V load, not the GPIO. Recommended:

- **Logic-level N-MOSFET** (e.g. AO3401A, IRLZ44N) on a small
  perfboard. Source to GND, drain to relay coil (or directly to
  the low side of a resistive load if you skip the relay). Gate
  to GPIO39 via a 100Ω gate resistor.
- **Or a 12V automotive relay module** (the kind with a screw
  terminal block, ~$3). Drive the relay coil from GPIO39 through
  a 1kΩ base resistor if the module's input is BJT-based, or
  direct if it's MOSFET-based. The relay's switched contact
  handles the heating mat.

The heating mat goes in the bed on top of the soil, covered by
mulch. The soil-temperature sensor sits in the soil at 5 cm depth
within ~30 cm of the mat so the control loop is closed on the
temperature the mat is actually warming.

### Wiring the USB grow light (5V)

The wattplot's PCB already carries 5V (the MP1584EN buck
output). Tap that rail through a low-side N-MOSFET to a USB-A
jack, or use a 5V relay module. Most USB grow light panels
draw 0.5-2A at 5V (2.5-10W) and provide a few degrees of
radiant heat.

For a 12V grow light panel (more common, brighter, more heat):
drive a 12V relay from GPIO40 the same way as the heater.

### Power budget

| Load | Voltage | Current | Wattage |
|---|---|---|---|
| 30W heating mat | 12V | 2.5A | 30W |
| 10W USB grow light | 5V | 2A | 10W |
| Both (worst case) | mixed | mixed | 40W |

At 40W the LiFePO4 pack (10Ah × 12V = 120Wh) lasts ~3 hours.
The default 30-min watchdog will trip first — that's the point.
A cold snap that lasts 4 hours will see two watchdog cycles.

## Sensors required

- `Soil Temperature` (DS18B20, 5cm depth, waterproof) — required
- `Canopy Air Temperature` (DS18B20, in plant canopy) —
  recommended; without it, only the soil sensor drives the
  decision. The sensor has placeholder address `0x0000000000000000`
  in `wattplot.yaml` — wire the third probe and replace the
  address with the real ROM ID from the bus scan log.

If only one of the two sensors is wired, the tick uses whichever
one is valid. The behavior is symmetric — the same NaN guard
that handles a wiring fault also handles a single-sensor build.

## Tunable parameters

All five are `number:` entities in Home Assistant. The defaults
are tuned for Phoenix, AZ (USDA zone 9b, design temp 25°F /
-4°C). Tighter for spring transplants, looser for mature fall
plants.

| Parameter | Default | Range | What it controls |
|---|---|---|---|
| `Frost Soil Threshold (°C)` | 4.0 | -5 to 10 | Below this → turn ON |
| `Frost Canopy Threshold (°C)` | 2.0 | -5 to 10 | Below this → turn ON |
| `Frost Warm-Above (°C)` | 6.0 | 0 to 15 | Above this (both) → turn OFF |
| `Frost Max Runtime (min)` | 30 | 5 to 240 | Watchdog (sensor arm) |
| `Frost Preheat Max Runtime (min)` | 480 | 30 to 1440 | Watchdog (forecast arm) |
| `Frost Min Battery SOC (%)` | 50 | 10 to 80 | Force off below this |
| `Frost Forecast Threshold (°C)` | 2.0 | -20 to 10 | NWS forecast preheat trigger |

## Frost State text sensor

`Frost State` is a 5-second-updated text sensor that surfaces the
most recent decision. Values:

| Value | Meaning |
|---|---|
| `Off` | `Frost Mode` is `Off`, automation is disabled |
| `Standby` | Mode is enabled but temps are above threshold |
| `Heater` | Heater relay is energized |
| `Grow Light` | Grow light relay is energized |
| `Both` | Both relays are energized |
| `Battery low` | SOC below floor; both forced off |
| `Sensor error` | Both temps NaN; latched until a sensor recovers |

## Logging

The frost tick logs every state change at INFO level under the
`frost` tag. Watchdog trips log at WARN. Sensor errors log at
ERROR (once per latch, not once per tick). To see these in the
HA log, make sure the `mqtt.log_topic: "wattplot/log"` config is
in place — the local log subscriber at
`tools/log_subscriber.py` writes them to `logs/wattplot.log`.

## Manual control

Set `Frost Mode` to `Off` and the two switches (`Frost Heater`,
`Frost Grow Light`) become purely manual — they can be toggled
from HA and the tick will leave them alone. Useful for:

- Testing the wiring before trusting automation
- Running the heater outside the frost logic (e.g. to dry out
  the bed after a long rain)
- Forcing the lights on during a heat wave (some growers shade
  with reflective material under the lights)

## Limitations

- **NWS forecast errors cost the battery.** The forecast is
  sometimes wrong. If NWS says -5°C and the actual low is +2°C,
  the heater runs for hours for nothing. The `Frost Preheat
  Max Runtime` watchdog (default 480 min = 8h) caps the
  damage. For full overnight coverage, use a low-wattage load
  (5-10 W LED panel) — see the power budget table above.
- **No flat-panel-on-frost optimization.** At 35° tilt the
  panel shades most of the bed, which slows solar heating the
  next morning. The frost tick doesn't change tilt; the user
  can drop `Commanded Tilt` to 0° manually if they want the
  bed to catch morning sun sooner.
- **Soil moisture is not a guard.** The tick will run the heater
  even if the soil is bone-dry, which is fine (the frost
  protection takes priority) but the user should still run the
  irrigation automation. They're independent.

## Tests

`firmware/tests/test_frost_state.py` ports the C++ lambda to
Python and pins the behavior with 50 tests:

- Mode select (Off / Heater / Grow Light / Both)
- Threshold + hysteresis logic
- Forecast preheat (engages, holds against hysteresis, ignores
  stale forecasts, respects battery floor and mode gating,
  drives load with sensors broken, subjected to watchdog)
- NaN guards (single + both sensors)
- Battery floor (low SOC, NaN SOC, at-floor)
- Watchdog (under, at, over, per-output independence)
- End-to-end overnight cycle, cold snap with sensor dropout,
  battery-during-event

`firmware/tests/test_nws_parser.py` ports the C++ JSON parser
in the `nws_poll` script and pins the behavior with 15 tests:

- Wind speed extraction (basic, range, max across periods,
  missing field)
- Rain forecast detection (Rain, Showers, no rain, partial
  match quirk)
- Min temp extraction (first overnight, subsequent ignored,
  no overnight in 12 periods, missing isDaytime quirk)

Run with:

```bash
pytest firmware/tests/test_frost_state.py firmware/tests/test_nws_parser.py -v
```

The wattplot.yaml is the source of truth — if you change the C++
in the `frost_tick` lambda or `nws_poll` script, update the
Python port and add a test for the new behavior.

## Wiring up the canopy sensor (third DS18B20)

The 1-Wire bus on GPIO16 currently has 2 sensors (panel back,
soil). To add a third:

1. Wire the canopy probe to the same bus (parallel with the
   other two, single 4.7kΩ pull-up stays in place).
2. Power up the wattplot and watch the boot log:

   ```
   [one_wire] found device 0x....
   ```

3. Copy the third address into `wattplot.yaml`:

   ```yaml
   - platform: dallas_temp
     one_wire_id: panel_temp_bus
     address: 0x<real_address_here>   # <-- replace placeholder
     name: "Canopy Air Temperature"
     id: canopy_temperature
     ...
   ```

4. The placeholder `0x0000000000000000` will read as `127.0°C` if
   the address is wrong — easy to spot in HA.
