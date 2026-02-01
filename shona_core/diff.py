from __future__ import annotations

from pathlib import Path
from shona_core.utils.io import list_files_sorted, read_json

SNAP_DIR = Path(".shona/snapshots")


def _dict_diff(a: dict, b: dict) -> dict:
    changes = {}
    keys = set(a.keys()) | set(b.keys())
    for k in sorted(keys):
        av = a.get(k, None)
        bv = b.get(k, None)
        if av != bv:
            changes[k] = {"from": av, "to": bv}
    return changes


def _process_set(snapshot: dict) -> set[str]:
    procs = snapshot.get("processes", [])
    return set(p.get("name", "") for p in procs if p.get("name"))


def _ports_set(snapshot: dict) -> set[str]:
    ports = snapshot.get("listening_ports", [])
    return set(f"{p.get('proto')}:{p.get('local')}" for p in ports if p.get("proto") and p.get("local"))


def diff_latest_two() -> dict:
    snaps = list_files_sorted(SNAP_DIR, ".json")
    if len(snaps) < 2:
        return {
            "ok": False,
            "message": "Need at least 2 snapshots. Run `shona scan` twice.",
            "snapshots_found": len(snaps),
        }

    a_path, b_path = snaps[-2], snaps[-1]
    a = read_json(a_path)
    b = read_json(b_path)

    sys_a = a.get("system", {})
    sys_b = b.get("system", {})

    proc_added = sorted(_process_set(b) - _process_set(a))
    proc_removed = sorted(_process_set(a) - _process_set(b))

    ports_added = sorted(_ports_set(b) - _ports_set(a))
    ports_removed = sorted(_ports_set(a) - _ports_set(b))

    return {
        "ok": True,
        "from": a_path.name,
        "to": b_path.name,
        "changes": _dict_diff(sys_a, sys_b),
        "processes": {"added": proc_added, "removed": proc_removed},
        "ports": {"added": ports_added, "removed": ports_removed},
    }
