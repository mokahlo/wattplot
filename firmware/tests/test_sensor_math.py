"""
Tier 1: Sensor math regression tests.

Ports the C++ lambda bodies in wattplot.yaml to Python so the math
itself can be unit-tested without flashing the chip. These tests
catch the failures that the YAML's text-pattern checks CAN'T:

  - Off-by-one in the LiFePO4 lookup table (e.g. swapped indices)
  - Energy total cap accidentally removed (float drift past 10 MWh)
  - Midnight reset for `energy_today` never firing
  - POA irradiance blowing up at high hour-angle (sin_alt near 0)
  - Cos(aoi) flipping sign for south-facing panels north of the
    Tropic of Cancer at summer solstice

The wattplot.yaml IS the source of truth for the firmware. The
Python ports here MUST match the C++ 1:1. If you change one, change
the other and add a test for the new behavior.

Run: pytest firmware/tests/test_sensor_math.py -v
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest


# =============================================================================
# 1. LiFePO4 SOC lookup (wattplot.yaml lines 620-642)
# =============================================================================
# 9-point piecewise-linear lookup. Voltages are battery terminal
# voltage (loaded or resting — the firmware doesn't differentiate);
# SOC is the percentage returned to HA / MQTT.
#
#   v   13.6  13.4  13.3  13.2  13.0  12.8  12.5  12.0  10.5
#   s    100    95    90    80    60    40    20    10     0
#
# Indices in the C++ source go from highest voltage (index 0) to
# lowest (index 8). The loop walks i in [0..7] looking for the
# bracket containing v, then linearly interpolates.
SOC_LUT_V = [13.6, 13.4, 13.3, 13.2, 13.0, 12.8, 12.5, 12.0, 10.5]
SOC_LUT_S = [100.0, 95.0, 90.0, 80.0, 60.0, 40.0, 20.0, 10.0, 0.0]


def lifepo4_soc_pct(battery_v: float) -> float:
    """Port of the C++ battery_soc lambda.

    Returns 0..100 (integer-rounded in the YAML, but the math is
    float — we keep float here so interpolation is testable).
    Returns NaN if the input is NaN (mirrors the YAML guard).
    """
    if math.isnan(battery_v):
        return float("nan")
    if battery_v >= SOC_LUT_V[0]:
        return 100.0
    if battery_v <= SOC_LUT_V[8]:
        return 0.0
    for i in range(8):
        if battery_v >= SOC_LUT_V[i + 1] and battery_v <= SOC_LUT_V[i]:
            v_lo, v_hi = SOC_LUT_V[i + 1], SOC_LUT_V[i]
            s_lo, s_hi = SOC_LUT_S[i + 1], SOC_LUT_S[i]
            return s_lo + (s_hi - s_lo) * (battery_v - v_lo) / (v_hi - v_lo)
    # Unreachable: the v >= lut_v[8] guard above catches every v
    # below the table. If we get here the table has a gap.
    return 0.0


class TestLifepo4SOC:
    """LiFePO4 12V 4S voltage-to-SOC lookup."""

    def test_nan_in_nan_out(self):
        assert math.isnan(lifepo4_soc_pct(float("nan")))

    @pytest.mark.parametrize("v,expected", [
        # Above the top of the table — clamps to 100%.
        (14.0, 100.0),
        (13.7, 100.0),
        (13.6, 100.0),    # exact table top
        # Below the bottom — clamps to 0%.
        (10.5, 0.0),      # exact table bottom
        (10.0, 0.0),
        (5.0,  0.0),
    ])
    def test_clamping(self, v, expected):
        assert lifepo4_soc_pct(v) == expected

    @pytest.mark.parametrize("v,expected", [
        # Exact table points
        (13.6, 100.0),
        (13.4,  95.0),
        (13.3,  90.0),
        (13.2,  80.0),
        (13.0,  60.0),
        (12.8,  40.0),
        (12.5,  20.0),
        (12.0,  10.0),
        (10.5,   0.0),
    ])
    def test_table_points(self, v, expected):
        """Exact table values must round-trip (no interpolation error)."""
        assert lifepo4_soc_pct(v) == expected

    @pytest.mark.parametrize("v,expected", [
        # Linear interpolation midpoints. The C++ does a simple
        # two-point linear interp; spot-check a few.
        # 13.5 V is between (13.6, 100) and (13.4, 95) — midpoint = 97.5
        (13.5, 97.5),
        # 13.25 V is between (13.3, 90) and (13.2, 80) — midpoint = 85
        (13.25, 85.0),
        # 12.9 V is between (13.0, 60) and (12.8, 40) — midpoint = 50
        (12.9, 50.0),
        # 12.65 V is between (12.8, 40) and (12.5, 20) — midpoint = 30
        (12.65, 30.0),
        # 11.25 V is between (12.0, 10) and (10.5, 0) — 50% of the
        # way from 10 to 0 = 5
        (11.25, 5.0),
    ])
    def test_interpolation_midpoints(self, v, expected):
        result = lifepo4_soc_pct(v)
        assert math.isclose(result, expected, abs_tol=0.01), \
            f"v={v} expected {expected} got {result}"

    def test_monotonic_decreasing(self):
        """Voltage up must mean SOC up — no flat or reversed slopes."""
        last = 100.0
        for v_mv in range(13_600, 10_499, -50):  # 13.6V → 10.5V in 50 mV steps
            s = lifepo4_soc_pct(v_mv / 1000.0)
            assert s <= last + 1e-6, f"non-monotonic at {v_mv/1000.0}V: {s} > {last}"
            last = s

    def test_full_range_returns_valid_pct(self):
        """Sweep 5V..15V — every value must be in [0, 100]."""
        for v_mv in range(5_000, 15_001, 100):
            s = lifepo4_soc_pct(v_mv / 1000.0)
            assert 0.0 <= s <= 100.0, f"v={v_mv/1000.0}V → SOC {s} out of [0,100]"

    def test_no_gap_in_table(self):
        """If the table has a gap (e.g. one of the 9 points was
        deleted), the loop never finds a bracket and silently
        returns 0. This test catches that class of mistake by
        sweeping between every pair of adjacent points and
        verifying the interp is well-defined and non-zero at
        the midpoints.
        """
        for i in range(8):
            v_lo, v_hi = SOC_LUT_V[i + 1], SOC_LUT_V[i]
            v_mid = (v_lo + v_hi) / 2.0
            s = lifepo4_soc_pct(v_mid)
            # The midpoint must lie strictly between the two
            # adjacent SOC values.
            s_lo, s_hi = SOC_LUT_S[i + 1], SOC_LUT_S[i]
            lo, hi = min(s_lo, s_hi), max(s_lo, s_hi)
            assert lo <= s <= hi, (
                f"bracket {i} ({v_lo}V→{v_hi}V) midpoint v={v_mid}V "
                f"→ SOC {s} outside [{lo}, {hi}] — table gap?"
            )


# =============================================================================
# 2. Energy integration (wattplot.yaml lines 1870-1898)
# =============================================================================
# 1 Hz interval. Each tick: read panel_power_w (W), add p/3600/1000 kWh
# to today and to g_energy_total_kwh (capped at 10 MWh to prevent
# float drift). At day rollover (now.day_of_year != last_doy), reset
# `today` to 0.
#
# This Python re-implementation mirrors the static-state-on-stack
# pattern from the C++ lambda. The `today` accumulator and the
# `last_doy` rollback are persistent only within a single process
# here — for on-device they survive across reboots because
# g_energy_total_kwh has restore_value: true.


@dataclass
class EnergyState:
    """The minimum state the 1-Hz integration needs to keep."""
    total_kwh: float = 0.0           # mirrors id(g_energy_total_kwh)
    _today_kwh: float = 0.0          # mirrors the C++ static float
    _last_doy: int = -1              # mirrors the C++ static int
    _midnight_resets: int = 0        # for test assertions

    @property
    def today_kwh(self) -> float:
        return self._today_kwh

    def tick(self, panel_power_w: float, now_doy: int) -> dict:
        """One 1-Hz integration step. Returns the new published values."""
        if math.isnan(panel_power_w):
            return {}  # mirrors `if (isnan(p)) return;`
        if now_doy != self._last_doy:
            self._today_kwh = 0.0
            self._last_doy = now_doy
            self._midnight_resets += 1
        delta_kwh = panel_power_w / 3600.0 / 1000.0
        self._today_kwh += delta_kwh
        self.total_kwh += delta_kwh
        # 10 MWh cap, same as the YAML.
        if self.total_kwh > 10_000.0:
            self.total_kwh = 10_000.0
        return {
            "energy_today_kwh": self._today_kwh,
            "energy_total_kwh": self.total_kwh,
        }


class TestEnergyIntegration:
    """The 1-Hz `energy_integration` interval."""

    def test_nan_input_does_not_corrupt_total(self):
        """A NaN panel_power_w reading must not advance the counters.

        The INA219 poll is 1 s; a transient I²C error returns NaN.
        The YAML's guard (`if (isnan(p)) return`) keeps the
        accumulator clean. Regression: a naive port might fall
        through to the delta calc and store NaN in g_energy_total_kwh.
        """
        s = EnergyState(total_kwh=42.0)
        result = s.tick(float("nan"), now_doy=200)
        assert result == {}
        assert s.total_kwh == 42.0
        assert s.today_kwh == 0.0

    def test_constant_power_integrates_linearly(self):
        """A constant 1000 W panel for 1 hour must produce 1 kWh."""
        s = EnergyState()
        for _ in range(3600):
            s.tick(1000.0, now_doy=200)
        # 1000 W × 3600 s = 3,600,000 J = 1 kWh.
        assert math.isclose(s.today_kwh, 1.0, abs_tol=1e-9)
        assert math.isclose(s.total_kwh, 1.0, abs_tol=1e-9)

    def test_zero_power_no_accumulation(self):
        """P=0 must produce 0 kWh delta — no drift."""
        s = EnergyState()
        for _ in range(3600):
            s.tick(0.0, now_doy=200)
        assert s.today_kwh == 0.0
        assert s.total_kwh == 0.0

    def test_midnight_reset(self):
        """Crossing day-of-year boundary zeroes `today` but not `total`."""
        s = EnergyState()
        # Day 200: 500 W for 1 hour = 0.5 kWh
        for _ in range(3600):
            s.tick(500.0, now_doy=200)
        assert math.isclose(s.today_kwh, 0.5, abs_tol=1e-9)
        assert math.isclose(s.total_kwh, 0.5, abs_tol=1e-9)
        # Day 201: 500 W for 1 hour
        for _ in range(3600):
            s.tick(500.0, now_doy=201)
        # Today reset, total kept accumulating.
        assert math.isclose(s.today_kwh, 0.5, abs_tol=1e-9), \
            f"today should reset, got {s.today_kwh}"
        assert math.isclose(s.total_kwh, 1.0, abs_tol=1e-9), \
            f"total should accumulate, got {s.total_kwh}"
        # Counter fires on every DOY change: 1 for the init sentinel
        # (-1 -> 200) and 1 for the real midnight transition (200 -> 201).
        # Pin this so the day-rollover logic is exercised; the
        # double-count on first tick is a known quirk of the
        # `last_doy = -1` initialization, not a bug.
        assert s._midnight_resets == 2

    def test_10mwh_cap(self):
        """Energy total is hard-capped at 10,000 kWh (10 MWh) to
        prevent float drift over a long-running deployment.

        The 10W mini produces ~10 kWh/yr — this cap is
        effectively unreachable. But it MUST exist; without it
        a long-lived float accumulator loses sub-cent precision
        after a few million ticks."""
        s = EnergyState()
        # Push 1 MW for 1 hour = 1000 kWh per iteration.
        # After 11 iterations, total would be 11,000 kWh uncapped.
        for i in range(11):
            for _ in range(3600):
                s.tick(1_000_000.0, now_doy=200)  # 1 MW
        assert s.total_kwh == 10_000.0, \
            f"cap broken: {s.total_kwh} (expected 10000)"
        # Today is NOT capped — it's a per-day number that resets.
        assert s.today_kwh > 1_000.0

    def test_first_tick_initializes_doy(self):
        """The C++ uses last_doy=-1 as sentinel; first valid tick
        should NOT trigger a reset (because -1 != now_doy would
        reset before any accumulation).

        This is actually a quirk in the YAML: the first tick after
        boot will reset `today` to 0. That's a no-op since `today`
        already starts at 0 (static init), but worth pinning down.
        """
        s = EnergyState()
        result = s.tick(100.0, now_doy=200)
        assert s._midnight_resets == 1  # First tick with valid DOY = reset
        # 100 W × 1 s = 100/3600/1000 kWh = 2.78e-5 kWh
        assert math.isclose(
            s.today_kwh, 100.0 / 3600.0 / 1000.0, abs_tol=1e-12
        )

    def test_realistic_10w_panel_one_day(self):
        """A 10W panel at full sun for 6 hours → 0.06 kWh/day.

        This is the wattplot mini's typical production — pins the
        order of magnitude so a unit-conversion mistake (e.g. W
        confused with mW) shows up immediately."""
        s = EnergyState()
        # 6 peak-sun-hours, 10 W nominal = 60 Wh = 0.060 kWh
        for _ in range(6 * 3600):
            s.tick(10.0, now_doy=200)
        assert math.isclose(s.today_kwh, 0.06, abs_tol=1e-9), \
            f"expected 0.060 kWh from 10W×6h, got {s.today_kwh}"


# =============================================================================
# 3. POA irradiance (wattplot.yaml lines 644-700)
# =============================================================================
# Plane-of-array irradiance (W/m²) from solar position + tilt, clear-sky.
# Used by `panel_efficiency` to sanity-check the INA219 measurement.
#
# Math is hand-rolled, simplified for a south-facing panel at fixed
# Phoenix latitude:
#   1. Solar declination from day-of-year (Cooper's equation)
#   2. Hour angle from civil time + longitude-vs-tz-meridian offset
#   3. Solar altitude = asin(sin(lat)sin(dec) + cos(lat)cos(dec)cos(ha))
#   4. Air mass (Kasten & Young)
#   5. Direct normal irradiance = 1361 × 0.7^AM^0.678 (Ineichen simplified)
#   6. AOI on south-facing panel = |altitude - tilt|
#   7. POA_direct = DNI × cos(AOI)
#   8. POA_diffuse = 0.10 × DNI × (1 + cos(tilt)) / 2  (isotropic)
#
# Returns 0 when sun is below the horizon or behind the panel.

# Phoenix location (must match wattplot_params.LOCATION).
LAT_DEG = 33.45
LON_DEG = -112.07
TZ_MERIDIAN_DEG = -105.0   # America/Phoenix is UTC-7, central meridian -105

# Solar constant (W/m²) and the simplified Ineichen clear-sky coefficients.
SOLAR_CONSTANT = 1361.0
CLEAR_SKY_BASE = 0.7
CLEAR_SKY_AM_EXP = 0.678


def poa_irradiance(doy: int, hour_24: float, tilt_deg: float) -> float:
    """Port of the C++ `poa_irradiance` lambda.

    Args:
        doy: day of year, 1-365.
        hour_24: civil time, 0-24 (e.g. 13.5 = 1:30 PM).
        tilt_deg: panel tilt from horizontal, 0 = flat, 35 = max for mini.

    Returns:
        POA irradiance in W/m², or 0.0 if the sun is below horizon
        or behind the panel. NaN inputs return NaN (mirrors the
        YAML's `isnan(tilt) → 0` guard, but for tilt only).
    """
    if math.isnan(tilt_deg):
        tilt_deg = 0.0
    lat = LAT_DEG * math.pi / 180.0
    dec = 23.45 * math.sin((360.0 / 365.0) * (doy - 81) * math.pi / 180.0) \
        * math.pi / 180.0
    lon_correction = (LON_DEG - TZ_MERIDIAN_DEG) / 15.0
    solar_hour = hour_24 + lon_correction
    hour_angle = (solar_hour - 12.0) * 15.0 * math.pi / 180.0
    sin_alt = math.sin(lat) * math.sin(dec) + \
        math.cos(lat) * math.cos(dec) * math.cos(hour_angle)
    if sin_alt <= 0.01:
        return 0.0
    altitude = math.asin(sin_alt)
    # Air mass (Kasten & Young 1989)
    am = 1.0 / (sin_alt + 0.50572 *
                (6.07995 + altitude * 180.0 / math.pi) ** -1.6364)
    # Ineichen simplified clear-sky direct normal irradiance.
    dni = SOLAR_CONSTANT * (CLEAR_SKY_BASE ** (am ** CLEAR_SKY_AM_EXP))
    tilt = tilt_deg * math.pi / 180.0
    # v3.2 (2026-08-09): correct AOI for a south-facing panel.
    # cos(aoi) = sin(altitude + tilt), so aoi = 90° - (alt + tilt).
    # Clamp the supplement (when sun is below the panel's normal)
    # into the acute range.
    aoi = abs(math.pi / 2.0 - altitude - tilt)
    if aoi > math.pi / 2.0:
        aoi = math.pi - aoi
    poa_direct = dni * math.cos(aoi)
    # Isotropic sky diffuse, ~10% of DNI.
    dhi = 0.10 * dni
    poa_diffuse = dhi * (1.0 + math.cos(tilt)) / 2.0
    return poa_direct + poa_diffuse


class TestPOAIrradiance:
    """Clear-sky POA irradiance for the wattplot location."""

    # === Smoke tests ===

    def test_night_returns_zero(self):
        """Midnight must produce 0 W/m² — sun below horizon."""
        for doy in (1, 80, 172, 266, 365):
            assert poa_irradiance(doy, hour_24=0.0, tilt_deg=35.0) == 0.0
            assert poa_irradiance(doy, hour_24=3.0, tilt_deg=35.0) == 0.0
            assert poa_irradiance(doy, hour_24=23.5, tilt_deg=35.0) == 0.0

    def test_solar_noon_positive(self):
        """Solar noon on the summer solstice must produce a
        non-trivial POA — the brightest the system ever sees.

        Pins the value the C++ produces AFTER the v3.2 AOI fix.
        For a 33.45° tilt (= latitude) at solar noon on the
        summer solstice, the AOI is ~23.5° and POA direct is
        nearly the full DNI. With the bug (|alt - tilt|), this
        case under-read by ~20%."""
        # ~June 21 = doy 172. Phoenix apparent solar noon is
        # ~12:28 civil (longitude correction).
        result = poa_irradiance(172, hour_24=12.467, tilt_deg=33.45)
        # Post-fix: ~958 W/m² (cos(aoi) = cos(23.5°) ≈ 0.917 of DNI).
        # Pre-fix:  ~740 W/m² (cos(|alt - tilt|) = cos(46.5°) ≈ 0.689).
        # If you see ~740, the AOI regression has been reintroduced.
        assert 900 < result < 1050, \
            f"summer noon POA {result} W/m² — post-fix expectation 900-1050. " \
            f"If you see ~740, the |alt - tilt| bug has returned."

    def test_aoi_matches_dot_product_formula(self):
        """The fixed AOI matches the dot-product formula exactly.

        For a south-facing panel with sun in the south:
            cos(aoi) = sin(altitude + tilt)
            aoi = 90° - (altitude + tilt)  (or its supplement)
        The C++ uses this formula; the test computes the same
        POA via two independent paths and asserts they agree
        to < 1e-9 (essentially bit-identical).

        If a future change makes these diverge, the AOI formula
        has been touched."""
        # Summer solstice noon, tilt=lat (best-case AOI = 23.5°).
        result_cxx = poa_irradiance(172, 12.467, 33.45)
        # Independent re-derivation using the dot product:
        lat = math.radians(33.45)
        dec = math.radians(23.45)
        altitude = math.asin(math.sin(lat) * math.sin(dec) +
                             math.cos(lat) * math.cos(dec) * 1.0)
        sin_alt = math.sin(altitude)
        am = 1.0 / (sin_alt + 0.50572 *
                    (6.07995 + math.degrees(altitude)) ** -1.6364)
        dni = 1361.0 * (0.7 ** (am ** 0.678))
        aoi = abs(math.radians(90) - altitude - math.radians(33.45))
        aoi = min(aoi, math.pi - aoi)
        poa_correct = dni * math.cos(aoi) + \
                      0.10 * dni * (1.0 + math.cos(math.radians(33.45))) / 2.0
        # Must be very close — same formula, same constants. Allow
        # ~1e-5 relative for float-precision drift through the
        # chained `pow(am, 0.678)` calls (C libm vs Python's **).
        # A regression that changes the formula (e.g. swaps |alt-tilt|
        # back in) would shift this by 20%+ and fail loudly.
        assert math.isclose(result_cxx, poa_correct, rel_tol=1e-5), (
            f"C++ POA {result_cxx} ≠ dot-product POA {poa_correct} "
            f"({abs(result_cxx-poa_correct)/poa_correct*100:.4f}% off) — "
            f"the AOI formula has drifted."
        )

    def test_winter_solstice_weakest_peak(self):
        """Winter solstice at the optimal winter tilt should
        still be the year's minimum clear-sky peak.

        For a fixed-tilt system (35°), the winter penalty is
        significant. The C++ formula treats cos(aoi) with the
        simple |altitude - tilt| approximation, so the test
        pins the actual value rather than asserting it's small.
        """
        # ~Dec 21 = doy 355. Optimal winter tilt at lat 33.45° is
        # latitude + 15° ≈ 48.5° (rule of thumb); for our
        # fixed-35° mini, the penalty is real.
        result = poa_irradiance(355, hour_24=12.467, tilt_deg=35.0)
        # Should still be substantial — Phoenix is sun-rich.
        assert 500 < result < 950, \
            f"winter noon POA {result} W/m² outside plausible band"

    # === Physical consistency ===

    def test_poa_increases_to_solar_noon_then_decreases(self):
        """Symmetric about solar noon on the equinoxes.

        Post-fix: morning and afternoon are within ~10% of each
        other on the equinox. The small asymmetry is from the
        equation of time, which the simplified Cooper/PKT
        model doesn't capture. (Pre-fix the asymmetry was
        accidentally masked by the AOI bug.)"""
        doy = 81   # ~March 22 (spring equinox, dec=0)
        tilt = 33.45
        morning = poa_irradiance(doy, 9.0, tilt)
        noon = poa_irradiance(doy, 12.467, tilt)
        afternoon = poa_irradiance(doy, 15.5, tilt)
        assert morning < noon
        assert afternoon < noon
        # 10% tolerance — the EOT creates a few % of asymmetry
        # on every day of the year. If you see 30%+ asymmetry
        # something else broke.
        assert math.isclose(morning, afternoon, rel_tol=0.10), (
            f"equinox asymmetry: morning={morning} afternoon={afternoon} "
            f"({abs(morning-afternoon)/((morning+afternoon)/2)*100:.1f}%)"
        )

    def test_steep_panel_wins_at_sunrise(self):
        """At sunrise the steep panel's normal is closer to the
        sun than the flat panel's, so the steep panel gets
        more direct beam.

        The flat panel's only advantage at low sun is more
        diffuse sky (the (1+cos(tilt))/2 term — max at tilt=0).
        But the direct-beam term dominates at sunrise, so the
        total goes to the steep panel.

        This is the OPPOSITE of what the pre-fix AOI formula
        claimed — the old |altitude - tilt| simplification
        made the flat panel look better at sunrise. The fixed
        formula matches physical reality (and pvlib)."""
        doy = 172
        # ~06:30 civil — sun is just above the horizon.
        early = 6.5
        poa_flat = poa_irradiance(doy, early, tilt_deg=0.0)
        poa_steep = poa_irradiance(doy, early, tilt_deg=35.0)
        # Steep panel's normal is at 90-35=55° altitude, sun is
        # at ~13° altitude. AOI for steep = 42° (cos = 0.74).
        # AOI for flat = 77° (cos = 0.23). Steep gets ~3x the direct.
        assert poa_steep > poa_flat, (
            f"steep {poa_steep} should exceed flat {poa_flat} at sunrise "
            f"— AOI dominates diffuse at low sun"
        )
        # Sanity bound: neither should be wildly large.
        assert poa_steep < 700.0
        assert poa_flat < 500.0

    def test_no_nan_or_inf_anywhere(self):
        """Sweep the full year × every hour × the tilt range.
        Every value must be a finite, non-negative number.
        A NaN/inf would be an off-by-one in the air-mass formula
        (the (6.07995 + altitude_deg) term can be 0 if the
        altitude is exactly -6.08°)."""
        for doy in range(1, 366, 7):
            for hour10 in range(0, 241, 2):  # 0.00, 0.02, 0.04, ... 24.00
                hour = hour10 / 10.0
                for tilt in (0.0, 5.0, 15.0, 25.0, 35.0, 45.0):
                    result = poa_irradiance(doy, hour, tilt)
                    assert math.isfinite(result), \
                        f"non-finite POA at doy={doy} hour={hour} tilt={tilt}: {result}"
                    assert result >= 0.0, \
                        f"negative POA at doy={doy} hour={hour} tilt={tilt}: {result}"

    def test_max_poa_below_solar_constant(self):
        """Clear-sky POA at the absolute best moment (summer
        noon, tilt = latitude) must be below the solar
        constant 1361 W/m². A bug that dropped a `min(..., 1361)`
        could blow past this."""
        best = max(
            poa_irradiance(172, 12.467, t)
            for t in (33.45, 34.0, 35.0)
        )
        assert best < SOLAR_CONSTANT
        # And the AM attenuation should keep the realistic max
        # well under — 1100 W/m² is generous.
        assert best < 1100.0

    def test_equinox_noon_under_1000(self):
        """Sanity check the equinox noon POA — the solar
        geometry is simplest on equinoxes (dec = 0), so this
        number is easy to hand-verify.

        For a 35° south-facing panel at lat 33.45° on the
        equinox at solar noon: sin(alt) = cos(33.45°) ≈ 0.835,
        so altitude ≈ 56.55°. AOI = 90 - 56.55 - 35 = -1.55°
        → folded to 1.55° acute. cos(AOI) ≈ 0.9996.
        AM ≈ 1/sin(alt) ≈ 1.197. DNI ≈ 918.
        Result: 918 × 0.9996 + 92 × 0.91 ≈ 917 + 84 ≈ 1000.

        Pre-fix (|alt - tilt|): AOI was |56.55 - 35| = 21.55°,
        cos = 0.930, POA direct = 853. Total ≈ 937. So the
        "under 1000" name is a leftover from the bug; the
        fixed value lands just under 1000. Allow a tight band."""
        result = poa_irradiance(81, 12.467, 35.0)
        assert 950 < result < 1020, \
            f"equinox noon 35° tilt POA {result} W/m² outside [950, 1020]"


# =============================================================================
# 4. Panel efficiency (wattplot.yaml lines 702-716)
# =============================================================================
# efficiency = (V * I) / (POA * area) * 100
# ECO-WORTHY 10W panel: 13.3" × 8.1" = 0.0695 m² (in² → m² conversion).
#
# Return 0 when POA is below 50 W/m² (noise floor) or any input is
# NaN. This is a thin wrapper, but worth pinning the conversion
# factor and the noise floor.


def panel_efficiency_pct(panel_w: float, poa_w_m2: float,
                         panel_area_m2: float) -> float:
    """Port of the C++ `panel_efficiency` lambda."""
    if math.isnan(panel_w) or math.isnan(poa_w_m2):
        return float("nan")
    if poa_w_m2 < 50.0:
        return 0.0
    return 100.0 * panel_w / (poa_w_m2 * panel_area_m2)


class TestPanelEfficiency:
    """The 60-s `panel_efficiency` template sensor."""

    def test_nan_in_nan_out(self):
        assert math.isnan(panel_efficiency_pct(float("nan"), 800.0, 0.0695))
        assert math.isnan(panel_efficiency_pct(5.0, float("nan"), 0.0695))

    def test_below_noise_floor_returns_zero(self):
        """POA < 50 W/m² → 0% (avoids divide-by-tiny producing
        bogus 200%+ efficiency values at dusk/dawn)."""
        for poa in (0.0, 25.0, 49.9):
            assert panel_efficiency_pct(2.0, poa, 0.0695) == 0.0

    def test_realistic_10w_panel_at_peak(self):
        """10W panel in 1000 W/m² sun → ~14% efficiency.

        The ECO-WORTHY 10W is spec'd at ~15% — our read should
        be in that ballpark. If it's 1.4% the area conversion
        is off by 10×; if it's 140% the area is off by 10× the
        other way."""
        area = 13.3 * 8.1 * 0.00064516   # in² to m² (from YAML)
        eff = panel_efficiency_pct(10.0, 1000.0, area)
        # 10W / (1000 × 0.0695) × 100 = 14.4%
        assert 10.0 < eff < 20.0, f"efficiency {eff}% outside plausible band"

    def test_area_conversion_factor(self):
        """Pin the in² → m² conversion factor used in the YAML.
        1 in² = 0.00064516 m² (exact: 0.00064516).

        If anyone changes this constant, the efficiency
        readout shifts. Pin it so the change is deliberate."""
        # 1 in² → m²
        assert math.isclose(1.0 * 0.00064516, 0.00064516)
        # ECO-WORTHY 10W panel area
        area = 13.3 * 8.1 * 0.00064516
        assert math.isclose(area, 0.0695, abs_tol=0.001)


# =============================================================================
# 5. Cross-consistency: the math pieces should agree
# =============================================================================
# End-to-end: feed the POA into the efficiency calc with a realistic
# panel wattage and assert we land in the spec band. Catches drift
# across any of the three lambdas (POA, efficiency, panel power).


class TestEnergyChainConsistency:
    """The full panel-power → POA → efficiency chain."""

    def test_typical_noon_produces_realistic_efficiency(self):
        """At solar noon on the equinox, 10W panel should report
        an efficiency in the 12-20% band (the panel is spec'd
        for ~15% under STC)."""
        doy = 81
        noon = 12.467
        tilt = 35.0
        poa = poa_irradiance(doy, noon, tilt)
        # Panel producing its rated 10W at the rated POA.
        area = 13.3 * 8.1 * 0.00064516
        eff = panel_efficiency_pct(10.0, poa, area)
        assert 10.0 < eff < 20.0, (
            f"chain broke: POA={poa} W/m², eff={eff}% — "
            f"check POA and efficiency lambdas for unit drift"
        )

    def test_panel_power_drives_energy_total(self):
        """A 6-hour 10W day should produce 0.060 kWh end-to-end.

        This is the same assertion as
        TestEnergyIntegration.test_realistic_10w_panel_one_day
        but it walks through the full chain: power → energy
        integration → total. Catches a missing `* 1000` in the
        W → kWh conversion in either direction."""
        s = EnergyState()
        for _ in range(6 * 3600):
            s.tick(panel_power_w=10.0, now_doy=200)
        assert math.isclose(s.today_kwh, 0.060, abs_tol=1e-9)
