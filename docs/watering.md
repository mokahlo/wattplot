# Wattplot Smart Planter — Watering + Monitoring Spec (v2.4)

## Overview

The mini v2.4 turns the planter into a fully-instrumented smart garden:

- **Watering**: tap-pressurized water → 12V solenoid → drip emitter.
  No pump, no reservoir, no priming. Fail-safe (closed when de-energized).
- **Sensing**: 3× DS18B20 (panel/soil/battery temp) + 1× capacitive soil
  moisture + INA219 for panel V/I + DPS5005 readback for battery V.
- **Energy monitoring**: integrate panel V×I every 1s → `energy_today_kwh`
  + `energy_total_kwh` (cumulative, capped at 10 MWh).
- **Battery SOC**: voltage → SOC lookup (LiFePO4 4S, 13.6V=100%, 10.5V=0%).
- **POA irradiance**: from solar position (lat/lon/day-of-year/time) +
  panel tilt (current state) + clear-sky model → `poa_irradiance_w_m2`.
  This is the irradiance *the plant actually receives* at the bed's
  soil surface (and the irradiance the panel sees, with the small
  adjustment for incidence angle).

**No internet required** — all decisions are local, using thresholds
in `wattplot_params.py` (MINI dict).

---

## v2.3 → v2.4 changes

| What | v2.3 (pump + bucket) | v2.4 (solenoid + tap) |
|---|---|---|
| Water source | 5-gallon bucket, refill weekly | Tap water (already pressurized) |
| Pump | 12V peristaltic, ~0.5 L/min, $15-20 | none |
| Reservoir | Bucket, 18.9 L, $5 | none |
| Solenoid | none | 12V NC, 1/4", $10-12 |
| Tee on cold line | none | 1/4" brass tee, $3 |
| Pressure regulator | none | optional 5-30 PSI, $10 |
| Total watering | ~$45 | ~$46 (similar) |
| Refill cadence | Weekly in summer | **Never** (tap water is unlimited) |
| Failure mode | Pump run-dry → overheat | Solenoid stuck closed → no water (safer) |
| Energy monitoring | none | panel V×I → kWh, battery SOC, POA |

The big win: **no refilling**, **fail-safe**, and we get full energy
telemetry from the panel + battery for free.

---

## Hardware

### Watering (solenoid on tap)

| Component | Spec | Notes |
|---|---|---|
| Solenoid | 12V DC normally-closed, 1/4" barb, ~2 GPM | Held open by ~4W, fail-safe closed |
| Relay | 1-channel 5V low-level trigger | Switches 12V to solenoid, driven by ESP32 GPIO 5 |
| Tee | 1/4" brass cold-water tee | Taps into existing supply line (e.g. hose bib) |
| Pressure regulator | 5-30 PSI adjustable, 1/4" NPT | Optional, recommended for drip emitter |
| Tubing | 1/4" vinyl, food-safe | Solenoid → drip emitter |
| Drip emitter | Pressure-compensating, 2 GPH | Buried 1" deep in bed soil |
| Power | 12V from main battery | Solenoid draws ~0.33A when held open |

**Where to tee in:** the easiest is a hose bib (outdoor faucet) — the
existing 3/4" thread can take a 1/4" barb adapter. Or under the kitchen
sink on the cold water line. Total run is typically 5-20 ft of 1/4" tubing.

### Sensors (same as v2.3)

| Sensor | Type | Pin | Use |
|---|---|---|---|
| Panel temp | DS18B20 | GPIO 10 (1-Wire) | MPPT temp derating, fold decision |
| Soil temp | DS18B20 | GPIO 10 (1-Wire) | Plant health |
| Battery temp | DS18B20 | GPIO 10 (1-Wire) | Safety cutoff |
| Soil moisture | V1.2 capacitive | GPIO 4 (ADC) | Watering trigger |
| Panel V/I | INA219 (I2C 0x40) | GPIO 8/9 (I2C) | Energy monitoring |
| Battery V | DPS5005 readback | GPIO 20/21 (UART) | SOC calculation |
| Panel tilt | BMI160 (I2C 0x68) | GPIO 8/9 (I2C) | Tilt → POA calculation |

---

## ESP32-C3 Pin Assignments

