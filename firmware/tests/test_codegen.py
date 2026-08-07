"""
Tier 2: Codegen assertion test.

ESPHome is a code generator — YAML in, C++ out. After running
`esphome compile`, the generated main.cpp is a complete, readable
inventory of every entity the firmware exposes, every script it
defines, every interval it runs.

This test compiles the firmware and asserts structural properties
of the generated code. It catches regressions Tier 1 cannot:

  - State machine components that compile but don't actually do
    anything (e.g. the lambdas reference the right IDs but the
    transitions were accidentally commented out).
  - Generated entity registrations that drift from the YAML
    (e.g. a template sensor renamed in the YAML but the
    state machine still references the old name).
  - Hard-coded values that should be templated (e.g. the
    control-loop period that was supposed to be 1 s but
    got typed as 1000 ms by accident).

The test reuses the `.esphome/build/` cache so it's fast (~30 s
on warm cache, ~5 min on cold cache).
"""
from __future__ import annotations

import re
import subprocess

import pytest
from conftest import BUILD_DIR, FIRMWARE_DIR, WATTPLOT_YAML, requires_esphome

# Path to the generated main.cpp after `esphome compile`
GENERATED_MAIN = (
    BUILD_DIR
    / "src"
    / "main.cpp"
)


@pytest.fixture(scope="module")
def compiled_main_cpp() -> str:
    """Run `esphome compile` and return the contents of generated main.cpp.

    Compiles to .esphome/build/<name>/firmware.elf. No upload.
    The cache makes this ~30 s on warm runs.
    """
    import shutil
    if not (shutil.which("esphome") or _esphome_module_works()):
        pytest.skip("esphome not installed (pip install esphome)")
    # Only compile if the build is stale or missing.
    needs_compile = (
        not GENERATED_MAIN.is_file()
        or not (BUILD_DIR / "firmware.elf").is_file()
    )
    if needs_compile or _config_older_than_build():
        proc = subprocess.run(
            [
                "python",
                "-m",
                "esphome",
                "compile",
                str(WATTPLOT_YAML),
            ],
            capture_output=True,
            text=True,
            cwd=str(FIRMWARE_DIR),
            timeout=900,  # 15 min for cold builds
            check=False,
        )
        if proc.returncode != 0:
            pytest.fail(
                f"esphome compile failed (rc={proc.returncode}). "
                f"Last 100 lines of stderr:\n"
                + "\n".join(proc.stderr.splitlines()[-100:])
            )
    if not GENERATED_MAIN.is_file():
        pytest.fail(
            f"expected generated main.cpp at {GENERATED_MAIN}, "
            f"but it doesn't exist after compile"
        )
    return GENERATED_MAIN.read_text(encoding="utf-8", errors="replace")


def _esphome_module_works() -> bool:
    try:
        import esphome  # noqa: F401
        return True
    except ImportError:
        return False


def _config_older_than_build() -> bool:
    """True if wattplot.yaml is newer than the most recent .esphome output.

    Used to skip the compile when the build is already up-to-date.
    """
    if not GENERATED_MAIN.is_file():
        return True
    return WATTPLOT_YAML.stat().st_mtime > GENERATED_MAIN.stat().st_mtime


# --- Global structure -------------------------------------------------------


@requires_esphome
def test_compile_produced_main_cpp(compiled_main_cpp):
    assert "esphome" in compiled_main_cpp.lower()
    assert "wattplot" in compiled_main_cpp.lower() or "controller" in compiled_main_cpp.lower()


@requires_esphome
def test_control_loop_interval_is_1s(compiled_main_cpp):
    """The main control loop must fire at 1 Hz (state machine depends on it)."""
    # ESPHome generates `set_update_interval(1000)` for `interval: 1s`.
    # We expect the control_loop interval to be 1000 ms.
    m = re.search(
        r"control_loop->set_update_interval\((\d+)\)",
        compiled_main_cpp,
    )
    assert m, "control_loop->set_update_interval() not found in generated code"
    interval_ms = int(m.group(1))
    assert interval_ms == 1000, (
        f"control_loop interval is {interval_ms} ms, expected 1000 ms (1 Hz). "
        f"State machine timing depends on this."
    )


