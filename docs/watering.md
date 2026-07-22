# Wattplot Smart Planter — Watering System Spec (v2.3)

## Overview

The mini v2.3 adds a closed-loop watering system. The ESP32 reads soil
moisture (and other sensor data), decides when to water, and switches a
12V peristaltic pump via a relay.

**No internet required** — all decisions are local, using thresholds
in `wattplot_params.py` (MINI dict).

---

## Hardware

| Component | Spec | Notes |
|---|---|---|
| Pump | 12V DC peristaltic, ~8 mL/sec | Food-safe, no contamination, self-priming |
| Relay | 1-channel 5V low-level trigger | Switches 12V to pump, driven by ESP32 GPIO 5 |
| Reservoir | 5-gallon bucket, 18.9 L | ~14 days autonomy at 1.3 L/day |
| Tubing | 1/4" vinyl, food-safe | Pump outlet → drip emitter in bed |
| Drip emitter | Pressure-compensating, 2 GPH | Buried 1" deep in bed soil |
| Power | 12V from main battery | Pump draws ~0.5A when running |

## ESP32-C3 Pin Assignments

```
GPIO 5  →  Relay IN (low-side switch, pump control)
GPIO 4  →  Soil moisture sensor (V1.2 analog out, ADC)
GPIO 10 →  1-Wire data (all 3 DS18B20 sensors on shared bus, 4.7k pullup)
GPIO 8  →  I2C SDA (BMI160 + INA219)
GPIO 9  →  I2C SCL
GPIO 20 →  DPS5005 UART TX (ESP32 → DPS)
GPIO 21 →  DPS5005 UART RX (DPS → ESP32)
GPIO 6  →  Limit switch 0° (digital input, pullup)
GPIO 7  →  Limit switch 35° (digital input, pullup)
```

