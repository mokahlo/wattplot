# ADR-002: Sunapex 10A MPPT for the Mini, off-the-shelf hardware MPPT for full-size

**Status:** Accepted (v2.4, 2026-07-30; reaffirmed in `firmware/README.md` § Hardware assumptions)
**Deciders:** mokah (project owner)
**Consulted:** `tools/recommend_mppt` in `bring_your_own_panel.py`, sun simulator, ESPHome native API

## Context

The wattplot has a 12 V battery that powers the ESPHome controller,
the DRV8871 H-bridges, the DS18B20 / INA219 sensors, and (in v2)
the grow-light / irrigation solenoid. The battery needs charge
control:

- **Mini v2.4** runs a 10 W ECO-WORTHY panel at ~0.5 A Imp into a
  ~7 Ah LiFePO4 pack.
- **Full-size** runs a 620 W LONGi panel at ~17 A Imp into a 100 Ah
  LiFePO4 pack.

Earlier revisions (v2.0 – v2.3) used a DPS5005 programmable buck
modbus-controlled as a charge controller. That had two problems:

1. **It was a hack.** The DPS5005 is a bench PSU, not an MPPT.
   It does have constant-voltage and constant-current modes that
   approximate CC/CV charging, but no bulk/absorption/float
   profile and no LiFePO4-specific behavior. We were using it as
   if it were a Victron.
2. **It was undersized.** The DPS5005 maxes out at 5 A. For the
   620 W panel at 17 A Imp, we'd have thrown away ~70 % of the
   panel's potential. The full-size build needed real MPPT.

## Decision

- **Mini:** **Sunapex HC-SM10A** (also sold as Sunapex 10A). 10 A
  MPPT, IP67 waterproof, LiFePO4-aware out of the box, no host
  connection.
- **Full-size:** **Victron SmartSolar 100/30** (30 A, 100 V) or
  **EPEver Tracer 4210AN** (40 A, 100 V). Both handle the 620 W
  panel's ~17 A Imp with margin. Both have telemetry interfaces
  (VE.Direct / RS-485) that future ESPHome firmware can read for
  HA visibility.
- **ESPHome firmware does not command the MPPT.** It only reads
  panel-side V/I (via the second INA219 at 0x41) and battery V
  (via the 100k/10k divider on GPIO7). This is the deliberate
  simplification that removed ~80 lines of UART/MPPT code in v2.4.

## Rationale

1. **LiFePO4 profile.** Both MPPTs have a configurable LiFePO4
   charge profile (bulk to absorption to float at the right
   voltages for our 12 V pack). The DPS5005 didn't.
2. **IP rating.** Sunapex is IP67 — designed to live outside on
   the bed wall. The DPS5005 needed a separate enclosure.
3. **Standalone operation.** No host connection required for
   charging to work. The ESP32 failing doesn't stop the battery
   from charging. The DPS5005 needed UART commands to enable
   output.
4. **Cost.** Sunapex is ~$30 for the 10 A. Victron SmartSolar
   100/30 is ~$200. EPEver Tracer 4210AN is ~$190. The DPS5005
   was ~$25, but you'd need a Victron-equivalent anyway for the
   full-size.

## Consequences

- **MPPT telemetry is read-only in the firmware.** The "MPPT loop"
  code from v2.0 – v2.3 is gone (see `analysis/wind_load_report.md`
  for the post-mortem in the firmware's boot log). The controller
  reads `Panel V`, `Panel Current`, `Panel Power` from the
  panel-side INA219 for display and energy integration.
- **The bench-side log stream doesn't get MPPT-internal logs.**
  The DPS5005 used to log `MPPT step: V=..., I=..., P=...`; the
  Sunapex and the Victron / EPEver don't expose that level of
  detail. The panel INA219 gives us enough for the booth
  display; deeper MPPT telemetry needs the MPPT's own interface
  (VE.Direct or RS-485), which is a future firmware extension.
- **MPPT choice is in `tools/recommend_mppt` in
  `bring_your_own_panel.py`.** Running the script with a
  non-Sunapex/Victron/EPEver panel size picks the right controller
  for the panel's Imp. The 5 panel presets all map cleanly.
- **The disclaimers HTML got the model number wrong** (Victron
  SmartSolar 75/15 — 15 A is undersized for 620 W). Fixed to
  100/30 in commit ca20eaf (this ADR documents the rationale).

## When to revisit

- If we ever add a max-PPT tracking mode in the firmware that
  actually commands the MPPT's setpoint (rather than just
  reading its telemetry), we'd need a UART/RS-485 path on the
  ESP32 to the MPPT. GPIO 26/27 are reserved on the full-size
  PCB for exactly this.
- If we add a high-voltage (>100 V Voc) panel, the MPPT choice
  changes (Victron SmartSolar 150/35 or similar).

## Alternatives considered

- **DIY MPPT (ESP32 + synchronous buck):** rejected. Reference
  designs exist (`fugu-mppt-firmware`, `akgang ESP32 MPPT`) but
  we'd need UL/IEC certification for a high-current MPPT and
  that's a multi-month effort that doesn't add to the design's
  purpose (DIY solar canopy). Off-the-shelf is faster, cheaper,
  and safer.
- **No MPPT (direct panel → battery via Schottky):** rejected.
  Panel Voc at 620 W is ~50 V cold; battery is 12 V. Without a
  buck stage, the battery sees > battery-voltage charging with
  no regulation. Would damage the LiFePO4 cells within a season.
- **PWM-only charge controller (cheap $20 units):** rejected.
  They work but are ~70 % efficient at best. We pay for the MPPT
  efficiency on a 2-3 year payback.