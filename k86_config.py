"""Configuration management for K86 Display Studio.

Provides safe defaults, schema validation, and platform-aware persistence for
K86 Display settings.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "screen": {
        "width": 240,
        "height": 128,
        "show_clock": True,
        "brightness": 4,
    },
    "providers": {
        "claude": {"enabled": True, "show_5h": True, "show_weekly": True},
        "codex": {"enabled": True, "show_5h": True, "show_weekly": True},
        "antigravity": {"enabled": True, "show_5h": True, "show_weekly": True},
        "copilot": {"enabled": False, "show_5h": True, "show_weekly": True},
        "cursor": {"enabled": False, "show_5h": True, "show_weekly": True},
        "opencode": {"enabled": False, "show_5h": True, "show_weekly": True},
        "grok": {"enabled": False, "show_5h": True, "show_weekly": True},
        "glm": {"enabled": False, "show_5h": True, "show_weekly": True},
    },
    "system_metrics": {
        "enabled": False,
        "show_cpu": False,
        "show_ram": False,
    },
    "daemon": {
        "refresh_seconds": 15,
    },
}


def get_data_dir() -> Path:
    """Return the directory containing provider quota data and user icons."""
    override = os.environ.get("K86_DATA_DIR")
    if override:
        return Path(override).expanduser()

    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "codenotch"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "codenotch"

    # Keep the established Linux location for existing quota caches and icons.
    return Path.home() / ".config" / "codenotch"


def get_config_dir() -> Path:
    """Return the per-user configuration directory for this application."""
    override = os.environ.get("K86_CONFIG_DIR")
    if override:
        return Path(override).expanduser()

    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "K86 Display Studio"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "K86 Display Studio"

    # Preserve the existing Linux config path during the platform migration.
    return get_data_dir()


def get_config_path() -> Path:
    """Return the default configuration file path."""
    return get_config_dir() / "k86_config.json"


def load_config(path: Optional[Path | str] = None) -> dict[str, Any]:
    """Load configuration from the specified or default path.

    Returns DEFAULT_CONFIG if the file does not exist, cannot be read,
    or contains invalid JSON.
    """
    config_path = Path(path) if path is not None else get_config_path()

    if not config_path.is_file():
        return copy.deepcopy(DEFAULT_CONFIG)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return copy.deepcopy(DEFAULT_CONFIG)
        return data
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return copy.deepcopy(DEFAULT_CONFIG)


def save_config(cfg: dict[str, Any], path: Optional[Path | str] = None) -> None:
    """Save configuration to the specified or default path atomically.

    Creates parent directories if necessary.
    """
    config_path = Path(path) if path is not None else get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write via temporary file in the same directory
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=config_path.parent,
            prefix=f".{config_path.name}.",
            delete=False,
        ) as tmp:
            temp_file = Path(tmp.name)
            json.dump(cfg, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())

        os.replace(temp_file, config_path)
    except Exception:
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
        raise
