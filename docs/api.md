# Wattplot Live Control API

The `tools/wattplot_control.py` server (port `8765`) speaks a small
JSON HTTP API on top of the ESPHome native API. This page documents
every endpoint; it's the contract for `docs/control.html` and for any
third-party client.

The Cloudflare Access policy on `control.phxtraffic.com` is the
**real** auth gate for the write endpoints. The endpoints described
below are reachable in cleartext from `localhost`; the Access
policy sits in front of the public hostname. See
[`docs/_internal/remote-access.md`](_internal/remote-access.md) for
the policy setup.

## Common conventions

- **Content type:** every request and response is `application/json`
  unless noted.
- **CORS:** read endpoints (`/api/state`, `/api/whoami`,
  `/api/logs`) carry `Access-Control-Allow-Origin` for
  `https://mokahlo.github.io`, `http://localhost:4000`,
  `http://127.0.0.1:4000`. Control POSTs are same-origin only — no
  `Access-Control-Allow-Credentials` on any endpoint.
- **Errors:** write endpoints return
  `{"ok": false, "error": "<message>"}` with an appropriate HTTP
  status (400 for bad input, 503 when the wattplot link is down).
- **NaN/inf:** sensors that return NaN or inf serialize as `null`
  in `/api/state`. Browsers reject bare `NaN` JSON tokens; sending
  `null` instead keeps the panel from blanking on a single bad
  sensor.

---

## Endpoints

### `GET /`

Returns the contents of `docs/control.html` (the panel UI). Same as
`/control.html`.

### `GET /control.html`

Same as `/`.

### `GET /logs.html`

Returns the contents of `docs/logs.html` (the log viewer UI).

### `GET /api/state`

Snapshot of every entity exposed by the firmware. The response
shape is:

```json
{
  "Controller State":          "Folding",
  "Commanded Tilt (°)":         0,
  "Panel Tilt":                 0,
  "Motor Current":              0.12,
  "Motor IPROPI Current":       0.08,
  "Panel V":                    41.2,
  "Panel Current":              1.4,
  "Panel Power":                57.7,
  "Battery Voltage":            12.6,
  "Battery SOC":                96,
  "POA Irradiance":             821.0,
  "Panel Efficiency":           null,
  "Energy Today":               0.342,
  "Energy Total":               18.5,
  "Soil Moisture":              42.3,
  "Soil Temperature":           22.1,
  "Panel Temperature":          38.5,
  "WiFi Signal":                -52,
  "Uptime":                     4823,
  "Free Memory":                184320,
  "MCU Temperature":            41,
  "Last Event":                 "Boot: Aug  6 2026 16:55:00 reason=0 heap=184320",
  "Solenoid Mode":              "Off",
  "Solenoid Valve":             false,
  "Actuator nFAULT":            false,
  "Solenoid nFAULT":            false,
  "Solenoid Fault Alarm":       false,
  "Calibration In Progress":    false,
  "Last Calibration (s)":       1730,
  "Last MAX Endstop Current":   1.12,
  "Last ZERO Endstop Current":  0.95,
  "Solenoid On Time (s)":       0,
  "Solenoid Budget (s)":        0,
  "Solenoid Max On-Time (s)":   300,
  "Actuator Bus V":             12.6,
  "_meta": {
    "connected":        true,
    "stale_for_s":      0.4,
    "last_update_epoch": 1722894812.3,
    "stale":            false,
    "server_epoch":     1722894812.7
  }
}
```

The `_meta` block is not an entity; the panel uses `connected`,
`stale_for_s`, and `stale` to decide whether to render the
stale-data banner.

**Cache:** no `Cache-Control`. The control panel polls every 2 s.

### `GET /api/whoami`

Reports whether this request carries a Cloudflare Access session.
Used by the panel to decide whether to enable the control widgets.

```json
{
  "authed": true,
  "email":  "mokahlou@gmail.com"
}
```

- `authed` is `true` when the `CF_Authorization` cookie is set (the
  caller passed the Access policy).
- `email` is the Cloudflare-asserted user email. **Trust this value
  in the UI; it comes from Cloudflare's edge, not from the request
  itself.**
- This endpoint is on the Access BYPASS list, so anyone may call it
  — the response only describes the calling request.

### `GET /login?return_to=/control.html`

Deliberately NOT on the Access bypass list. Cloudflare intercepts
the request and runs the email one-time-PIN flow. Once authed, the
caller is redirected back to `return_to` (validated to be a
same-origin path — `//evil.com` is rejected).

### `GET /api/logs?file=current|rotated&lines=500&level=info`

Returns the tail of the wattplot.log file(s).

