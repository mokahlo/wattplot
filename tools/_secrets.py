"""Shared loader for the wattplot controller's API encryption key.

The key was hardcoded in 9 tools/*.py files between 2026-08-05 and
2026-08-06 (5 public commits). It is no longer safe to use -- rotate
the key on the chip, then point the tools at the new value via one
of the lookup paths below.

Resolution order (first match wins):

  1. ``WATTPLOT_API_KEY`` environment variable. Preferred for the
     bench/booth PC and for CI. Set in your shell, in a `.env`, or
     in the Task Scheduler entry that runs ``wattplot_control.py``.

  2. ``firmware/secrets.yaml`` in the repo root. Read once at import
     time; cached for the lifetime of the process. Suitable for the
     primary dev workstation where you already keep the secrets
     file.

  3. ``~/.config/wattplot/api_key`` (or ``%USERPROFILE%\\.config\\
     wattplot\\api_key`` on Windows). Per-user override; a single
     line containing the base64 key.

If none of the three resolves, we raise ``WattplotConfigError`` at
import time -- NOT at the point of use, so a missing key fails fast
with a clear error instead of a confusing ``TypeError`` deep inside
``aioesphomeapi``.

The hardcoded fallback has been deliberately removed. The previous
key (``cz0STvY6M+0ob9ydfsi28MDAL9b5P8VsmXsnZv3t7BU=``) is treated as
compromised; do not paste it back into a tool, a secrets.yaml, or a
commit. Rotate the key on the chip (generate a fresh one with
``python -c "import secrets,base64;
print(base64.b64encode(secrets.token_bytes(32)).decode())"``), update
``firmware/secrets.yaml`` to match, reflash, then point the tools at
the new value via the paths above.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


class WattplotConfigError(RuntimeError):
    """Raised when the API key cannot be resolved."""


def _read_yaml_key(path: Path) -> str | None:
    """Read ``api_encryption_key:`` from a YAML file. Minimal parser
    so we don't take a PyYAML dependency on every tool."""
    if not path.is_file():
        return None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.startswith("api_encryption_key:"):
            continue
        value = line.split(":", 1)[1].strip().strip('"').strip("'")
        return value or None
    return None


def _user_config_path() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("USERPROFILE", str(Path.home())))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "wattplot" / "api_key"


def load_api_key(*, repo_root: Path | None = None) -> str:
    """Resolve the wattplot controller's API encryption key.

    Args:
      repo_root: Override the repo root used to find
        ``firmware/secrets.yaml``. Defaults to the parent of the
        ``tools/`` directory containing this module.

    Returns:
      The base64-encoded API encryption key (44 chars).

    Raises:
      WattplotConfigError: If none of the lookup paths yield a key.
    """
    env = os.environ.get("WATTPLOT_API_KEY", "").strip()
    if env:
        return env

    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent
    secret_path = repo_root / "firmware" / "secrets.yaml"
    from_yaml = _read_yaml_key(secret_path)
    if from_yaml:
        return from_yaml

    user_path = _user_config_path()
    if user_path.is_file():
        text = user_path.read_text(encoding="utf-8").strip()
        if text:
            return text

    raise WattplotConfigError(
        "Wattplot API key not found. Set one of:\n"
        "  - env var WATTPLOT_API_KEY (recommended for CI / booth)\n"
        "  - firmware/secrets.yaml api_encryption_key: field\n"
        "  - ~/.config/wattplot/api_key (per-user file)\n"
        "The previous hardcoded key was removed because it was "
        "committed in public history; rotate the key on the chip "
        "before re-using any of the live control tools."
    )


# Module-level singleton so each tool imports once.
_API_KEY: str | None = None


def get_api_key() -> str:
    """Cached lookup. Use this from the tools."""
    global _API_KEY
    if _API_KEY is None:
        _API_KEY = load_api_key()
    return _API_KEY