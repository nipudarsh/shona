from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def list_files_sorted(folder: Path, suffix: str):
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.name.endswith(suffix)])
