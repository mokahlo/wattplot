"""Parity test: wattplot_params.py vs models/openscad/wattplot_params.scad.

These two files are maintained by hand. Either can drift, and a
drift means the OpenSCAD model renders a different wattplot than
the Python code analyzes. This test reads both and asserts that
the canonical numbers match.

Adding a new param?
  1. Add it to wattplot_params.py at the repo root.
  2. Add it to models/openscad/wattplot_params.scad with a comment
     pointing back to the Python location.
  3. Add a SCAD_FIELD entry below with the expected value.
  4. The test will fail until both files agree.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PY_PARAMS = REPO_ROOT / "wattplot_params.py"
SCAD_PARAMS = REPO_ROOT / "models" / "openscad" / "wattplot_params.scad"


# (python_attribute_path, expected_value, scad_variable_name, tolerance)
# Tolerance is the absolute difference allowed between Python and
# SCAD (hand-maintained mirror; 0 for ints, 0.01 for floats in inches).
PARAM_TABLE = [
    # BED
    ("BED.outer_L_in",       96.0,  "bed_outer_L_in",       0.01),
    ("BED.outer_W_in",       44.6,  "bed_outer_W_in",       0.01),
    ("BED.wall_thk_in",      0.75,  "bed_wall_thk_in",      0.01),
    ("BED.wall_h_in",        27.5,  "bed_wall_h_in",        0.01),
    ("BED.soil_fill_in",     25.5,  "bed_soil_fill_in",     0.01),
    ("BED.skid_h_in",        1.5,   "bed_skid_h_in",        0.01),
    ("BED.skid_side_in",     3.5,   "bed_skid_side_in",     0.01),

    # BED_WALL
    ("BED_WALL.skin_thk_in", 0.75,  "wall_skin_thk_in",     0.01),
    ("BED_WALL.course_h_in", 5.5,   "wall_course_h_in",     0.01),
    ("BED_WALL.courses",     5,     "wall_courses",         0),    # int
    ("BED_WALL.cleats_long_wall",  5, "wall_cleats_long",   0),    # int
    ("BED_WALL.cleats_short_wall", 3, "wall_cleats_short",  0),    # int

    # POSTS
    ("POSTS.thickness_in",   3.5,   "post_thk_in",          0.01),
    ("POSTS.height_in",      72.0,  "post_height_in",       0.01),
    ("POSTS.count",          4,     "post_count",           0),    # int
    ("POSTS.rail_thickness_in", 1.5, "post_rail_thk_in",     0.01),
    ("POSTS.rail_width_in",  5.5,   "post_rail_wid_in",     0.01),

    # PANEL (default LONGi 620W)
    ("PANEL.L_in",           97.0,  "panel_L_in",           0.01),
    ("PANEL.W_in",           44.6,  "panel_W_in",           0.01),
    ("PANEL.thickness_in",   1.4,   "panel_thk_in",         0.01),
    ("PANEL.mass_lb",        65.0,  "panel_mass_lb",        0.1),
    ("PANEL.wattage",        620,   "panel_wattage",        0),    # int
    ("PANEL.panel_tilt_deg", 35.0,  "panel_tilt_deg",       0.01),

    # CONTROL
    ("CONTROL.max_tilt_deg", 35.0,  "control_max_tilt_deg", 0.01),

    # FRAME
    ("FRAME.long_rail.thickness_in",  1.5,  "frame_long_rail_thk_in",   0.01),
    ("FRAME.long_rail.height_in",     5.5,  "frame_long_rail_wid_in",   0.01),
    ("FRAME.long_rail.length_in",     96.0, "frame_long_rail_length_in", 0.01),
    ("FRAME.cross_rail.length_in",    42.0, "frame_cross_rail_length_in", 0.01),
    ("FRAME.diagonal_brace.length_in", 102.0, "frame_brace_length_in",     0.01),

    # HINGE + CLAMPS
    ("FRAME.hinge.leaf_in",         4.0,  "hinge_leaf_in",       0.01),
    ("FRAME.hinge.pin_d_in",         0.5,  "hinge_pin_d_in",       0.01),
    ("FRAME.hinge.count",           4,    "hinge_count",         0),    # int
    ("FRAME.hinge.spacing_in",      22.0, "hinge_spacing_in",   0.01),
    ("FRAME.hinge.rod_length_in",   72.0, "hinge_rod_length_in", 0.01),

    # ACTUATOR
    ("ACTUATOR.stroke_in", 4.0, "actuator_stroke_in", 0.01),

    # LOCATION
    ("LOCATION.design_wind_speed_mph", 115.0, "location_design_wind_mph", 0.01),
]


def _load_scad():
    """Extract SCAD variable assignments from wattplot_params.scad.

    Returns a dict {name: float-or-int}. Comments and blank lines
    are skipped. Variable names with a trailing comment have the
    comment stripped.
    """
    text = SCAD_PARAMS.read_text(encoding="utf-8")
    out = {}
    for line in text.splitlines():
        stripped = line.split("//", 1)[0].rstrip()
        if "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        name = name.strip()
        value = value.strip().rstrip(";").strip()
        if not name or not value:
            continue
        try:
            out[name] = int(value)
        except ValueError:
            try:
                out[name] = float(value)
            except ValueError:
                pass  # not a numeric assignment (e.g. a string)
    return out


def _resolve_py(py_path: str, params):
    """Walk a dotted path through wattplot_params. The top level
    (e.g. BED) is a dict; the next level is a dict key; further
    levels are dict keys again (e.g. FRAME.long_rail.thickness_in).
    """
    parts = py_path.split(".")
    obj = params
    for part in parts:
        if isinstance(obj, dict):
            obj = obj[part]
        else:
            obj = getattr(obj, part)
    return obj


def test_scad_params_parity():
    scad = _load_scad()
    assert scad, f"no SCAD variables parsed from {SCAD_PARAMS}"

    sys.path.insert(0, str(REPO_ROOT))
    import wattplot_params
    failures = []
    for py_path, expected, scad_name, tol in PARAM_TABLE:
        if scad_name not in scad:
            failures.append(f"  MISSING in SCAD: {scad_name} (Python has {py_path}={expected})")
            continue
        py_val = _resolve_py(py_path, wattplot_params)
        if abs(py_val - expected) > tol:
            failures.append(
                f"  STALE TEST: expected Python {py_path}={expected}, got {py_val}"
            )
        if abs(scad[scad_name] - expected) > tol:
            failures.append(
                f"  SCAD DRIFT: {scad_name}={scad[scad_name]} in .scad, expected {expected}"
            )
        if abs(scad[scad_name] - py_val) > tol:
            failures.append(
                f"  PY vs SCAD MISMATCH: {py_path}={py_val} vs {scad_name}={scad[scad_name]}"
            )
    assert not failures, "wattplot_params.py / .scad drift:\n" + "\n".join(failures)


def test_scad_file_has_parity_header():
    """The .scad file's top comment must say it's a mirror and
    reference the Python source of truth. Catches the case where
    someone added a new SCAD variable without updating the comment."""
    text = SCAD_PARAMS.read_text(encoding="utf-8")
    assert "wattplot_params.py" in text, (
        "wattplot_params.scad must reference wattplot_params.py in the header"
    )
    assert "DO NOT EDIT" in text or "do not edit" in text.lower(), (
        "wattplot_params.scad must warn against editing numbers directly"
    )


def test_canonical_model_compiles():
    """The canonical wattplot.scad must parse without errors.

    OpenSCAD has its own syntax errors (unmatched braces, undefined
    variables, etc.) that don't surface until render time. This
    test invokes `openscad -o /dev/null --export-format=bin` (or
    `csg` to /dev/null in newer OpenSCAD) which does a full parse
    + evaluate pass without writing a real STL. Skip if OpenSCAD
    is not installed -- the parity test above is the primary
    signal.
    """
    import shutil
    import subprocess
    import tempfile

    openscad = shutil.which("openscad")
    if not openscad:
        import pytest
        pytest.skip("openscad not installed; install via apt/brew/choco")

    for scad_file in [
        "wattplot.scad",
        "technical_drawing.scad",
        "parts/bed.scad",
        "parts/posts.scad",
        "parts/hinges.scad",
        "parts/panel.scad",
        "parts/frame.scad",
        "parts/actuator.scad",
    ]:
        with tempfile.TemporaryDirectory() as tmp:
            # --export-format=csg writes the evaluated CSG tree
            # without tessellating -- fast, no real STL produced,
            # but a parse failure surfaces as a nonzero exit code.
            out = Path(tmp) / "out.csg"
            result = subprocess.run(
                [openscad, "-o", str(out),
                 str(REPO_ROOT / "models" / "openscad" / scad_file)],
                capture_output=True, text=True, timeout=60,
                check=False,
            )
            assert result.returncode == 0, (
                f"openscad parse failed for {scad_file} "
                f"(exit {result.returncode}):\n"
                f"  stderr: {result.stderr[:2000]}\n"
                f"  stdout: {result.stdout[:2000]}"
            )
            assert out.exists() and out.stat().st_size > 0, (
                f"openscad produced no CSG output for {scad_file} "
                f"(file {out} missing or empty)"
            )