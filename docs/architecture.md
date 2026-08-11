# Wattplot — Software Architecture

This document maps the runtime components, the data they exchange,
and the trust boundaries. The hardware architecture lives in
[`docs/pinmap.html`](pinmap.html) and
[`docs/schematic.html`](schematic.html); this document is the
software side.

```
┌────────────────────────────────────────────────────────────────────────┐
│  github.io (static site)                                              │
│  https://wattplot.org/                                  │
│  - HTML, CSS, three.js 3D viewer, dashboard, gallery                   │
│  - Reads live data via CORS to control.wattplot.org                  │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │ HTTPS (CORS allowlist: github.io)
                                 │ GET /api/state, /api/whoami, /api/logs
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Cloudflare edge (control.wattplot.org)                             │
│  - TLS termination, DDoS                                              │
│  - Access policy on POSTs: email OTP → mokahlou@gmail.com only        │
│  - Path Bypass list: GET /api/state, /api/logs, /api/whoami           │
│    (public, no auth)                                                  │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │ tunneled (cloudflared service)
                                 │ localhost:8765 (HTTP, plain)
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│  tools/wattplot_control.py  (operator's PC, Windows)                  │
│  - aiohttp server on 127.0.0.1:8765                                   │
│  - zeroconf discovery → wattplot-controller.local:6053                │
│  - ReconnectLogic + 30 s link watchdog                                │
│  - Translates /api/{switch,number,select,button} → ESPHome commands    │
│  - Logs to rotating wattplot.log (when MQTT broker is up)             │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │ Noise PSK (encrypted ESPHome native API)
                                 │ ESPHome native protocol over TCP:6053
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│  ESP32-S3-DevKitC-1-N16R8  (the wattplot-controller device)            │
│  firmware/wattplot.yaml (2029 lines)                                  │
│  - 1 Hz control loop (state machine + PI)                             │
│  - 100 ms endpoint_detector (current-spike endstops)                  │
│  - 1 s energy integration (INA219 V × I → kWh)                        │
│  - 60 s grow_light_tick (auto-watering policy)                        │
│  - 5 s alive_tick (DEBUG ping)                                        │
│  - 15 min NWS poll (forecast globals)                                 │
│  - 5 min DLI update                                                    │
│  - MQTT → wattplot/log topic (when broker configured)                  │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │ DC bus, I²C, 1-Wire, GPIO, IPROPI
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Hardware (schematic rev B, 2026-08-03)                                │
│  - 620 W LONGi Hi-MO X10 bifacial panel (or Mini's 10 W ECO-WORTHY)   │
│  - DRV8871 U5a (actuator) on GPIO1/2/11                               │
│  - DRV8871 U5b (solenoid) on GPIO10/12                                 │
│  - INA219 at 0x40 (motor), INA219 at 0x41 (panel)                       │
│  - 3× DS18B20 on GPIO16 (1-Wire)                                       │
│  - Capacitive soil moisture on GPIO6                                  │
│  - Battery V divider (100k / 10k) on GPIO7                            │
│  - Actuator IPROPI on GPIO4, solenoid IPROPI on GPIO5                   │
│  - Status LED on GPIO17 (LEDC PWM)                                     │
│  - Sunapex 10A MPPT (standalone, IP67) → 12V LiFePO4                   │
│  - Same panel + Y-splitter → Enphase IQ7+ microinverter                 │
└────────────────────────────────────────────────────────────────────────┘
```

## Data flow (one tick, ~1 s)

1. **ESPHome firmware (on the chip):**
   - ADC reads (10 Hz, internal): motor IPROPI, solenoid IPROPI,
     battery V, soil moisture. The IPROPI sensors are `internal: true`
     so they aren't published to MQTT / HA — they exist only for
     the `endpoint_detector` script.
   - Public sensors (1-2 s, named): Panel V, Panel Current, Panel
     Power, Battery Voltage, Battery SOC, Soil Moisture, Soil
     Temperature, Panel Temperature, Canopy Air Temperature,
     POA Irradiance, Panel Efficiency, Energy Today, Energy Total.
   - `control_loop` runs every 1 s. Reads `panel_tilt`, `i_motor`,
     `i_safe_limit`, `at_zero`, `at_max`. Applies PI to adjust
     commanded tilt.
