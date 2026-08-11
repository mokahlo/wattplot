# Glossary

Terms that appear across the docs without a single canonical reference,
with the definition + where to look for the detail. Roughly grouped
domain-by-domain.

## Hardware

**DRV8871** — TI brushed-DC motor driver. Two of these in the
schematic rev B: U5a drives the panel-tilt linear actuator (IN1 =
GPIO1, IN2 = GPIO2); U5b drives the irrigation solenoid (IN1 =
GPIO10, IN2 = GPIO12 compat-only, schematic ties IN2 → GND). Has a
current-mirror output (`IPROPI`, see below) and a fault output
(`nFAULT`). Internal current limit is ~1.15 A typical. See
`docs/schematic.html`.

**INA219** — TI I²C current/voltage/power monitor. Two of these in
the schematic rev B: U6a at I²C 0x40 measures motor current + bus V
(0.1 Ω shunt, 3.2 A range); U6b at 0x41 measures panel V + I for the
energy integrator (0.1 Ω shunt, 1.0 A range). ALERT pin is unused
on both — overcurrent detection is firmware-side.

**IPROPI** — "current proportional output" on the DRV8871. A pin
that sources/sinks a current proportional to the load current. On
the wattplot, the IPROPI pins are routed to ADC1 inputs (motor
IPROPI = GPIO4, solenoid IPROPI = GPIO5) so the firmware can read
the motor current directly. The DRV8871's ITRIP comparator trips
around 1.15 A and the IPROPI signal at that trip is the firmware's
endstop detector — see `firmware/wattplot.yaml` `endpoint_detector`.

**nFAULT** — open-drain fault output on the DRV8871. Asserts (LOW)
on overcurrent, overtemperature, or undervoltage. Wattplot routes
them to direct GPIO (motor = GPIO21, solenoid = GPIO13; the MCP23017
existed in v2.x but was removed in v3 / rev B). The control loop
folds on `nFAULT` persistent > 2 s.

**BMI160** — Bosch IMU (accelerometer + gyroscope). Was the v1/v2.4
closed-loop tilt feedback sensor; **disabled in v3.2** because
ESPHome 2026.7.2 no longer exposes `bmi160` via YAML. Replaced by
current-based homing via IPROPI. The dead block is preserved in
`wattplot.yaml` for a future MPU6050 swap-in.

**DS18B20** — Maxim 1-Wire digital temperature sensor. Three
sensors on one bus on GPIO16 (panel, soil, canopy-air). Each is
address-pinned by 64-bit ROM ID so the firmware can tell them apart
without bus scanning. 4.7 kΩ pullup to 3.3 V on the PCB.

**MCP23017** — Microchip I²C 16-bit GPIO expander. **Removed in v3.**
Used to read nFAULT in v2.x; replaced by direct GPIO in rev B.

**Sunapex 10A MPPT** (or "Sunapex HC-SM10A") — IP67 waterproof MPPT
charge controller, LiFePO4-aware out of the box, no host connection.
Used on the Mini. The full-size build needs a bigger MPPT (Victron
SmartSolar 100/30 or EPEver Tracer 4210AN) for the 620 W panel's
~17 A Imp.

**Victron SmartSolar 100/30** — Victron's MPPT charge controller
(30 A, 100 V). For the full-size build. Earlier revisions of the
disclaimers mentioned a 75/15, which is undersized (15 A only). The
100/30 was the correct number.

**EPEver Tracer 4210AN** — 40 A / 100 V MPPT. Alternative to the
Victron for the full-size build. Same form factor, similar price,
different telemetry interface (Modbus vs VE.Direct).

**LiFePO4** — Lithium iron phosphate battery chemistry. 12 V 100 Ah
in the wattplot build (LiTime or similar). Less thermal runaway risk
than LiPo, but the off-gas is still flammable and toxic.

## Sensor quantities

**POA** — Plane-of-Array irradiance (W/m²). The total solar
radiation hitting the panel surface (direct + diffuse, including
the ground-reflected component). pvlib's `get_total_irradiance()`
computes it from direct normal irradiance, diffuse horizontal
irradiance, and the panel's tilt + azimuth.