```
GPIO 5  →  Solenoid relay (low-side switch)
GPIO 4  →  Soil moisture sensor (V1.2 analog out, ADC)
GPIO 10 →  1-Wire data (3× DS18B20 sensors on shared bus, 4.7k pullup)
GPIO 8  →  I2C SDA (BMI160 + INA219)
GPIO 9  →  I2C SCL
GPIO 20 →  DPS5005 UART TX (ESP32 → DPS)
GPIO 21 →  DPS5005 UART RX (DPS → ESP32)
GPIO 6  →  Limit switch 0° (digital input, pullup)
GPIO 7  →  Limit switch 35° (digital input, pullup)
```

---

## Firmware entities (ESPHome)

### Sensors (sensing + monitoring)

| Entity | Type | Source | Notes |
|---|---|---|---|
| `sensor.panel_temp_c` | sensor | DS18B20 #1 | Back of panel |
| `sensor.soil_temp_c` | sensor | DS18B20 #2 | Buried 2" in soil |
| `sensor.battery_temp_c` | sensor | DS18B20 #3 | On battery case |
| `sensor.soil_moisture_pct` | sensor | V1.2 capacitive (calibrated) | 0-100% |
| `sensor.battery_v` | sensor | DPS5005 readback (V) | 12V LiFePO4 |
| `sensor.battery_soc_pct` | sensor | voltage_to_soc(battery_v) | Lookup table |
| `sensor.panel_voltage_v` | sensor | INA219 bus voltage | 17.3V Vmp |
| `sensor.panel_current_a` | sensor | INA219 current | 0.58A Imp |
| `sensor.panel_power_w` | sensor | V × I (computed) | ~10W peak |
| `sensor.energy_today_kwh` | sensor | Integrator, reset at midnight | Daily kWh |
| `sensor.energy_total_kwh` | sensor | Integrator, persists across reboots | Lifetime kWh |
| `sensor.poa_irradiance_w_m2` | sensor | Solar position + tilt + clear-sky | W/m² |
| `sensor.panel_efficiency_pct` | sensor | (V×I) / (POA × area) × 100 | % |
| `sensor.water_ml_today` | sensor | Counter, reset at midnight | mL |
| `sensor.watering_events_today` | sensor | Counter, reset at midnight | count |
| `sensor.last_watering` | sensor | Timestamp | datetime |
| `sensor.current_tilt_deg` | sensor | BMI160 fused with motor count | degrees |

### Binary sensors + switches (control)

| Entity | Type | Source |
|---|---|---|
| `binary_sensor.solenoid_state` | binary_sensor | GPIO 5 high = solenoid energized |
| `binary_sensor.is_night` | binary_sensor | `panel_power_w < 0.5` |
| `switch.watering_solenoid` | switch | GPIO 5 manual override |
| `switch.watering_automation` | switch | Enable/disable auto-watering |

---

## POA irradiance calculation

**POA = Plane of Array irradiance** — the solar power per unit area
hitting the tilted panel surface. This is the *true* input to the
panel (and the same value the plant soil sees, roughly).

The ESPHome firmware computes POA from first principles every minute:

```python
# Pseudo-code (firmware/wattplot.yaml lambda)
def compute_poa(lat, lon, tilt, azimuth, dt):
    # 1. Solar position (NOAA simplified algorithm)
    day_of_year = dt.timetuple().tm_yday
    declination = 23.45 * sin(360/365 * (day_of_year - 81))  # degrees
    hour_angle = 15 * (dt.hour + dt.minute/60 - 12)          # degrees
    # (with longitude correction for solar time)
    altitude = asin(sin(lat)*sin(declination) +
                    cos(lat)*cos(declination)*cos(hour_angle))
    azimuth_sun = atan2(-sin(hour_angle),
                        tan(declination)*cos(lat) - sin(lat)*cos(hour_angle))
    # 2. Air mass (Kasten & Young)
    air_mass = 1 / (sin(altitude) + 0.50572*(6.07995 + altitude)**-1.6364)
    # 3. Clear-sky direct normal irradiance (Ineichen model, simplified)
    dni = 1361 * 0.7 ** (air_mass ** 0.678)  # W/m²
    # 4. Angle of incidence on tilted panel
    aoi = acos(sin(altitude)*cos(tilt) +
               cos(altitude)*sin(tilt)*cos(azimuth_sun - azimuth))
    # 5. POA = direct × cos(aoi) + diffuse × (1 + cos(tilt))/2
    dhi = 0.1 * dni  # diffuse horizontal (rough estimate)
    poa_direct = max(0, dni * cos(aoi))
    poa_diffuse = dhi * (1 + cos(tilt)) / 2
    return poa_direct + poa_diffuse  # W/m²
```

