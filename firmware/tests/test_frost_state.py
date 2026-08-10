"""
Tier 1: Frost protection state machine tests.

Ports the C++ lambda body of the `frost_tick` interval in
wattplot.yaml to Python. Covers:

  - Mode select (Off / Heater / Grow Light / Both)
  - Threshold + hysteresis logic (turn on below, turn off above)
  - NaN guard: any single sensor error must not permanently latch
  - Sensor error path: BOTH sensors NaN → force off + "Sensor error"
  - Battery floor: SOC below minimum → force off + "Battery low"
  - Watchdog: max continuous on-time → force off + counter bump
  - Sensor recovery: clears the latched error flag

These tests run in <1 s and catch the failure modes that would
otherwise burn a winter's worth of plants during a single bad
night:

  - Misconfigured thresholds (heater on at 20°C, off at 5°C)
  - Stuck relay (heater on for 6 hours, battery flat by dawn)
  - DS18B20 wiring glitch (sensor reads -127°C, latches heater on)
  - Mode select doesn't actually gate the load (caller forgot
    to AND with heater_enabled / grow_light_enabled)

The wattplot.yaml IS the source of truth. The Python ports here
MUST match the C++ 1:1. If you change one, change the other and
add a test for the new behavior.

Run: pytest firmware/tests/test_frost_state.py -v
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import pytest


# =============================================================================
# 1. The state machine — direct port of the C++ `frost_tick` lambda
# =============================================================================
# Defaults match the YAML's initial_value for the corresponding
# number: templates. If the YAML defaults change, update these.
DEFAULT_SOIL_THRESHOLD_C = 4.0
DEFAULT_CANOPY_THRESHOLD_C = 2.0
DEFAULT_WARM_ABOVE_C = 6.0
DEFAULT_MAX_RUNTIME_MIN = 30
DEFAULT_MIN_BATTERY_SOC = 50


@dataclass
class FrostInputs:
    """All the knobs and sensors the tick reads.

    Defaults match the YAML initial values. A None for any
    temperature is treated as NaN (sensor error)."""
    soil_c: Optional[float] = 3.0            # below soil threshold by default
    canopy_c: Optional[float] = 1.0          # below canopy threshold by default
    battery_soc_pct: Optional[float] = 80.0  # well above floor

    soil_threshold_c: float = DEFAULT_SOIL_THRESHOLD_C
    canopy_threshold_c: float = DEFAULT_CANOPY_THRESHOLD_C
    warm_above_c: float = DEFAULT_WARM_ABOVE_C
    max_runtime_min: float = DEFAULT_MAX_RUNTIME_MIN
    min_battery_soc: float = DEFAULT_MIN_BATTERY_SOC


@dataclass
class FrostState:
    """The persistent state the tick mutates."""
    # Switches — true = load energized.
    heater_on: bool = False
    grow_light_on: bool = False
    # Timers — millis() when each switch was last turned on.
    # 0 = switch is off.
    heater_on_since_ms: int = 0
    grow_light_on_since_ms: int = 0
    # Latched flags.
    sensor_error: bool = False
    # Counters.
    watchdog_trips: int = 0
    # Human-readable state string. Mirrors g_frost_state in the YAML.
    frost_state: str = "Off"


def frost_tick(
    state: FrostState,
    inputs: FrostInputs,
    mode: str,
    now_ms: int,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """One 60s tick of the frost automation.

    Args:
        state:    persistent state mutated in place.
        inputs:   current sensor readings + tunable thresholds.
        mode:     one of "Off" / "Heater" / "Grow Light" / "Both".
        now_ms:   current time in millis() (test passes it explicitly
                  so the watchdog is deterministic).
        log:      optional callable for log lines; tests can ignore.
    """
    def L(msg: str) -> None:
        if log is not None:
            log(msg)

    soil = inputs.soil_c if inputs.soil_c is not None else float("nan")
    canopy = inputs.canopy_c if inputs.canopy_c is not None else float("nan")
    soc = inputs.battery_soc_pct if inputs.battery_soc_pct is not None else float("nan")
    soil_th = inputs.soil_threshold_c
    canopy_th = inputs.canopy_threshold_c
    warm_above = inputs.warm_above_c
    max_runtime_ms = int(inputs.max_runtime_min * 60.0 * 1000.0)
    min_soc = inputs.min_battery_soc
    soil_bad = math.isnan(soil)
    canopy_bad = math.isnan(canopy)

    # ---- Mode "Off" → both switches off, exit ----
    if mode == "Off":
        if state.heater_on:
            state.heater_on = False
            state.heater_on_since_ms = 0
        if state.grow_light_on:
            state.grow_light_on = False
            state.grow_light_on_since_ms = 0
        state.frost_state = "Off"
        return

    # ---- Sensor error path: BOTH NaN ----
    if soil_bad and canopy_bad:
        if not state.sensor_error:
            L("Both temp sensors NaN — disabling frost")
            state.sensor_error = True
        if state.heater_on:
            state.heater_on = False
            state.heater_on_since_ms = 0
        if state.grow_light_on:
            state.grow_light_on = False
            state.grow_light_on_since_ms = 0
        state.frost_state = "Sensor error"
        return

    # One sensor recovered — clear the latch.
    if state.sensor_error:
        L("Temp sensors recovered")
        state.sensor_error = False

    # ---- Battery floor check ----
    battery_low = math.isnan(soc) or soc < min_soc
    if battery_low:
        if state.heater_on or state.grow_light_on:
            L(f"Battery low (SOC={soc if not math.isnan(soc) else -1.0}%) — forcing off")
            if state.heater_on:
                state.heater_on = False
                state.heater_on_since_ms = 0
            if state.grow_light_on:
                state.grow_light_on = False
                state.grow_light_on_since_ms = 0
        state.frost_state = "Battery low"
        return

    # ---- Mode gating ----
    heater_enabled = mode in ("Heater", "Both")
    grow_light_enabled = mode in ("Grow Light", "Both")

    # ---- Compute desired state for each output ----
    def compute_want(is_on, bad_a, bad_b, a, b, th_a, th_b, warm):
        if is_on:
            # Currently ON: turn OFF only when BOTH valid temps are above warm_above.
            a_warm = bad_a or a > warm
            b_warm = bad_b or b > warm
            return not (a_warm and b_warm)
        # Currently OFF: turn ON if EITHER valid temp is below its threshold.
        a_cold = (not bad_a) and a < th_a
        b_cold = (not bad_b) and b < th_b
        return a_cold or b_cold

    want_on_heater = compute_want(
        state.heater_on, soil_bad, canopy_bad,
        soil, canopy, soil_th, canopy_th, warm_above,
    )
    want_on_light = compute_want(
        state.grow_light_on, soil_bad, canopy_bad,
        soil, canopy, soil_th, canopy_th, warm_above,
    )
    if not heater_enabled:
        want_on_heater = False
    if not grow_light_enabled:
        want_on_light = False

    # ---- Watchdog enforcement ----
    def apply_watchdog(want_on, on_since_ms, name):
        if want_on and on_since_ms != 0:
            elapsed = now_ms - on_since_ms
            if elapsed > max_runtime_ms:
                L(f"{name} watchdog tripped ({elapsed//1000}s > {max_runtime_ms//1000}s)")
                state.watchdog_trips += 1
                return False
        return want_on

    want_on_heater = apply_watchdog(want_on_heater, state.heater_on_since_ms, "heater")
    want_on_light = apply_watchdog(want_on_light, state.grow_light_on_since_ms, "light")

    # ---- Apply to switches ----
    if want_on_heater != state.heater_on:
        if want_on_heater:
            state.heater_on = True
            state.heater_on_since_ms = now_ms
            L(f"Heater ON (soil={soil:.1f} canopy={canopy:.1f})")
        else:
            state.heater_on = False
            state.heater_on_since_ms = 0
            L("Heater OFF")
    if want_on_light != state.grow_light_on:
        if want_on_light:
            state.grow_light_on = True
            state.grow_light_on_since_ms = now_ms
            L(f"Grow light ON (soil={soil:.1f} canopy={canopy:.1f})")
        else:
            state.grow_light_on = False
            state.grow_light_on_since_ms = 0
            L("Grow light OFF")

    # ---- Update state string ----
    if state.heater_on and state.grow_light_on:
        state.frost_state = "Both"
    elif state.heater_on:
        state.frost_state = "Heater"
    elif state.grow_light_on:
        state.frost_state = "Grow Light"
    else:
        state.frost_state = "Standby"


# =============================================================================
# 2. Tests
# =============================================================================


class TestModeOff:
    """Mode = Off is the master disable. The tick must force
    both switches off and never engage automation, regardless of
    temperature, SOC, or sensor health."""

    def test_mode_off_forces_both_off(self):
        """Even when temps are well below threshold, Off means off."""
        state = FrostState(heater_on=True, grow_light_on=True)
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=-2.0),
                   mode="Off", now_ms=0)
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.frost_state == "Off"

    def test_mode_off_clears_watchdog_timers(self):
        """The on_since_ms counters reset to 0 when Off forces them off."""
        state = FrostState(heater_on=True, heater_on_since_ms=999_999)
        frost_tick(state, FrostInputs(), mode="Off", now_ms=1_000_000)
        assert state.heater_on_since_ms == 0

    def test_mode_off_overrides_cold_temps(self):
        """The classic foot-gun: user sets Mode=Off for a test,
        then forgets, then a cold snap comes. The tick must NOT
        silently re-enable the heater."""
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=-5.0, canopy_c=-10.0),
                   mode="Off", now_ms=0)
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.frost_state == "Off"


class TestModeGating:
    """Mode = Heater / Grow Light / Both must gate the output
    correctly. A bug here means the heater turns on when only
    the grow light was requested (or vice versa), or the user
    setting Both=Heater accidentally runs both loads."""

    def test_heater_mode_runs_only_heater(self):
        """Mode=Heater must NOT drive the grow light switch."""
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Heater", now_ms=0)
        assert state.heater_on
        assert not state.grow_light_on
        assert state.frost_state == "Heater"

    def test_grow_light_mode_runs_only_light(self):
        """Mode=Grow Light must NOT drive the heater switch."""
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Grow Light", now_ms=0)
        assert not state.heater_on
        assert state.grow_light_on
        assert state.frost_state == "Grow Light"

    def test_both_mode_runs_both(self):
        """Mode=Both drives both switches with independent hysteresis."""
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on
        assert state.frost_state == "Both"

    def test_switching_modes_does_not_latch(self):
        """User toggles mode at runtime — the previous mode's
        on-state must release, not latch on. The next tick with
        a different mode should reflect the new mode's choice.
        """
        state = FrostState(heater_on=True, grow_light_on=True)
        # Switch from Both to Heater. The grow light should drop.
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Heater", now_ms=0)
        assert state.heater_on
        assert not state.grow_light_on


class TestThresholdAndHysteresis:
    """The core on/off logic. Below the threshold → ON. Above
    warm_above → OFF. In between → hold previous state."""

    def test_cold_soil_turns_heater_on(self):
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=3.0, canopy_c=10.0),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on

    def test_cold_canopy_alone_engages_heater(self):
        """Soil is fine but canopy is freezing — still turn on.
        Either temp below threshold is enough."""
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=10.0, canopy_c=1.0),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on

    def test_warm_both_turns_heater_off(self):
        """Both above warm_above → off."""
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=10.0, canopy_c=10.0),
                   mode="Both", now_ms=0)
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.frost_state == "Standby"

    def test_hysteresis_deadband(self):
        """Inside the deadband (between threshold and warm_above),
        hold the previous state. This is the whole point of the
        warm_above parameter — prevent relay chatter at the
        threshold edge.
        """
        # Currently ON, both temps in the deadband (4 < soil < 6,
        # 2 < canopy < 6). Must stay ON.
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=5.0, canopy_c=4.0),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on

    def test_one_warm_one_cold_stays_on(self):
        """Soil above warm_above but canopy still cold → stay on.
        The OFF condition requires BOTH above warm_above."""
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=10.0, canopy_c=1.5),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on

    def test_only_canopy_cold_keeps_relay_on(self):
        """A single cold sensor (with the other in the deadband)
        must keep the relay on. Catches a bug where the off
        condition uses OR instead of AND.
        """
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=5.0, canopy_c=1.0),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on

    def test_warm_above_must_exceed_thresholds(self):
        """Pin a design rule: warm_above >= both thresholds.

        If warm_above < max(soil_threshold, canopy_threshold),
        the hysteresis would be NEGATIVE — the relay would
        chatter (turn off before the threshold is even crossed
        when going up, or fail to turn off when temps are clearly
        above the threshold).

        The YAML doesn't enforce this; it's a configuration trap.
        The test pins the design rule and would catch a future
        'improvement' that removed the deadband requirement.
        """
        # The C++ doesn't validate this; the test simply documents
        # the contract by asserting the design intent holds for
        # the defaults.
        i = FrostInputs()
        assert i.warm_above_c >= i.soil_threshold_c, (
            "warm_above must be >= soil_threshold (positive deadband)"
        )
        assert i.warm_above_c >= i.canopy_threshold_c, (
            "warm_above must be >= canopy_threshold (positive deadband)"
        )


class TestNaNAndSensorError:
    """NaN guards. A single bad sensor must not permanently
    latch the relay on (or off). Both sensors bad → latched
    'Sensor error' state until at least one recovers."""

    def test_single_nan_does_not_latch_on(self):
        """One sensor NaN, the other cold. Engages (canopy is
        below threshold). The NaN sensor is treated as 'ignore
        for this tick' — the valid sensor's reading decides.
        """
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=None, canopy_c=0.0),
                   mode="Both", now_ms=0)
        # Canopy 0°C < 2°C threshold → ON.
        assert state.heater_on
        assert state.grow_light_on
        assert not state.sensor_error

    def test_single_nan_holds_off_when_other_is_warm(self):
        """One sensor NaN, the other warm. Both temps in
        'warm' effectively (canopy is the only signal and it's
        above warm_above) → OFF.
        """
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=None, canopy_c=10.0),
                   mode="Both", now_ms=0)
        assert not state.heater_on
        assert not state.grow_light_on

    def test_both_nan_latches_sensor_error(self):
        """Both NaN → force off + latch sensor_error."""
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=None, canopy_c=None),
                   mode="Both", now_ms=0)
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.sensor_error
        assert state.frost_state == "Sensor error"

    def test_sensor_recovery_clears_latch(self):
        """After a latched error, one valid reading clears it."""
        state = FrostState(sensor_error=True)
        frost_tick(state, FrostInputs(soil_c=5.0, canopy_c=5.0),
                   mode="Both", now_ms=0)
        assert not state.sensor_error

    def test_sensor_error_latch_only_fires_once(self):
        """The 'Both temp sensors NaN' log line must not fire
        every tick — only on the transition. The C++ guards
        with `if (!id(g_frost_sensor_error))`.
        """
        sensor_error_log: list[str] = []

        def log(msg: str) -> None:
            sensor_error_log.append(msg)

        state = FrostState()
        for t in range(0, 300_000, 60_000):  # 5 ticks of NaN
            frost_tick(state, FrostInputs(soil_c=None, canopy_c=None),
                       mode="Both", now_ms=t, log=log)
        # Exactly one "Both temp sensors NaN" log line, not 5.
        error_lines = [m for m in sensor_error_log if "NaN" in m]
        assert len(error_lines) == 1, (
            f"sensor-error log fired {len(error_lines)} times — "
            f"should fire only on the 0→1 transition. "
            f"Lines: {sensor_error_log}"
        )


class TestBatteryFloor:
    """The battery floor guard. Below SOC threshold, the tick
    must force off even if temps are well below freezing. NaN
    SOC is treated as 'assume low' (better to lose plants than
    brick the pack overnight)."""

    def test_low_soc_forces_off(self):
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0,
                                      battery_soc_pct=30.0),
                   mode="Both", now_ms=0)
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.frost_state == "Battery low"

    def test_soc_at_floor_keeps_automation(self):
        """SOC == floor is allowed (the check is strict <).
        The C++ uses `soc < min_soc` — equal stays on."""
        state = FrostState()
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0,
                                      battery_soc_pct=50.0),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on

    def test_nan_soc_treated_as_low(self):
        """No recent SOC reading → assume low. The pack might be
        at 5% and we just don't know. Better to lose plants
        than wake up to a bricked LiFePO4."""
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0,
                                      battery_soc_pct=None),
                   mode="Both", now_ms=0)
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.frost_state == "Battery low"

    def test_battery_low_does_not_latch(self):
        """Battery-low is per-tick, not latched. As soon as SOC
        recovers, the tick re-evaluates the temp logic."""
        state = FrostState(frost_state="Battery low")
        # SOC recovered, temp still cold
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0,
                                      battery_soc_pct=80.0),
                   mode="Both", now_ms=0)
        assert state.heater_on
        assert state.grow_light_on
        assert state.frost_state == "Both"


class TestWatchdog:
    """The max-runtime watchdog. A stuck relay would otherwise
    drain the pack overnight — the watchdog force-off after
    max_runtime_min is the safety net."""

    def test_watchdog_force_off_after_runtime(self):
        """Heater has been on for 31 minutes. Watchdog (30 min
        default) trips → force off."""
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=60_000,   # 1 min ago
                           grow_light_on_since_ms=60_000)
        # Advance now_ms to 31 min past heater_on_since_ms
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Both",
                   now_ms=60_000 + 31 * 60 * 1000)  # 31 min later
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.watchdog_trips == 2  # one for heater, one for light

    def test_watchdog_does_not_trip_under_runtime(self):
        """Heater on for 29 min, max is 30 — must stay on.

        Uses a non-zero time base so the on_since_ms timers don't
        collide with the 0 = "relay off" sentinel."""
        base = 60 * 60 * 1000
        now = base + 29 * 60 * 1000
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=base,
                           grow_light_on_since_ms=base)
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Both", now_ms=now)
        assert state.heater_on
        assert state.grow_light_on
        assert state.watchdog_trips == 0

    def test_watchdog_at_exact_runtime(self):
        """elapsed == max_runtime. C++ uses `elapsed > max_runtime_ms`
        (strict greater), so the boundary is the last tick where
        it stays on."""
        base = 60 * 60 * 1000
        now = base + 30 * 60 * 1000
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=base,
                           grow_light_on_since_ms=base)
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Both", now_ms=now)
        assert state.heater_on
        assert state.grow_light_on
        assert state.watchdog_trips == 0

    def test_watchdog_independent_per_output(self):
        """Heater was on for 31 min, light was on for 5 min. Only
        the heater trips the watchdog.

        Note: the on-since timers use a non-zero time base so they
        don't collide with the 0 = "relay off" sentinel."""
        # Start 1 hour into the deployment (1h = 3,600,000 ms).
        # Heater on_since = 1h. Light on_since = 1h26m.
        # now = 1h31m → heater elapsed = 31m, light elapsed = 5m.
        base = 60 * 60 * 1000
        now = base + 31 * 60 * 1000
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=base,
                           grow_light_on_since_ms=base + 26 * 60 * 1000)
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Both", now_ms=now)
        assert not state.heater_on
        assert state.grow_light_on  # still under its own limit
        assert state.watchdog_trips == 1  # only heater

    def test_watchdog_only_blocks_turn_on_not_hold(self):
        """If the relay is already on and the watchdog tripped
        previously, the timer reset to 0 (we force off). A new
        cold tick should re-engage it cleanly with a fresh timer.
        """
        state = FrostState(heater_on=False, heater_on_since_ms=0,
                           watchdog_trips=5)
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0),
                   mode="Heater", now_ms=100_000)
        assert state.heater_on
        assert state.heater_on_since_ms == 100_000


