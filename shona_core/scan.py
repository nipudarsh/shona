from __future__ import annotations
import platform, socket, getpass
from pathlib import Path
from shona_core.utils.io import utc_now_compact, write_json

SNAP_DIR = Path(".shona/snapshots")

def run_scan() -> Path:
    ts = utc_now_compact()
    info = {
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }
    snap = {
        "schema": "shona.snapshot.v1",
        "timestamp_utc": ts,
        "system": info,
    }
    out = SNAP_DIR / f"{info['hostname']}_{ts}.json"
    write_json(out, snap)
    return out
