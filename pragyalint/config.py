"""Configuration loading for PragyaLint.

Supported sources (first found wins):
  * ``pragyalint.toml``
  * ``pragyalint.json``
  * ``[tool.pragyalint]`` section of ``pyproject.toml``
"""

from __future__ import annotations

import json
import os
import tomllib
from typing import Any, Dict


DEFAULTS: Dict[str, Any] = {
    "root_dir": ".",
    "entry": [],
    "ignore": [],
    "extensions": [".py"],
    "include": [],
    "rules": [],
    "report_unused_exports": True,
    "conventional_entries": True,
    "include_entry_exports": False,
    "ignore_tests": False,
    "detect_cycles": False,
    "fail_on": None,
    "output": "terminal",
}


class ConfigError(Exception):
    """Raised for malformed configuration."""


CONFIG_FILENAMES = ["pragyalint.toml", "pragyalint.json"]


def load_config(root_dir: str) -> Dict[str, Any]:
    """Locate and load a configuration file under ``root_dir``."""
    for name in CONFIG_FILENAMES:
        path = os.path.join(root_dir, name)
        if os.path.isfile(path):
            return _merge(DEFAULTS, _read(path))
    pyproject = os.path.join(root_dir, "pyproject.toml")
    if os.path.isfile(pyproject):
        try:
            with open(pyproject, "rb") as fh:
                data = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ConfigError(f"cannot read {pyproject}: {exc}")
        section = data.get("tool", {}).get("pragyalint")
        if isinstance(section, dict):
            return _merge(DEFAULTS, section)
    return dict(DEFAULTS)


def _read(path: str) -> Dict[str, Any]:
    try:
        if path.endswith(".toml"):
            with open(path, "rb") as fh:
                return tomllib.load(fh)
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}")


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    allowed = set(DEFAULTS.keys())
    for key, value in override.items():
        if key in allowed:
            merged[key] = value
    return merged


__all__ = ["DEFAULTS", "ConfigError", "load_config"]
