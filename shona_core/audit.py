from __future__ import annotations

import json
import time
from pathlib import Path

AUDIT_DIR = Path(".shona/audit")
AUDIT_FILE = AUDIT_DIR / "events.jsonl"


def _ensure() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def log_event(kind: str, data: dict) -> None:
    _ensure()
    event = {
        "ts": int(time.time()),
        "kind": kind,
        "data": data,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def tail(n: int = 50) -> list[dict]:
    _ensure()
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    for line in lines[-max(1, min(n, 500)):]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out
