"""Cross-platform controls for the K86 screen synchronization daemon."""
from __future__ import annotations

import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import time
from typing import Optional

from k86_config import get_config_dir

SERVICE_NAME = "k86-screen.service"
TASK_NAME = "K86 Display Studio Screen"
LAUNCHD_LABEL = "io.github.codenotch.k86-screen"
DAEMON_PATH = Path(__file__).resolve().with_name("k86_trio_daemon.py")
IS_FROZEN = bool(getattr(sys, "frozen", False))
SERVICE_PATH = Path(sys.executable if IS_FROZEN else __file__).resolve()
PID_PATH = get_config_dir() / "k86-screen-daemon.json"
LOG_PATH = get_config_dir() / "k86-screen-daemon.log"
MANAGED_FLAG = "--k86-managed"


def _managed_command() -> list[str]:
    if IS_FROZEN:
        return [sys.executable, "--k86-run-daemon", MANAGED_FLAG]
    return [sys.executable, str(DAEMON_PATH), MANAGED_FLAG]


def _startup_command() -> list[str]:
    if IS_FROZEN:
        return [sys.executable, "--k86-start-daemon"]
    return [sys.executable, str(SERVICE_PATH), "--start-daemon"]


def _working_directory() -> Path:
    if IS_FROZEN:
        return Path(sys.executable).resolve().parent
    return DAEMON_PATH.parent


def _is_linux() -> bool:
    return sys.platform.startswith("linux")


def _psutil():
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError(
            "Daemon management requires psutil; install it with "
            "python -m pip install psutil."
        ) from exc
    return psutil


def _read_managed_process() -> Optional[object]:
    """Return our detached daemon process, ignoring stale or reused PIDs."""
    try:
        data = json.loads(PID_PATH.read_text(encoding="utf-8"))
        pid = int(data["pid"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        PID_PATH.unlink(missing_ok=True)
        return None

    psutil = _psutil()
    try:
        process = psutil.Process(pid)
        args = process.cmdline()
        if IS_FROZEN:
            executable_match = Path(process.exe()).resolve() == Path(sys.executable).resolve()
            daemon_match = "--k86-run-daemon" in args
        else:
            executable_match = any(
                Path(arg).resolve() == DAEMON_PATH
                for arg in args
                if arg.lower().endswith(".py")
            )
            daemon_match = True
        managed_match = MANAGED_FLAG in args and executable_match and daemon_match
        if not managed_match or not process.is_running():
            PID_PATH.unlink(missing_ok=True)
            return None
        return process
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        PID_PATH.unlink(missing_ok=True)
        return None


def is_running() -> bool:
    """Return whether the platform daemon is active."""
    if _is_linux():
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", SERVICE_NAME],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.stdout.strip() == "active"
        except (OSError, subprocess.TimeoutExpired):
            return False
    return _read_managed_process() is not None


def start() -> None:
    """Start the Linux user service or a detached per-user daemon elsewhere."""
    if _is_linux():
        subprocess.run(
            ["systemctl", "--user", "start", SERVICE_NAME],
            check=True,
            timeout=10,
        )
        return

    if _read_managed_process() is not None:
        return

    get_config_dir().mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_file = LOG_PATH.open("ab")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    popen_options = {
        "cwd": str(_working_directory()),
        "stdin": subprocess.DEVNULL,
        "stdout": log_file,
        "stderr": subprocess.STDOUT,
        "env": env,
        "close_fds": True,
    }
    if sys.platform == "win32":
        popen_options["creationflags"] = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        popen_options["start_new_session"] = True

    try:
        process = subprocess.Popen(
            _managed_command(),
            **popen_options,
        )
    finally:
        log_file.close()

    PID_PATH.write_text(
        json.dumps({"pid": process.pid, "script": str(DAEMON_PATH)}),
        encoding="utf-8",
    )
    time.sleep(0.2)
    if process.poll() is not None:
        PID_PATH.unlink(missing_ok=True)
        raise RuntimeError(
            f"The K86 daemon exited during startup. See its log at {LOG_PATH}."
        )


def stop() -> None:
    """Stop the Linux user service or our detached per-user daemon."""
    if _is_linux():
        subprocess.run(
            ["systemctl", "--user", "stop", SERVICE_NAME],
            check=True,
            timeout=10,
        )
        return

    process = _read_managed_process()
    if process is None:
        return

    psutil = _psutil()
    process.terminate()
    try:
        process.wait(timeout=5)
    except psutil.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    PID_PATH.unlink(missing_ok=True)


def restart() -> None:
    """Restart the daemon, starting it if no managed process is active."""
    if _is_linux():
        result = subprocess.run(
            ["systemctl", "--user", "restart", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.args,
                output=result.stdout,
                stderr=result.stderr,
            )
        return
    stop()
    start()


def status_label() -> str:
    """Return a short status label suitable for the settings interface."""
    try:
        return "Running" if is_running() else "Stopped"
    except RuntimeError:
        return "psutil ausente"


def is_autostart_enabled() -> bool:
    """Return whether the daemon is configured to run at user login."""
    if _is_linux():
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-enabled", SERVICE_NAME],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0 and result.stdout.strip().startswith("enabled")
        except (OSError, subprocess.TimeoutExpired):
            return False
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", TASK_NAME],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False
    if sys.platform == "darwin":
        return _launch_agent_path().is_file()
    return False


def _launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


def set_autostart(enabled: bool) -> None:
    """Enable or remove the current user's login startup entry."""
    if _is_linux():
        action = "enable" if enabled else "disable"
        subprocess.run(
            ["systemctl", "--user", action, SERVICE_NAME],
            check=True,
            timeout=10,
        )
        return

    if sys.platform == "win32":
        if enabled:
            command = subprocess.list2cmdline(_startup_command())
            subprocess.run(
                [
                    "schtasks",
                    "/Create",
                    "/F",
                    "/SC",
                    "ONLOGON",
                    "/TN",
                    TASK_NAME,
                    "/TR",
                    command,
                    "/RL",
                    "LIMITED",
                ],
                check=True,
                timeout=15,
            )
        else:
            subprocess.run(
                ["schtasks", "/Delete", "/F", "/TN", TASK_NAME],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        return

    if sys.platform == "darwin":
        path = _launch_agent_path()
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            plist = {
                "Label": LAUNCHD_LABEL,
                "ProgramArguments": _startup_command(),
                "RunAtLoad": True,
                "WorkingDirectory": str(_working_directory()),
                "StandardOutPath": str(LOG_PATH),
                "StandardErrorPath": str(LOG_PATH),
            }
            temporary_path = path.with_suffix(".plist.tmp")
            with temporary_path.open("wb") as stream:
                plistlib.dump(plist, stream)
            temporary_path.replace(path)
        else:
            subprocess.run(
                ["launchctl", "bootout", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            path.unlink(missing_ok=True)
        return

    raise RuntimeError(f"Automatic startup is not supported on {sys.platform}.")


if __name__ == "__main__" and "--start-daemon" in sys.argv[1:]:
    start()

