from __future__ import annotations

import platform
import subprocess
import re


def list_listening_ports() -> list[dict]:
    """
    Returns listening ports:
    [{"proto":"TCP/UDP","local":"IP:PORT","pid":int|None}]
    """
    system = platform.system().lower()

    if system == "windows":
        cmd = ["netstat", "-ano"]
        out = subprocess.check_output(cmd, text=True, errors="ignore")
        results: list[dict] = []
        for line in out.splitlines():
            line = line.strip()
            if not line.startswith(("TCP", "UDP")):
                continue
            parts = re.split(r"\s+", line)
            if len(parts) < 4:
                continue

            proto = parts[0]
            local = parts[1]
            pid = None

            if proto == "TCP":
                if "LISTENING" not in parts:
                    continue
                pid_str = parts[-1]
                if pid_str.isdigit():
                    pid = int(pid_str)
                results.append({"proto": proto, "local": local, "pid": pid})
            else:
                pid_str = parts[-1]
                if pid_str.isdigit():
                    pid = int(pid_str)
                results.append({"proto": proto, "local": local, "pid": pid})

        results.sort(key=lambda x: (x["proto"], x["local"], x["pid"] or -1))
        return results

    # Linux/macOS: try ss
    try:
        cmd = ["ss", "-lntu", "-p"]
        out = subprocess.check_output(cmd, text=True, errors="ignore")
        results: list[dict] = []
        for line in out.splitlines():
            if line.startswith("Netid") or not line.strip():
                continue
            parts = re.split(r"\s+", line.strip())
            proto = parts[0].upper()
            local = parts[4] if len(parts) > 4 else ""
            pid = None
            m = re.search(r"pid=(\d+)", line)
            if m:
                pid = int(m.group(1))
            if local:
                results.append({"proto": proto, "local": local, "pid": pid})
        results.sort(key=lambda x: (x["proto"], x["local"], x["pid"] or -1))
        return results
    except Exception:
        return []
