# Wattplot v2 — Control Law

The smart controller's goal, decision logic, and state machine. This is the
canonical reference for the firmware. The implementation is in ESPHome YAML
(proposed) or Arduino C++ (alternative); the law is the same either way.

## Goal (verbatim)

> **Keep motor current below `I_safe`, while maximizing desired tilt for desired sun exposure.**

Where:
- `I_safe` = the structural limit on the actuator, ~2.5 A (DRV8871 trips at 3.6 A; 2.5 A leaves margin)
- "Desired tilt" = the highest-priority non-null value from the decision stack below
- "Sun exposure" = whatever the bed and panel jointly produce, both shadow and irradiance

## Architecture

The controller is a **PI loop on motor current** (safety constraint) with a
**decision stack** providing the setpoint (objective). The PI loop runs at 1 Hz
and tries to maintain `θ_actual ≈ θ_desired`, but reduces tilt if motor
current approaches `I_safe`.

```
   NWS / soil / time-of-day  ───►  decision stack  ───►  θ_desired
                                                              │
                                                              ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
   │  INA219      │───►│  PI loop     │───►│  Rate limiter    │──► actuator
   │  motor I (A) │    │  + deadband  │    │  + clamps        │
   └──────────────┘    └──────────────┘    └──────────────────┘
            │                                        ▲
            └────── I_safe as the safety constraint ──┘
```

