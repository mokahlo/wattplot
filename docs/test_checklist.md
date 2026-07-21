# Wattplot v2 — Test & Validation Checklist

What to verify, in what order, and how to interpret the results. The
build guide (`docs/build_guide.md`) covers the mechanical assembly. This
doc covers the **testing and validation** at every level.

---

## Phase A: PCB bench test (before installing in enclosure)

Power the PCB on the bench with a 12V bench supply (current limit set
to 1A). Verify each subsystem before installing in the enclosure.

### A.1 Power rails

| Test | Expected | Pass? |
|---|---|---|
| 12V input (TP1) | 11.5-12.6 V | ☐ |
| 5V output (TP2) | 4.9-5.1 V | ☐ |
| 3.3V output (TP3) | 3.2-3.4 V | ☐ |
| Quiescent current (no peripherals) | 80-150 mA | ☐ |
| 5V under load (ESP32 + sensors) | < 500 mA | ☐ |

If the 5V rail is missing or low, check the MP1584 enable and feedback
network. If the 3.3V rail is missing, check the AMS1117 input.

### A.2 ESP32 boot

| Test | Expected | Pass? |
|---|---|---|
| USB-C connection detected | Yes | ☐ |
| ESP32 visible in esptool | Yes | ☐ |
| Flash via USB-C (test sketch) | Success | ☐ |
| Reset button (SW2) | Reboot | ☐ |
| BOOT button (SW1) | Enter download mode | ☐ |
| WiFi connection (with credentials) | Connect | ☐ |

### A.3 I2C bus scan

Run an I2C scanner (Arduino sketch or ESPHome dump config). Expected
devices on the bus:

| Address | Device | Found? |
|---|---|---|
| 0x40 | INA219 (current sensor) | ☐ |
| 0x68 | BMI160 (IMU) | ☐ |
| 0x70 (or similar) | (optional) external I2C breakout | ☐ |

If a device is missing, check the wiring, the 4.7 kΩ pullups, and the
solder joints.

### A.4 INA219 (current sensor)

| Test | Expected | Pass? |
|---|---|---|
| Bus voltage reading (3.3V rail) | 3.30 ± 0.05 V | ☐ |
| Current reading with no load | 0 ± 0.01 A | ☐ |
| Current reading with 1A load | 1.0 ± 0.05 A | ☐ |
| Power calculation | V × I (correct) | ☐ |

Calibration: the INA219's shunt resistor value is configured in software
(default is 0.1 Ω on most breakouts, 1 A max). Verify the calibration
register matches your hardware.

### A.5 BMI160 (IMU)

| Test | Expected | Pass? |
|---|---|---|
| Accel X (frame flat, X = bed long axis) | 0 ± 0.05 g | ☐ |
| Accel Y (frame flat, Y = bed short axis) | 0 ± 0.05 g | ☐ |
| Accel Z (frame flat, Z = up) | 1.0 ± 0.05 g | ☐ |
| Tilt 35° (manually tilt the IMU): atan2(accel_z, accel_x) | 35° ± 2° | ☐ |
| Gyro X, Y, Z (no motion) | 0 ± 0.5 °/s | ☐ |
| Gyro drift (1 minute, no motion) | < 1° total | ☐ |

If the tilt reading is off by 90° or 180°, the IMU's orientation on
the board is different from the firmware's expectation. Update the
firmware's `accel_x: ...` etc. configuration.

### A.6 DS18B20 (1-Wire temperature)

| Test | Expected | Pass? |
|---|---|---|
| Sensor detected on 1-Wire bus | Yes | ☐ |
| Temperature reading (room temp ~70°F) | 68-75°F | ☐ |
| Temperature reading (touch sensor with finger) | Rises 2-5°F | ☐ |
| Resolution = 12-bit | Yes | ☐ |

If the sensor is not detected, check the 4.7 kΩ pullup. If the reading
is -196.6°F (the "disconnected" default), the pullup is missing.

### A.7 DRV8871 (motor driver)

| Test | Expected | Pass? |
|---|---|---|
| Quiescent current (motor idle) | < 10 mA | ☐ |
| IN1=HIGH, IN2=LOW, EN=HIGH → motor forward | Yes | ☐ |
| IN1=LOW, IN2=HIGH, EN=HIGH → motor reverse | Yes | ☐ |
| EN=LOW → motor stop (coast) | Yes | ☐ |
| Current limit trip (motor stalled) | DRV8871 limits at ~3.6 A | ☐ |
| Overcurrent fault flag (nFAULT pin) | Goes LOW on overcurrent | ☐ |

Test with a small DC motor (e.g., 12V gearmotor) or the actual
actuator. Verify the motor direction matches the firmware's expectation
(forward = extend, reverse = retract).

### A.8 UART (DPS5005)

