# Wattplot Controller v3.2 — ESPHome firmware

ESPHome configuration for the Wattplot controller. The single source of
truth for what the chip actually does is `wattplot.yaml` at the top of
this directory — if anything in this README disagrees with that file,
the YAML wins. This README explains the structure, the pin map, and
how to flash / tune the controller.

**Spec & math behind the state machine / PI loop:** [`../docs/control_law.md`](../docs/control_law.md)
(pinned to YAML behavior; the 10-priority decision stack described in
that doc is aspirational — only the wind-safety 4-state machine is
implemented. See `docs/_internal/` for the chip-recovery notes.)

---

## Hardware assumptions

Target hardware is **ESP32-S3-DevKitC-1-N16R8** (16 MB flash, 8 MB
PSRAM). The schematic is **rev B (2026-08-03)** — see
[`../docs/schematic.html`](../docs/schematic.html) and the pin-map
audit at [`../docs/pinmap.html`](../docs/pinmap.html). The full pin
table is at the top of `wattplot.yaml`.

| Subsystem | Component | GPIO / Bus |
|---|---|---|
| **Actuator H-bridge** (panel tilt) | DRV8871 U5a | IN1 = GPIO1, IN2 = GPIO2, EN = GPIO11 (compat-only, schematic ties EN → 3V3) |
| **Actuator IPROPI** (current sense for endstops) | ADC1_CH4 | GPIO4 |
| **Motor nFAULT** | direct GPIO | GPIO21 |
| **Solenoid H-bridge** (water valve) | DRV8871 U5b | IN1 = GPIO10, IN2 = GPIO12 (compat-only, schematic ties IN2 → GND) |
| **Solenoid IPROPI** (jam detect) | ADC1_CH5 | GPIO5 |
| **Solenoid nFAULT** | direct GPIO | GPIO13 |
| **Motor current + actuator bus V** | INA219 @ I²C 0x40 | SDA = GPIO8, SCL = GPIO18 |
| **Panel V/I** (energy monitor) | INA219 @ I²C 0x41 | same I²C bus |
| **DS18B20** (3 sensors on one bus) | 1-Wire | GPIO16, 4.7 kΩ pullup |
| **Soil moisture** (capacitive) | ADC1_CH6 | GPIO6 |
| **Battery V** (100k / 10k divider, ×11.0) | ADC1_CH7 | GPIO7 |
| **Status LED** (monochromatic, LEDC) | output | GPIO17 (compat-only, removed from rev B schematic) |

**Reserved / unused (do not reassign):** GPIO 19, 20 (native USB);
GPIO 26–32 (SPI flash on the WROOM module); GPIO 33–37 (PSRAM on the
N16R8 variant). GPIO 39, 40, 41, 42, 47, 48 are free on the
DevKitC-1-N16R8 carrier.

**Removed in rev B, kept in firmware as compat-only stubs:** the
physical limit switches (GPIO 14, 15 — "compat-only" placeholders
that the state machine never reads), the WS2812B status LED (now a
monochromatic LEDC PWM on GPIO 17), and the MCP23017 I²C expander
(nFAULT is now direct GPIO on 13 and 21). The IDs (`actuator_nfault`,
`solenoid_nfault`, `status_led_pwm`, etc.) are preserved so the
state-machine references compile against a future re-spin.

