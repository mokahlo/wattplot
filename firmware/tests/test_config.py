"""
Tier 1: ESPHome config smoke test.

Runs `esphome config` against wattplot.yaml and asserts:
  - Exit code is 0 (catches YAML syntax errors, missing IDs, broken refs).
  - All required entity IDs are present (the same list the state machine
    references in its lambdas — if you remove one, the state machine
    breaks).
  - Secrets file exists (or the example is there to copy from).
  - No stray `id(script_*)` references (we hit this bug once already;
    regression guard).
  - No `.state.c_str()` on TemplateSelect objects (the 2026.7 API
    migration — another regression guard).

These tests run in CI without hardware. They are fast (<30 s) and catch
the same class of regression that ate an hour of our time during the
initial flash: API drift and missing IDs.

Only `test_esphome_config_succeeds` actually shells out to esphome, so
it alone carries the `requires_esphome` marker. Everything else here
reads wattplot.yaml as text and must run everywhere — including CI,
where esphome is not installed. Gating the text-only checks on esphome
is how this suite silently rotted through the whole v3 / rev-B pin
migration.
"""
from __future__ import annotations

import re
import subprocess

import pytest
from conftest import (
    FIRMWARE_DIR,
    SECRETS_EXAMPLE,
    SECRETS_YAML,
    WATTPLOT_YAML,
    requires_esphome,
)

# --- File presence ----------------------------------------------------------


def test_wattplot_yaml_exists():
    assert WATTPLOT_YAML.is_file(), f"missing firmware config: {WATTPLOT_YAML}"


def test_secrets_file_present():
    """Real secrets.yaml OR the example must be present."""
    assert SECRETS_YAML.is_file() or SECRETS_EXAMPLE.is_file(), (
        f"need {SECRETS_YAML.name} or {SECRETS_EXAMPLE.name}"
    )


def test_secrets_not_committed():
    """secrets.yaml must be gitignored. Sanity-check via .gitignore."""
    gitignore = FIRMWARE_DIR.parent / ".gitignore"
    if not gitignore.is_file():
        pytest.skip("no .gitignore at repo root")
    contents = gitignore.read_text(encoding="utf-8", errors="replace")
    assert "secrets.yaml" in contents, (
        "secrets.yaml is not in .gitignore — it would leak Wi-Fi creds"
    )


# --- esphome config -- the heavy hitter --------------------------------------


