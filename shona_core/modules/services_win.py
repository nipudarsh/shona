from __future__ import annotations

import platform
import subprocess
import re


def _not_supported() -> list[dict]:
    return [{"error": "services scan not supported on this OS"}]


def list_services(limit: int = 400) -> list[dict]:
    """
    Windows services listing via sc queryex type= service state= all
    """
    if platform.system().lower() != "windows":
        return _not_supported()

    try:
        out = subprocess.check_output(["sc", "queryex", "type=", "service", "state=", "all"], text=True, errors="ignore")  # noqa: S603,S607
    except Exception:
        return [{"error": "failed to query services"}]

    items: list[dict] = []
    current: dict | None = None

    for line in out.splitlines():
        line = line.strip()
        if line.startswith("SERVICE_NAME:"):
            if current:
                items.append(current)
            current = {"service_name": line.split(":", 1)[1].strip()}
        elif current is not None:
            if line.startswith("DISPLAY_NAME:"):
                current["display_name"] = line.split(":", 1)[1].strip()
            elif line.startswith("STATE"):
                # STATE              : 4  RUNNING
                m = re.search(r":\s+\d+\s+(\w+)", line)
                if m:
                    current["state"] = m.group(1)
            elif line.startswith("PID"):
                pid = line.split(":", 1)[1].strip()
                if pid.isdigit():
                    current["pid"] = int(pid)

    if current:
        items.append(current)

    items = items[:limit]
    items.sort(key=lambda x: (x.get("service_name", "")))
    return items


def suspicious_services(services: list[dict]) -> list[dict]:
    """
    Heuristics: weird names, missing display name, running with no display name, etc.
    (No false "malware" claims; just flags.)
    """
    flagged = []
    for s in services:
        name = (s.get("service_name") or "").lower()
        disp = (s.get("display_name") or "").lower()
        state = (s.get("state") or "").lower()

        score = 0
        reasons = []

        if not disp:
            score += 2
            reasons.append("missing display name")

        if state == "running" and (len(name) <= 4 or name.isdigit()):
            score += 3
            reasons.append("odd short name running")

        if any(x in name for x in ["miner", "proxy", "rat", "hack", "steal", "keylog"]):
            score += 5
            reasons.append("suspicious keyword in name")

        if score >= 3:
            x = dict(s)
            x["flag_score"] = score
            x["reasons"] = reasons
            flagged.append(x)

    flagged.sort(key=lambda x: (-x.get("flag_score", 0), x.get("service_name", "")))
    return flagged
