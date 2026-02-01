from __future__ import annotations

import platform
import subprocess


def list_processes() -> list[dict]:
    """
    Returns a lightweight process list: [{"pid": int, "name": str}]
    Windows: tasklist CSV
    Linux/macOS: ps
    """
    system = platform.system().lower()

    if system == "windows":
        cmd = ["tasklist", "/fo", "csv", "/nh"]
        out = subprocess.check_output(cmd, text=True, errors="ignore")
        procs: list[dict] = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip().strip('"') for p in line.split('","')]
            if len(parts) < 2:
                continue
            name = parts[0]
            pid_str = parts[1]
            if pid_str.isdigit():
                procs.append({"pid": int(pid_str), "name": name})
        procs.sort(key=lambda x: (x["name"].lower(), x["pid"]))
        return procs

    cmd = ["ps", "-eo", "pid,comm"]
    out = subprocess.check_output(cmd, text=True, errors="ignore")
    procs: list[dict] = []
    for i, line in enumerate(out.splitlines()):
        if i == 0:
            continue
        line = line.strip()
        if not line:
            continue
        pid_str, *name_parts = line.split()
        if not pid_str.isdigit():
            continue
        name = " ".join(name_parts) if name_parts else "unknown"
        procs.append({"pid": int(pid_str), "name": name})
    procs.sort(key=lambda x: (x["name"].lower(), x["pid"]))
    return procs
