from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from shona_core.audit import log_event, tail as audit_tail
from shona_core.diff import diff_against_baseline, diff_latest_two
from shona_core.modules.ports import list_listening_ports
from shona_core.modules.processes import list_processes
from shona_core.owner import owner_init, owner_verify, require_token
from shona_core.retention import baseline_set, ignore_add, load_ignore
from shona_core.risk import score_diff
from shona_core.scan import run_scan
from shona_core.settings import load_settings, set_setting
from shona_core.voice import listen_ptt, speak, voice_status

RUNTIME_DIR = Path(".shona")
STATE_DIR = RUNTIME_DIR / "state"
PID_FILE = STATE_DIR / "web.pid"
URL_FILE = STATE_DIR / "web.url"


def _ensure_runtime() -> None:
    (RUNTIME_DIR / "snapshots").mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------
# Core commands
# ----------------------------
def cmd_scan() -> int:
    _ensure_runtime()
    path = run_scan()
    print(path)
    return 0


def cmd_diff(use_baseline: bool) -> int:
    _ensure_runtime()
    d = diff_against_baseline() if use_baseline else diff_latest_two()
    r = score_diff(d)
    out = {"diff": d, "risk": r}
    print(json.dumps(out, indent=2))
    return 0 if d.get("ok") else 2


def cmd_ps(limit: int) -> int:
    procs = list_processes()
    procs = procs[: max(1, min(limit, 200))] if limit else procs
    print(json.dumps(procs, indent=2))
    return 0


def cmd_ports() -> int:
    ports = list_listening_ports()
    print(json.dumps(ports, indent=2))
    return 0


# ----------------------------
# Defender (Windows persistence)
# ----------------------------
def cmd_startup_list() -> int:
    import platform

    if platform.system().lower() != "windows":
        print(json.dumps({"ok": False, "message": "startup list is windows-only"}, indent=2))
        return 2
    from shona_core.modules.startup_win import list_startup_entries

    print(json.dumps({"ok": True, "items": list_startup_entries()}, indent=2))
    return 0


def cmd_tasks_list(limit: int) -> int:
    import platform

    if platform.system().lower() != "windows":
        print(json.dumps({"ok": False, "message": "tasks list is windows-only"}, indent=2))
        return 2
    from shona_core.modules.tasks_win import list_scheduled_tasks

    print(json.dumps({"ok": True, "items": list_scheduled_tasks(limit=max(1, min(limit, 1000)))}, indent=2))
    return 0


def cmd_services_list(limit: int) -> int:
    import platform

    if platform.system().lower() != "windows":
        print(json.dumps({"ok": False, "message": "services list is windows-only"}, indent=2))
        return 2
    from shona_core.modules.services_win import list_services

    print(json.dumps({"ok": True, "items": list_services(limit=max(1, min(limit, 2000)))}, indent=2))
    return 0


def cmd_services_suspicious() -> int:
    import platform

    if platform.system().lower() != "windows":
        print(json.dumps({"ok": False, "message": "services suspicious is windows-only"}, indent=2))
        return 2
    from shona_core.modules.services_win import list_services, suspicious_services

    items = list_services()
    flagged = suspicious_services(items)
    print(json.dumps({"ok": True, "flagged": flagged}, indent=2))
    return 0


# ----------------------------
# Retention: ignore + baseline
# ----------------------------
def cmd_ignore_add(kind: str, value: str) -> int:
    data = ignore_add(kind, value)
    print(json.dumps({"ok": True, "ignore": data}, indent=2))
    return 0


def cmd_ignore_list() -> int:
    print(json.dumps({"ok": True, "ignore": load_ignore()}, indent=2))
    return 0


def cmd_baseline_accept(snapshot: str) -> int:
    _ensure_runtime()
    p = Path(snapshot)
    if not p.exists():
        alt = Path(".shona/snapshots") / snapshot
        if alt.exists():
            p = alt
        else:
            print(json.dumps({"ok": False, "message": f"snapshot not found: {snapshot}"}, indent=2))
            return 2
    data = baseline_set(str(p))
    print(json.dumps({"ok": True, "baseline": data}, indent=2))
    return 0


