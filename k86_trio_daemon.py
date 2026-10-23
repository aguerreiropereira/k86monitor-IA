#!/usr/bin/env python3
"""
Attack Shark K86 Background Screen Daemon (Panoramic 240x128)
Continuously monitors Codenotch AI quotas (Claude, Codex, Antigravity)
and dynamic settings from k86_config.json, updating the keyboard's 240x128
screen when data/settings change or on the minute clock tick.
"""
from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

from k86_config import load_config, get_config_path
from k86_renderer import render_display, frame_to_rgb565, load_live_stats, CONFIG_DIR
from k86_trio_monitor import K86ScreenDirect

DEFAULT_DEVICE_PATH: str = "/dev/hidraw6"
DEFAULT_REFRESH_SECONDS: int = 15

_running: bool = True


def find_k86_hidraw() -> str:
    """Find the Attack Shark K86 Interface 2 (screen control) hidraw device dynamically."""
    base = Path("/sys/class/hidraw")
    if base.is_dir():
        for hid in sorted(base.glob("hidraw*")):
            uevent = hid / "device" / "uevent"
            if uevent.is_file():
                try:
                    content = uevent.read_text(encoding="utf-8", errors="ignore")
                    if "00003151:00004015" in content and "input2" in content:
                        return f"/dev/{hid.name}"
                except OSError:
                    pass
    if os.path.exists("/dev/hidraw5"):
        return "/dev/hidraw5"
    return DEFAULT_DEVICE_PATH


def get_watched_files(
    config_dir: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> list[Path]:
    """Return the list of paths monitored for changes."""
    base_dir = config_dir if config_dir is not None else CONFIG_DIR
    cfg_p = config_path if config_path is not None else get_config_path()
    return [
        cfg_p,
        base_dir / "usage.json",
        base_dir / "codex.json",
        base_dir / "antigravity.json",
        base_dir / "copilot.json",
        base_dir / "cursor.json",
        base_dir / "opencode-usage.json",
        base_dir / "grok.json",
        base_dir / "glm-usage.json",
    ]


def compute_state_hash(
    cfg: Optional[dict[str, Any]] = None,
    config_dir: Optional[Path] = None,
    config_path: Optional[Path] = None,
    cur_minute: Optional[str] = None,
) -> tuple[tuple[tuple[str, Optional[float]], ...], Optional[str]]:
    """Compute a hashable fingerprint of file timestamps and current minute."""
    if cfg is None:
        cfg = load_config(config_path)

    watched = get_watched_files(config_dir=config_dir, config_path=config_path)
    mtimes: list[tuple[str, Optional[float]]] = []
    for p in watched:
        try:
            if p.is_file():
                mtimes.append((p.name, p.stat().st_mtime))
            else:
                mtimes.append((p.name, None))
        except OSError:
            mtimes.append((p.name, None))

    show_clock = cfg.get("screen", {}).get("show_clock", True)
    minute_val = (cur_minute if cur_minute is not None else time.strftime("%H:%M")) if show_clock else None

    return (tuple(mtimes), minute_val)


def get_refresh_interval(cfg: Optional[dict[str, Any]] = None) -> int:
    """Extract refresh interval in seconds from configuration with safe fallback."""
    if cfg is None:
        cfg = load_config()
    try:
        val = int(cfg.get("daemon", {}).get("refresh_seconds", DEFAULT_REFRESH_SECONDS))
        return max(1, val)
    except (ValueError, TypeError):
        return DEFAULT_REFRESH_SECONDS


def run_iteration(
    last_state: Any = None,
    device_path: str = DEFAULT_DEVICE_PATH,
    config_path: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    screen_factory: Any = K86ScreenDirect,
    renderer_func: Any = render_display,
) -> tuple[Any, bool]:
    """Execute a single poll iteration.

    Returns (new_state, updated) indicating whether the physical screen was rewritten.
    """
    cfg = load_config(config_path)
    state = compute_state_hash(cfg=cfg, config_dir=config_dir, config_path=config_path)

    if state == last_state:
        return last_state, False

    effective_dev = find_k86_hidraw() if device_path == DEFAULT_DEVICE_PATH else device_path

    img = renderer_func(cfg)
    screen = None
    try:
        screen = screen_factory(effective_dev)
        screen.write_screen(img)
        print(f"[{time.strftime('%X')}] Screen updated (240x128).", flush=True)
        return state, True
    except Exception as e:
        print(f"[{time.strftime('%X')}] Warning: Failed to write to screen: {e}", flush=True)
        # Keep last_state so retry will occur on next iteration
        return last_state, False
    finally:
        if screen is not None:
            try:
                screen.close()
            except Exception:
                pass


def _signal_handler(signum: int, frame: Any) -> None:
    """Handle termination signals for clean shutdown under systemd."""
    global _running
    sig_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
    print(f"\nReceived signal {sig_name}, stopping K86 screen daemon gracefully...", flush=True)
    _running = False


def main(device_path: str = DEFAULT_DEVICE_PATH, config_path: Optional[Path] = None) -> None:
    """Main daemon loop."""
    global _running
    _running = True

    try:
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
    except (ValueError, AttributeError):
        pass

    print("Starting Attack Shark K86 Panoramic 240x128 AI Screen Daemon...", flush=True)
    last_state: Any = None

    while _running:
        try:
            cfg = load_config(config_path)
            last_state, _ = run_iteration(
                last_state=last_state,
                device_path=device_path,
                config_path=config_path,
            )
            refresh_seconds = get_refresh_interval(cfg)
        except Exception as e:
            print(f"Daemon error in main loop: {e}", flush=True)
            refresh_seconds = DEFAULT_REFRESH_SECONDS

        # Sliced sleep allowing responsive shutdown when _running becomes False
        for _ in range(refresh_seconds):
            if not _running:
                break
            time.sleep(1)

    print("K86 Screen Daemon stopped.", flush=True)


if __name__ == "__main__":
    main()
