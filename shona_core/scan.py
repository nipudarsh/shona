from __future__ import annotations

import platform
import socket
import getpass
from pathlib import Path

from shona_core.utils.io import utc_now_compact, write_json
from shona_core.modules.processes import list_processes
from shona_core.modules.ports import list_listening_ports

SNAP_DIR = Path(".shona/snapshots")


def _basic_system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


def _maybe_startup() -> list[dict]:
    if platform.system().lower() != "windows":
        return []
    from shona_core.modules.startup_win import list_startup_entries
    return list_startup_entries()


def _maybe_tasks() -> list[dict]:
    if platform.system().lower() != "windows":
        return []
    from shona_core.modules.tasks_win import list_scheduled_tasks
    return list_scheduled_tasks()


def _maybe_services() -> list[dict]:
    if platform.system().lower() != "windows":
        return []
    from shona_core.modules.services_win import list_services
    return list_services()


def run_scan() -> Path:
    ts = utc_now_compact()
    info = _basic_system_info()

    snapshot = {
        "schema": "shona.snapshot.v3",
        "timestamp_utc": ts,
        "system": info,
        "processes": list_processes(),
        "listening_ports": list_listening_ports(),
        "startup": _maybe_startup(),
        "scheduled_tasks": _maybe_tasks(),
        "services": _maybe_services(),
        "notes": "v0.2.0 snapshot includes persistence surfaces",
    }

    filename = f"{info['hostname']}_{ts}.json"
    out_path = SNAP_DIR / filename
    write_json(out_path, snapshot)
    return out_path
