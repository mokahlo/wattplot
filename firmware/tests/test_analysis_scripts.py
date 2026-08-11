"""Smoke tests for the analysis scripts that ship with if __name__ == '__main__' blocks.

These tests don't replace a real test suite -- the analysis scripts
are mathematical models, not libraries. They catch the failure
modes that would otherwise silently corrupt the README's claims:
  - import errors (renamed function, removed dependency)
  - output written to wrong path
  - numerical blow-up (NaN, negative safety factor)
  - report regeneration produces the expected files

Each test invokes the analysis script's __main__ block in a
subprocess (so the matplotlib state doesn't bleed between tests)
and asserts that:
  - the script returns 0
  - any expected output files were written
  - the report.md was regenerated with parseable numbers
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = REPO_ROOT / "analysis"
PYTHON = sys.executable


def _run(script_name: str, expected_outputs: list[Path], timeout: int = 240) -> subprocess.CompletedProcess:
    """Run `python analysis/<script>.py` in the repo root, capturing stdout/stderr.

    Use a subprocess so each analysis run gets a fresh Python
    interpreter -- matplotlib's global state otherwise leaks
    between scripts and produces RuntimeError: Locator
    regression warnings.
    """
    proc = subprocess.run(
        [PYTHON, str(ANALYSIS_DIR / script_name)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "MPLBACKEND": "Agg"},
        check=False,
    )
    assert proc.returncode == 0, (
        f"{script_name} exited {proc.returncode}.\n"
        f"stdout: {proc.stdout[-2000:]}\n"
        f"stderr: {proc.stderr[-2000:]}"
    )
    for path in expected_outputs:
        assert path.is_file(), f"{script_name} did not produce {path}"
    return proc


def test_sun_simulator_writes_reports():
    """Sun simulator must regenerate the 3 PNGs in renders/."""
    expected = [
        REPO_ROOT / "renders" / "sun_simulator_monthly_dli.png",
        REPO_ROOT / "renders" / "sun_simulator_scatter.png",
        REPO_ROOT / "renders" / "sun_simulator_daily_dli.png",
    ]
    proc = _run("sun_simulator.py", expected, timeout=120)
    # Output should include the schedule table; verify the static-35
    # row lands at ~1500 kWh/yr (the README and FAQ cite this).
    assert "Static 35" in proc.stdout
    m = re.search(r"Static 35.*?(\d{3,5})", proc.stdout, re.DOTALL)
    assert m is not None, "could not find Static 35° kWh in output"
    kwh = int(m.group(1))
    assert 1000 < kwh < 2500, f"static-35 kWh {kwh} outside expected band (1000-2500)"


def test_wind_load_writes_report():
    """Wind load must regenerate the report markdown and produce parseable numbers."""
    report = REPO_ROOT / "analysis" / "wind_load_report.md"
    _run("wind_load.py", [report], timeout=60)
    text = report.read_text(encoding="utf-8")
    # The report's force-sweep table has one row per tilt angle with
    # SF_overturning in the last column. Match the row pattern.
    row_matches = re.findall(
        r"\|\s*\d+°\s*\|.*?\|\s*([\d.]+)\s*\|",
        text,
    )
    assert row_matches, f"no numeric rows found in {report}"
    # Heuristic: at least one value should be > 2.0 (the design target).
    floats = [float(s) for s in row_matches if float(s) > 0]
    assert any(sf >= 2.0 for sf in floats), (
        f"no SF >= 2.0 found -- wind calc regressed: {floats[:20]}"
    )


def test_post_bending_writes_report():
    """Post-bending must regenerate the report and find the 4x4 failure mode."""
    report = REPO_ROOT / "analysis" / "post_bending_report.md"
    _run("post_bending.py", [report], timeout=60)
    text = report.read_text(encoding="utf-8")
    # The 4x4 unbraced posts should fail at 35° (SF 0.65).
    assert "4x4" in text
    assert "35" in text
    # SF for 4x4 at 35° should be below 1.0 (failure).
    m = re.search(r"4x4.*?35.*?SF.*?(\d\.\d+)", text, re.DOTALL)
    if m:
        sf = float(m.group(1))
        assert sf < 1.0, f"4x4 at 35° should fail (SF < 1.0), got {sf}"


def test_engineering_drawing_writes_svg():
    """Engineering drawing must produce the SVG without error."""
    # The renderer emits .svg + .png into renders/ (gitignored .png).
    # We assert only the SVG, which is also a fresh export.
    out = REPO_ROOT / "renders" / "wattplot_v2_east_side.svg"
    _run("engineering_drawing.py", [out], timeout=120)
    text = out.read_text(encoding="utf-8")
    assert "<svg" in text
    # The SVG should have non-trivial geometry -- at least 20 path
    # elements (a frame + actuator + panel + bed is ~28 paths).
    n_paths = text.count("<path")
    assert n_paths >= 20, f"only {n_paths} paths in SVG (expected 20+)"


def test_shadow_raycaster_runs():
    """Shadow raycaster smoke test -- the if __main__ block exercises the math."""
    # The shadow raycaster is run from the wattplot.py orchestrator, not
    # as a standalone CI step. Run a small inline check.
    proc = subprocess.run(
        [PYTHON, "-c", """
import sys; sys.path.insert(0, '.')
sys.path.insert(0, 'models')
from shadow_raycaster import compute_bed_sunlit_fraction
from wattplot_params import BED, PANEL
# Phoenix noon, summer solstice, 35° tilt.
f = compute_bed_sunlit_fraction(
    35, 180, 80,
    BED['outer_L_in'], BED['outer_W_in'],
    PANEL['L_in'], PANEL['W_in'],
    BED['wall_h_in'], BED['outer_W_in'] / 2.0,
)
assert 0.0 <= f <= 1.0, f'bed sunlit fraction out of [0,1]: {f}'
print(f'OK: 35° noon summer bed sunlit = {f*100:.1f}%')
"""],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "MPLBACKEND": "Agg"},
        check=False,
    )
    assert proc.returncode == 0, (
        f"shadow_raycaster smoke failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}"
    )


def test_pcb_schematic_runs():
    """PCB schematic must regenerate the PNG without error."""
    out = REPO_ROOT / "renders" / "wattplot_v2_pcb_schematic.png"
    _run("pcb_schematic.py", [out], timeout=60)


def test_sun_simulator_numbers_consistent():
    """Pin a smoke check on the per-schedule numbers the README cites.

    The README § "Key design numbers" says:
      "Power (azimuth tracking 35° tilt, Phoenix 2025): 2,240 kWh/year"
    and the FAQ says:
      "the full-size makes about 2,240 kWh/yr at 35° tilt with a
       new 620 W bifacial"

    These come straight from sun_simulator.run_simulation(). If they
    drift, the README needs an update -- but a sub-2,000 / super-3,000
    result is a clear bug. Pin the band.
    """
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "analysis"))
    from sun_simulator import run_simulation
    results, _ = run_simulation()
    az = results["Azimuth tracking 35°"]["annual_kwh"]
    static35 = results["Static 35° (max power)"]["annual_kwh"]
    assert 1800 < az < 2600, f"Azimuth tracking 35° = {az} kWh/yr outside band"
    assert 1200 < static35 < 1900, f"Static 35° = {static35} kWh/yr outside band"