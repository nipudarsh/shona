from __future__ import annotations
from pathlib import Path
from shona_core.utils.io import list_files_sorted, read_json

SNAP_DIR = Path("data/snapshots")

def diff_latest_two():
    snaps = list_files_sorted(SNAP_DIR, ".json")
    if len(snaps) < 2:
        return {"ok": False, "message": "Run scan twice"}
    a, b = read_json(snaps[-2]), read_json(snaps[-1])
    changes = {}
    for k in set(a["system"]) | set(b["system"]):
        if a["system"].get(k) != b["system"].get(k):
            changes[k] = {"from": a["system"].get(k), "to": b["system"].get(k)}
    return {"ok": True, "changes": changes}