**DNI** — Direct Normal Irradiance (W/m²). The beam component,
coming straight from the sun's disk. Used to compute POA together
with diffuse + ground-reflected.

**DHI** — Diffuse Horizontal Irradiance (W/m²). The sky-scattered
component (clouds, haze, atmospheric scattering).

**DLI** — Daily Light Integral (mol/m²/day). The total photosyntheti-
cally active photons delivered to a surface over 24 h. Tomatoes
want ~12-20 mol/m²/day; lower yields leafy growth, higher wastes
water. Wattplot computes DLI from POA via the 4.57 μmol/J PAR
conversion.

**ASCE 7-22** — American Society of Civil Engineers' "Minimum Design
Loads" standard. Wattplot's wind calc uses Table 26.10-1 (velocity
pressure exposure coefficients) for the Phoenix, Cat II, 700-yr
return, Exposure C site. See `analysis/wind_load.py` and
`analysis/wind_load_report.md`.

**ITRIP** — internal current-limit comparator on the DRV8871.
Trips around 1.15 A typical (datasheet min/typ/max is 1.0/1.15/1.3).
The IPROPI pin voltage at ITRIP is approximately 1.15 V × (R_ext /
R_ISENSE), where R_ISENSE is internal to the DRV8871. The
firmware's `endstop_current_threshold` (default 0.90 A) reads
IPROPI and declares an endstop hit when the read is sustained
above this threshold for `endstop_debounce_ms` (default 1000 ms).

## Software

**ESPHome** — the YAML-to-C++ framework that turns the firmware
config into a real ESP32/ESP32-S3 binary. Wattplot uses ESPHome
2026.7.2 (`min_version: 2024.6.0` declared in the YAML header).
The compile output goes to `firmware/.esphome/build/<device>/`.

**mDNS** — multicast DNS. ESPHome devices advertise themselves as
`<device_name>.local` on the LAN. The control tools use
`wattplot-controller.local` as the default host.

**Noise protocol** — ESPHome's encrypted transport (the
`api_encryption_key` in `firmware/secrets.yaml`). Each side proves
knowledge of the shared key without sending it on the wire. NOT
plaintext-over-TLS — it's a custom challenge-response with a PSK.

**HA / Home Assistant** — open-source home-automation platform. The
ESPHome integration auto-discovers the wattplot on the LAN.
`tools/_secrets.py` documents how the API key resolves for
third-party clients.

**Cloudflare Tunnel + Access** — the public-hostname edge proxy
in front of `tools/wattplot_control.py`. Cloudflare Access is the
real auth gate for the control POSTs; see
`docs/_internal/remote-access.md`.

**Zeroconf** — multicast service discovery. The wattplot_control
server uses `aioesphomeapi`'s `ReconnectLogic` + zeroconf to find
the wattplot by mDNS, even when the IP changes.

## Project / process

**STALE banner** — the blockquote at the top of a doc that says "this
was written for the v1/v2 architecture, see firmware/wattplot.yaml
for current truth." Tells the reader the prose is design intent,
not deployed behavior. Applied to build_guide.md, wiring.md,
pcb_design.md, sensor_placement.md, watering.md, test_checklist.md,
control_law.md, and the booth materials.

**Canonical source** — the file a STALE banner points at. For
electronics: `firmware/wattplot.yaml`, `firmware/README.md`,
`docs/pinmap.html`, `docs/schematic.html`. These four files must
**never** be marked STALE themselves — CI enforces this (see the
"Check for STALE banners on canonical sources" step in
`.github/workflows/test.yml`).

**Symbiosis** — the framing the README leads with: "the same
square foot grows tomatoes *and* generates electricity." The
bed needs the structure; the panel needs the angle; both want to
be in the sun. Replacing "tradeoff" or "feature" with "symbiosis"
in user-facing language was a deliberate reframing commit
(4ea6ca1).

**Wind-sized** — adjective for a design parameter that's governed
by the wind calc rather than convenience or accessibility. "The
bed depth is wind-sized" means the 27.5" walls aren't for
ergonomics — they're the minimum that gives SF ≥ 2.0 at 35° tilt
under Phoenix design wind.