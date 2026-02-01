from __future__ import annotations

import platform
import subprocess
from pathlib import Path


def _win_only() -> tuple[bool, str]:
    if platform.system().lower() != "windows":
        return False, "This action is Windows-only."
    return True, ""


def disable_startup_shortcut(name_contains: str) -> dict:
    """
    Safe action: disable startup folder shortcut by renaming to .disabled
    (does NOT delete).
    """
    ok, msg = _win_only()
    if not ok:
        return {"ok": False, "message": msg}

    # target both user + all users startup folders
    import os
    items = []
    appdata = os.environ.get("APPDATA", "")
    programdata = os.environ.get("PROGRAMDATA", "")

    paths = []
    if appdata:
        paths.append(Path(appdata) / "Microsoft/Windows/Start Menu/Programs/Startup")
    if programdata:
        paths.append(Path(programdata) / "Microsoft/Windows/Start Menu/Programs/Startup")

    needle = name_contains.lower().strip()
    if not needle:
        return {"ok": False, "message": "Provide a name fragment to match."}

    hits = []
    for p in paths:
        if not p.exists():
            continue
        for f in p.iterdir():
            if not f.is_file():
                continue
            if needle in f.name.lower():
                hits.append(f)

    if not hits:
        return {"ok": False, "message": "No startup folder entries matched."}

    changed = []
    for f in hits[:10]:
        dst = f.with_name(f.name + ".disabled")
        try:
            f.rename(dst)
            changed.append({"from": str(f), "to": str(dst)})
        except Exception as e:
            changed.append({"from": str(f), "error": str(e)})

    return {"ok": True, "changed": changed}


def disable_scheduled_task(task_name: str) -> dict:
    ok, msg = _win_only()
    if not ok:
        return {"ok": False, "message": msg}

    task_name = task_name.strip()
    if not task_name:
        return {"ok": False, "message": "Task name required."}

    # schtasks requires exact task path name; user should paste from list
    try:
        r = subprocess.run(
            ["schtasks", "/Change", "/TN", task_name, "/Disable"],
            text=True,
            capture_output=True,
        )  # noqa: S603,S607
        if r.returncode != 0:
            return {"ok": False, "message": r.stderr.strip() or r.stdout.strip() or "Failed to disable task."}
        return {"ok": True, "message": r.stdout.strip() or "Task disabled."}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def stop_service(service_name: str) -> dict:
    ok, msg = _win_only()
    if not ok:
        return {"ok": False, "message": msg}

    service_name = service_name.strip()
    if not service_name:
        return {"ok": False, "message": "Service name required."}

    try:
        r = subprocess.run(
            ["sc", "stop", service_name],
            text=True,
            capture_output=True,
        )  # noqa: S603,S607
        if r.returncode != 0:
            return {"ok": False, "message": r.stderr.strip() or r.stdout.strip() or "Failed to stop service."}
        return {"ok": True, "message": r.stdout.strip() or "Service stop requested."}
    except Exception as e:
        return {"ok": False, "message": str(e)}