**Charge control is out of the firmware.** The mini uses a standalone
**Sunapex 10A MPPT** (IP67, LiFePO4-aware, no host connection). The
full-size build needs a **Victron SmartSolar 100/30** or
**EPEver Tracer 4210AN** (both handle the 620 W panel's ~17 A Imp).
The ESP32 only *reads* battery voltage (via the on-PCB 100k / 10k
divider on GPIO7) and panel-side V/I (via the panel INA219) — it does
not command a charge controller. This is the deliberate simplification
that replaced the v2.0-2.3 DPS5005-as-MPPT hack.

**IMU / closed-loop tilt feedback: not currently used.** The
schematic rev B removed the BMI160 footprint. `panel_tilt` mirrors
`commanded_tilt` (open-loop position) and the H-bridge uses
**current-based homing** via the actuator IPROPI pin (GPIO4): when
the panel hits a hard stop the DRV8871's internal current limit
trips, IPROPI sees a sustained ≥ 0.90 A spike, and the firmware sets
`g_at_zero` / `g_at_max` accordingly. The dead `bmi160:` block is
preserved in `wattplot.yaml` for a future MPU6050 swap-in (drop-in
I²C at 0x68, full ESPHome 2026.7 YAML support).

---

## What it does — five concurrent loops

All driven from a single YAML file (`wattplot.yaml`):

| Interval | Period | Purpose |
|---|---|---|
| `control_loop` | 1 s | State machine: NORMAL → MONITORING → FOLDING → LOCKED. PI loop on motor current. |
| `nws_poll_interval` | 15 min | Pulls NWS forecast; populates globals (`g_nws_max_wind_mph`, `g_nws_rain_forecast`). *Note: the 1 Hz loop does not currently read these globals; the wind-event state transitions are triggered by motor current only.* |
| `dli_update` | 5 min | Integrates PAR over the day; the `grow_light_tick` reads this to decide if the solenoid should run in auto mode. |
| `energy_integration` | 1 s | Sums panel V × I → `Energy Today`, `Energy Total`. |
| `endpoint_detector` | 100 ms | Looks for the IPROPI current spike that signals end-of-travel. |
| `grow_light_tick` | 60 s | Auto-water logic (the "grow light" name was retained from when this drove a light; the load is now a 12 V solenoid valve). |
| `alive_tick` | 5 s | DEBUG ping only (does not gate actuation). |

State machine and tuning constants are exposed in Home Assistant as
`number:` and `select:` entities — no re-flash needed for routine
tuning.

---

## Quick start

### 1. Install ESPHome CLI

```powershell
pip install esphome
```

Verify:

```powershell
esphome version
```

ESPHome version is pinned loosely — `wattplot.yaml` declares
`min_version: 2024.6.0`; anything past that with current sensor/INA219
support works. (Note: the disabled `bmi160` block and several
component migrations were last validated against ESPHome 2026.7.2.)

### 2. Create your secrets file

```powershell
cd C:\dev\wattplot\firmware
Copy-Item secrets.yaml.example secrets.yaml
```

Open `secrets.yaml` and replace every `CHANGE_ME_*` / `YOUR_WIFI_*`
value. For `api_encryption_key`, generate a fresh one:

```powershell
python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### 3. Flash the device

Wire the ESP32-S3 to USB and run:

```powershell
esphome run wattplot.yaml
```

ESPHome will:
1. Compile the firmware.
2. Detect the serial port.
3. Upload to the chip (first time requires USB; later you can use
   OTA).
4. Start streaming logs (`Ctrl+C` to exit, device keeps running).

If the chip is wedged (the recovery procedure for this is in
`docs/_internal/esp32-s3.md` §8):

```powershell
python -m esptool --chip esp32s3 --port COM## --before no-reset --after watchdog-reset --baud 460800 write_flash 0x0 firmware\.esphome\build\wattplot-controller\build\firmware.factory.bin
```

### 4. Watch the logs

```powershell
esphome logs wattplot.yaml
```

You should see a v3.2 boot banner:

```
[boot] === Wattplot v3.2 ===
[boot]   build:       Aug  6 2026 16:55:00
[boot]   reason:      0
[boot]   free heap:   1234567 bytes
[state:to_folding] Hold position during boot
[endpoint:099] Extended 0° — g_at_zero SET
```

If the controller state shows `Folding` at boot, that's intentional —
the safe default is to wait for valid INA219 reads before trusting
actuator motion.

### 5. Adopt in Home Assistant

The ESPHome integration auto-discovers the device. Click **Configure**
in HA → Settings → Devices & Services. Use the same
`api_encryption_key` from `secrets.yaml` if prompted.

---

## Customization without re-flashing

All tuning constants and the controller mode are exposed as HA
entities:

| Entity | Type | Default | Effect |
|---|---|---|---|
| `number.target_current` | A | 0.50 | Motor-current PI setpoint |
| `number.i_safe` | A | 2.50 | Hard fold if motor current exceeds `i_safe + 0.3` |
| `number.deadband_a` | A | 0.15 | No PI update if `|I - target| < deadband` |
| `number.commanded_tilt` | ° | 35 | Target tilt in NORMAL state (structurally capped at 35° per `analysis/wind_load.py`) |
| `number.kp_value` | deg/A | 2.0 | PI proportional gain |
| `number.ki_value` | deg/(A·s) | 0.10 | PI integral gain |
| `number.max_step_per_sec` | °/s | 3.0 | Actuator slew-rate cap |
| `number.solenoid_max_water_sec` | s | 300 | Force-off the solenoid after this continuous on-time (safety guard) |
| `number.battery_water_floor_v` | V | 11.5 | Don't water if battery V is below this |
| `number.one_off_water_sec` | s | 5 | Duration of the "Water Now" button press |
| `number.endstop_current_threshold` | A | 0.90 | IPROPI threshold for end-of-travel detection |
| `select.controller_state` | — | Folding | `Normal` / `Monitoring` / `Folding` / `Locked` |
| `select.controller_mode` | — | Power | `Power` only — `BedSun` (90°) was retired (fails the wind calc at design wind) |
| `select.grow_light_mode` | — | Off | `Off` / `Auto` / `Manual` (the "grow light" name is historical; the load is now a 12 V solenoid valve) |
| `switch.solenoid_valve` | — | off | Toggle the solenoid manually |
| `button.water_now` | — | — | One-shot pulse (`one_off_water_sec`) |
| `button.calibrate_actuator` | — | — | Run the actuator self-calibration (zero + max endstop discovery) |

If you want to change the **state machine** or **decision stack**
itself, edit the YAML. After editing:

```powershell
esphome run wattplot.yaml        # compile + upload (OTA if reachable)
esphome logs wattplot.yaml       # follow logs
```

---

## Decision stack (what's actually implemented)

The control loop (1 Hz `control_loop` interval) implements only the
**wind-safety state machine** from `docs/control_law.md`. The
10-priority "sun + soil + rain + wind + user" decision stack
described in that doc is aspirational — globals for NWS wind/rain
exist, but the 1 Hz loop does not yet read them. Today's behavior:

1. **Motor current > `i_safe + 0.3`** → fold (override everything)
2. **Actuator nFAULT persistent > 2 s** (DRV8871 internal ITRIP trip) →
   fold
3. Otherwise the 4-state machine runs:
   - **NORMAL** → PI loop drives tilt to `commanded_tilt`
   - **MONITORING** → entered when `i_motor > 0.5 * i_safe` (i.e. the
     wind is loading the panel); 15-min countdown to either resume or
     fold
   - **FOLDING** → retract actuator to 0° (stow flat)
   - **LOCKED** → 30-min hold at 0°; exit on `i_motor < 0.3 * i_safe`
     for a single 1-Hz sample
4. **State on boot: FOLDING** (`controller_state.initial_option`,
   `on_boot` script runs `state_to_folding`)

The "5-min settle" and the SOC-based light gating described in
`docs/control_law.md` are not implemented yet. Full math + edge cases
in [`../docs/control_law.md`](../docs/control_law.md) — but treat the
doc as design intent, not a literal description of today's behavior.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Battery not charging | Sunapex wiring (panel MC4 polarity, battery polarity) or Li mode not selected | Red MC4 → Sunapex PV+ (via SAE), black MC4 → Sunapex PV−; battery + to BAT+, − to BAT−; press MODE button until LCD shows "Li" or "LiFePO4" |
| Sunapex LCD blank | No battery connected (Sunapex is powered by the battery, not the panel) | Connect battery first, then panel |
| `INA219 not detected` at 0x40 / 0x41 | Missing chip on I²C bus, SDA/SCL swapped, or no pullups | Both INA219s must be present before flashing — `esphome config` will fail with a clear I2C error if either is missing |
| `actuator_nfault` ON in logs (and stays > 2 s) | DRV8871 internal current limit tripped (panel jammed, stuck at endstop) | Check mechanical path; run `button.calibrate_actuator` to re-discover endpoints |
| Chip wedged, won't enter SPI Boot mode | The DevKitC-1's native USB-Serial/JTAG has no DTR/RTS reset; esptool's default `--after hard-reset` is a no-op | Use `--after watchdog-reset`. Full procedure in `docs/_internal/esp32-s3.md` §8 |
| `Panel Power` sensor is 0 W | Panel-side INA219 not installed, or panel in shade | Confirm second INA219 at I²C 0x41; check Sunapex LED shows charging |
| Solenoid won't run in Auto | `grow_light_mode` is `Off`, or battery V < `battery_water_floor_v`, or `solenoid_fault_alarm` is latched | Switch to `Auto`; check `Battery Voltage` and `Solenoid Fault Alarm`; latch clears on next fault-free tick |
| Solenoid turns off after 5 min on `Manual` | `solenoid_max_water_sec` safety guard | Expected. Raise the number, or switch to `Auto` for demand-driven watering |
| Wi-Fi not connecting | Wrong SSID / password | Edit `secrets.yaml`, re-run `esphome run` (USB) |
| Canopy won't fold under wind | `i_safe` too high OR NWS poll failing (and the wind-event path is motor-current-based anyway — see Decision stack) | Check `number.i_safe`; the wind-event state transitions are driven by motor current, not NWS wind forecast, in the current firmware |

---

## OTA updates

Once the device is on Wi-Fi, you can push firmware updates over the
network:

```powershell
esphome upload wattplot.yaml --device wattplot.local
```

ESPHome uses mDNS (`wattplot.local`) and falls back to the IP if mDNS
is blocked. You'll be prompted for `ota_password` (from `secrets.yaml`).

---

## Files

```
firmware/
├── wattplot.yaml              ← the firmware (2029 lines, single source of truth)
├── secrets.yaml.example       ← template (copy to secrets.yaml, never commit)
├── secrets.yaml               ← your real secrets (gitignored)
├── README.md                  ← this file
├── watch_boot.py              ← serial-monitor helper for the wedged-chip recovery (standalone)
├── .gitignore                 ← keeps the .esphome build cache out of git
└── tests/                     ← pytest suite (config + codegen checks)
    ├── conftest.py
    ├── test_config.py         ← pin/ID presence tests, S3 constraint guards
    └── test_codegen.py        ← lambda / generated-code regression checks
```

`firmware/logic/` is reserved for future Python reference
implementations of the lambdas (POA hour-angle, SOC lookup, etc.) — the
directory is currently empty of `.py` sources. The math is implemented
inline in the YAML; see the comments in `wattplot.yaml` for pointers.

`secrets.yaml` is in `.gitignore` at the repo root. Don't add it.