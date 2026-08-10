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
| `Frost Max Runtime (min)` | 30 | 5 to 240 | Watchdog force-off |
| `Frost Min Battery SOC (%)` | 50 | 10 to 80 | Force off below this |

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

- **No forecast awareness yet.** The tick reacts to current
  sensor readings, not the NWS forecast. The `nws_poll_interval`
  does pull the forecast (wind + rain) every 15 min but the frost
  automation doesn't read those globals. A "preheat if NWS says
  < 0°C tonight" feature is a clean follow-on.
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
Python and pins the behavior with 31 tests:

- Mode select (Off / Heater / Grow Light / Both)
- Threshold + hysteresis logic
- NaN guards (single + both sensors)
- Battery floor (low SOC, NaN SOC, at-floor)
- Watchdog (under, at, over, per-output independence)
- End-to-end overnight cycle, cold snap with sensor dropout,
  battery-during-event

Run with:

```bash
pytest firmware/tests/test_frost_state.py -v
```

The wattplot.yaml is the source of truth — if you change the C++
in the `frost_tick` lambda, update the Python port and add a
test for the new behavior.

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
