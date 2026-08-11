# tools/ — operator + bench + booth scripts

Every script in this directory either talks to the wattplot
controller over its native ESPHome API (port 6053), drives one of
the simulation/analysis tools, or maintains the docs site.

## Common pattern

All scripts that connect to the controller resolve the API encryption
key via `tools/_secrets.py`:

  1. `WATTPLOT_API_KEY` environment variable (recommended for CI,
     the bench PC, and the booth PC).
  2. `firmware/secrets.yaml` `api_encryption_key:` field (dev box).
  3. `~/.config/wattplot/api_key` (per-user override).

If none of the three resolves, the script fails fast at import time
with a clear `WattplotConfigError` — never at the point of use. See
`_secrets.py` for the rotation procedure if the previous hardcoded
key was leaked.

Default host: `wattplot-controller.local` (mDNS). Override with the
first CLI arg if your chip answers a different hostname.

## Live debug + bench tests

| Script | What it does |
|---|---|
| `dump_state.py` | Full state dump — every exposed entity's name, type, current value, organized into sections (power, sensors, actuator, solenoid, calibration, diagnostics). Read-only. |
| `show_state.py` | Condensed dump of the high-signal entities (controller state, commanded tilt, panel/battery voltages, fault flags). Read-only. |
| `check_soil.py` | Soil moisture sensor (raw V + percent). |
| `check_temps.py` | Panel, soil, and canopy air temperature. |
| `check_wattplot_state.py` | Lists all entities and their values. |
| `calibrate_watch.py` | Runs `button.calibrate_actuator` and watches the calibration progress: endstop current, spike duration, peak IPROPI. Logs the full timeline. |
| `run_calibration.py` | Triggers the calibration button and polls `Last MAX / ZERO Endstop Current` as they fill in. |
| `demo_tilt.py` | Sets Controller Mode to Power, commands a tilt, verifies the manual control path. |
| `test_actuator_motion.py` | Drives the actuator extend + retract with a live battery. Auto-stops on endstop spike (>0.90 A for ≥1 s) or nFAULT. Safety-bounded. |
| `test_hbridge.py` | Logic-level H-bridge test only. Drives IN1/IN2 in 4 phases (idle, fwd, rev, idle) with **no motor connected**. Confirms the firmware can drive the GPIOs and the DRV8871 is responding on its logic inputs. |
| `test_solenoid.py` | Drives the solenoid H-bridge in 3 phases (idle, 1 s ON, OFF/settle) and logs IPROPI + nFAULT. |

## Live control server

| Script | What it does |
|---|---|
| `wattplot_control.py` | aiohttp server on `127.0.0.1:8765` that proxies to the wattplot's native API and serves the control panel UI (`docs/control.html`). Exposes `/api/state`, `/api/whoami`, `/api/switch`, `/api/number`, `/api/select`, `/api/button`, `/api/logs`, plus `/logs.html`. Includes a zeroconf/mDNS discovery, a 30 s link watchdog, and a CORS allowlist for github.io reads. **Cloudflare Access is the real auth gate on the POSTs** — see `docs/_internal/remote-access.md`. |

## Logging

| Script | What it does |
|---|---|
| `log_subscriber.py` | Subscribes to `wattplot/#` over MQTT, writes every line to a daily-rotated, gzipped `logs/wattplot.log`. Keeps 30 days by default. Pairs with the Mosquitto broker setup in `docs/logging.md`. |

## Docs / site maintenance

| Script | What it does |
|---|---|
| `audit_gallery.py` | Scores every image in `docs/gallery/` on uniqueness + variance. Low scores = flat / placeholder / broken. Catches regressions when an image is deleted but the gallery tile remains (or vice versa). |
| `parse_ci.py` | One-liner: `python tools/parse_ci.py ci_run.json` — print a flat summary of job + step conclusions from a GitHub Actions run JSON. Hand-rolled; doesn't depend on any package. |
| `add_live_nav_link.ps1` | Splice the "Live ↗" button into every HTML page that has the topnav. Idempotent (skips files that already have the class). Useful if the Live URL changes. |

## What's deliberately *not* here

- **Analysis scripts** (`analysis/*.py`) — those are the simulation
  pipeline; they don't touch the live controller.
- **3D model scripts** (`models/freecad/_run.py`,
  `models/render_3d_views.py`, etc.) — those belong with the model.
- **The ESPHome firmware** (`firmware/wattplot.yaml`) — that's the
  firmware.

## Adding a new tool

1. Resolve the key via `from _secrets import get_api_key`.
2. Use `HOST = "wattplot-controller.local"` as the default.
3. Match the existing script style (top docstring describing what it
   does, an `async def main()` entry point, `if __name__ == "__main__":
   asyncio.run(main())`).
4. Add a row to the relevant table above.
5. Update `tools/README.md` (this file) in the same PR.