2. **Push:**
   - The ESPHome native API pushes the full state vector over the
     Noise-PSK-encrypted TCP connection (port 6053).
3. **Server (`wattplot_control.py`):**
   - `aioesphomeapi` callback updates the in-memory state.
   - `_last_push` timestamp recorded; the watchdog compares against
     `STALE_FORCE_RECONNECT_S = 30.0`.
   - On `/api/state` request: serialize the state to JSON with a
     `_meta` block (`connected`, `stale_for_s`, `last_update_epoch`,
     `stale`).
4. **Panel (`docs/control.html`):**
   - Polls `/api/state` every 2 s.
   - Renders each sensor; shows the stale-data banner if
     `_meta.stale`.
   - On control click: `POST /api/{switch,number,select,button}`.
5. **Cloudflare Access:**
   - Intercepts the POST. If no `CF_Authorization` cookie, runs
     the email-OTP flow.
   - Authorized requests are forwarded to `wattplot_control.py`.
6. **Server writes back:**
   - Maps `{label, value}` to the ESPHome entity by name (labels
     are stable strings, server looks up the key).
   - `aioesphomeapi.{switch,number,select,button}_command(key=...)`.

## Trust boundaries

| Boundary | Trust | Mechanism |
|---|---|---|
| Browser ↔ Cloudflare | Public | TLS, Cloudflare Access (email OTP for POSTs) |
| Cloudflare ↔ `wattplot_control.py` | Same operator | `cloudflared` tunnel, plain HTTP on localhost |
| `wattplot_control.py` ↔ ESPHome chip | Same operator | Noise PSK (encrypted), mDNS discovery |
| ESPHome ↔ Sensors / DRV8871s | Same operator | I²C bus (PCB), 1-Wire pullup, GPIO |
| ESPHome ↔ MPPT | None (decoupled) | Sunapex is standalone; no host connection |
| `bring_your_own_panel.py` ↔ wattplot_params | Operator | Same workstation, plain Python |
| `analysis/*.py` ↔ pvlib TMY data | Public | pvlib ships its own TMY files |

The **only** external attack surface is the Cloudflare edge. The
ESPHome Noise PSK on the LAN is an opaque string but anyone on the
local network who learns it can drive the actuator — see
[`CONTRIBUTING.md`](../CONTRIBUTING.md) § Security for the rotation
posture.

## Component lifetimes (what runs where)

| Process | Where | Always on? | Notes |
|---|---|---|---|
| `firmware/wattplot.yaml` (compiled to C++) | ESP32-S3 | Yes | Boots into `Folding` (safe default). |
| `tools/wattplot_control.py` | Operator's PC | Booth: yes. Bench: on demand. | Background service via Task Scheduler (Windows) or systemd (Linux). |
| `tools/log_subscriber.py` | Operator's PC | Booth: yes. Bench: optional. | Only meaningful when Mosquitto is running. |
| `cloudflared` (Cloudflare Tunnel) | Operator's PC | Booth: yes. Bench: optional. | Runs as a Windows service. |
| `jekyll serve` (local dev preview) | Operator's PC | No | Only when iterating on `docs/`. |
| GitHub Actions | GitHub infra | No | PR + push only. |

## What is *not* in this architecture (yet)

- **No MQTT broker in CI.** The CI runs pytest on `firmware/tests/`
  and the analysis scripts; it doesn't need a live chip or a broker.
- **No Jetson / edge compute.** The ESPHome firmware runs on the
  chip; the server is the thin proxy in front. Adding a local
  ML/data pipeline (e.g., for DLI prediction) would be a new layer.
- **No HA addon.** Home Assistant is downstream of the ESPHome
  integration; we don't ship a custom component.
- **No OTA signing server.** OTA password is sufficient for the
  booth's threat model.