The state machine below wraps this loop with conventional solar-tracker UX
(borrowed from the [SolarArduino project](https://github.com/HDwayne/SolarArduino)
which does wind safety well).

## Decision stack (priority order)

The setpoint `θ_desired` is the highest non-null value from this list:

| Priority | Source | Sets `θ_desired` to |
|---|---|---|
| 1 | **User override** (panic button, maintenance lock) | arbitrary 0–90 |
| 2 | **Hard current limit** (I > 2.8 A for 0.5 s) | 0 (safety net) |
| 3 | **NWS rain forecast + dry soil** | 0 (capture rain) |
| 4 | **NWS wind forecast > 50 mph in 3 h** | 15 (preemptive shallow) |
| 5 | **Wind ≥ 50% of I_safe** (motor current high) | current value (pause tracking) |
| 6 | **Soil wet 72 h+** | 90 (wring out, dry the bed) |
| 7 | **Soil dry 48 h+ + no rain forecast** | 35 (conserve water) |
| 8 | **Time-of-day + tracking mode** | 0–90 (azimuth tracks sun) |
| 9 | **Time-of-day + power mode** | 35 (max power) |
| 10 | **Time-of-day + bed-sun mode** | 90 (full bed sun) |

Lights and tilt are decoupled — see "Grow lights" section below.

## Wind safety state machine (SolarArduino-style)

This is the conventional solar-tracker UX. The user-facing behavior should
match what a person would expect: the panel folds during a wind event and
unfolds when it passes, with hysteresis to prevent flapping.

```
                     I_motor ≤ I_safe (settled)
                  ┌──────────────────────────┐
                  │                          │
                  ▼                          │
   ┌────────────────────┐                  │
   │     NORMAL         │  (panel at commanded angle) │
   │                    │                  ▲
   └────────┬───────────┘                  │
            │                              │
   I_motor > I_safe (sustained)             │
   OR NWS forecast > 50 mph in 3h         │
            │                              │
            ▼                              │
   ┌────────────────────┐                  │
   │    MONITORING       │  (alarm latched, wind check each 5 min)   │
   │  countdown: 15 min │                  │
   └────────┬───────────┘                  │
            │                              │
   alarm still firing after 15 min         │
            │                              │
            ▼                              │
   ┌────────────────────┐                  │
   │     FOLDING         │  (actuator retracts to 0° at 3°/sec)        │
   │                    │                  │
   └────────┬───────────┘                  │
            │                              │
   reaches 0° (limit switch)              │
            │                              │
            ▼                              │
   ┌────────────────────┐                  │
   │     LOCKED         │  (panel flat, motor disabled)            │
   │  hold time: 30 min │                  │
   └────────┬───────────┘                  │
            │                              │
   hold time elapsed AND                  │
   I_motor < 0.5 I_safe for 5 min         │
            │                              │
            └──────────────────────────────┘
                  (back to NORMAL)
```

### State transitions

| From | To | Trigger |
|---|---|---|
| NORMAL | MONITORING | I_motor > I_safe for 30 sec, OR NWS forecast wind > 50 mph in 3 h |
| MONITORING | NORMAL | After 15 min, condition not present anymore (no wind) |
| MONITORING | FOLDING | After 15 min, alarm still firing |
| FOLDING | LOCKED | Limit switch at 0° reached |
| LOCKED | FOLDING | Hold time elapsed, but I_motor still > 0.5 I_safe |
| LOCKED | NORMAL | Hold time elapsed AND I_motor < 0.5 I_safe for 5 min |

### Why these specific numbers

- **15 min monitor countdown** — gives the wind event a chance to pass without needing to physically fold
- **30 min locked hold** — enough time for a typical storm cell to pass; prevents oscillation
- **5 min settle before re-extending** — confirms the wind is really gone, not just a lull
- **0.5 × I_safe as the "safe to unfold" threshold** — current must be well below limit, not just barely

This is the SolarArduino pattern (15 min monitor, 30 min hold) adapted to use
motor current instead of an anemometer.

## PI controller (the actual safety constraint)

Within NORMAL state, the PI loop runs at 1 Hz:

```python
target_current = 0.5    # A, target safe operating current
deadband      = 0.15   # A, don't act if within this band
max_step_per_sec = 3.0  # deg/sec, rate limit
hard_limit    = 2.5    # A, hard safety (triggers FOLDING)
i_safe        = 2.5    # A, structural safety

Kp = 2.0    # deg / A
Ki = 0.10   # deg / (A·s)

# Each tick:
i_motor = read_ina219()   # mA, low-pass filtered
error = i_motor - target_current
integral_error += error * dt
integral_error = clamp(integral_error, -5, 5)  # anti-windup

if abs(error) > deadband:
    adjustment = Kp * error + Ki * integral_error
else:
    integral_error *= 0.9
    adjustment = 0

target_angle = current_angle - adjustment  # high current → reduce angle
target_angle = clamp(target_angle, 0, θ_desired)
step = rate_limit(target_angle - current_angle, max_step_per_sec * dt)

if abs(step) > 0.5:  # deadband to avoid jitter
    move_actuator(step)
```

The controller is **intentionally not trying to track the sun** — that's a
separate feature (priority 8 in the decision stack). In default power mode,
`θ_desired = 35°` and the PI loop just keeps the panel at 35° while managing
wind load. The user opts into sun-tracking mode explicitly.

## Grow lights (independent of tilt)

The grow light is a 12V relay output on the same battery, decoupled from tilt.

| Logic | Condition | Action |
|---|---|---|
| L1 | Battery SOC < 50% | Lights off (preserve for safety) |
| L2 | Natural DLI > target (e.g., 20 mol/m²/day) | Lights off (no need) |
| L3 | Natural DLI < target AND deficit > 0 | Lights on (pre/post-dawn) |
| L4 | Photoperiod constraint | Min 8 hr dark, max 16 hr light |

Implementation: pre-dawn (4-7 am) and post-sunset (6-9 pm) light extension.
Skipped entirely on summer days (natural DLI suffices).

## IMU (closed-loop position)

Without an IMU, the actuator's open-loop position drifts. With a BMI160 IMU
($2, I2C), the firmware knows the actual tilt to ±0.5°.

```python
# Each tick, fuse accelerometer + gyroscope for tilt angle
tilt_actual = bmi160.read_tilt()  # degrees, fused

# Compare to commanded
position_error = θ_desired - tilt_actual
if abs(position_error) > 0.5:  # within IMU accuracy
    # correct position
    adjust_actuator(position_error * 0.3)  # proportional correction
```

This is **complementary** to the motor current loop:
- **Current loop** = safety (don't let wind damage the structure)
- **IMU loop** = accuracy (the panel is where you told it to be)

Both run at 1 Hz. They don't conflict — current limits what the actuator
*can* do, IMU ensures the actuator *did* what you wanted.

## Safety net (independent of all the above)

If anything goes wrong (sensor failure, controller crash, RF noise), the
actuator has built-in limit switches at 0° and 90°. The H-bridge driver
(DRV8871) has hardware overcurrent protection that trips at 3.6 A.

The firmware should also:
- Watchdog timer resets ESP32 if it hangs
- Brownout detector triggers emergency fold on low battery
- Default to FOLDING state on boot (better safe than deployed at 90°)

## Parameters

| Symbol | Value | Source |
|---|---|---|
| I_safe | 2.5 A | `CONTROL["i_safe_A"]` in `wattplot_params.py` |
| target_current | 0.5 A | `CONTROL["target_current_A"]` |
| deadband | 0.15 A | `CONTROL["deadband_A"]` |
| max_step | 3°/sec | `CONTROL["max_step_deg_per_sec"]` |
| hard_limit | 2.5 A | `CONTROL["hard_current_A"]` |
| Kp | 2.0 deg/A | `CONTROL["Kp"]` (proposed) |
| Ki | 0.10 deg/(A·s) | `CONTROL["Ki"]` (proposed) |

Tune Kp/Ki by running the simulator against replayed Phoenix weather.

## Reference

- **SolarArduino** (HDwayne) — wind-safety state machine inspiration: https://github.com/HDwayne/SolarArduino
- **Sunchronizer** (Nerdiyde) — IMU-based closed-loop position: https://github.com/Nerdiyde/Sunchronizer
- **Helioduino** (NachtRaveVL) — professional-grade tracker control: https://github.com/NachtRaveVL/Simple-SolarTracker-Arduino
- **PVlib** — for sun position in tracking mode: https://pvlib-python.readthedocs.io/