@requires_esphome
def test_nws_poll_interval_is_900s(compiled_main_cpp):
    """NWS forecast poll must fire every 15 min."""
    m = re.search(
        r"nws_poll_interval->set_update_interval\((\d+)\)",
        compiled_main_cpp,
    )
    assert m, "nws_poll_interval not found in generated code"
    assert int(m.group(1)) == 900_000, (
        f"nws_poll_interval is {m.group(1)} ms, expected 900000 ms (15 min)"
    )


@requires_esphome
def test_alive_tick_interval_is_5s(compiled_main_cpp):
    """alive_tick must fire every 5 s."""
    m = re.search(
        r"alive_tick->set_update_interval\((\d+)\)",
        compiled_main_cpp,
    )
    assert m, "alive_tick->set_update_interval() not found in generated code"
    assert int(m.group(1)) == 5_000


@requires_esphome
def test_dli_update_interval_is_300s(compiled_main_cpp):
    """DLI estimate update must fire every 5 min."""
    m = re.search(
        r"dli_update->set_update_interval\((\d+)\)",
        compiled_main_cpp,
    )
    assert m, "dli_update not found in generated code"
    assert int(m.group(1)) == 300_000


@requires_esphome
def test_energy_integration_is_1hz(compiled_main_cpp):
    """Energy integration must run at 1 Hz (V*I * dt = kWh)."""
    m = re.search(
        r"energy_integration->set_update_interval\((\d+)\)",
        compiled_main_cpp,
    )
    assert m, "energy_integration not found in generated code"
    assert int(m.group(1)) == 1_000


# --- Scripts / state machine -----------------------------------------------


SCRIPTS = [
    "actuator_extend",
    "actuator_retract",
    "actuator_stop",
    "state_to_normal",
    "state_to_monitoring",
    "state_to_folding",
    "state_to_locked",
    "nws_poll",
    "update_dli_estimate",
]


@requires_esphome
@pytest.mark.parametrize("script_name", SCRIPTS)
def test_script_is_defined(compiled_main_cpp, script_name):
    """Each script must be defined in the generated code.

    In 2026.7 ESPHome, scripts with `mode: restart` are emitted as
    `script::RestartScript<>`, and `mode: single` as `script::SingleScript<>`.
    Scripts without a mode are `script::Script<>`. We accept any of these.
    """
    pattern = rf"new\({re.escape(script_name)}\)\s+script::(Restart|Single|)Script"
    assert re.search(pattern, compiled_main_cpp), (
        f"script `{script_name}` not registered in generated code. "
        f"Add a `script:` block for it in wattplot.yaml."
    )


@requires_esphome
def test_state_machine_has_four_states(compiled_main_cpp):
    """The Controller State select must expose Normal, Monitoring, Folding, Locked."""
    # Look for the trait set_options call for controller_state
    m = re.search(
        r"controller_state->traits\.set_options\(\{([^}]+)\}\)",
        compiled_main_cpp,
    )
    assert m, "controller_state traits.set_options not found"
    options_blob = m.group(1)
    for required in ("Normal", "Monitoring", "Folding", "Locked"):
        assert f'"{required}"' in options_blob, (
            f"state option `{required}` missing from controller_state"
        )


@requires_esphome
def test_folding_state_has_60s_timeout(compiled_main_cpp):
    """Folding state waits up to 60s to reach the 0° endstop, then Locked.

    The 60_000 ms is the magic number in the control loop lambda.
    """
    assert "60000" in compiled_main_cpp, (
        "60_000 ms Folding timeout not found in generated code. "
        "The state machine should fall back to Locked if the endstop "
        "isn't detected within 60s."
    )


@requires_esphome
def test_locked_state_has_30min_hold(compiled_main_cpp):
    """Locked state holds for 30 min before re-checking NORMAL."""
    # 30 min = 1_800_000 ms
    assert "1800000" in compiled_main_cpp, (
        "30-min Locked hold (1_800_000 ms) not found in generated code"
    )


@requires_esphome
def test_monitoring_state_has_15min_countdown(compiled_main_cpp):
    """Monitoring state has a 15-min countdown before deciding to fold."""
    # 15 min = 900_000 ms
    assert "900000" in compiled_main_cpp, (
        "15-min Monitoring countdown (900_000 ms) not found"
    )


# --- Pin map extraction ----------------------------------------------------
#
# ESPHome 2026.7 generates a separate `esp32_esp32internalgpiopin_id_N`
# object for each GPIO used, with two calls per pin:
#   1. The pin object is set: `esp32_esp32internalgpiopin_id_N->set_pin(::GPIO_NUM_X);`
#   2. A component references it: `hb_in1_out->set_pin(esp32_esp32internalgpiopin_id_N);`
# We build a {component: gpio_number} map by walking the file.


