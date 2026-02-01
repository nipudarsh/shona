from __future__ import annotations

from pathlib import Path
from shona_core.utils.io import list_files_sorted, read_json
from shona_core.retention import baseline_get, apply_ignore_to_diff

SNAP_DIR = Path(".shona/snapshots")


def _process_set(snapshot: dict) -> set[str]:
    procs = snapshot.get("processes", [])
    return set(p.get("name", "") for p in procs if p.get("name"))


def _ports_set(snapshot: dict) -> set[str]:
    ports = snapshot.get("listening_ports", [])
    return set(f"{p.get('proto')}:{p.get('local')}" for p in ports if p.get("proto") and p.get("local"))


def _startup_set(snapshot: dict) -> set[str]:
    items = snapshot.get("startup", [])
    s = set()
    for it in items:
        src = it.get("source", "")
        name = it.get("name", "")
        val = it.get("value", "")
        key = it.get("key", "")
        if src == "registry_run":
            s.add(f"reg:{key}:{name}:{val}")
        elif src == "startup_folder":
            s.add(f"folder:{name}:{val}")
    return s


def _tasks_set(snapshot: dict) -> set[str]:
    items = snapshot.get("scheduled_tasks", [])
    s = set()
    for it in items:
        tn = it.get("TaskName")
        run = it.get("Task To Run")
        if tn:
            s.add(f"{tn}|{run}")
    return s


def _services_set(snapshot: dict) -> set[str]:
    items = snapshot.get("services", [])
    s = set()
    for it in items:
        name = it.get("service_name")
        disp = it.get("display_name")
        if name:
            s.add(f"{name}|{disp}")
    return s


def _diff_sets(a: set[str], b: set[str]) -> dict:
    return {"added": sorted(b - a), "removed": sorted(a - b)}


def _load_snapshot(path: Path) -> dict:
    return read_json(path)


def diff_latest_two() -> dict:
    snaps = list_files_sorted(SNAP_DIR, ".json")
    if len(snaps) < 2:
        return {"ok": False, "message": "Need at least 2 snapshots. Run `shona scan` twice.", "snapshots_found": len(snaps)}

    a_path, b_path = snaps[-2], snaps[-1]
    return diff_between(a_path, b_path)


def diff_between(a_path: Path, b_path: Path) -> dict:
    a = _load_snapshot(a_path)
    b = _load_snapshot(b_path)

    diff = {
        "ok": True,
        "from": a_path.name,
        "to": b_path.name,
        "processes": _diff_sets(_process_set(a), _process_set(b)),
        "ports": _diff_sets(_ports_set(a), _ports_set(b)),
        "startup": _diff_sets(_startup_set(a), _startup_set(b)),
        "scheduled_tasks": _diff_sets(_tasks_set(a), _tasks_set(b)),
        "services": _diff_sets(_services_set(a), _services_set(b)),
    }
    return apply_ignore_to_diff(diff)


def diff_against_baseline() -> dict:
    base = baseline_get()
    if not base or not base.get("snapshot"):
        return {"ok": False, "message": "No baseline set. Use: shona baseline accept <snapshot.json>"}

    base_path = Path(base["snapshot"])
    if not base_path.exists():
        return {"ok": False, "message": f"Baseline snapshot missing: {base_path}"}

    snaps = list_files_sorted(SNAP_DIR, ".json")
    if not snaps:
        return {"ok": False, "message": "No snapshots found. Run: shona scan"}

    latest = snaps[-1]
    return diff_between(base_path, latest)