# ----------------------------
# Owner verification + audit
# ----------------------------
def cmd_owner_init(pin: str) -> int:
    res = owner_init(pin)
    print(json.dumps(res, indent=2))
    log_event("owner_init", {"ok": bool(res.get("ok"))})
    return 0 if res.get("ok") else 2


def cmd_owner_verify(pin: str, ttl: int) -> int:
    res = owner_verify(pin, ttl_seconds=ttl)
    print(json.dumps(res, indent=2))
    log_event("owner_verify", {"ok": bool(res.get("ok")), "ttl": ttl})
    return 0 if res.get("ok") else 2


def cmd_audit_show(tail_n: int) -> int:
    items = audit_tail(max(1, min(tail_n, 500)))
    print(json.dumps({"ok": True, "items": items}, indent=2))
    return 0


# ----------------------------
# Safe Actions (owner token required)
# ----------------------------
def cmd_startup_disable(name: str, token: str) -> int:
    chk = require_token(token)
    if not chk.get("ok"):
        print(json.dumps(chk, indent=2))
        log_event("startup_disable", {"ok": False, "reason": chk.get("message")})
        return 2

    from shona_core.modules.actions_win import disable_startup_shortcut

    res = disable_startup_shortcut(name)
    print(json.dumps(res, indent=2))
    log_event("startup_disable", {"ok": bool(res.get("ok")), "name": name})
    return 0 if res.get("ok") else 2


def cmd_tasks_disable(taskname: str, token: str) -> int:
    chk = require_token(token)
    if not chk.get("ok"):
        print(json.dumps(chk, indent=2))
        log_event("tasks_disable", {"ok": False, "reason": chk.get("message")})
        return 2

    from shona_core.modules.actions_win import disable_scheduled_task

    res = disable_scheduled_task(taskname)
    print(json.dumps(res, indent=2))
    log_event("tasks_disable", {"ok": bool(res.get("ok")), "task": taskname})
    return 0 if res.get("ok") else 2


def cmd_services_stop(service: str, token: str) -> int:
    chk = require_token(token)
    if not chk.get("ok"):
        print(json.dumps(chk, indent=2))
        log_event("services_stop", {"ok": False, "reason": chk.get("message")})
        return 2

    from shona_core.modules.actions_win import stop_service

    res = stop_service(service)
    print(json.dumps(res, indent=2))
    log_event("services_stop", {"ok": bool(res.get("ok")), "service": service})
    return 0 if res.get("ok") else 2


# ----------------------------
# Settings + Voice (Friend Mode)
# ----------------------------
def cmd_config_get() -> int:
    print(json.dumps({"ok": True, "settings": load_settings()}, indent=2))
    return 0


def cmd_config_set(key: str, value: str) -> int:
    # simple type parsing
    v = value
    if isinstance(value, str) and value.lower() in ["true", "false"]:
        v = (value.lower() == "true")
    else:
        try:
            if isinstance(value, str) and "." in value:
                v = float(value)
            else:
                v = int(value)
        except Exception:
            v = value

    data = set_setting(key, v)
    print(json.dumps({"ok": True, "settings": data}, indent=2))
    return 0


def cmd_voice_status() -> int:
    st = voice_status()
    print(json.dumps({"ok": True, "tts_ok": st.tts_ok, "stt_ok": st.stt_ok, "message": st.message}, indent=2))
    return 0


def cmd_voice_say(text: str) -> int:
    res = speak(text)
    print(json.dumps(res, indent=2))
    return 0 if res.get("ok") else 2


def cmd_voice_talk_ptt(seconds: int) -> int:
    seconds = max(1, min(int(seconds), 20))
    print(json.dumps({"ok": True, "message": f"Listening for {seconds}s (push-to-talk)…"}, indent=2))

    r = listen_ptt(seconds=seconds)
    print(json.dumps(r, indent=2))

    if r.get("ok") and r.get("text"):
        reply = f"I heard: {r['text']}. Want me to run scan or diff?"
        _ = speak(reply)

    return 0 if r.get("ok") else 2