For Phoenix (33.45°N) at noon on the summer solstice, POA on a 0° flat
panel is ~1000 W/m²; on a 35° south-tilted panel is ~920 W/m². The
difference is small because the panel is nearly facing the sun at noon.

**Why this matters for the plant**: DLI (Daily Light Integral) is the
total moles of photons the plant receives per day. The Wattplot can
integrate POA over the day → DLI → plant growth metric. This becomes
the foundation of the long-term "design tool" vision: input your
location, get a recommendation for bed size + panel size to hit a
target DLI for tomatoes (25 mol/m²/day) or herbs (12 mol/m²/day).

---

## Battery SOC calculation

LiFePO4 voltage-to-SOC is highly nonlinear at the top and bottom of
the curve, but flat in the middle. The lookup table in
`wattplot_params.py` is the simplest accurate-enough approach:

```python
# Pseudo-code (firmware/wattplot.yaml lambda)
def voltage_to_soc(v):
    lut = [
        (13.6, 100), (13.4, 95), (13.3, 90), (13.2, 80),
        (13.0, 60), (12.8, 40), (12.5, 20), (12.0, 10), (10.5, 0)
    ]
    if v >= lut[0][0]: return 100
    if v <= lut[-1][0]: return 0
    # Linear interpolation between table points
    for i in range(len(lut) - 1):
        v_hi, soc_hi = lut[i]
        v_lo, soc_lo = lut[i+1]
        if v_lo <= v <= v_hi:
            return soc_lo + (soc_hi - soc_lo) * (v - v_lo) / (v_hi - v_lo)
    return 0
```

The ESPHome version uses a `select` or `lambda` returning the
interpolated value. For higher accuracy, a Coulomb counter (integrate
current in/out) can be added, but for a 7Ah battery the voltage curve
is good enough.

---

## Energy integration

```python
# Pseudo-code (1-Hz loop in firmware)
def integrate_energy():
    p = id(panel_power_w).state  # W (V × I from INA219)
    dt = 1.0  # sec
    delta_kwh = p * dt / 3600 / 1000
    today = id(energy_today_kwh).state + delta_kwh
    total = id(energy_total_kwh).state + delta_kwh
    # cap at 10 MWh to prevent float drift over years
    total = min(total, 10000)
    id(energy_today_kwh).publish(today)
    id(energy_total_kwh).publish(total)
```

`energy_today_kwh` resets at midnight (cron trigger in ESPHome).
`energy_total_kwh` persists across reboots (stored in `preferences`).

---

## Panel efficiency calculation

```python
# Pseudo-code
def compute_efficiency():
    p = id(panel_power_w).state         # W
    poa = id(poa_irradiance_w_m2).state # W/m²
    area_m2 = 0.0697  # 13.3" × 8.1" = 0.088 m², but ~80% of cells
    if poa < 50: return 0  # noise floor at night
    return 100 * p / (poa * area_m2)
```

Expected efficiency for the ECO-WORTHY 10W panel: ~15-18%. If you see
consistently <12%, something's wrong (shading, soiling, bad MPPT, etc.).

---

## Watering automation (1-Hz control loop)

```python
# Pseudo-code (firmware/wattplot.yaml)
def watering_control():
    if not id(watering_automation).state: return  # manual mode
    if id(controller_state).state == "Folding": return  # never water while folding
    if id(solenoid_state).state: return  # already watering

    # Read state
    moisture = id(soil_moisture_pct).state
    panel_t = id(panel_temp_c).state
    bat_v = id(battery_v).state
    bat_soc = id(battery_soc_pct).state
    is_dark = id(is_night).state
    events_today = id(watering_events_today).state

    # Safety blocks
    if panel_t > 45: return  # heat stress
    if bat_v < 11.5: return  # battery too low
    if bat_soc < 20: return  # <20% SOC
    if is_dark: return  # nighttime
    if events_today >= 3: return  # daily limit

    # Decision
    if moisture < 30:  # below dry threshold
        duration_sec = 50  # 100 mL at 2 mL/sec
        run_solenoid(duration_sec)
        id(watering_events_today).publish(events_today + 1)
        id(water_ml_today).publish(water_ml_today + 100)
        log(f"Watered: moisture={moisture:.0f}%, "
            f"events_today={events_today + 1}")
```

