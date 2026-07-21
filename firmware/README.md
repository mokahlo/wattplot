# Wattplot Controller v1 — ESPHome firmware

This is the controller firmware for **Wattplot v2** — a 620 W bifacial solar canopy
mounted on an 8 ft × 3.7 ft raised-bed planter. The canopy smart-folds between
a 35° power position and a 90° vertical bed-sun position, and stows flat
(0°) for high-wind events.

The firmware runs on an **ESP32-WROOM-32** and is written in ESPHome (YAML),
not Arduino C++. Behavior is fully defined in YAML — no custom code to compile.

**Spec & math behind the state machine / PI loop:** [`../docs/control_law.md`](../docs/control_law.md)

---

## What it does

Five concurrent loops, all driven from a single YAML file:

| Loop | Period | Purpose |
|---|---|---|
| **Control loop** | 1 s | State machine: NORMAL → MONITORING → FOLDING → LOCKED. PI loop on motor current. |
| **MPPT loop** | 10 s | Step-adjusts DPS5005 setpoint toward the panel's max-power point (analog of P&O). |
| **NWS poll** | 15 min | Fetches OpenWeather forecast; folds the canopy if sustained winds > 30 mph. |
| **DLI update** | 5 min | Integrates PAR over the day; tops up with grow light if < target mol m⁻² day⁻¹. |
| **Watchdog** | 5 s | Refuses to actuate if BMI160 or DPS5005 is offline > 30 s. |

State machine and tuning constants are exposed in Home Assistant as `number:` and
`select:` entities — no re-flash needed for routine tuning.

---

## Hardware assumptions

See the top of `wattplot.yaml` for the full pin map. Summary:

- **MCU:** ESP32-WROOM-32 (DevKitC or equivalent)
- **IMU:** BMI160 on I²C (0x68) — closed-loop tilt
- **Current/voltage:** INA219 on I²C (0x40) — motor + battery monitoring
- **Temp:** DS18B20 on GPIO 4 (1-Wire, 4.7 kΩ pullup to 3.3 V)
- **Motor driver:** DRV8871 H-bridge on GPIO 16/17/18
- **MPPT:** DPS5005 buck converter on UART2 (GPIO 26/27) — UART-controlled setpoint
- **Battery sense:** GPIO 33 via 10 kΩ/10 kΩ divider
- **Soil moisture:** GPIO 32 (capacitive sensor, ADC)
- **Limit switches:** GPIO 34 (0°) and GPIO 35 (90°) — input-only, EXTERNAL 10 kΩ pullup
- **Grow light relay:** GPIO 19
- **Status LED:** GPIO 25 (WS2812B, optional)

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

### 2. Create your secrets file

```powershell
cd C:\dev\wattplot\firmware
Copy-Item secrets.yaml.example secrets.yaml
```

Open `secrets.yaml` and replace every `CHANGE_ME_*` / `YOUR_WIFI_*` value.
For `api_encryption_key`, generate a fresh one:

```powershell
python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### 3. Flash the device

Wire the ESP32 to USB and run:

```powershell
esphome run wattplot.yaml
```

ESPHome will:
1. Compile the firmware.
2. Detect the serial port.
3. Upload to the ESP32 (first time requires USB; later you can use OTA).
4. Start streaming logs (`Ctrl+C` to exit, device keeps running).

### 4. Watch the logs

```powershell
esphome logs wattplot.yaml
```

You should see:

```
[state:to_folding] Hold position during boot
[D] [binary_sensor:034] 'Limit 0°': 'ON'
[interval:control_loop] Tick
...
```

If the state shows `FOLDING` at boot, that's intentional — the safe default
is to wait for first valid IMU + DPS5005 read before trusting actuator motion.

### 5. Adopt in Home Assistant

The ESPHome integration auto-discovers the device. Click **Configure** in
HA → Settings → Devices & Services. Use the same `api_encryption_key` from
`secrets.yaml` if prompted.

---

## Customization without re-flashing

All tuning constants and the controller mode are exposed as HA entities:

| Entity | Type | Default | Effect |
|---|---|---|---|
| `number.target_current` | A | 0.50 | Motor-current PI setpoint |
| `number.i_safe` | A | 2.50 | Fold immediately if motor current exceeds this |
| `number.deadband_a` | A | 0.15 | No PWM update if `|I - target| < deadband` |
| `number.commanded_tilt` | ° | 35 | Target tilt in NORMAL state |
| `number.kp_value` | — | 2.0 | PI proportional gain |
| `number.ki_value` | — | 0.10 | PI integral gain |
| `number.max_step_per_sec` | °/s | 1.5 | Actuator slew-rate cap |
| `select.controller_mode` | — | Power | `Power` (35°), `BedSun` (90°), `Manual` (follows `commanded_tilt`) |
| `select.grow_light_mode` | — | DLI-TopUp | `Off`, `DLI-TopUp`, `Manual` |

If you want to change the **state machine** or **decision stack** itself, edit
the YAML. After editing:

```powershell
esphome run wattplot.yaml        # compile + upload (OTA if reachable)
esphome logs wattplot.yaml       # follow logs
```

---

## Decision stack (one-line summary)

The canopy picks its state using this priority, top wins:

1. **Watchdog failed** (IMU or DPS5005 offline > 30 s) → `FOLDING` (safe)
2. **Motor current > `i_safe`** (jammed) → `LOCKED`
3. **NWS forecast > 30 mph sustained or gust** → `FOLDING` → `LOCKED` 24 h
4. **NORMAL wind AND battery < 11.0 V** → `FOLDING` (protect battery)
5. **NORMAL wind AND time 11:00–15:00 AND clear sky** → `MONITORING` (stays in `Power` mode, watching)
6. Otherwise → `NORMAL` (follow `commanded_tilt`)

Full math + edge cases: [`../docs/control_law.md`](../docs/control_law.md).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `DPS5005 not detected` on boot | UART wiring, baud mismatch | DPS5005 must be set to 9600 baud, 3.3 V TX |
| `BMI160 not detected` | I²C address, wiring | Default 0x68; check SDA/SCL pullups |
| `Watchdog tripped` in logs | IMU or DPS5005 dropped | Check I²C bus / UART, restart device |
| Wi-Fi not connecting | Wrong SSID / password | Edit `secrets.yaml`, re-run `esphome run` (USB) |
| Canopy won't fold under wind | `i_safe` too high OR NWS poll failing | Check `number.i_safe`; HA shows last NWS error |
| MPPT setpoint stuck at 13.0 V | `mppt_loop` not running OR `target_current` = 0 | Check logs for `mppt_step`; verify DPS5005 responds to UART |
| Grow light always on | `grow_light_mode` set to `Manual` | Switch to `DLI-TopUp` or `Off` |

---

## OTA updates

Once the device is on Wi-Fi, you can push firmware updates over the network:

```powershell
esphome upload wattplot.yaml --device wattplot.local
```

ESPHome uses mDNS (`wattplot.local`) and falls back to the IP if mDNS is blocked.
You'll be prompted for `ota_password` (from `secrets.yaml`).

---

## Files

```
firmware/
├── wattplot.yaml              ← this firmware
├── secrets.yaml.example       ← template (copy to secrets.yaml, never commit)
├── secrets.yaml               ← your real secrets (gitignored)
└── README.md                  ← this file
```

`secrets.yaml` is in `.gitignore` at the repo root. Don't add it.
