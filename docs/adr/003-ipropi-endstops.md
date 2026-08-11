# ADR-003: IPROPI-based current-spike endstops replace physical limit switches

**Status:** Accepted (v3.1, 2026-08-05; reaffirmed in `firmware/README.md` § Hardware assumptions)
**Deciders:** mokah (project owner)
**Consulted:** `analysis/post_bending.py`, `analysis/wind_load.py`, DRV8871 datasheet, bench testing

## Context

The actuator needs to know when it's at the 0° and 35° end-of-
travel positions. v2.4 used two physical limit switches:

- 0° switch: NO roller switch on the south wall, GPIO34 (input-only,
  external 10 kΩ pullup).
- 90° switch: NO roller switch on the north wall, GPIO35.

The control loop read both inputs and stopped the actuator on the
rising edge. Three problems:

1. **Hardware cost and complexity.** Two switches, two wires to
   route through the hinge, two connectors on the PCB, two
   mounting brackets. ~$15 in parts plus an hour of assembly.
2. **Failure mode.** A stuck switch (mechanical wear, wire
   fatigue) is silent — the firmware doesn't know the actuator
   hit the stop but keeps driving. Worst case: motor stall → DRV8871
   trips internal current limit (1.15 A) → IPROPI pin sees ~1.15 V →
   firmware can read that, but only IF it's wired that way.
3. **PCB clutter.** GPIO34 and GPIO35 are input-only on the ESP32.
   Useful for limit switches, but they consume board real estate
   for a single mechanical-switch feature that's redundant with
   the DRV8871's own current-mirror output.

## Decision

**End-of-travel detection by DRV8871 IPROPI current spike.**

- Motor IPROPI on GPIO4 (ADC1_CH4).
- `endpoint_detector` interval (100 ms) reads IPROPI, looks for a
  sustained spike > `endstop_current_threshold` (default 0.90 A)
  for > `endstop_debounce_ms` (default 1000 ms).
- On detection: set `g_at_zero` or `g_at_max` flag (depending on
  direction), stop the actuator via `actuator_stop`, then call
  `state_to_folding` (for the calibration button) or simply
  short-circuit the PI loop until commanded_tilt changes.

The DRV8871's internal ITRIP comparator trips at ~1.15 A
(datasheet min/typ/max 1.0 / 1.15 / 1.3). When the panel hits a
hard stop, the motor stalls, the current jumps from ~0.3 A (free
running) to 1.15+ A (ITRIP), IPROPI sees a sustained high reading,
and the firmware declares end-of-travel.

## Rationale

1. **One signal instead of two wires.** IPROPI is already on the
   DRV8871 chip; the PCB just routes it to an ADC1 pin. No
   switches, no brackets, no extra connectors.
2. **Faster failure detection.** Current spikes happen within
   50-100 ms of contact; mechanical switches need debouncing and
   can chatter. The 1000 ms debounce in firmware is purely
   conservative.
3. **Self-calibrating.** The first time the actuator hits 0° after
   a reset, the firmware records the baseline current (free-
   running) and the spike current (ITRIP). If the actuator ages
   and the baseline drifts (e.g., bearing wear increases
   friction), the threshold automatically adjusts when the
   user runs `button.calibrate_actuator`.
4. **No safety regression.** The DRV8871's ITRIP trips *before*
   the actuator stalls for long enough to overheat. The firmware's
   `i_safe + 0.3` hard fold still applies; IPROPI endstops are an
   additional layer, not a replacement.

## Consequences

- **`nFAULT` is still wired** (motor nFAULT = GPIO21, solenoid
  nFAULT = GPIO13). nFAULT is the DRV8871's thermal /
  undervoltage / overcurrent fault line. The firmware folds on
  `nFAULT` persistent > 2 s — that's the "I tripped ITRIP for
  too long" detector.
- **Hardware watchdog needed?** The IPROPI endstops are
  software. If the firmware hangs, the actuator can drive past
  its physical stops. A hardware watchdog (e.g., a fuse on the
  H-bridge, or a fixed-time mechanical stop) would be the
  safety net. The IPROPI feature assumes the firmware is alive
  enough to read an ADC — which `alive_tick` every 5 s
  guarantees.
- **Calibration is mandatory before first deployment.** The
  threshold (0.90 A default) is conservative but not free. The
  `button.calibrate_actuator` button must be pressed once on
  first install to discover the actual baseline + spike currents
  for this actuator + this panel.
- **v2.4 firmware v3.0 removed the limit-switch GPIO assignments
  from the YAML.** GPIO 14 and GPIO 15 are reserved on the PCB
  for future use (or unused).

## When to revisit

- **If we add an IMU** (MPU6050 swap-in for the dead BMI160), the
  IMU's tilt reading becomes a third cross-check. The IPROPI
  spike still wins for end-of-travel detection (mechanical stop
  → motor stall is the cleanest signal), but the IMU would
  catch a missed IPROPI spike.
- **If we add a hardware watchdog** (e.g., a TPL5110 reset
  controller, or a fuse), the firmware-side IPROPI detector
  becomes the "fine" detection and the watchdog becomes the
  "absolute" safety net.

## Alternatives considered

- **Keep the limit switches.** Rejected. Cost, complexity,
  failure-mode risk. The IPROPI signal is already there.
- **Hall-effect sensors on the actuator body.** Considered.
  Same cost as limit switches, more reliable than mechanical,
  but still a separate wire. The IPROPI is free.
- **Encoder on the actuator shaft.** Considered. Most expensive
  option, requires panel modification. Accurate but
  over-engineered for a 0° / 35° two-position system.
- **Just use the DRV8871's ITRIP → nFAULT directly, no IPROPI
  reading.** Rejected. nFAULT is binary; IPROPI gives a number
  for self-calibration and trend tracking. The bench-side log
  viewer shows IPROPI as a `Motor IPROPI Current` sensor, which
  is useful for debugging.