**Solenoid behavior:**
- Energized = water flows
- De-energized = water stops (fail-safe)
- 50 sec at 2 mL/sec = 100 mL per event
- Hard-capped at 30 sec by hardware watchdog (won't run away even if
  firmware hangs)

---

## Daily water budget

**Plant needs (1 herb in 0.48 cu ft bed):**
- Phoenix summer: ~1.0-1.3 L/day
- Phoenix winter: ~0.2-0.3 L/day
- Spring/fall: ~0.5-0.7 L/day

**System delivery (solenoid at 2 mL/sec, 100 mL per event, max 3 events/day):**
- 3 events × 100 mL = 300 mL/day = 0.3 L/day
- Winter: plenty (need ~0.3 L/day)
- Spring/fall: a bit short, may need 4-5 events/day in shoulder seasons
- Summer: undersized — user should bump `solenoid_water_volume_ml_default`
  to 200 mL or `solenoid_max_events_per_day` to 5 in summer

(For a larger bed or more plants, scale up: 200 mL events, 5/day, with
the option to use the full `solenoid_max_runtime_sec=30` per event.)

---

## Safety logic

| Check | Threshold | Action |
|---|---|---|
| Panel temp > 45°C | `watering_block_panel_temp_c` | Block (water evaporates too fast) |
| Battery voltage < 11.5V | `watering_block_battery_v` | Block (conserve battery) |
| Battery SOC < 20% | `watering_block_battery_soc_pct` | Block (low energy) |
| Nighttime (panel power < 0.5W) | `watering_block_night` | Block (no charging) |
| Solenoid runtime > 30 sec | `solenoid_max_runtime_sec` | Force off (clogged line protection) |
| Daily events >= 3 | `solenoid_max_events_per_day` | Block (over-watering protection) |
| Controller state == "Folding" | (always) | Block (motor current spike protection) |

**Hard limit:** the solenoid is hard-capped at 30 seconds per event via
a hardware watchdog (ESP32 timer). Even if the firmware hangs, the
solenoid can't run forever.

---

## Manual override

User can always:
- Toggle `switch.watering_solenoid` from Home Assistant to run the
  solenoid manually for X seconds (firmware auto-stops at
  `solenoid_max_runtime_sec`)
- Disable auto-watering with `switch.watering_automation = OFF`
- See watering history in Home Assistant
  (`sensor.water_ml_today`, `sensor.last_watering`)
- Monitor energy: `sensor.energy_today_kwh`,
  `sensor.energy_total_kwh`, `sensor.battery_soc_pct`,
  `sensor.poa_irradiance_w_m2`, `sensor.panel_efficiency_pct`

---

## Wiring diagram (text)

```
                    12V LiFePO4 Battery
                          │
                          │ (12V+)
                          ├──── Solenoid + (red wire)
                          │      │
                       [Relay] ← Solenoid - (black wire)
                          │
                          │ (control coil 5V)
                          │
                       ESP32 GPIO 5
                          │
                       3.3V ── 4.7k ──┬─ 1-Wire bus
                          │           ├─ DS18B20 #1 (panel)
                          │           ├─ DS18B20 #2 (soil)
                          │           └─ DS18B20 #3 (battery)
                          │
                       GND ───────────┴─ (all sensor grounds)

                       INA219 (I2C 0x40)
                          │
                       GPIO 8/9 (I2C) ──  ESP32

                       BMI160 (I2C 0x68)
                          │
                       GPIO 8/9 (I2C) ──  ESP32 (shared bus)

                       DPS5005 (UART, panel V/I feedback + battery V)
                          │
                       GPIO 20/21 (UART) ── ESP32
```

**Solenoid power wiring:**
- 12V+ from battery → relay COM terminal
- Relay NO (normally open) terminal → solenoid + (red)
- Solenoid - (black) → battery 12V- (ground)
- Relay coil + → ESP32 GPIO 5
- Relay coil - → ESP32 GND
- Relay VCC (if needed for logic) → ESP32 5V or 3.3V

**Sensor wiring:**
- All 1-Wire sensors share GPIO 10, GND, and 3.3V (with 4.7k pullup on data)
- Soil moisture: VCC to 3.3V, GND to GND, AOUT to GPIO 4 (ADC)
- I2C sensors: SDA to GPIO 8, SCL to GPIO 9, VCC to 3.3V, GND to GND
  (BMI160 and INA219 on the same bus, different addresses)
