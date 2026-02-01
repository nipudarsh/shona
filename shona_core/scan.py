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


def run_scan() -> Path:
    ts = utc_now_compact()
    info = _basic_system_info()

    snapshot = {
        "schema": "shona.snapshot.v2",
        "timestamp_utc": ts,
        "system": info,
        "processes": list_processes(),
        "listening_ports": list_listening_ports(),
        "notes": "v0.1.0 inventory snapshot",
    }

    filename = f"{info['hostname']}_{ts}.json"
    out_path = SNAP_DIR / filename
    write_json(out_path, snapshot)
    return out_path