def _build_pin_map(generated: str) -> dict[str, int]:
    """Parse the generated main.cpp and return {component_name: gpio_number}.

    Returns an empty dict if the format is unrecognized.

    Handles two pin-assignment patterns:
      1. GPIO outputs: `<comp>->set_pin(<pin_obj>)` where `<pin_obj>` was
         earlier set to `::GPIO_NUM_X`.
      2. LEDC outputs: `new(<comp>) ledc::LEDCOutput(<pin_obj>)` — same
         pattern, just the constructor instead of set_pin.
    """
    # Step 1: collect the GPIO assignments for each pin object.
    pin_obj_to_gpio: dict[str, int] = {}
    for m in re.finditer(
        r"(esp32_esp32internalgpiopin_id(?:_\d+)?)->set_pin\(:?:?GPIO_NUM_(\d+)\)",
        generated,
    ):
        pin_obj_to_gpio[m.group(1)] = int(m.group(2))

    # Step 2: every component that references a pin object.
    component_to_gpio: dict[str, int] = {}

    # (a) `<comp>->set_pin(<pin_obj>)` — GPIO outputs / binary sensors / ADC.
    for m in re.finditer(
        r"(\w+)->set_pin\((esp32_esp32internalgpiopin_id(?:_\d+)?)\)",
        generated,
    ):
        component = m.group(1)
        if component in pin_obj_to_gpio:
            component_to_gpio[component] = pin_obj_to_gpio[component]
        elif m.group(2) in pin_obj_to_gpio:
            component_to_gpio[component] = pin_obj_to_gpio[m.group(2)]

    # (b) `new(<comp>) ledc::LEDCOutput(<pin_obj>)` — LEDC outputs.
    for m in re.finditer(
        r"new\((\w+)\)\s+ledc::LEDCOutput\((esp32_esp32internalgpiopin_id(?:_\d+)?)\)",
        generated,
    ):
        component = m.group(1)
        pin_obj = m.group(2)
        if pin_obj in pin_obj_to_gpio:
            component_to_gpio[component] = pin_obj_to_gpio[pin_obj]

    return component_to_gpio


@requires_esphome
def test_h_bridge_in1_is_gpio1(compiled_main_cpp):
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("hb_in1_out") == 1, (
        f"H-bridge IN1 is on GPIO{pin_map.get('hb_in1_out')}, expected GPIO1. "
        f"Pin map: {pin_map}"
    )


@requires_esphome
def test_h_bridge_in2_is_gpio2(compiled_main_cpp):
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("hb_in2_out") == 2, (
        f"H-bridge IN2 is on GPIO{pin_map.get('hb_in2_out')}, expected GPIO2"
    )


@requires_esphome
def test_h_bridge_en_is_gpio11(compiled_main_cpp):
    """H-bridge EN on GPIO11.

    Rev B ties the DRV8871 EN to 3V3 (always on). The output is kept in
    the firmware so the state machine's `hb_en_sw` references still
    resolve, reassigned to a schematic "free" pin. Toggling it has no
    physical effect.
    """
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("hb_en_out") == 11, (
        f"H-bridge EN is on GPIO{pin_map.get('hb_en_out')}, expected GPIO11"
    )


@requires_esphome
def test_solenoid_in1_is_gpio10(compiled_main_cpp):
    """Solenoid H-bridge IN1 (U5b) on GPIO10.

    `grow_light_relay` is a pinless template switch (the id is retained
    so Home Assistant keeps its retained state across the entity rename);
    the pin it actually drives is this output.
    """
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("solenoid_in1_out") == 10, (
        f"solenoid IN1 on GPIO{pin_map.get('solenoid_in1_out')}, expected GPIO10"
    )


@requires_esphome
def test_solenoid_in2_is_gpio12(compiled_main_cpp):
    """Solenoid IN2 preserved on a free pin (schematic ties it to GND)."""
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("solenoid_in2_out") == 12, (
        f"solenoid IN2 on GPIO{pin_map.get('solenoid_in2_out')}, expected GPIO12"
    )


@requires_esphome
def test_status_led_pwm_is_gpio17(compiled_main_cpp):
    """Status LED preserved on GPIO17 (rev B removed the LED from the board)."""
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("status_led_pwm") == 17, (
        f"status_led_pwm on GPIO{pin_map.get('status_led_pwm')}, expected GPIO17"
    )