class TestEndToEndScenarios:
    """A few realistic overnight scenarios pinned end-to-end.
    These don't test anything the unit tests don't already cover,
    but they make a regression visible to a human reading the
    test output."""

    def test_overnight_recovery_cycle(self):
        """A typical Phoenix winter night: warm at sundown,
        cools below 4°C at midnight, heats, warms above 6°C at
        7am, tick releases.

        Runtime is bumped to 240 min so the watchdog doesn't
        trip during the 1am "still cold" check. The default 30
        min is for actual deployment (catches stuck relays
        overnight) — for this scenario we want the full
        overnight cycle to play out without interference.
        """
        state = FrostState()
        overnight_inputs = FrostInputs(max_runtime_min=240.0)
        # 8 pm: still warm
        frost_tick(state, FrostInputs(soil_c=15.0, canopy_c=12.0,
                                      max_runtime_min=240.0),
                   mode="Heater", now_ms=0)
        assert not state.heater_on
        # Midnight: soil dropped to 3°C
        frost_tick(state, FrostInputs(soil_c=3.0, canopy_c=1.0,
                                      max_runtime_min=240.0),
                   mode="Heater", now_ms=4 * 3600 * 1000)
        assert state.heater_on
        # 1 am: still cold, still on, fresh 1h elapsed
        frost_tick(state, FrostInputs(soil_c=4.5, canopy_c=3.0,
                                      max_runtime_min=240.0),
                   mode="Heater", now_ms=5 * 3600 * 1000)
        assert state.heater_on
        # 7 am: warmed up, hysteresis released
        frost_tick(state, FrostInputs(soil_c=8.0, canopy_c=7.0,
                                      max_runtime_min=240.0),
                   mode="Heater", now_ms=11 * 3600 * 1000)
        assert not state.heater_on

    def test_cold_snap_with_sensor_dropout(self):
        """Cold snap hits, one sensor flakes for a few ticks
        (returns NaN), then recovers. The frost protection must
        not latch off or on during the dropout."""
        state = FrostState()
        # Cold snap begins, both sensors valid
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=-1.0),
                   mode="Heater", now_ms=0)
        assert state.heater_on
        # Soil sensor goes NaN for 2 ticks (e.g. loose connector)
        frost_tick(state, FrostInputs(soil_c=None, canopy_c=-1.0),
                   mode="Heater", now_ms=60_000)
        assert state.heater_on  # canopy still says cold
        frost_tick(state, FrostInputs(soil_c=None, canopy_c=-1.0),
                   mode="Heater", now_ms=120_000)
        assert state.heater_on
        assert not state.sensor_error  # only one sensor bad
        # Soil recovers
        frost_tick(state, FrostInputs(soil_c=2.0, canopy_c=-1.0),
                   mode="Heater", now_ms=180_000)
        assert state.heater_on
        # Warm arrives
        frost_tick(state, FrostInputs(soil_c=8.0, canopy_c=7.0),
                   mode="Heater", now_ms=240_000)
        assert not state.heater_on

    def test_battery_runs_low_during_event(self):
        """Frost event has been running for a few hours, battery
        is draining. SOC eventually hits the floor — tick force-
        off even though temps are still cold. The plants lose
        some heat but the pack survives."""
        state = FrostState(heater_on=True, grow_light_on=True,
                           heater_on_since_ms=0, grow_light_on_since_ms=0)
        # Cold temps, full battery
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0,
                                      battery_soc_pct=80.0),
                   mode="Both", now_ms=60_000)
        assert state.heater_on
        # Same temps, battery dropped below floor
        frost_tick(state, FrostInputs(soil_c=1.0, canopy_c=0.0,
                                      battery_soc_pct=40.0),
                   mode="Both", now_ms=120_000)
        assert not state.heater_on
        assert not state.grow_light_on
        assert state.frost_state == "Battery low"
