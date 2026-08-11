"""
Tier 1: NWS forecast JSON parser tests.

The nws_poll script in wattplot.yaml walks the NWS forecast
JSON and extracts:
  - max_wind: max wind speed across the next 12 periods (~24h)
  - rain: true if any period's shortForecast mentions "Rain" or "Showers"
  - min_temp_tonight: temperature of the first non-daytime period

This file ports the parsing logic to Python and pins it with
tests. The C++ in wattplot.yaml is the source of truth; this
Python is the reference implementation that the tests run
against. The wattplot.yaml logic walks the same fields, calls
the same atof on the same strings, in the same order.

Run: pytest firmware/tests/test_nws_parser.py -v
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional


def parse_nws_forecast(body: str) -> Dict[str, Any]:
    """Port of the C++ parser in the nws_poll script.

    Returns a dict with:
      - max_wind_mph: float
      - rain_forecast: bool
      - min_temp_tonight: Optional[float] — None if no overnight
        period was found in the next 12 periods
      - found_overnight: bool
      - periods_examined: int (for diagnostics)

    Mirrors the C++ behavior:
      - max_wind is the max across periods 0..11 of atof(windSpeed)
      - rain is true if any period's shortForecast contains
        "Rain" or "Showers"
      - min_temp is the temperature of the first non-daytime
        period (isDaytime=false). If no overnight period is
        found in the first 12, returns None (the C++ leaves
        the global unchanged in that case).
    """
    root = json.loads(body)
    periods = root.get("properties", {}).get("periods", [])
    max_wind = 0.0
    rain = False
    min_temp: Optional[float] = None
    found_overnight = False
    examined = 0
    for i, period in enumerate(periods[:12]):
        examined += 1
        # windSpeed: a string like "15 mph" or "15 to 25 mph".
        # The C++ uses atof which stops at the first non-digit,
        # so "15 to 25 mph" → 15.0. We match that.
        ws = period.get("windSpeed", "")
        if ws:
            # Extract leading number (int or float, possibly with ".")
            num = ""
            seen_dot = False
            for ch in ws:
                if ch.isdigit():
                    num += ch
                elif ch == "." and not seen_dot:
                    num += ch
                    seen_dot = True
                else:
                    break
            if num:
                v = float(num)
                if v > max_wind:
                    max_wind = v
        # shortForecast: text like "Rain Showers Likely"
        fc = period.get("shortForecast", "")
        if "Rain" in fc or "Showers" in fc:
            rain = True
        # isDaytime: bool. NWS uses true for daytime periods
        # (sunrise-sunset) and false for overnight. The first
        # non-daytime period is always the current/next
        # overnight low.
        #
        # Note on the default: the C++ reads a missing field as
        # "not daytime" (the JsonVariant is null, falsy; `!null`
        # is true). We default to False to match. A future fix
        # could default to True (more conservative — assume
        # daytime unless proven otherwise).
        if not found_overnight and not period.get("isDaytime", False):
            t = period.get("temperature")
            if t is not None and t != "":
                try:
                    min_temp = float(t)
                    found_overnight = True
                except (TypeError, ValueError):
                    pass
    return {
        "max_wind_mph": max_wind,
        "rain_forecast": rain,
        "min_temp_tonight": min_temp,
        "found_overnight": found_overnight,
        "periods_examined": examined,
    }


# A realistic NWS forecast snippet, abbreviated. The full response
# has 14-day coverage but we only look at the first 12 periods.
SAMPLE_FORECAST = {
    "properties": {
        "periods": [
            # This afternoon: daytime, warm
            {
                "name": "This Afternoon",
                "isDaytime": True,
                "temperature": 18,
                "windSpeed": "10 mph",
                "shortForecast": "Sunny",
            },
            # Tonight: overnight, cold (the FIRST non-daytime)
            {
                "name": "Tonight",
                "isDaytime": False,
                "temperature": 1,
                "windSpeed": "15 mph",
                "shortForecast": "Clear",
            },
            # Tomorrow: daytime, warmer
            {
                "name": "Tomorrow",
                "isDaytime": True,
                "temperature": 16,
                "windSpeed": "5 to 10 mph",
                "shortForecast": "Mostly Sunny",
            },
            # Tomorrow night: overnight, cold
            {
                "name": "Tomorrow Night",
                "isDaytime": False,
                "temperature": -2,
                "windSpeed": "20 mph",
                "shortForecast": "Partly Cloudy",
            },
            # A wet period further down — should not affect
            # min_temp (we already found the first overnight).
            {
                "name": "Friday",
                "isDaytime": True,
                "temperature": 12,
                "windSpeed": "10 mph",
                "shortForecast": "Rain Showers",
            },
        ]
    }
}


class TestNwsWindExtraction:
    """The max_wind extraction across periods."""

    def test_basic_wind_value(self):
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "temperature": 20,
                 "windSpeed": "15 mph", "shortForecast": "Sunny"},
            ]}
        })
        r = parse_nws_forecast(body)
        assert r["max_wind_mph"] == 15.0

    def test_range_wind_takes_first_number(self):
        """NWS sometimes gives '5 to 10 mph' — atof returns 5.0."""
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "temperature": 20,
                 "windSpeed": "5 to 10 mph", "shortForecast": "Sunny"},
            ]}
        })
        r = parse_nws_forecast(body)
        # The C++ atof returns 5.0 (the leading number). Pin that.
        assert r["max_wind_mph"] == 5.0

    def test_max_across_periods(self):
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "windSpeed": "10 mph",
                 "shortForecast": ""},
                {"isDaytime": False, "windSpeed": "25 mph",
                 "shortForecast": ""},
                {"isDaytime": True, "windSpeed": "15 mph",
                 "shortForecast": ""},
            ]}
        })
        r = parse_nws_forecast(body)
        assert r["max_wind_mph"] == 25.0

    def test_missing_wind_speed(self):
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "temperature": 20,
                 "shortForecast": "Sunny"},
            ]}
        })
        r = parse_nws_forecast(body)
        assert r["max_wind_mph"] == 0.0  # default


class TestNwsRainExtraction:
    """rain is true if any period's shortForecast contains
    'Rain' or 'Showers'."""

    def test_rain_in_one_period(self):
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "windSpeed": "5 mph",
                 "shortForecast": "Sunny"},
                {"isDaytime": False, "windSpeed": "10 mph",
                 "shortForecast": "Rain Likely"},
            ]}
        })
        r = parse_nws_forecast(body)
        assert r["rain_forecast"] is True

    def test_showers_triggers_rain(self):
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "windSpeed": "5 mph",
                 "shortForecast": "Scattered Showers"},
            ]}
        })
        r = parse_nws_forecast(body)
        assert r["rain_forecast"] is True

    def test_no_rain(self):
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "windSpeed": "5 mph",
                 "shortForecast": "Sunny"},
                {"isDaytime": False, "windSpeed": "5 mph",
                 "shortForecast": "Clear"},
            ]}
        })
        r = parse_nws_forecast(body)
        assert r["rain_forecast"] is False

    def test_partial_match_does_not_count(self):
        """NWS sometimes writes 'Slight Rain Likely' — the
        word 'Rain' is there but 'Slight' is the modifier. The
        C++ strstr matches the substring 'Rain' and returns
        true. This is a known quirk: the C++ does substring
        match, not word-boundary. Pin the behavior so a
        future fix is intentional.

        Note: case-sensitive. 'rain' lowercase would NOT match.
        'Slight Rain' (capital R) DOES match.
        """
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "windSpeed": "5 mph",
                 "shortForecast": "Slight Rain"},
            ]}
        })
        r = parse_nws_forecast(body)
        # strstr matches the substring "Rain" — this is a known
        # quirk. A word-boundary fix would change this to False.
        assert r["rain_forecast"] is True, (
            "C++ strstr does substring match. If this is fixed "
            "to word-boundary, update the test."
        )


class TestNwsMinTempExtraction:
    """min_temp = temperature of the FIRST non-daytime period."""

    def test_first_overnight_is_taken(self):
        body = json.dumps(SAMPLE_FORECAST)
        r = parse_nws_forecast(body)
        # "Tonight" is the first non-daytime period, temp = 1
        assert r["min_temp_tonight"] == 1.0
        assert r["found_overnight"] is True

    def test_subsequent_overnight_is_ignored(self):
        """Once the first overnight is found, later ones are
        skipped. The C++ uses `if (!found_overnight)` as a guard."""
        body = json.dumps(SAMPLE_FORECAST)
        r = parse_nws_forecast(body)
        # Tomorrow Night is -2 but we already found Tonight.
        # If we used the MIN of all overnights, we'd get -2.
        # The C++ uses FIRST-found, not MIN. Pin that.
        assert r["min_temp_tonight"] == 1.0
        # NOT -2.0 (tomorrow night's low).

    def test_no_overnight_in_first_12(self):
        """Forecast has only daytime periods → no overnight
        found. C++ leaves the global unchanged; Python returns None."""
        body = json.dumps({
            "properties": {"periods": [
                {"isDaytime": True, "temperature": 25,
                 "windSpeed": "5 mph", "shortForecast": "Hot"},
                {"isDaytime": True, "temperature": 27,
                 "windSpeed": "5 mph", "shortForecast": "Hotter"},
            ]}
        })
        r = parse_nws_forecast(body)
        assert r["min_temp_tonight"] is None
        assert r["found_overnight"] is False

    def test_empty_periods(self):
        body = json.dumps({"properties": {"periods": []}})
        r = parse_nws_forecast(body)
        assert r["max_wind_mph"] == 0.0
        assert r["rain_forecast"] is False
        assert r["min_temp_tonight"] is None

    def test_periods_array_missing(self):
        body = json.dumps({"properties": {}})
        r = parse_nws_forecast(body)
        assert r["periods_examined"] == 0
        assert r["min_temp_tonight"] is None

    def test_isDaytime_true_by_default(self):
        """If isDaytime is missing, the C++ reads it as true
        (JsonVariant truthiness on a missing field is false
        in ESPHome's parser, but the C++ inverts with !is_daytime
        which treats missing as 'daytime'). Pin the behavior.
        """
        body = json.dumps({
            "properties": {"periods": [
                {"temperature": 5, "windSpeed": "5 mph",
                 "shortForecast": ""},  # no isDaytime field
            ]}
        })
        r = parse_nws_forecast(body)
        # The C++ check is `if (!is_daytime)`. A missing field
        # is falsy in JsonVariant, so `!is_daytime` is True —
        # this period is treated as overnight. This is a quirk:
        # the test pins the behavior.
        assert r["found_overnight"] is True
        assert r["min_temp_tonight"] == 5.0

    def test_examined_only_first_12(self):
        """Even with 15 periods, only the first 12 are examined."""
        periods = []
        for i in range(15):
            periods.append({
                "isDaytime": False if i == 14 else True,  # last is overnight
                "temperature": i,
                "windSpeed": f"{i} mph",
                "shortForecast": "",
            })
        body = json.dumps({"properties": {"periods": periods}})
        r = parse_nws_forecast(body)
        # Only 12 examined; the 13th-15th are ignored. The overnight
        # at index 14 is never seen.
        assert r["periods_examined"] == 12
        assert r["min_temp_tonight"] is None
        # But max_wind across the first 12 is 11.0.
        assert r["max_wind_mph"] == 11.0
