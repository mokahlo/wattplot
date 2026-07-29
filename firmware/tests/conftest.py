"""
Shared pytest fixtures for the firmware test suite.

Build artifacts (esp32c3, IDF toolchain) are slow to produce (~5 min on
cold cache) and Linux-only in CI, so we gate the codegen test on a
marker and skip if esphome isn't installed.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

FIRMWARE_DIR = Path(__file__).resolve().parent.parent
WATTPLOT_YAML = FIRMWARE_DIR / "wattplot.yaml"
SECRETS_YAML = FIRMWARE_DIR / "secrets.yaml"
SECRETS_EXAMPLE = FIRMWARE_DIR / "secrets.yaml.example"
BUILD_DIR = FIRMWARE_DIR / ".esphome" / "build" / "wattplot-controller"


def _have_esphome() -> bool:
    return shutil.which("esphome") is not None or _esphome_module_works()


def _esphome_module_works() -> bool:
    try:
        import esphome  # noqa: F401
        return True
    except ImportError:
        return False


requires_esphome = pytest.mark.skipif(
    not _have_esphome(),
    reason="esphome not installed (pip install esphome)",
)


@pytest.fixture(scope="session")
def firmware_dir() -> Path:
    return FIRMWARE_DIR


@pytest.fixture(scope="session")
def config_path() -> Path:
    return WATTPLOT_YAML


@pytest.fixture(scope="session")
def esphome_config_output() -> str:
    """Run `esphome config` once and return stdout. Skips if esphome missing."""
    if not _have_esphome():
        pytest.skip("esphome not installed")
    # Use the Python module form so it picks up the same install as the build.
    proc = subprocess.run(
        ["python", "-m", "esphome", "config", str(WATTPLOT_YAML)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(FIRMWARE_DIR),
    )
    return proc.stdout + "\n--- STDERR ---\n" + proc.stderr


def pytest_collection_modifyitems(config, items):
    # Auto-mark any test named test_codegen* as requires_esphome + slow
    for item in items:
        if "codegen" in item.nodeid.lower():
            item.add_marker(requires_esphome)
