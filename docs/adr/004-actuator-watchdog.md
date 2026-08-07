# ADR-004: Actuator hardware watchdog (firmware-side) — proposed

**Status:** Proposed (not implemented)
**Deciders:** mokah (project owner)
**Consulted:** DRV8871 datasheet, IPROPI endstop ADR (003)

## Context

The IPROPI endstop detector (ADR-003) is a software safety: the
firmware reads IPROPI, declares end-of-travel when the current
spike exceeds a threshold, and stops the actuator. The `alive_tick`
interval (5 s) and the watchdog in `wattplot_control.py` (30 s
link watchdog) catch most firmware hangs.

**What they don't catch:** a firmware hang that leaves the actuator
H-bridge in the "extend" state. The DRV8871's internal ITRIP trips
at 1.15 A and protects the chip, but the actuator stalls against
the mechanical stop, draws stall current continuously, and the
motor + gearbox heat up. In a 12 V system with a 1 A stall
current, a stalled linear actuator dissipates 12 W. The actuator
body is rated for 25% duty cycle at full load; continuous stall
triggers the thermal cutoff internally, but the gearbox can
still be damaged by 30+ minutes of stalled driving.

A TPL5110 or TPL5010 reset controller on the ESP32 EN line
would force a hard reset every ~30 s if the firmware doesn't
toggle a GPIO. After reset, the firmware boots into `Folding`
state and the actuator retracts. The worst-case time spent
stalled is bounded by the watchdog period.

This is the "hardware watchdog" the brainstorm identified as
low-priority but worth documenting so a future firmware rev
knows it's a known gap.

## Decision (proposed)

**Add a TPL5110 (or equivalent) reset controller.** Wire:

```
ESP32-S3 EN pin
   |
   +-- R_pullup (10 kΩ) -- to 3V3 (so the chip is enabled by default)
   |
TPL5110 DONE -- driven by a GPIO from the ESP32-S3 (let's call it GPIO_WATCHDOG)
   |
TPL5110 DELAY -- to GND via 50 kΩ resistor (sets the period to ~30 s)
```

The ESP32-S3 firmware toggles GPIO_WATCHDOG HIGH every 5 s. The
TPL5110 counts; if DONE doesn't arrive within the 30 s window, it
pulls EN LOW for ~1 s, forcing a hard reset. After the reset, the
ESP32 boots into `Folding` state (per `on_boot` in the YAML), the
actuator retracts, the operator gets a chance to investigate.

## Rationale

1. **Bounded worst-case.** A hung firmware holding the H-bridge
   "extend" command results in a 30-second stall before the
   watchdog fires. The DRV8871's thermal cutoff will then
   protect the chip itself; the actuator is the only
   component at risk, and a 30 s stall is well within the
   actuator's thermal budget.
2. **No false positives.** The 5 s toggle vs. 30 s period gives
   6× margin. A busy but alive firmware (e.g., during a
   long-running POA calculation) doesn't accidentally trigger
   the watchdog.
3. **Cheap.** TPL5110 is $1.50 in single quantity, 6 pins, no
   firmware configuration needed. Adds 5 components total
   (TPL5110 + 1 cap + 3 resistors).

## Consequences

- **Requires a hardware rev.** Not a firmware-only change.
  Need to add the TPL5110 + supporting passives to the schematic
  rev C PCB. The v3.2 firmware in `wattplot.yaml` is unaware of
  the watchdog GPIO; the next firmware rev needs to toggle it.
- **Reset cycle is visible to the user.** A reset on the live
  panel means the panel goes into `Folding` (which is the safe
  default), but the panel briefly disconnects from Home
  Assistant. Better than a stalled actuator, but worth
  documenting in the booth runbook.
- **The 5 s toggle needs to NOT be in a deferred task.** A
  `delay(5s)` before the toggle is wrong. Use a hardware
  interval (`interval:`) or a real-time interrupt.

## When to implement

- **After the next PE review.** The mechanical-stop / gearbox
  damage from a 30 s stall is the actual concern. If the PE
  review says the actuator + panel can survive a 30 s stall
  without mechanical damage, this ADR can be downgraded to
  "nice to have" forever.
- **If the actuator is upgraded** to a higher-current model
  (the IKEA EKTORP arms used in some builds draw 2 A stall
  current — 24 W continuous dissipation), the thermal margin
  is gone. The TPL5110 becomes mandatory.
- **If the booth runs unattended for long periods** (a long
  weekend at a Maker Faire with no operator on hand), the
  TPL5110 provides a fallback in case the operator can't
  reset the chip manually.

## Alternatives considered

- **Firmware-only watchdog (Task Watchdog Timer, TWDT).** ESPHome
  has a built-in TWDT that resets the chip on task starvation.
  Would catch most hangs. Doesn't catch a hung CPU (e.g., tight
  loop in a lambda), and doesn't catch firmware that has
  stopped calling `loop()` entirely. Hardware watchdog is
  belt-and-suspenders.
- **Solid-state relay on the actuator lead.** A normally-closed
  SSR in series with the actuator, driven by a GPIO. Simpler
  than the TPL5110 but doesn't reset a hung firmware. Just
  cuts power. Useful as a second line of defense, not the
  primary.
- **Watchdog on the MPPT side.** The Victron SmartSolar has
  internal protection; cutting the 12 V output to the
  controller doesn't help if the firmware is the hung
  component.
- **Mechanical fuse on the actuator.** A shear pin or
  slip-clutch. Heavy, requires a real mechanical redesign.