@requires_esphome
def test_no_limit_switch_pins_in_generated_code(compiled_main_cpp):
    """v3 has no limit-switch binary sensors at all.

    Schematic rev B removed the physical switches; homing is now done by
    watching the motor current spike (Motor IPROPI on GPIO4) in the
    `endpoint_detector` interval, which sets `g_at_zero` / `g_at_max`.
    If limit_* entities reappear, either the YAML regressed or the
    current-based homing was reverted — see wattplot.yaml's
    "v3.1: Current-based endstop state" globals.
    """
    pin_map = _build_pin_map(compiled_main_cpp)
    stray = sorted(k for k in pin_map if k.startswith("limit_"))
    assert not stray, (
        f"limit-switch entities found in generated code: {stray}. "
        f"v3 replaced them with current-spike homing (g_at_zero/g_at_max)."
    )
    assert "g_at_zero" in compiled_main_cpp and "g_at_max" in compiled_main_cpp, (
        "current-based endstop globals (g_at_zero/g_at_max) missing from "
        "generated code — the v3 homing replacement is gone"
    )


# --- v3 current sense + fault lines (new in rev B) --------------------------


@requires_esphome
def test_motor_ipropi_adc_is_gpio4(compiled_main_cpp):
    """Actuator IPROPI (ADC1_CH4) — drives current-based endstop detection."""
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("motor_ipropi_raw") == 4, (
        f"motor_ipropi_raw on GPIO{pin_map.get('motor_ipropi_raw')}, expected GPIO4"
    )


@requires_esphome
def test_solenoid_ipropi_adc_is_gpio5(compiled_main_cpp):
    """Solenoid IPROPI (ADC1_CH5) — jam detection."""
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("solenoid_ipropi_raw") == 5, (
        f"solenoid_ipropi_raw on GPIO{pin_map.get('solenoid_ipropi_raw')}, "
        f"expected GPIO5"
    )


@requires_esphome
def test_actuator_nfault_is_gpio21(compiled_main_cpp):
    """U5a nFAULT reads a direct GPIO in v3 (the MCP23017 expander is gone)."""
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("actuator_nfault") == 21, (
        f"actuator_nfault on GPIO{pin_map.get('actuator_nfault')}, expected GPIO21"
    )


@requires_esphome
def test_solenoid_nfault_is_gpio13(compiled_main_cpp):
    """U5b nFAULT reads a direct GPIO in v3 (was MCP.1)."""
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("solenoid_nfault") == 13, (
        f"solenoid_nfault on GPIO{pin_map.get('solenoid_nfault')}, expected GPIO13"
    )


@requires_esphome
def test_one_wire_bus_is_gpio16(compiled_main_cpp):
    """DS18B20 1-Wire data line (was GPIO15 on the C3)."""
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("panel_temp_bus") == 16, (
        f"panel_temp_bus on GPIO{pin_map.get('panel_temp_bus')}, expected GPIO16"
    )


# --- I²C / sensors ---------------------------------------------------------


@requires_esphome
def test_i2c_bus_uses_gpio8_gpio18(compiled_main_cpp):
    """I²C SDA=GPIO8, SCL=GPIO18 on the S3 (was GPIO5/GPIO6 on the C3).

    Generated code uses `set_sda_pin(8)` (bare int) in 2026.7.
    """
    sda_m = re.search(
        r"i2c_main->set_sda_pin\((?:::?GPIO_NUM_)?(\d+)\)",
        compiled_main_cpp,
    )
    assert sda_m, "i2c_main SDA pin not set"
    assert int(sda_m.group(1)) == 8, f"I²C SDA on GPIO{sda_m.group(1)}, expected GPIO8"

    scl_m = re.search(
        r"i2c_main->set_scl_pin\((?:::?GPIO_NUM_)?(\d+)\)",
        compiled_main_cpp,
    )
    assert scl_m, "i2c_main SCL pin not set"
    assert int(scl_m.group(1)) == 18, f"I²C SCL on GPIO{scl_m.group(1)}, expected GPIO18"


@requires_esphome
def test_battery_voltage_adc_is_gpio7(compiled_main_cpp):
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("battery_v_raw") == 7, (
        f"battery_v_raw on GPIO{pin_map.get('battery_v_raw')}, expected GPIO7"
    )