| Param | Default | Notes |
|---|---|---|
| `file` | `current` | `current` = `logs/wattplot.log`. `rotated` = concat all `wattplot.*.log.gz`. |
| `lines` | `500` | Clamped to `[1, 5000]`. |
| `level` | `all` | `all` returns everything. `info` / `warn` / `error` filters by ESPHome log level tag. |

Response shape:

```json
{
  "lines": [
    "2026-08-06 12:00:00  [wattplot/log]  [12:00:00][I][boot:092]: === Wattplot v3.2 ===",
    "..."
  ],
  "files": [
    {"name": "wattplot.log",                "size": 12345},
    {"name": "wattplot.2026-08-05.log.1.gz", "size": 67890}
  ],
  "current_size": 12345
}
```

---

### `POST /api/switch`

Toggle a `switch:` entity. Body:

```json
{"label": "Solenoid Valve", "on": true}
```

The label must be in `ENTITY_KEYS` (see `tools/wattplot_control.py`).
Response:

```json
{"ok": true, "value": true}
```

**Returns 503 if the wattplot link is down.**

### `POST /api/number`

Set a `number:` entity. Body:

```json
{"label": "Commanded Tilt (°)", "value": 25}
```

Response:

```json
{"ok": true, "value": 25}
```

### `POST /api/select`

Set a `select:` entity. Body:

```json
{"label": "Controller Mode", "option": "Power"}
```

`option` must be a valid option for the select (firmware-defined).
Response:

```json
{"ok": true, "value": "Power"}
```

### `POST /api/button`

Press a `button:` entity. Body:

```json
{"label": "Water Now"}
```

`label` must be in `BUTTON_LABELS` (`Water Now`, `Calibrate Actuator`).
Response:

```json
{"ok": true}
```

---

## Entity labels (firmware v3.2)

The complete `ENTITY_KEYS` table lives in `tools/wattplot_control.py`.
Stable labels include:

**Numbers:** `Target Current (A)`, `I Safe (A)`, `Current Deadband
(A)`, `Commanded Tilt (°)`, `Kp (deg per A)`, `Ki (deg per (A·s))`,
`Max Step (° per s)`, `Solenoid Max On-Time (s)`,
`Battery Water Floor (V)`, `One-Off Water (s)`,
`Endstop Current Threshold (A)`.

**Selects:** `Controller State` (Normal / Monitoring / Folding /
Locked), `Controller Mode` (Power), `Solenoid Mode` (Off / Auto /
Manual).

**Switches:** `Solenoid Valve`, `Actuator H-bridge IN1 (U5a)`,
`Actuator H-bridge IN2 (U5a)`, `Actuator H-bridge EN (U5a)`. The
H-bridge switches are exposed for diagnostics — toggling them
directly bypasses the state machine.

**Buttons:** `Water Now`, `Calibrate Actuator`.

**Binary sensors:** `Actuator nFAULT`, `Solenoid nFAULT`,
`Solenoid Fault Alarm`, `Calibration In Progress`.

---

## Example: cURL

```bash
# Snapshot state
curl -s http://localhost:8765/api/state | jq ._meta

# Water for 5 s (the firmware caps at solenoid_max_water_sec = 300)
curl -s -X POST http://localhost:8765/api/button \
  -H 'Content-Type: application/json' \
  -d '{"label": "Water Now"}'

# Force a fold (override commanded tilt)
curl -s -X POST http://localhost:8765/api/select \
  -H 'Content-Type: application/json' \
  -d '{"label": "Controller State", "option": "Folding"}'
```

## Example: Python (aiohttp client)

```python
import aiohttp

async with aiohttp.ClientSession() as s:
    async with s.get("http://localhost:8765/api/state") as r:
        state = await r.json()
        print(state["Controller State"], state["Panel Tilt"])
    async with s.post("http://localhost:8765/api/number",
                      json={"label": "Commanded Tilt (°)", "value": 35}) as r:
        print(await r.json())
```

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `_meta.connected: false` | Link down or first poll before connect. | Check the server logs; the 30 s watchdog will force a reconnect. |
| `_meta.stale: true`, `stale_for_s` growing | Link TCP-up but no data. | Same watchdog; usually a WiFi blip. |
| `POST /api/switch` returns 400 `unknown label` | Label not in `ENTITY_KEYS`. | Cross-check against `firmware/wattplot.yaml` `name:` declarations. |
| `POST /api/switch` returns 503 | Wattplot link down. | Wait for `_meta.connected` to flip true. |
| CORS error from github.io | Origin not in the allowlist. | The list is in `tools/wattplot_control.py` `CORS_ORIGINS`. |