| Test | Expected | Pass? |
|---|---|---|
| DPS5005 detected (TX echo) | Yes | ☐ |
| Send `*IDN?` → response | `Ruideng DPS5005` | ☐ |
| Set voltage to 14.4V → DPS5005 outputs 14.4V (measured) | Yes | ☐ |
| Set current limit to 5A → DPS5005 limits at 5A | Yes | ☐ |

If no response, check the TX/RX wiring (ESP32 TX goes to DPS5005 RX, and
vice versa). Also check that the DPS5005 is configured for 9600 baud
(default).

### A.9 Soil moisture (analog input)

| Test | Expected | Pass? |
|---|---|---|
| Sensor in dry air | ~2.5-3.0 V (high = dry for capacitive) | ☐ |
| Sensor in water | ~1.0-1.5 V (low = wet) | ☐ |
| Sensor in moist soil | ~1.5-2.5 V | ☐ |

The exact values depend on the sensor. Calibrate in your soil.

### A.10 Battery voltage sense

| Test | Expected | Pass? |
|---|---|---|
| 12V input (battery) | ADC reads ~3.0 V (12V × 10/40) | ☐ |
| 13.5V input (full charge LiFePO4) | ADC reads ~3.375 V | ☐ |
| 11.0V input (low battery) | ADC reads ~2.75 V | ☐ |

The 10k/30k divider (revised from 10k/10k) scales 12V to 3.0V, within
the ESP32 ADC range.

### A.11 Status LED (WS2812B)

| Test | Expected | Pass? |
|---|---|---|
| LED lights up at boot | Yes (any color) | ☐ |
| Color = state mapping (red=normal, blue=folding, etc.) | Yes | ☐ |

### A.12 Relay (grow light)

| Test | Expected | Pass? |
|---|---|---|
| GPIO19 HIGH → relay clicks, K1.NO connects to K1.COM | Yes | ☐ |
| GPIO19 LOW → relay releases | Yes | ☐ |
| 12V at J5 pin 2 (when relay is energized) | 12V | ☐ |

---

## Phase B: Mechanical integration test (PCB in enclosure, frame mounted)

After Phase A passes, install the PCB in the enclosure, mount the
enclosure on the bed, and connect all the wiring. Re-verify each
subsystem end-to-end.

### B.1 IMU on the frame

| Test | Expected | Pass? |
|---|---|---|
| Tilt = 0° when frame is flat (visually) | 0° ± 1° | ☐ |
| Tilt = 35° when frame is at 35° (manually set) | 35° ± 1° | ☐ |
| Tilt = 90° when frame is vertical | 90° ± 1° | ☐ |
| Tilt reading is stable (no jitter > 0.1°/s) | Yes | ☐ |

If the tilt reading drifts, recalibrate the IMU (place the frame flat,
trigger the calibration command, wait for the calibration to complete).

### B.2 Limit switches

| Test | Expected | Pass? |
|---|---|---|
| 0° switch pressed when frame is at 0° | GPIO34 = LOW | ☐ |
| 0° switch released when frame is at 5°+ | GPIO34 = HIGH | ☐ |
| 90° switch pressed when frame is at 90° | GPIO35 = LOW | ☐ |
| 90° switch released when frame is at 80°- | GPIO35 = HIGH | ☐ |

Verify the firmware uses the limit switches as end-stops (the actuator
should stop when either limit is reached, not over-drive).

### B.3 Actuator end-to-end

| Test | Expected | Pass? |
|---|---|---|
| Command: extend to 35° → actuator moves, frame tilts to 35° | 5-10 sec | ☐ |
| Command: extend to 90° → frame goes to vertical | 5-10 sec | ☐ |
| Command: retract to 0° → frame goes flat | 5-10 sec | ☐ |
| Current during motion | 0.5-1.5 A | ☐ |
| Stall current (forcefully stop the actuator) | > 2.5 A, firmware stops | ☐ |

### B.4 Cable carrier

| Test | Expected | Pass? |
|---|---|---|
| Cables don't snag when tilting | Yes | ☐ |
| Cables don't kink or bind | Yes | ☐ |
| Min bend radius respected (> 5× cable diameter) | Yes | ☐ |

If cables snag, adjust the carrier position or add slack.

---

## Phase C: Software integration test (full system, WiFi connected)

With the build mechanically and electrically complete, test the
software state machine end-to-end.

### C.1 Connectivity

| Test | Expected | Pass? |
|---|---|---|
| ESP32 connects to WiFi | Yes | ☐ |
| Home Assistant auto-discovers device | Yes | ☐ |
| API encryption key accepted | Yes | ☐ |
| Web server (port 80) accessible | Yes | ☐ |
| OTA update works | Yes | ☐ |

### C.2 Sensor values in HA

| Sensor | Expected HA value | Pass? |
|---|---|---|
| Tilt angle | 0-90° | ☐ |
| Motor current | 0-2.5 A | ☐ |
| Battery voltage | 11-14 V | ☐ |
| Soil temperature | 50-90°F (Phoenix) | ☐ |
| Soil moisture | 0-100% | ☐ |
| Outdoor temperature (from NWS) | -20 to 120°F | ☐ |
| Wind speed (from NWS) | 0-100 mph | ☐ |

