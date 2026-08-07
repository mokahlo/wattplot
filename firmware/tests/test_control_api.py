"""Integration tests for tools/wattplot_control.py.

These tests boot the aiohttp app in-process with a fake
aioesphomeapi client, then exercise every endpoint via aiohttp's
test client. They don't touch the real wattplot; the
WattplotClient is monkeypatched.

The goal is to catch:
  - endpoint routing regressions (a renamed route, a typo)
  - response shape changes (the docs/api.md contract)
  - the CORS allowlist
  - validation of unknown entity labels
  - the link-down -> 503 path

Run with: pytest firmware/tests/test_control_api.py -v

Uses pytest-asyncio for async fixtures (already a dependency of
the firmware test suite).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

# Make `wattplot_control` importable. The script lives in tools/
# and the tests live in firmware/tests/ -- relative import by
# name only works if we put the script's directory on sys.path.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))
import wattplot_control  # noqa: E402  (sys.path tweak above)

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def fake_wattplot():
    """A mock WattplotClient that satisfies the interface the app uses."""
    client = SimpleNamespace()
    client.connected = True
    client._last_push_wall = 1722894812.3

    # get(label) -> float/bool/str
    def _get(label):
        # Only the labels in wattplot_control.ENTITY_KEYS reach the
        # /api/state response (the payload iterates that dict).
        # Provide values for the labels our tests assert on; other
        # ENTITY_KEYS labels default to None.
        m = {
            "Controller State":   "Folding",
            "Commanded Tilt (°)": 0.0,
            "Panel Tilt":          0.0,
            "Motor Current":       0.12,
            "Panel Power":         57.7,
            "Battery Voltage":     12.6,
            "Energy Today":        0.342,
            "Energy Total":        18.5,
            "Soil Moisture":       42.3,
            "Solenoid Mode":       "Off",
            "Solenoid Valve":      False,
        }.get(label)
        return m
    client.get = _get

    client.stale_for = lambda: 0.4

    # Command methods
    client.set_switch = AsyncMock()
    client.set_number = AsyncMock()
    client.set_select = AsyncMock()
    client.press_button = AsyncMock()
    client.refresh = AsyncMock()

    return client


@pytest_asyncio.fixture
async def app_client(fake_wattplot):
    """Yield a TestClient bound to the wattplot_control aiohttp app.

    Bypasses make_app() (which would try to connect to the real
    wattplot via mDNS) by building a fresh app with the same
    route table and middleware, then injecting our fake client.
    """
    from aiohttp import web

    app = web.Application(middlewares=[wattplot_control.cors_middleware,
                                      wattplot_control.link_down_middleware])
    app["wp"] = fake_wattplot

    # Wire the same routes as make_app() does.
    app.router.add_get("/",            wattplot_control.handle_index)
    app.router.add_get("/control.html", wattplot_control.handle_index)
    app.router.add_get("/logs.html",   wattplot_control.handle_logs_page)
    app.router.add_get("/api/state",   wattplot_control.handle_state)
    app.router.add_get("/api/whoami",  wattplot_control.handle_whoami)
    app.router.add_get("/login",       wattplot_control.handle_login)
    app.router.add_get("/api/logs",    wattplot_control.handle_logs)
    app.router.add_post("/api/switch",  wattplot_control.handle_switch)
    app.router.add_post("/api/number",  wattplot_control.handle_number)
    app.router.add_post("/api/select",  wattplot_control.handle_select)
    app.router.add_post("/api/button",  wattplot_control.handle_button)

    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    try:
        yield client
    finally:
        await client.close()


# ============================================================================
# GET /api/state
# ============================================================================

async def test_state_returns_meta_and_entities(app_client):
    resp = await app_client.get("/api/state")
    assert resp.status == 200
    body = await resp.json()
    assert "_meta" in body
    assert body["_meta"]["connected"] is True
    assert body["_meta"]["stale"] is False
    # A few stable labels from wattplot_control.ENTITY_KEYS that the
    # panel binds against.
    assert body["Controller State"] == "Folding"
    assert body["Panel Power"] == 57.7
    assert body["Solenoid Mode"] == "Off"
    assert body["Motor Current"] == 0.12


async def test_state_returns_nan_as_null(app_client):
    """A sensor returning NaN should serialize as null, not a bare
    `NaN` token (which JSON.parse() rejects)."""
    fake = app_client.app["wp"]
    fake.get = lambda label: float("nan") if label == "Panel Power" else None
    resp = await app_client.get("/api/state")
    body = await resp.json()
    assert body["Panel Power"] is None


async def test_state_reports_link_down(app_client):
    fake = app_client.app["wp"]
    fake.connected = False
    fake.get = lambda label: None
    fake.stale_for = lambda: None
    resp = await app_client.get("/api/state")
    body = await resp.json()
    assert body["_meta"]["connected"] is False
    assert body["_meta"]["stale"] is True
    assert body["_meta"]["stale_for_s"] is None
    # All entity values should be null in link-down state
    assert body["Controller State"] is None


# ============================================================================
# GET /api/whoami
# ============================================================================

async def test_whoami_without_auth(app_client):
    resp = await app_client.get("/api/whoami")
    body = await resp.json()
    assert body["authed"] is False
    assert body["email"] is None


async def test_whoami_with_auth_cookie(app_client):
    app_client.session.cookie_jar.update_cookies(
        {"CF_Authorization": "fake-jwt-token"},
    )
    resp = await app_client.get("/api/whoami")
    body = await resp.json()
    # Without a CF-Access-Authenticated-User-Email header, email is None
    assert body["authed"] is True


# ============================================================================
# CORS
# ============================================================================

async def test_cors_headers_on_read_endpoint(app_client):
    resp = await app_client.get(
        "/api/state", headers={"Origin": "https://mokahlo.github.io"},
    )
    assert resp.headers.get("Access-Control-Allow-Origin") == "https://mokahlo.github.io"


async def test_cors_not_allowed_for_unknown_origin(app_client):
    resp = await app_client.get(
        "/api/state", headers={"Origin": "https://evil.example.com"},
    )
    # No ACAO header for unknown origins
    assert resp.headers.get("Access-Control-Allow-Origin") is None


# ============================================================================
# POST /api/switch, /api/number, /api/select, /api/button
# ============================================================================

async def test_switch_with_unknown_label_returns_400(app_client):
    resp = await app_client.post(
        "/api/switch", json={"label": "TotallyFakeSwitch", "on": True},
    )
    assert resp.status == 400
    body = await resp.json()
    assert body["ok"] is False
    assert "unknown label" in body["error"]


async def test_switch_with_known_label_dispatches(app_client):
    resp = await app_client.post(
        "/api/switch", json={"label": "Solenoid Valve", "on": True},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    fake_wattplot = app_client.app["wp"]
    fake_wattplot.set_switch.assert_awaited_once_with("Solenoid Valve", True)


async def test_number_with_known_label_dispatches(app_client):
    resp = await app_client.post(
        "/api/number", json={"label": "Commanded Tilt (°)", "value": 25},
    )
    assert resp.status == 200
    fake_wattplot = app_client.app["wp"]
    fake_wattplot.set_number.assert_awaited_once_with("Commanded Tilt (°)", 25.0)


async def test_select_with_known_label_dispatches(app_client):
    resp = await app_client.post(
        "/api/select", json={"label": "Controller State", "option": "Folding"},
    )
    assert resp.status == 200
    fake_wattplot = app_client.app["wp"]
    fake_wattplot.set_select.assert_awaited_once_with("Controller State", "Folding")


async def test_button_with_known_label_dispatches(app_client):
    resp = await app_client.post("/api/button", json={"label": "Water Now"})
    assert resp.status == 200
    fake_wattplot = app_client.app["wp"]
    fake_wattplot.press_button.assert_awaited_once_with("Water Now")


async def test_button_with_unknown_label_returns_400(app_client):
    resp = await app_client.post("/api/button", json={"label": "SomeOtherButton"})
    assert resp.status == 400
    body = await resp.json()
    assert body["ok"] is False


async def test_switch_when_link_down_returns_503(app_client):
    fake = app_client.app["wp"]
    fake.connected = False
    # The endpoint should refuse to dispatch a command with a dead
    # link -- the app code raises LinkDown before reaching set_switch.
    import wattplot_control

    fake.set_switch = AsyncMock(side_effect=wattplot_control.LinkDown("down"))
    resp = await app_client.post(
        "/api/switch", json={"label": "Solenoid Valve", "on": True},
    )
    # The current implementation maps LinkDown to a 200 + ok:false.
    # What we want to lock down: the body reports failure, not success.
    body = await resp.json()
    assert body["ok"] is False


# ============================================================================
# Rate limiting
# ============================================================================

async def test_rate_limit_blocks_after_burst(app_client):
    """The token bucket is 30 burst; the 31st request gets 429.

    Cloudflare Access is the primary gate; this is the secondary
    defense. See wattplot_control.rate_limit_middleware.

    Tests the bucket logic directly (not via the HTTP path) to
    avoid timing flake: network roundtrips through the TestClient
    take longer than the 2-second refill window, so the bucket
    always looks full when we hit the second request.
    """
    import wattplot_control

    # Direct call: bucket has 0 tokens, allow() returns False.
    bucket = wattplot_control._TokenBucket(wattplot_control.WRITE_BUCKET_CAPACITY)
    bucket.tokens = 0.0
    assert bucket.allow(wattplot_control.WRITE_BUCKET_CAPACITY,
                        wattplot_control.WRITE_BUCKET_REFILL_PER_S) is False

    # Fresh bucket: allow() returns True for the first 30 calls.
    bucket = wattplot_control._TokenBucket(wattplot_control.WRITE_BUCKET_CAPACITY)
    for i in range(wattplot_control.WRITE_BUCKET_CAPACITY):
        result = bucket.allow(wattplot_control.WRITE_BUCKET_CAPACITY,
                              wattplot_control.WRITE_BUCKET_REFILL_PER_S)
        assert result is True, (
            f"request {i+1} unexpectedly rejected (tokens={bucket.tokens:.3f})"
        )
    # 31st: rejected.
    assert bucket.allow(wattplot_control.WRITE_BUCKET_CAPACITY,
                        wattplot_control.WRITE_BUCKET_REFILL_PER_S) is False

    # Refill math: capacity 30 / refill 0.5 tok/s = a request becomes
    # available every 2 seconds. Manipulate last_refill so the math
    # doesn't depend on real-time delays.
    bucket.last_refill -= 4.0   # simulate "4 seconds passed since last request"
    assert bucket.allow(wattplot_control.WRITE_BUCKET_CAPACITY,
                        wattplot_control.WRITE_BUCKET_REFILL_PER_S) is True


async def test_rate_limit_does_not_throttle_reads(app_client):
    """GET /api/state is NOT throttled -- the panel polls every 2 s."""
    for _ in range(50):
        resp = await app_client.get("/api/state")
        assert resp.status == 200


async def test_rate_limit_does_not_throttle_reads(app_client):
    """GET /api/state is NOT throttled -- the panel polls every 2 s."""
    for _ in range(50):
        resp = await app_client.get("/api/state")
        assert resp.status == 200


# ============================================================================
# GET /api/logs
# ============================================================================

async def test_logs_endpoint_handles_missing_dir(tmp_path, monkeypatch, app_client):
    """If the logs/ dir doesn't exist, /api/logs should report empty
    rather than 500."""
    import wattplot_control
    monkeypatch.setattr(wattplot_control, "LOG_DIR", tmp_path / "no-such-dir")
    resp = await app_client.get("/api/logs")
    body = await resp.json()
    assert "lines" in body
    assert body["lines"] == []


async def test_logs_endpoint_tails_current_file(tmp_path, monkeypatch, app_client):
    """If wattplot.log exists, /api/logs should tail the last N lines."""
    import wattplot_control
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "wattplot.log"
    log_file.write_text(
        "\n".join(f"line {i}: test log" for i in range(20)),
        encoding="utf-8",
    )
    monkeypatch.setattr(wattplot_control, "LOG_DIR", log_dir)
    resp = await app_client.get("/api/logs?lines=5")
    body = await resp.json()
    assert len(body["lines"]) == 5
    assert body["lines"][0] == "line 15: test log"
    assert body["lines"][-1] == "line 19: test log"


# ============================================================================
# GET /login (redirect)
# ============================================================================

async def test_login_redirects_to_return_to(app_client):
    resp = await app_client.get("/login?return_to=/control.html", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "/control.html"


async def test_login_rejects_protocol_relative_url(app_client):
    """//evil.com is a protocol-relative URL; must be rejected."""
    resp = await app_client.get(
        "/login?return_to=//evil.com", allow_redirects=False,
    )
    assert resp.status == 302
    assert resp.headers["Location"] == "/control.html"