- DPS5005: TX/RX crossed to GPIO 20/21, GND to GND

**Plumbing (solenoid on tap water):**
- Cold water supply (hose bib or under-sink pipe) → 1/4" tee
- Tee → 1/4" tubing → pressure regulator (optional) → solenoid INLET
- Solenoid OUTLET → 1/4" tubing → drip emitter (buried 1" in soil)

---

## Build sequence (mini v2.4)

1. Phase 1-9: build bed, frame, panel, kickstand, wire electronics (existing)
2. **Phase 10: Watering system (solenoid on tap)**
   - Locate a cold water tap accessible to the bed (hose bib on patio,
     or 1/4" tee on under-sink cold water line)
   - Cut into the cold water line with the 1/4" tee (shut off water
     first, drain, install tee, restore pressure, test for leaks)
   - Run 1/4" tubing from the tee to where the solenoid will mount
     (typically on the bed's east short wall, near the electronics)
   - (Optional) Install pressure regulator in the tubing run, set to
     ~15 PSI for the drip emitter
   - Mount solenoid on bed's east wall at ~6" height (above any potential
     water splash)
   - Connect solenoid INLET to the supply tubing
   - Run 1/4" tubing from solenoid OUTLET to the bed soil, attach drip
     emitter, insert into soil at 1" depth
   - Wire solenoid through relay to 12V battery and ESP32 GPIO 5
   - Test: toggle `switch.watering_solenoid` from HA for 10 sec,
     verify water flows and stops
3. **Phase 11: Energy + SOC + POA monitoring**
   - Already wired (INA219 on I2C, DPS5005 on UART)
   - Verify in Home Assistant: `sensor.battery_v`, `sensor.battery_soc_pct`,
     `sensor.energy_today_kwh`, `sensor.poa_irradiance_w_m2`,
     `sensor.panel_efficiency_pct`
4. Phase 12: Test & validate (1 week)
   - Monitor soil moisture trends
   - Verify auto-watering fires when soil drops below threshold
   - Verify energy total matches expected (10W × 5 peak sun hours = ~50 Wh/day)
   - Check SOC follows the expected LiFePO4 discharge curve
   - Check POA irradiance peaks at ~1000 W/m² around solar noon
   - Adjust thresholds in `wattplot_params.py` if needed

---

## Adjustable parameters (`wattplot_params.py`)

```python
MINI = dict(
    # ... existing fields ...

    # Watering thresholds (solenoid on tap water)
    soil_moisture_dry_pct=30,        # below this, trigger watering
    soil_moisture_wet_pct=60,        # above this, skip watering
    solenoid_water_volume_ml_default=100,  # per event (~50 sec at 2 mL/sec)
    solenoid_max_events_per_day=3,
    solenoid_max_runtime_sec=30,     # safety watchdog
    solenoid_flow_rate_ml_per_sec=2,  # at ~15 PSI after regulator

    # Safety blocks
    watering_block_panel_temp_c=45,
    watering_block_battery_v=11.5,
    watering_block_battery_soc_pct=20,
    watering_block_night=True,

    # Battery SOC (LiFePO4 4S, voltage → %)
    battery_ah=7,
    battery_soc_lut=[(13.6, 100), (13.4, 95), (13.3, 90), (13.2, 80),
                       (13.0, 60), (12.8, 40), (12.5, 20), (12.0, 10),
                       (10.5, 0)],

    # Energy integration
    energy_integration_interval_s=1,
    energy_total_max_kwh=10000,

    # POA + efficiency
    panel_rated_efficiency_pct=18,
    # panel_area_m2 is computed in firmware from panel_L_in × panel_W_in
)
```

Edit these values, reflash the firmware, and the new thresholds take
effect immediately. No hardware changes needed.

---

## What's next (v2.5+)

- **Coulomb counter**: integrate INA219 current in/out of battery for
  more accurate SOC than voltage lookup. (For 7Ah battery, voltage is
  fine; for full-size 100Ah battery, Coulomb counter is essential.)
- **Weather integration**: pull forecast cloud cover from local NWS,
  scale POA irradiance by cloud factor. (Optional, current clear-sky
  is conservative.)
- **Soil DLI**: integrate POA over the day → DLI (mol/m²/day) for plant
  growth tracking. Pairs with the long-term "design tool" vision.
- **Multi-zone**: scale to 2-4 beds, each with its own ESP32 + sensors
  + solenoid, all reporting to one Home Assistant.