### C.3 State machine transitions

| Test | Expected | Pass? |
|---|---|---|
| Initial state at boot | FOLDING | ☐ |
| NORMAL command → frame tilts to 35° | Yes | ☐ |
| BEDSUN command → frame tilts to 90° | Yes | ☐ |
| Storm (mock NWS high winds) → frame goes to 0° | Yes | ☐ |
| Battery low (< 11V) → FOLDING | Yes | ☐ |
| Watchdog (IMU disconnect) → FOLDING after 30s | Yes | ☐ |
| After storm passes → state returns to commanded | Yes | ☐ |

### C.4 MPPT (DPS5005)

| Test | Expected | Pass? |
|---|---|---|
| DPS5005 outputs 14.4V (LiFePO4 charge V) | 14.4 ± 0.2 V | ☐ |
| MPPT loop adjusts setpoint (every 10s) | Setpoint changes | ☐ |
| Battery voltage rises during sun exposure | Yes | ☐ |
| DPS5005 current limit (5A) holds | Yes | ☐ |

### C.5 DLI grow light

| Test | Expected | Pass? |
|---|---|---|
| Light turns on when DLI < target | Yes | ☐ |
| Light turns off when DLI ≥ target | Yes | ☐ |
| Light off between midnight and 6am (8-hr dark minimum) | Yes | ☐ |
| Total photo period (light + sun) | ≤ 16 hours | ☐ |

### C.6 Smart-fold safety

| Test | Expected | Pass? |
|---|---|---|
| Forcefully hold the actuator during NORMAL → motor current > 2.5 A → state = FOLDING | Yes | ☐ |
| Cut the IMU cable → watchdog triggers after 30s → state = FOLDING | Yes | ☐ |
| Cut the WiFi → state continues operating | Yes | ☐ |
| Power cycle → state comes back as FOLDING (safe) | Yes | ☐ |

---

## Phase D: Field validation (operational, over weeks)

After all the above passes, run the system in production mode. Track
metrics over time.

### D.1 Daily checks (first week)

| Check | Expected | Pass? |
|---|---|---|
| Frame at 35° in morning (NORMAL) | Yes | ☐ |
| Frame at 35° in afternoon (NORMAL) | Yes | ☐ |
| Frame flat at night (storm watch) | Yes | ☐ |
| Daily kWh from DPS5005 | 4-6 kWh (Phoenix summer) | ☐ |
| Battery voltage at end of day | 12.5-13.5 V | ☐ |
| Soil moisture reading | 30-60% | ☐ |
| No false FOLDING events (wind < 30 mph) | Yes | ☐ |
| No missed storm folds (wind > 50 mph) | Yes | ☐ |

### D.2 Weekly checks

| Check | Expected | Pass? |
|---|---|---|
| IMU calibration drift | < 1°/week | ☐ |
| Hinge pin (no rust) | Clean | ☐ |
| Panel frame (no cracks) | Clean | ☐ |
| Bed walls (no rot) | Clean | ☐ |
| DPS5005 efficiency (charging amps × 14.4V) / (panel V × panel A) | > 90% | ☐ |
| Tomato plant height | Growing | ☐ |

### D.3 Monthly checks

| Check | Expected | Pass? |
|---|---|---|
| Frame lubrication (spray the hinge pin with silicone) | Yes | ☐ |
| Soil test (pH, NPK) | OK | ☐ |
| Battery state of health | > 95% | ☐ |
| Total kWh this month (target: ~120 kWh in summer) | Yes | ☐ |
| Total tomato yield this month (target: ~10 kg/plant) | Yes | ☐ |

---

## Phase E: Long-term validation (3-12 months)

After 3 months, evaluate whether the design is meeting goals.

| Metric | Target | Actual |
|---|---|---|
| Total kWh produced (3 mo) | 360 kWh | ___ |
| Total tomato yield (3 mo) | 30 kg | ___ |
| System uptime | > 99% | ___ |
| False-fold events (wind < 30 mph) | < 1/week | ___ |
| Missed storm folds (wind > 50 mph) | 0 | ___ |
| Mechanical issues (broken parts) | 0 | ___ |
| Software bugs | < 1/quarter | ___ |

If metrics are off, see `docs/control_law.md` for tuning the state machine.
If mechanical issues, see `docs/build_guide.md` for build quality.

---

## Validation summary

After completing all the above, the system is ready for production.
Final sign-off requires:

- [ ] All Phase A bench tests pass
- [ ] All Phase B mechanical integration tests pass
- [ ] All Phase C software integration tests pass
- [ ] Phase D daily checks pass for 1 week
- [ ] Phase D weekly checks pass for 1 month
- [ ] No outstanding issues in the GitHub issue tracker

**The apparatus is ready. Sign off and enjoy the tomatoes.**
