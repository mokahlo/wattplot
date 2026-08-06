"""
Wattplot control panel — local Python server.

A small web server that:
  - Serves a live control panel HTML page
  - Talks to the wattplot via the native API (aioesphomeapi)
  - Exposes JSON endpoints for the panel to call

Run:  python tools/wattplot_control.py
Then open http://localhost:8765/ in a browser.

Endpoints (all JSON, POST unless noted):
  GET  /                control panel HTML
  GET  /api/state       all current values
  POST /api/switch      {"label": "Solenoid Valve", "on": true|false}
  POST /api/number      {"label": "Commanded Tilt (°)", "value": 20}
  POST /api/select      {"label": "Controller State", "option": "Normal"}
  POST /api/button      {"label": "Calibrate Actuator"}
"""
import asyncio
from pathlib import Path

import aioesphomeapi
from aiohttp import web


# ---- Config ----
WATTPLOT_HOST = "wattplot-controller.local"
WATTPLOT_KEY  = "cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU="
LOCAL_PORT    = 8765

# Entity keys (stable, computed from entity name). The control panel
# references labels, the server maps labels -> keys.
ENTITY_KEYS = {
    "Controller State":           1592049331,
    "Controller Mode":            2816441741,
    "Solenoid Mode":              3792266734,
    "Solenoid Valve":             4222604611,
    "Solenoid IPROPI Current":    182416010,
    "Solenoid nFAULT":            3413365401,
    "Solenoid Fault Alarm":       1057942567,
    "Solenoid On Time (s)":       1393952356,
    "Solenoid Budget (s)":        10022656,
    "Solenoid Max On-Time (s)":   1832551921,
    "Solenoid Battery Floor (V)": 3002951846,
    "Calibration In Progress":    2872278387,
    "Last Calibration (s)":       2252638468,
    "Last MAX Endstop Current":   516998126,
    "Last ZERO Endstop Current":  1314387666,
    "Motor IPROPI Current":       587565470,
    "Motor Current":              1965930050,
    "Actuator Bus V":             1531162880,
    "Actuator nFAULT":            1853948805,
    "Battery Voltage":            1226776003,
    "Panel Tilt":                 1386931973,
    "Commanded Tilt (\u00b0)":     2551930971,
    "WiFi Signal":                799351157,
    "Soil Moisture":              1215959833,
    "Panel Power":                2217231739,
    "Energy Today":               1447915999,
    "H-bridge IN1":               970142872,
    "H-bridge IN2":               970142875,
    "H-bridge EN":                618246967,
    "Calibrate Actuator":         3817736166,  # button
    "Water Now":                  2963331103,  # button
}

BUTTON_LABELS = {"Calibrate Actuator", "Water Now"}


# ---- API client wrapper ----
class WattplotClient:
    def __init__(self, host, key):
        self.host = host
        self.key = key
        self.api = None
        self.states = {}

    async def connect(self):
        self.api = aioesphomeapi.APIClient(self.host, 6053, noise_psk=self.key)
        await self.api.connect(login=True)
        self.api.subscribe_states(self._on_state)
        await asyncio.sleep(0.5)
        return await self.api.device_info()

    def _on_state(self, s):
        self.states[s.key] = s

    def get(self, label):
        key = ENTITY_KEYS.get(label)
        if key is None:
            return None
        s = self.states.get(key)
        if s is None or getattr(s, "missing_state", False):
            return None
        return s.state

    async def set_switch(self, label, on):
        self.api.switch_command(key=ENTITY_KEYS[label], state=bool(on))

    async def set_number(self, label, value):
        self.api.number_command(key=ENTITY_KEYS[label], state=float(value))

    async def set_select(self, label, option):
        self.api.select_command(key=ENTITY_KEYS[label], state=str(option))

    async def press_button(self, label):
        self.api.button_command(key=ENTITY_KEYS[label])

    async def refresh(self, settle_s=0.2):
        await asyncio.sleep(settle_s)


def make_state_payload(c: WattplotClient):
    out = {}
    for label in ENTITY_KEYS:
        v = c.get(label)
        if v is None:
            out[label] = None
        elif isinstance(v, bool):
            out[label] = bool(v)
        elif isinstance(v, (int, float)):
            out[label] = round(float(v), 3)
        else:
            out[label] = str(v)
    return out


# ---- HTTP handlers ----
async def handle_state(request):
    return web.json_response(make_state_payload(request.app["wp"]))


async def handle_switch(request):
    body = await request.json()
    label = body.get("label", "")
    on = bool(body.get("on", False))
    if label not in ENTITY_KEYS:
        return web.json_response({"ok": False, "error": "unknown label"}, status=400)
    c = request.app["wp"]
    await c.set_switch(label, on)
    await c.refresh(0.1)
    return web.json_response({"ok": True, "value": c.get(label)})


async def handle_number(request):
    body = await request.json()
    label = body.get("label", "")
    value = float(body.get("value", 0))
    if label not in ENTITY_KEYS:
        return web.json_response({"ok": False, "error": "unknown label"}, status=400)
    c = request.app["wp"]
    await c.set_number(label, value)
    await c.refresh(0.1)
    return web.json_response({"ok": True, "value": c.get(label)})


async def handle_select(request):
    body = await request.json()
    label = body.get("label", "")
    option = body.get("option", "")
    if label not in ENTITY_KEYS:
        return web.json_response({"ok": False, "error": "unknown label"}, status=400)
    c = request.app["wp"]
    await c.set_select(label, option)
    await c.refresh(0.1)
    return web.json_response({"ok": True, "value": c.get(label)})


async def handle_button(request):
    body = await request.json()
    label = body.get("label", "")
    if label not in BUTTON_LABELS:
        return web.json_response({"ok": False, "error": "not a button"}, status=400)
    c = request.app["wp"]
    await c.press_button(label)
    return web.json_response({"ok": True})


async def handle_index(request):
    html_path = Path(__file__).resolve().parent.parent / "docs" / "control.html"
    if html_path.exists():
        return web.Response(text=html_path.read_text(encoding="utf-8"),
                            content_type="text/html")
    return web.Response(text="<h1>docs/control.html not found</h1>",
                        content_type="text/html")


# ---- App factory ----
async def make_app():
    app = web.Application()
    wp = WattplotClient(WATTPLOT_HOST, WATTPLOT_KEY)
    print(f"Connecting to wattplot @ {WATTPLOT_HOST} ...")
    info = await wp.connect()
    print(f"  device: {info.name}  (mac: {info.mac_address})  sw: {info.esphome_version}")
    app["wp"] = wp
    app.router.add_get("/", handle_index)
    app.router.add_get("/control.html", handle_index)
    app.router.add_get("/api/state", handle_state)
    app.router.add_post("/api/switch", handle_switch)
    app.router.add_post("/api/number", handle_number)
    app.router.add_post("/api/select", handle_select)
    app.router.add_post("/api/button", handle_button)
    return app


def main():
    print(f"Wattplot control panel -> http://localhost:{LOCAL_PORT}/")
    web.run_app(make_app(), port=LOCAL_PORT, print=lambda *a, **k: None)


if __name__ == "__main__":
    main()
