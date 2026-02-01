from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from shona_core.scan import run_scan
from shona_core.diff import diff_latest_two
from shona_core.risk import score_diff
from shona_core.modules.processes import list_processes
from shona_core.modules.ports import list_listening_ports

# Web/tray imports are optional at runtime
# (import inside functions to keep CLI fast)


RUNTIME_DIR = Path(".shona")
STATE_DIR = RUNTIME_DIR / "state"
PID_FILE = STATE_DIR / "web.pid"
URL_FILE = STATE_DIR / "web.url"


def _ensure_runtime() -> None:
    (RUNTIME_DIR / "snapshots").mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def cmd_scan() -> int:
    _ensure_runtime()
    path = run_scan()
    print(path)
    return 0


def cmd_diff() -> int:
    _ensure_runtime()
    d = diff_latest_two()
    r = score_diff(d)
    out = {"diff": d, "risk": r}
    print(json.dumps(out, indent=2))
    return 0 if d.get("ok") else 2


def cmd_ps(limit: int) -> int:
    procs = list_processes()
    if limit > 0:
        procs = procs[:limit]
    print(json.dumps(procs, indent=2))
    return 0


def cmd_ports() -> int:
    ports = list_listening_ports()
    print(json.dumps(ports, indent=2))
    return 0


def _home_dirs() -> list[Path]:
    # Windows-friendly search bases
    home = Path.home()
    bases = [home]
    for name in ("Desktop", "Downloads", "Documents"):
        p = home / name
        if p.exists():
            bases.append(p)
    return bases


def cmd_find(query: str, limit: int) -> int:
    query_l = query.lower()
    hits: list[str] = []
    for base in _home_dirs():
        try:
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                if query_l in p.name.lower():
                    hits.append(str(p))
                    if len(hits) >= limit:
                        print(json.dumps(hits, indent=2))
                        return 0
        except Exception:
            continue
    print(json.dumps(hits, indent=2))
    return 0


def cmd_open(path_str: str) -> int:
    p = Path(path_str).expanduser()
    if not p.exists():
        print(f"[ERR] File not found: {p}", file=sys.stderr)
        return 2

    if sys.platform.startswith("win"):
        os.startfile(str(p))  # noqa: S606
        return 0

    # macOS / Linux
    import subprocess

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(p)])  # noqa: S603,S607
    else:
        subprocess.Popen(["xdg-open", str(p)])  # noqa: S603,S607
    return 0


def _is_web_running() -> bool:
    return PID_FILE.exists()


def cmd_status() -> int:
    _ensure_runtime()
    status = {
        "web_running": _is_web_running(),
        "web_url": URL_FILE.read_text(encoding="utf-8").strip() if URL_FILE.exists() else None,
    }
    print(json.dumps(status, indent=2))
    return 0


def cmd_web_start(host: str, port: int) -> int:
    _ensure_runtime()
    if _is_web_running():
        print("[OK] Web already running.")
        return 0

    import subprocess

    # Start uvicorn in background
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "shona_core.web.app:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
    PID_FILE.write_text(str(p.pid), encoding="utf-8")
    url = f"http://{host}:{port}"
    URL_FILE.write_text(url, encoding="utf-8")
    print(f"[OK] Web started: {url}")
    return 0


def cmd_web_open() -> int:
    _ensure_runtime()
    url = URL_FILE.read_text(encoding="utf-8").strip() if URL_FILE.exists() else "http://127.0.0.1:7860"
    import webbrowser

    webbrowser.open(url)
    print(f"[OK] Opened: {url}")
    return 0


def cmd_web_stop() -> int:
    _ensure_runtime()
    if not PID_FILE.exists():
        print("[OK] Web not running.")
        return 0

    pid_str = PID_FILE.read_text(encoding="utf-8").strip()
    PID_FILE.unlink(missing_ok=True)
    try:
        pid = int(pid_str)
    except ValueError:
        print("[WARN] Invalid PID file.")
        return 0

    if sys.platform.startswith("win"):
        import subprocess

        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)  # noqa: S603,S607
    else:
        try:
            os.kill(pid, 15)
        except Exception:
            pass

    print("[OK] Web stopped.")
    return 0


def cmd_tray() -> int:
    _ensure_runtime()
    from shona_core.tray import run_tray

    run_tray()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="shona", description="SHONA - local-first cybersecurity assistant")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("scan", help="Create a new security snapshot")
    sub.add_parser("diff", help="Diff the latest two snapshots")

    ps_p = sub.add_parser("ps", help="List running processes")
    ps_p.add_argument("--limit", type=int, default=50)

    sub.add_parser("ports", help="List listening ports")

    find_p = sub.add_parser("find", help="Search for files by name")
    find_p.add_argument("query", type=str)
    find_p.add_argument("--limit", type=int, default=30)

    open_p = sub.add_parser("open", help="Open a file path with default app")
    open_p.add_argument("path", type=str)

    sub.add_parser("status", help="Show SHONA runtime status")

    web_p = sub.add_parser("web", help="Control local SHONA web UI")
    web_sub = web_p.add_subparsers(dest="webcmd", required=True)
    web_start = web_sub.add_parser("start", help="Start web UI server")
    web_start.add_argument("--host", type=str, default="127.0.0.1")
    web_start.add_argument("--port", type=int, default=7860)
    web_sub.add_parser("open", help="Open web UI in browser")
    web_sub.add_parser("stop", help="Stop web UI server")

    sub.add_parser("tray", help="Run SHONA tray app (Windows-friendly)")

    args = parser.parse_args()

    rc = 0
    if args.cmd == "scan":
        rc = cmd_scan()
    elif args.cmd == "diff":
        rc = cmd_diff()
    elif args.cmd == "ps":
        rc = cmd_ps(args.limit)
    elif args.cmd == "ports":
        rc = cmd_ports()
    elif args.cmd == "find":
        rc = cmd_find(args.query, args.limit)
    elif args.cmd == "open":
        rc = cmd_open(args.path)
    elif args.cmd == "status":
        rc = cmd_status()
    elif args.cmd == "web":
        if args.webcmd == "start":
            rc = cmd_web_start(args.host, args.port)
        elif args.webcmd == "open":
            rc = cmd_web_open()
        elif args.webcmd == "stop":
            rc = cmd_web_stop()
    elif args.cmd == "tray":
        rc = cmd_tray()

    raise SystemExit(rc)