# ----------------------------
# Web control + Tray
# ----------------------------
def _is_web_running() -> bool:
    if not URL_FILE.exists():
        return False
    url = URL_FILE.read_text(encoding="utf-8").strip()
    if not url:
        return False
    try:
        import urllib.request

        with urllib.request.urlopen(url + "/api/health", timeout=1.2) as r:
            return r.status == 200
    except Exception:
        return False


def cmd_status() -> int:
    _ensure_runtime()
    status = {
        "web_running": _is_web_running(),
        "web_url": URL_FILE.read_text(encoding="utf-8").strip() if URL_FILE.exists() else None,
        "settings": load_settings(),
    }
    print(json.dumps(status, indent=2))
    return 0


def cmd_web_start(host: str, port: int) -> int:
    _ensure_runtime()
    if _is_web_running():
        print("[OK] Web already running.")
        return 0

    PID_FILE.unlink(missing_ok=True)
    URL_FILE.unlink(missing_ok=True)

    import subprocess

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

    diff_p = sub.add_parser("diff", help="Diff snapshots")
    diff_p.add_argument("--baseline", action="store_true", help="Diff latest snapshot against accepted baseline")

    ps_p = sub.add_parser("ps", help="List running processes")
    ps_p.add_argument("--limit", type=int, default=50)

    sub.add_parser("ports", help="List listening ports")

    # Persistence
    startup_p = sub.add_parser("startup", help="Startup persistence (Windows)")
    startup_sub = startup_p.add_subparsers(dest="startup_cmd", required=True)
    startup_sub.add_parser("list", help="List startup entries")
    sd = startup_sub.add_parser("disable", help="Disable a startup folder entry (safe rename)")
    sd.add_argument("name", type=str, help="Name fragment to match")
    sd.add_argument("--token", required=True)

    tasks_p = sub.add_parser("tasks", help="Scheduled tasks (Windows)")
    tasks_sub = tasks_p.add_subparsers(dest="tasks_cmd", required=True)
    tl = tasks_sub.add_parser("list", help="List scheduled tasks")
    tl.add_argument("--limit", type=int, default=200)
    td = tasks_sub.add_parser("disable", help="Disable a scheduled task by name")
    td.add_argument("taskname", type=str)
    td.add_argument("--token", required=True)

    services_p = sub.add_parser("services", help="Windows services")
    services_sub = services_p.add_subparsers(dest="services_cmd", required=True)
    sl = services_sub.add_parser("list", help="List services")
    sl.add_argument("--limit", type=int, default=300)
    services_sub.add_parser("suspicious", help="Heuristic flags (non-judgemental)")
    ss = services_sub.add_parser("stop", help="Stop a service (requests stop)")
    ss.add_argument("service", type=str)
    ss.add_argument("--token", required=True)

    # Retention
    ignore_p = sub.add_parser("ignore", help="Ignore list to reduce noise")
    ignore_sub = ignore_p.add_subparsers(dest="ignore_cmd", required=True)
    ignore_add_p = ignore_sub.add_parser("add", help="Add ignore entry")
    ignore_add_p.add_argument("kind", choices=["processes", "ports"], help="Ignore category")
    ignore_add_p.add_argument("value", type=str, help="Value to ignore (exact match)")
    ignore_sub.add_parser("list", help="Show ignore list")

    baseline_p = sub.add_parser("baseline", help="Baseline control")
    baseline_sub = baseline_p.add_subparsers(dest="baseline_cmd", required=True)
    base_acc = baseline_sub.add_parser("accept", help="Accept a snapshot as baseline")
    base_acc.add_argument("snapshot", type=str, help="Snapshot filename or path")

    # Owner + audit
    owner_p = sub.add_parser("owner", help="Owner verification (PIN)")
    owner_sub = owner_p.add_subparsers(dest="owner_cmd", required=True)
    oi = owner_sub.add_parser("init", help="Initialize owner PIN")
    oi.add_argument("--pin", required=True)
    ov = owner_sub.add_parser("verify", help="Verify PIN and get short-lived token")
    ov.add_argument("--pin", required=True)
    ov.add_argument("--ttl", type=int, default=300)

    audit_p = sub.add_parser("audit", help="Audit log")
    audit_sub = audit_p.add_subparsers(dest="audit_cmd", required=True)
    ash = audit_sub.add_parser("show", help="Show recent audit events")
    ash.add_argument("--tail", type=int, default=50)

    # Friend mode: settings + voice
    config_p = sub.add_parser("config", help="Settings")
    config_sub = config_p.add_subparsers(dest="config_cmd", required=True)
    config_sub.add_parser("get", help="Show settings")
    cs = config_sub.add_parser("set", help="Set a setting")
    cs.add_argument("key", type=str)
    cs.add_argument("value", type=str)

    voice_p = sub.add_parser("voice", help="Voice features (opt-in)")
    voice_sub = voice_p.add_subparsers(dest="voice_cmd", required=True)
    voice_sub.add_parser("status", help="Show voice readiness")
    say_p = voice_sub.add_parser("say", help="Speak text (offline TTS)")
    say_p.add_argument("text", type=str)
    talk_p = voice_sub.add_parser("talk", help="Push-to-talk (offline STT if installed)")
    talk_p.add_argument("--seconds", type=int, default=5)

    # Status + web + tray
    sub.add_parser("status", help="Show SHONA runtime status")

    web_p = sub.add_parser("web", help="Control local SHONA web UI")
    web_sub = web_p.add_subparsers(dest="webcmd", required=True)
    web_start = web_sub.add_parser("start", help="Start web UI server")
    web_start.add_argument("--host", type=str, default="127.0.0.1")
    web_start.add_argument("--port", type=int, default=7860)
    web_sub.add_parser("open", help="Open web UI in browser")
    web_sub.add_parser("stop", help="Stop web UI server")

    sub.add_parser("tray", help="Run SHONA tray app")

    args = parser.parse_args()

    rc = 0
    if args.cmd == "scan":
        rc = cmd_scan()
    elif args.cmd == "diff":
        rc = cmd_diff(args.baseline)
    elif args.cmd == "ps":
        rc = cmd_ps(args.limit)
    elif args.cmd == "ports":
        rc = cmd_ports()
    elif args.cmd == "startup":
        if args.startup_cmd == "list":
            rc = cmd_startup_list()
        else:
            rc = cmd_startup_disable(args.name, args.token)
    elif args.cmd == "tasks":
        if args.tasks_cmd == "list":
            rc = cmd_tasks_list(args.limit)
        else:
            rc = cmd_tasks_disable(args.taskname, args.token)
    elif args.cmd == "services":
        if args.services_cmd == "list":
            rc = cmd_services_list(args.limit)
        elif args.services_cmd == "suspicious":
            rc = cmd_services_suspicious()
        else:
            rc = cmd_services_stop(args.service, args.token)
    elif args.cmd == "ignore":
        if args.ignore_cmd == "add":
            rc = cmd_ignore_add(args.kind, args.value)
        else:
            rc = cmd_ignore_list()
    elif args.cmd == "baseline":
        rc = cmd_baseline_accept(args.snapshot)
    elif args.cmd == "owner":
        if args.owner_cmd == "init":
            rc = cmd_owner_init(args.pin)
        else:
            rc = cmd_owner_verify(args.pin, args.ttl)
    elif args.cmd == "audit":
        rc = cmd_audit_show(args.tail)
    elif args.cmd == "config":
        if args.config_cmd == "get":
            rc = cmd_config_get()
        else:
            rc = cmd_config_set(args.key, args.value)
    elif args.cmd == "voice":
        if args.voice_cmd == "status":
            rc = cmd_voice_status()
        elif args.voice_cmd == "say":
            rc = cmd_voice_say(args.text)
        else:
            rc = cmd_voice_talk_ptt(args.seconds)
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