1-Wire bus (GPIO 10) carries three sensors:
- **Panel temp** (back of panel, attached with thermal tape)
- **Soil temp** (buried 2" deep in bed soil)
- **Battery temp** (taped to 12V LiFePO4 case)

Each DS18B20 has a unique 64-bit ROM ID burned at the factory. ESPHome
auto-discovers them by ID. The first-discovered device is assumed to be
the panel, the second soil, the third battery. (Order can be verified in
the serial log at boot.)

---

## Firmware entities (ESPHome)

| Entity | Type | Source |
|---|---|---|
| `sensor.panel_temp_c` | sensor | DS18B20 #1 (panel back) |
| `sensor.soil_temp_c` | sensor | DS18B20 #2 (soil) |
| `sensor.battery_temp_c` | sensor | DS18B20 #3 (battery) |
| `sensor.soil_moisture_pct` | sensor | V1.2 capacitive (analog 0-100%) |
| `sensor.battery_v` | sensor | DPS5005 readback (V) |
| `sensor.water_ml_today` | sensor | Counter, reset at midnight |
| `sensor.watering_events_today` | sensor | Counter, reset at midnight |
| `sensor.last_watering` | sensor | Timestamp of last watering event |
| `binary_sensor.pump_state` | binary_sensor | GPIO 5 high = pump on |
| `switch.watering_pump` | switch | GPIO 5 manual override (for Home Assistant) |
| `switch.watering_automation` | switch | Enable/disable auto-watering |

---

## Automation logic (1-Hz control loop)

```python
# Pseudo-code (firmware/wattplot.yaml)
def watering_control():
    if not id(watering_automation).state:
        return  # automation disabled, only manual

    if id(controller_state).state == "Folding":
        return  # never water while folding (motor is busy)

    if id(pump_state).state:
        return  # pump already running, don't restart

    # Read current state
    moisture = id(soil_moisture_pct).state
    panel_t = id(panel_temp_c).state
    bat_v = id(battery_v).state
    is_dark = id(panel_power_w).state < 0.5  # ~nighttime
    events_today = id(watering_events_today).state

    # Safety blocks
    if panel_t > 45:  # heat stress, water evaporates too fast
        return
    if bat_v < 11.5:  # battery too low
        return
    if is_dark:  # no solar charging
        return
    if events_today >= 3:  # daily limit
        return

    # Decision: water if too dry
    if moisture < 30:  # below dry threshold
        # Trigger watering event
        run_pump(duration_sec=12)  # ~100 mL
        log("Watered: moisture={moisture:.0f}%")
```

The pump runs for 12 seconds = ~100 mL. Adjust `pump_water_volume_ml_default`
in `wattplot_params.py` to change.

---

## Daily water budget

**Plant needs (1 herb in 0.48 cu ft bed):**
- Phoenix summer: ~1.0-1.3 L/day
- Phoenix winter: ~0.2-0.3 L/day
- Spring/fall: ~0.5-0.7 L/day

**Reservoir (18.9 L bucket):**
- Summer: ~14-19 days autonomy
- Winter: ~63-95 days autonomy
- Refill every ~2 weeks in summer

**Daily watering events (max 3):**
- Each event: 100 mL = 0.1 L
- 3 events/day = 0.3 L/day max
- That's enough for winter; in summer the user may need to refill weekly
  and increase events to 4-5 per day

---

## Safety logic

| Check | Threshold | Action |
|---|---|---|
| Panel temp > 45°C | `watering_block_panel_temp_c` | Block (water evaporates too fast) |
| Battery voltage < 11.5V | `watering_block_battery_v` | Block (conserve battery) |
| Nighttime (panel power < 0.5W) | `watering_block_night` | Block (no charging) |
| Pump runtime > 30 sec | `pump_max_runtime_sec` | Force off (clogged line protection) |
| Daily events >= 3 | `pump_max_events_per_day` | Block (over-watering protection) |
| Controller state == "Folding" | (always) | Block (motor current spike protection) |

**Hard limit:** the pump is hard-capped at 30 seconds per event via a
hardware watchdog (ESP32 timer). Even if the firmware hangs, the pump
won't run forever.

---

## Manual override

User can always:
- Toggle `switch.watering_pump` from Home Assistant to run the pump
  manually for X seconds (firmware auto-stops at `pump_max_runtime_sec`)
- Disable auto-watering with `switch.watering_automation = OFF`
- See watering history in Home Assistant
  (`sensor.water_ml_today`, `sensor.last_watering`)

---

## Wiring diagram (text)

```
                    12V LiFePO4 Battery
                          │
                          │ (12V+)
                          ├──── Pump + (red wire)
                          │      │
                       [Relay] ← Pump - (black wire)
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
```

**Pump power wiring:**
- 12V+ from battery → relay COM terminal
- Relay NO (normally open) terminal → pump + (red)
- Pump - (black) → battery 12V- (ground)
- Relay coil + → ESP32 GPIO 5
- Relay coil - → ESP32 GND
- Relay VCC (if needed for logic) → ESP32 5V or 3.3V (depends on relay module)

**Sensor wiring:**
- All 1-Wire sensors share GPIO 10, GND, and 3.3V (with 4.7k pullup on data)
- Soil moisture: VCC to 3.3V, GND to GND, AOUT to GPIO 4 (ADC)
- I2C sensors: SDA to GPIO 8, SCL to GPIO 9, VCC to 3.3V, GND to GND

---

## Build sequence (mini v2.3)

1. Phase 1-9: build bed, frame, panel, kickstand, wire electronics (existing)
2. **Phase 10: Watering system**
   - Mount pump next to bed (on workbench or shelf)
   - Place reservoir next to pump
   - Cut 4-6 ft of 1/4" vinyl tubing
   - Connect one end to pump outlet, run to bed, attach drip emitter, insert into soil
   - Connect pump inlet to reservoir (submerge end in water)
   - Wire pump through relay to 12V battery and ESP32 GPIO 5
   - Test: toggle `switch.watering_pump` from HA, verify water flows

3. Phase 11: Test & validate
   - Run 1 week, monitor soil moisture trends in Home Assistant
   - Verify auto-watering fires when soil drops below threshold
   - Check water consumption vs expected
   - Adjust thresholds in `wattplot_params.py` if needed

---

## Adjustable parameters (`wattplot_params.py`)

```python
MINI = dict(
    # ... existing fields ...
    
    # Watering thresholds
    soil_moisture_dry_pct=30,        # below this, trigger watering
    soil_moisture_wet_pct=60,        # above this, skip watering
    pump_water_volume_ml_default=100,  # per event
    pump_max_events_per_day=3,
    pump_max_runtime_sec=30,        # safety watchdog
    pump_flow_rate_ml_per_sec=8,    # ~0.5 L/min
    
    # Safety blocks
    watering_block_panel_temp_c=45,
    watering_block_battery_v=11.5,
    watering_block_night=True,
)
```

Edit these values, reflash the firmware, and the new thresholds take
effect immediately. No hardware changes needed.
