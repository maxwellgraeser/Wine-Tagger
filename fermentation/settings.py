"""User-adjustable settings that persist between runs — `settings.json` at
the repo root.

Precedence for a knob like the confidence threshold:

    CLI flag  >  environment variable  >  settings.json  >  constants.py default

The Cellar dashboard reads and writes this file (`GET/PATCH /api/settings`);
`python -m fermentation.ferment` reads it, so a threshold saved from the UI
also applies to console runs. Only known keys are kept.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from . import constants
from .paths import PROJECT_ROOT

SETTINGS_PATH = PROJECT_ROOT / "settings.json"


def _to_bool(v: Any) -> bool:
    if isinstance(v, str):
        if v.strip().lower() in ("1", "true", "yes", "on"):
            return True
        if v.strip().lower() in ("0", "false", "no", "off"):
            return False
        raise ValueError(v)
    return bool(v)


# key -> (default, coercer)
_KNOWN: dict[str, tuple[Any, Any]] = {
    "confidence_threshold": (constants.DEFAULT_CONFIDENCE_THRESHOLD, int),
    "lookup_grape_color": (constants.DEFAULT_LOOKUP_GRAPE_COLOR, _to_bool),
}


def defaults() -> dict[str, Any]:
    return {k: v for k, (v, _) in _KNOWN.items()}


def load_settings() -> dict[str, Any]:
    """Defaults overlaid with whatever settings.json holds (bad values ignored)."""
    out = defaults()
    if not SETTINGS_PATH.exists():
        return out
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return out
    if not isinstance(data, dict):
        return out
    for key, (_, coerce) in _KNOWN.items():
        if key in data and data[key] is not None:
            try:
                out[key] = coerce(data[key])
            except (TypeError, ValueError):
                pass
    return out


def save_settings(updates: dict[str, Any]) -> dict[str, Any]:
    """Merge `updates` (unknown keys dropped) into settings.json atomically.
    Returns the full effective settings afterwards."""
    current = load_settings()
    for key, (_, coerce) in _KNOWN.items():
        if key in updates and updates[key] is not None:
            current[key] = coerce(updates[key])
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=SETTINGS_PATH.parent, prefix=".settings-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
            f.write("\n")
        os.replace(tmp, SETTINGS_PATH)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return current


def confidence_threshold() -> int:
    return int(load_settings()["confidence_threshold"])


def lookup_grape_color() -> bool:
    return bool(load_settings()["lookup_grape_color"])
