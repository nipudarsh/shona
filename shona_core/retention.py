from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path(".shona")
STATE_DIR = RUNTIME_DIR / "state"
IGNORE_FILE = STATE_DIR / "ignore.json"
BASELINE_FILE = STATE_DIR / "baseline.json"


def _ensure() -> None:
    (RUNTIME_DIR / "snapshots").mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_ignore() -> dict:
    _ensure()
    if not IGNORE_FILE.exists():
        return {"processes": [], "ports": [], "paths": []}
    return json.loads(IGNORE_FILE.read_text(encoding="utf-8"))


def save_ignore(data: dict) -> None:
    _ensure()
    IGNORE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ignore_add(kind: str, value: str) -> dict:
    data = load_ignore()
    if kind not in data:
        data[kind] = []
    if value not in data[kind]:
        data[kind].append(value)
    save_ignore(data)
    return data


def baseline_set(snapshot_path: str) -> dict:
    _ensure()
    data = {"snapshot": snapshot_path}
    BASELINE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def baseline_get() -> dict | None:
    _ensure()
    if not BASELINE_FILE.exists():
        return None
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))


def apply_ignore_to_diff(diff: dict) -> dict:
    """
    Removes ignored items from diff output. Keeps structure stable.
    """
    ig = load_ignore()
    out = json.loads(json.dumps(diff))  # deep copy

    procs_added = out.get("processes", {}).get("added", [])
    procs_removed = out.get("processes", {}).get("removed", [])
    ignored_procs = set(ig.get("processes", []))

    out["processes"]["added"] = [p for p in procs_added if p not in ignored_procs]
    out["processes"]["removed"] = [p for p in procs_removed if p not in ignored_procs]

    ports_added = out.get("ports", {}).get("added", [])
    ports_removed = out.get("ports", {}).get("removed", [])
    ignored_ports = set(ig.get("ports", []))

    out["ports"]["added"] = [p for p in ports_added if p not in ignored_ports]
    out["ports"]["removed"] = [p for p in ports_removed if p not in ignored_ports]

    return out