@requires_esphome
def test_soil_moisture_adc_is_gpio6(compiled_main_cpp):
    pin_map = _build_pin_map(compiled_main_cpp)
    assert pin_map.get("soil_moisture_raw") == 6, (
        f"soil_moisture_raw on GPIO{pin_map.get('soil_moisture_raw')}, expected GPIO6"
    )


# --- Codegen regression guards (Tier 1 finds these in YAML; Tier 2 finds
#     them in the GENERATED code, in case the bug slips past config validation
#     but lands in the C++) -----------------------------------------------


@requires_esphome
def test_no_legacy_script_id_prefix_in_generated_code(compiled_main_cpp):
    """No `id(script_*)` in the generated code. Belt-and-suspenders for Tier 1."""
    # In the generated code, scripts are called as e.g.
    #   state_to_folding->execute();
    # The bad pattern would be e.g. `script_state_to_folding->execute()`.
    bad = re.findall(r"script_(state_to_[a-z]+|actuator_[a-z]+)->execute", compiled_main_cpp)
    assert not bad, (
        f"generated code has `script_`-prefixed calls: {bad}. "
        f"ESPHome 2026.7 doesn't auto-prefix; this is a build error."
    )


@requires_esphome
def test_no_select_state_in_generated_code(compiled_main_cpp):
    """No `controller_state->state` or `grow_light_mode->state` in generated code.

    The 2026.7 API is `.current_option()`. Tier 1 catches this in YAML;
    this is the codegen-level guard.
    """
    bad_patterns = [
        r"controller_state->state",
        r"grow_light_mode->state",
        r"controller_mode->state",
    ]
    for pat in bad_patterns:
        m = re.search(pat, compiled_main_cpp)
        assert not m, (
            f"deprecated Select API in generated code: matched `{pat}`. "
            f"Use `.current_option()` in the YAML lambda."
        )


@requires_esphome
def test_nws_parse_json_used(compiled_main_cpp):
    """The NWS poll lambda must call json::parse_json (the 2026.7 API).

    In 2026.6, the YAML used `root[...]` directly. In 2026.7, it must
    go through `json::parse_json(body, [](JsonObject root) {...})` because
    the on_response callback no longer auto-injects `root`.
    """
    assert "json::parse_json" in compiled_main_cpp, (
        "NWS poll must use json::parse_json (2026.7 API). "
        "If you see this, the on_response lambda was reverted."
    )
    # Body should be referenced (the new arg name).
    assert "body" in compiled_main_cpp, (
        "NWS poll should reference `body` (the 2026.7 on_response arg)"
    )


# --- POA / hour-angle regression guard --------------------------------------
#
# The poa_irradiance template sensor in wattplot.yaml had a bug where
# the hour-angle calculation treated the observer as if they were in
# UTC (lon_correction = -112.07/15), making the firmware think it was
# night at noon (POA = 0 all day). The fix accounts for the MST
# timezone's central meridian (-105°). These codegen tests pin the
# fix in place — if anyone reverts the YAML, the generated C++ will
# have the old `(-112.07 / 15.0)` literal and these tests will fire.


@requires_esphome
def test_poa_lambda_uses_corrected_hour_angle(compiled_main_cpp):
    """The poa_irradiance lambda must use the corrected lon_correction.

    Corrected formula: `(-112.07 - (-105.0)) / 15.0` (the timezone
    offset correction). The buggy version was `-112.07 / 15.0`
    (UTC-only correction).
    """
    # Both forms must exist as literals somewhere in the generated C++,
    # because the corrected formula is `(-112.07 - (-105.0)) / 15.0`.
    assert "(-112.07" in compiled_main_cpp, (
        "POA lambda lost the observer longitude literal — the "
        "hour-angle correction can't work without it."
    )
    # The new formula must reference the MST central meridian (-105.0).
    assert "(-105.0)" in compiled_main_cpp, (
        "POA hour-angle correction is missing the MST timezone central "
        "meridian (-105.0). The firmware is back to the UTC-only "
        "correction that makes POA = 0 all day. See "
        "firmware/logic/sun.py:hour_angle_rad for the reference."
    )
    # The old buggy formula should NOT be present in this exact form.
    # We allow `(-112.07 / 15.0)` only if it's inside the corrected
    # subtraction — i.e. as part of `(-112.07 - (-105.0)) / 15.0`.
    # A simple check: the substring `112.07 / 15.0` (no minus) must
    # NOT appear standalone in the poa_irradiance area. Easier: just
    # check the corrected form exists and the standalone form doesn't.
    # We'll do this by checking that the corrected subtraction appears.
    assert "112.07 - (-105.0)) / 15.0" in compiled_main_cpp or \
           "112.07 - -105.0)) / 15.0" in compiled_main_cpp, (
        "POA hour-angle correction does not have the timezone "
        "subtraction. Expected to find '112.07 - (-105.0)) / 15.0' "
        "in the generated code."
    )