@requires_esphome
def test_esphome_config_succeeds():
    """`esphome config` exit code must be 0. This is the catch-all."""
    proc = subprocess.run(
        ["python", "-m", "esphome", "config", str(WATTPLOT_YAML)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(FIRMWARE_DIR),
    )
    assert proc.returncode == 0, (
        f"esphome config failed (rc={proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )


# --- Required entity IDs -----------------------------------------------------
#
# These are the entities the state machine, scripts, and intervals reference
# via `id(...)`. If you remove one of these from wattplot.yaml without also
# fixing the lambdas, the build fails with "Couldn't find ID". This test
# makes that class of breakage a fast local failure instead of a 5-minute
# compile cycle.
REQUIRED_IDS = [
    # State machine + scripts
    "controller_state",
    "controller_mode",
    "grow_light_mode",
    "frost_mode",
    "actuator_extend",
    "actuator_retract",
    "actuator_stop",
    "state_to_normal",
    "state_to_monitoring",
    "state_to_folding",
    "state_to_locked",
    # Sensors (live or stubbed)
    "panel_tilt",
    "panel_power_w",
    # NB: v3 has no `panel_voltage` — that was a v2-era stub, superseded by
    # the real INA219 bus-voltage sensor `panel_v`.
    "panel_current",
    "panel_v",
    # Energy + irradiance chain — every link in the math has to compile.
    # If anyone deletes a `template` sensor, the energy integration or
    # POA / efficiency readouts in HA will silently go missing.
    "panel_efficiency",
    "poa_irradiance",
    "energy_today",
    "energy_total",
    "battery_voltage",
    "battery_soc",
    "soil_moisture_raw",
    "soil_moisture_pct",
    "soil_temperature",
    "canopy_temperature",
    # v3 current sense (rev B): IPROPI analog taps on both DRV8871s.
    "motor_ipropi_raw",
    "motor_current_ipropi",
    "solenoid_ipropi_raw",
    "solenoid_current_ipropi",
    # Numbers (tuning + setpoints)
    "target_current",
    "i_safe",
    "deadband_a",
    "commanded_tilt",
    "kp_value",
    "ki_value",
    "max_step_per_sec",
    "frost_soil_threshold_c",
    "frost_canopy_threshold_c",
    "frost_warm_above_c",
    "frost_max_runtime_min",
    "frost_min_battery_soc",
    "frost_forecast_threshold_c",
    # Switches / outputs / binary sensors
    "grow_light_relay",
    "hb_in1_sw",
    "hb_in2_sw",
    "hb_en_sw",
    # v3.3: Frost protection (heater + USB grow light).
    # Two parallel outputs — wire one to a 12V heating mat, the
    # other to a 5V USB grow light, depending on what you have.
    "frost_heater_out",
    "frost_grow_light_out",
    "frost_heater_sw",
    "frost_grow_light_sw",
    # v3 (rev B) removed the limit switches — `limit_0` / `limit_90` are gone.
    # Homing is current-based; the nFAULT lines moved off the MCP23017 onto
    # direct GPIO.
    "actuator_nfault",
    "solenoid_nfault",
    # Globals (state)
    "g_integral",
    "g_state_entered_ms",
    "g_nws_max_wind_mph",
    "g_nws_rain_forecast",
    "g_nws_last_poll_ms",
    "g_monitoring_countdown_ms",
    "g_locked_countdown_ms",
    "g_daily_dli_mol",
    "g_dli_target_mol",
    "g_energy_total_kwh",
    "g_frost_heater_on_since_ms",
    "g_frost_light_on_since_ms",
    "g_frost_sensor_error",
    "g_frost_watchdog_trips",
    "g_frost_state",
    "g_nws_min_temp_tonight",
    "is_night_flag",
    # v3.1: current-spike endstop flags that replaced the limit switches.
    "g_at_zero",
    "g_at_max",
    # Time
    "sntp_time",
    # Light
    "status_led",
    "status_led_pwm",
    # Text sensors
    "wp_last_event",
    "wp_frost_state",
]


@pytest.mark.parametrize("entity_id", REQUIRED_IDS)
def test_required_id_present_in_yaml(entity_id):
    """Every ID the state machine references must be defined in wattplot.yaml."""
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    # Match `id: <name>` or `id(<name>)` but be careful with substrings.
    pattern = rf"(?<![\w.])id:\s*{re.escape(entity_id)}\b"
    assert re.search(pattern, contents), (
        f"required id `{entity_id}` not declared in wattplot.yaml. "
        f"Either add `id: {entity_id}` to the appropriate component, "
        f"or update REQUIRED_IDS in test_config.py if intentional."
    )


# --- Known-bad patterns (regression guards) ----------------------------------


# This pattern was the actual root cause of a 99%-complete build failure.
# If anyone re-introduces the `id(script_*)` style (e.g. via search-replace
# in the wrong direction), this test fires.
SCRIPT_ID_BAD = re.compile(r"id\(script_[a-z_]+\)", re.IGNORECASE)


def test_no_stray_script_prefix_in_lambdas():
    """No `id(script_*)` references in lambdas.

    ESPHome 2026.7 does NOT auto-prefix script ids. Scripts are defined
    with bare ids like `id: state_to_folding` and called as
    `id(state_to_folding)`. Adding the `script_` prefix breaks the build.
    """
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    matches = SCRIPT_ID_BAD.findall(contents)
    assert not matches, (
        f"found stray `script_`-prefixed id() calls: {matches}. "
        f"Use `id(<name>)` without the `script_` prefix."
    )


def test_no_select_state_c_str_in_lambdas():
    """No `.state.c_str()` on TemplateSelect objects.

    In ESPHome 2026.7, Select's `.state` member was removed. The new API
    is `.current_option()`. If anyone re-introduces `.state.c_str()` on a
    TemplateSelect, this test fires.
    """
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    # Match id(<name>).state.c_str() or id(<name>).state
    pattern = re.compile(
        r"id\((controller_state|grow_light_mode|controller_mode)\)\.state(\.|\b)"
    )
    matches = pattern.findall(contents)
    assert not matches, (
        f"found deprecated `id(...).state` on a TemplateSelect: {matches}. "
        f"Use `id(<name>).current_option()` (returns StringRef) instead."
    )


def test_board_is_esp32_s3():
    """The active board must be the S3 DevKitC-1 that v3 migrated to.

    v2.x targeted `esp32-c3-devkitm-1`. Schematic rev B moved to the
    ESP32-S3-DevKitC-1-N16R8; the whole pin map in the YAML header
    assumes it.
    """
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    assert "board: esp32-s3-devkitc-1" in contents, (
        "board declaration should be `esp32-s3-devkitc-1` for the v3 port"
    )


def test_framework_is_arduino():
    """Framework pin — was Arduino in this build (ArduinoJson, Arduino.h)."""
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    assert "type: arduino" in contents, "framework must be arduino for this build"


def test_no_imu_accel_x_references():
    """If the BMI160 is disabled, no lambda may reference its IDs.

    The `panel_tilt` template was stubbed to return NaN instead of using
    imu_accel_x/y/z. This test guards against someone copy-pasting the
    old lambda body back in.
    """
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    pattern = re.compile(r"id\(imu_accel_[xyz]\)")
    matches = pattern.findall(contents)
    assert not matches, (
        f"BMI160 is disabled but lambdas reference: {matches}. "
        f"Either re-enable the bmi160 block, or remove the lambda body."
    )


def test_both_ina219s_present():
    """v3 runs two INA219s on the shared I²C bus — this is the inverse of
    the old v2-era guard.

    In v2.x the INA219s were unpopulated, `panel_power_w` was stubbed to
    return NaN, and a test asserted that *no* lambda referenced their IDs.
    Rev B populates both (U6a at 0x40 = motor current + actuator bus V,
    U6b at 0x41 = panel V/I for the energy monitor), so the constraint is
    now the opposite: they must be configured, because `panel_power_w`
    and the 1 Hz energy integration read them.
    """
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    # Match list entries only — the file also mentions `- platform: ina219`
    # inside a comment explaining the 2026.7.2 schema change.
    blocks = re.findall(r"^\s*-\s*platform:\s*ina219\s*$", contents, re.MULTILINE)
    assert len(blocks) == 2, (
        f"expected 2 INA219 sensor blocks, found {len(blocks)}"
    )
    for address in ("0x40", "0x41"):
        assert f"address: {address}" in contents, (
            f"INA219 at {address} missing — v3 needs both U6a (0x40) and "
            f"U6b (0x41) on i2c_main"
        )
    for entity in ("ina_motor", "ina_panel", "motor_current", "panel_current", "panel_v"):
        assert re.search(rf"(?<![\w.])id:\s*{entity}\b", contents), (
            f"INA219 entity `{entity}` not declared — panel_power_w and the "
            f"energy integration depend on it"
        )


def test_no_dallas_temp_references():
    """DS18B20 is disabled; no lambda may read panel_temperature."""
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    pattern = re.compile(r"id\(panel_temperature\)")
    matches = pattern.findall(contents)
    assert not matches, (
        f"DS18B20 is disabled but lambdas reference panel_temperature: {matches}"
    )


# --- Logging + time sanity --------------------------------------------------


def test_log_level_is_valid():
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    m = re.search(r"level:\s*(\w+)", contents)
    assert m, "logger.level not set"
    level = m.group(1).upper()
    assert level in {"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "VERBOSE"}, (
        f"unexpected log level: {level}"
    )


def test_timezone_set_to_phoenix():
    """Wattplot is in Phoenix. Timezone mismatch = wrong DLI estimate."""
    contents = WATTPLOT_YAML.read_text(encoding="utf-8")
    assert "America/Phoenix" in contents, (
        "timezone must be America/Phoenix — DLI logic depends on it"
    )


# --- Build artifact stale check --------------------------------------------


def test_no_committed_build_artifacts():
    """The .esphome build dir must be gitignored.

    The ignore lives in firmware/.gitignore (ESPHome writes its own), not
    the repo root. The root file only mentions `.esphome` incidentally, via
    the `firmware/.esphome_*.log` pattern — which is why checking the root
    used to pass even with the build dir untracked-but-unignored.
    """
    gitignore = FIRMWARE_DIR / ".gitignore"
    assert gitignore.is_file(), (
        f"missing {gitignore} — ESPHome's build dir would be left untracked "
        f"but unignored (1+ GB of toolchain cache)"
    )
    contents = gitignore.read_text(encoding="utf-8", errors="replace")
    assert re.search(r"^/?\.esphome/?$", contents, re.MULTILINE), (
        f".esphome build artifacts must be gitignored in {gitignore} "
        f"(1+ GB of toolchain cache)"
    )
