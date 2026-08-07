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
  GET  /api/state       all current values, plus a _meta block carrying
                        link health (connected / stale_for_s / stale)
  GET  /api/whoami      whether the caller has a Cloudflare Access session
  POST /api/switch      {"label": "Solenoid Valve", "on": true|false}
  POST /api/number      {"label": "Commanded Tilt (°)", "value": 20}
  POST /api/select      {"label": "Controller State", "option": "Normal"}
  POST /api/button      {"label": "Calibrate Actuator"}
"""
import asyncio
import math
import time
from pathlib import Path

import aioesphomeapi
from aiohttp import web
from zeroconf.asyncio import AsyncZeroconf

from _secrets import get_api_key


# ---- Config ----
WATTPLOT_HOST = "wattplot-controller.local"
WATTPLOT_KEY  = get_api_key()
LOCAL_PORT    = 8765

# The fastest sensors push every 100 ms and several push every 1 s, so a
# healthy link is never quiet for long. If nothing arrives for this many
# seconds the link is wedged (TCP up, no data) — drop it so ReconnectLogic
# rebuilds it. This is the bug that left the panel serving a frozen
# snapshot: the old code connected once and never noticed the link die.
STALE_FORCE_RECONNECT_S = 30.0
WATCHDOG_INTERVAL_S     = 5.0

# Origins allowed to read the public endpoints cross-origin, so the
# github.io site can render live tiles. Read-only and uncredentialed:
# these responses never carry Access-Control-Allow-Credentials, so a
# browser will not attach the CF_Authorization cookie to them and no
# other site can borrow the operator's session. The control POSTs are
# deliberately absent from CORS_PATHS below — they are same-origin only.
CORS_ORIGINS = {
    "https://mokahlo.github.io",
    "http://localhost:4000",   # local `jekyll serve`
    "http://127.0.0.1:4000",
}
CORS_PATHS = {"/api/state", "/api/logs", "/api/whoami"}

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
    "Uptime":                     1324261225,
    "Free Memory":                2070763131,
    "MCU Temperature":            487821941,
    "Last Event":                 1381377912,
}

BUTTON_LABELS = {"Calibrate Actuator", "Water Now"}


class LinkDown(RuntimeError):
    """Raised when a command is attempted while the wattplot link is down."""


# ---- API client wrapper ----
class WattplotClient:
    def __init__(self, host, key):
        self.host = host
        self.key = key
        self.api = None
        self.states = {}
        self.connected = False
        self.device_info = None
        self._last_push = None      # time.monotonic() of the last state message
        self._last_push_wall = None  # time.time() equivalent, for display
        self._zc = None
        self._reconnect = None
        self._watchdog_task = None

    async def start(self):
        """Bring up the link and keep it up. Returns immediately — the
        server comes up even if the wattplot is unreachable, and
        ReconnectLogic keeps retrying with backoff in the background."""
        self._zc = AsyncZeroconf()
        self.api = aioesphomeapi.APIClient(
            self.host, 6053, None,
            noise_psk=self.key,
            zeroconf_instance=self._zc.zeroconf,
        )
        self._reconnect = aioesphomeapi.ReconnectLogic(
            client=self.api,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
            zeroconf_instance=self._zc.zeroconf,
            name=self.host,
        )
        await self._reconnect.start()
        self._watchdog_task = asyncio.create_task(self._watchdog())

    async def stop(self):
        if self._watchdog_task:
            self._watchdog_task.cancel()
        if self._reconnect:
            await self._reconnect.stop()
        if self._zc:
            await self._zc.async_close()

    async def _on_connect(self):
        self.api.subscribe_states(self._on_state)
        self._mark_push()
        self.connected = True
        try:
            self.device_info = await self.api.device_info()
            print(f"[wattplot] connected: {self.device_info.name} "
                  f"(mac {self.device_info.mac_address}, "
                  f"esphome {self.device_info.esphome_version})")
        except Exception as e:
            print(f"[wattplot] connected, device_info failed: {e}")

    async def _on_disconnect(self, expected: bool):
        self.connected = False
        print(f"[wattplot] disconnected (expected={expected}) - will retry")

    def _mark_push(self):
        self._last_push = time.monotonic()
        self._last_push_wall = time.time()

    def stale_for(self):
        """Seconds since the last state message, or None if none ever."""
        if self._last_push is None:
            return None
        return time.monotonic() - self._last_push

    async def _watchdog(self):
        """Force a reconnect if the link goes quiet while nominally up."""
        while True:
            await asyncio.sleep(WATCHDOG_INTERVAL_S)
            age = self.stale_for()
            if self.connected and age is not None and age > STALE_FORCE_RECONNECT_S:
                print(f"[wattplot] no state for {age:.0f}s - forcing reconnect")
                self.connected = False
                try:
                    await self.api.disconnect(force=True)
                except Exception as e:
                    print(f"[wattplot] forced disconnect failed: {e}")

    def _on_state(self, s):
        self.states[s.key] = s
        self._mark_push()

    def get(self, label):
        key = ENTITY_KEYS.get(label)
        if key is None:
            return None
        s = self.states.get(key)
        if s is None or getattr(s, "missing_state", False):
            return None
        return s.state

    def _require_link(self):
        """Raise if the wattplot link is down, so a command fails loudly
        instead of being swallowed by a dead client object."""
        if self.api is None or not self.connected:
            raise LinkDown("wattplot link is down")

    async def set_switch(self, label, on):
        self._require_link()
        self.api.switch_command(key=ENTITY_KEYS[label], state=bool(on))

    async def set_number(self, label, value):
        self._require_link()
        self.api.number_command(key=ENTITY_KEYS[label], state=float(value))

    async def set_select(self, label, option):
        self._require_link()
        self.api.select_command(key=ENTITY_KEYS[label], state=str(option))

    async def press_button(self, label):
        self._require_link()
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
            f = float(v)
            # NaN/inf are not valid JSON: json.dumps emits a bare `NaN`
            # token, which JSON.parse() in the browser rejects — one NaN
            # sensor would blank the whole panel. Send null instead.
            out[label] = round(f, 3) if math.isfinite(f) else None
        else:
            out[label] = str(v)

    age = c.stale_for()
    out["_meta"] = {
        "connected": c.connected,
        "stale_for_s": round(age, 1) if age is not None else None,
        "last_update_epoch": c._last_push_wall,
        "stale": (age is None) or (age > STALE_FORCE_RECONNECT_S),
        "server_epoch": time.time(),
    }
    return out


# ---- HTTP handlers ----
async def handle_state(request):
    return web.json_response(make_state_payload(request.app["wp"]))


async def handle_login(request):
    """GET /login?return_to=/control.html — the sign-in entry point.

    This path is deliberately NOT on the Access bypass list, so Cloudflare
    intercepts it and runs the email one-time-PIN flow before the request
    ever arrives here. Reaching this handler therefore means the caller is
    already authenticated, and all that is left is to bounce them back to
    the page they came from. Keeping the flow here means the Access team
    name never has to be hardcoded in the HTML.
    """
    target = request.query.get("return_to", "/control.html")
    # Only ever redirect within this site. "//evil.com" is a protocol-
    # relative URL, so checking for a leading "/" alone is not enough.
    if not target.startswith("/") or target.startswith("//"):
        target = "/control.html"
    raise web.HTTPFound(target)


async def handle_whoami(request):
    """Report whether this request carries a Cloudflare Access session.

    This endpoint is on the Access BYPASS list, so anyone may call it —
    the answer only describes *this* request. The panel uses it to decide
    whether to enable the control widgets. It is a UI hint, not a
    security boundary: the real gate is the Access policy on the POST
    endpoints, enforced at Cloudflare's edge before traffic reaches here.
    """
    authed = bool(request.cookies.get("CF_Authorization"))
    return web.json_response({
        "authed": authed,
        "email": request.headers.get("Cf-Access-Authenticated-User-Email"),
    })


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


# ---- Log file endpoints ----
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def tail_lines(path: Path, n: int) -> list[str]:
    """Return the last `n` lines of a text file, memory-efficient."""
    if not path.exists():
        return []
    block_size = 8192
    data = b""
    with open(path, "rb") as f:
        f.seek(0, 2)
        pos = f.tell()
        while pos > 0 and data.count(b"\n") <= n:
            read_size = min(block_size, pos)
            pos -= read_size
            f.seek(pos)
            data = f.read(read_size) + data
    return data.decode("utf-8", errors="replace").splitlines()[-n:]


async def handle_logs(request):
    """GET /api/logs?file=current|rotated&lines=500&level=info"""
    which = request.query.get("file", "current")
    try:
        n = int(request.query.get("lines", "500"))
    except ValueError:
        n = 500
    n = max(1, min(n, 5000))
    level = request.query.get("level", "all").lower()

    if not LOG_DIR.exists():
        return web.json_response({"lines": [], "files": [], "error": "no logs/ dir"})

    rotated = sorted(
        [p for p in LOG_DIR.glob("wattplot.*.log.gz")],
        key=lambda p: p.name, reverse=True,
    )
    current = LOG_DIR / "wattplot.log"
    current_size = current.stat().st_size if current.exists() else 0

    if which in ("current", "live"):
        if not current.exists():
            return web.json_response({"lines": [], "files": [], "error": "no wattplot.log"})
        lines = tail_lines(current, n)
    elif which == "rotated":
        import gzip
        all_lines = []
        for f in rotated:
            try:
                with gzip.open(f, "rt", encoding="utf-8", errors="replace") as gz:
                    all_lines.extend(gz.read().splitlines())
            except Exception:
                pass
        lines = all_lines[-n:]
    else:
        return web.json_response({"lines": [], "files": [], "error": f"unknown file: {which}"})

    level_prefixes = {
        "error": ("E",),
        "warn":  ("W",),
        "info":  ("I",),
        "debug": ("D", "V"),
    }
    if level in level_prefixes:
        prefixes = level_prefixes[level]
        lines = [ln for ln in lines if any(f"[{p}]" in ln for p in prefixes)]

    files = [{
        "name": p.name,
        "size": p.stat().st_size,
        "mtime": p.stat().st_mtime,
    } for p in rotated]
    files.insert(0, {
        "name": "wattplot.log",
        "size": current_size,
        "mtime": current.stat().st_mtime if current.exists() else 0,
        "current": True,
    })

    return web.json_response({
        "lines": lines,
        "files": files,
        "current_size": current_size,
        "total_size": sum(f["size"] for f in files),
    })


async def handle_logs_page(request):
    """GET /logs.html — viewer page for the wattplot.log files."""
    html_path = Path(__file__).resolve().parent.parent / "docs" / "logs.html"
    if html_path.exists():
        return web.Response(text=html_path.read_text(encoding="utf-8"),
                            content_type="text/html")
    return web.Response(text="<h1>docs/logs.html not found</h1>",
                        content_type="text/html")


# ---- App factory ----
@web.middleware
async def cors_middleware(request, handler):
    """Allow the github.io site to read the public endpoints.

    Scoped deliberately: only the read-only paths, only known origins,
    and never with credentials. A plain GET of these paths needs no
    preflight, so this stays a single response header and does not
    interact with Cloudflare Access.
    """
    response = await handler(request)
    origin = request.headers.get("Origin")
    if origin in CORS_ORIGINS and request.path in CORS_PATHS:
        response.headers["Access-Control-Allow-Origin"] = origin
        # Same URL answers differently per origin; keep caches honest.
        response.headers["Vary"] = "Origin"
    return response


@web.middleware
async def link_down_middleware(request, handler):
    """Turn a dead wattplot link into an honest 503 rather than a 500."""
    try:
        return await handler(request)
    except LinkDown:
        wp = request.app["wp"]
        age = wp.stale_for()
        return web.json_response({
            "ok": False,
            "error": "wattplot link is down — command not sent",
            "stale_for_s": round(age, 1) if age is not None else None,
        }, status=503)


async def on_shutdown(app):
    await app["wp"].stop()


async def make_app():
    app = web.Application(middlewares=[cors_middleware, link_down_middleware])
    wp = WattplotClient(WATTPLOT_HOST, WATTPLOT_KEY)
    app["wp"] = wp
    print(f"Connecting to wattplot @ {WATTPLOT_HOST} (auto-reconnecting) ...")
    # Non-blocking: the HTTP server comes up even when the wattplot is
    # unreachable, and /api/state reports connected=false instead of the
    # whole process failing to start.
    await wp.start()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", handle_index)
    app.router.add_get("/control.html", handle_index)
    app.router.add_get("/logs.html", handle_logs_page)
    app.router.add_get("/api/state", handle_state)
    app.router.add_get("/api/whoami", handle_whoami)
    app.router.add_get("/login", handle_login)
    app.router.add_get("/api/logs", handle_logs)
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