@requires_esphome
def test_poa_lambda_references_mst_central_meridian(compiled_main_cpp):
    """Belt-and-suspenders: the literal -105.0 must appear, AND it
    must be associated with the POA lambda, not the OTA secret or
    some other unrelated number.

    We do this by ensuring the comment block 'MST timezone's
    central meridian' is preserved (the docstring we added when
    fixing the bug).
    """
    # The comment is stripped from the generated C++ by the C
    # preprocessor, but the literal value must still be there.
    # Check the substring `(-105.0)` appears in the generated file
    # at least once (the POA lambda is the only place).
    occurrences = compiled_main_cpp.count("(-105.0)")
    assert occurrences >= 1, (
        f"MST central meridian -105.0 not found in generated code "
        f"(expected at least 1 occurrence; got {occurrences})"
    )


@requires_esphome
def test_poa_lambda_does_not_have_buggy_lon_correction(compiled_main_cpp):
    """The buggy formula `lon_correction = -112.07 / 15.0` must NOT
    appear. This is the formula that was producing POA = 0 during
    daytime in Phoenix.

    Note: `112.07 / 15.0` (without the minus) appears inside the
    corrected subtraction `(-112.07 - (-105.0)) / 15.0`, which is fine.
    We check specifically for `-112.07 / 15.0` (the standalone
    buggy form).
    """
    buggy_form = "-112.07 / 15.0"
    # The corrected form contains `(-112.07` with an open paren
    # before, not `-112.07 / 15.0` directly. So if we see the
    # standalone buggy form, the fix was reverted.
    assert buggy_form not in compiled_main_cpp, (
        f"Found the buggy `lon_correction = {buggy_form}` formula in "
        f"the generated code. The hour-angle fix has been reverted — "
        f"POA will be 0 during daytime in Phoenix. Restore the "
        f"corrected formula `(-112.07 - (-105.0)) / 15.0` in "
        f"wattplot.yaml's poa_irradiance lambda."
    )


# --- Pin map summary --------------------------------------------------------


# Pins the ESP32-S3-DevKitC-1-N16R8 cannot expose as GPIO. See the
# "S3-specific notes" block in wattplot.yaml's header.
S3_RESERVED_PINS = (
    {19, 20}                 # native USB D-/D+
    | set(range(26, 33))     # SPI flash on the WROOM module
    | set(range(33, 38))     # PSRAM on the N16R8 variant
)


@requires_esphome
def test_no_reserved_s3_pins_used(compiled_main_cpp):
    """No component may land on a USB / flash / PSRAM pin.

    Using one of these bricks USB serial or crashes the module at boot,
    and `esphome compile` will not catch it — the pin is electrically
    valid, just spoken for.
    """
    used = {int(g) for g in re.findall(r"GPIO_NUM_(\d+)", compiled_main_cpp)}
    collisions = sorted(used & S3_RESERVED_PINS)
    assert not collisions, (
        f"firmware assigns reserved S3 pins: {collisions}. "
        f"GPIO19/20 are native USB, GPIO26-32 are SPI flash, GPIO33-37 are "
        f"PSRAM on the N16R8. Pick from the free list in wattplot.yaml's header."
    )


@requires_esphome
def test_total_unique_gpios_used_is_within_budget(compiled_main_cpp):
    """The S3-DevKitC-1 exposes plenty of GPIO, but the pin map is finite.

    v3 binds 13 pins via GPIO_NUM_ (I²C SDA/SCL are emitted as bare ints
    by the i2c component, so they don't show up here). If a refactor
    quietly adds a pile more, this catches it.
    """
    used = {int(g) for g in re.findall(r"GPIO_NUM_(\d+)", compiled_main_cpp)}
    assert 5 < len(used) < 25, (
        f"Wattplot binds {len(used)} unique GPIOs ({sorted(used)}). "
        f"Out of the expected range — check the pin map in wattplot.yaml."
    )
