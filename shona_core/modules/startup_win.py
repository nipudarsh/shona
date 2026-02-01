from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path


def _not_supported() -> list[dict]:
    return [{"error": "startup scan not supported on this OS"}]


def list_startup_entries() -> list[dict]:
    """
    Windows startup persistence sources:
    - Startup folders (current user + all users)
    - Registry Run keys (HKCU/HKLM)
    Read-only listing.
    """
    if platform.system().lower() != "windows":
        return _not_supported()

    items: list[dict] = []

    # Startup folders
    appdata = os.environ.get("APPDATA", "")
    programdata = os.environ.get("PROGRAMDATA", "")

    paths = []
    if appdata:
        paths.append(Path(appdata) / "Microsoft/Windows/Start Menu/Programs/Startup")
    if programdata:
        paths.append(Path(programdata) / "Microsoft/Windows/Start Menu/Programs/Startup")

    for p in paths:
        try:
            if p.exists():
                for f in p.iterdir():
                    if f.is_file():
                        items.append({"source": "startup_folder", "name": f.name, "value": str(f)})
        except Exception:
            continue

    # Registry Run keys
    run_keys = [
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce",
        r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
        r"HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    ]

    for key in run_keys:
        try:
            out = subprocess.check_output(["reg", "query", key], text=True, errors="ignore")  # noqa: S603,S607
            for line in out.splitlines():
                line = line.strip()
                if not line or line.startswith(key):
                    continue
                # Example:  OneDrive    REG_SZ    "C:\...\OneDrive.exe" /background
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    name, reg_type, value = parts[0], parts[1], parts[2]
                    items.append({"source": "registry_run", "key": key, "name": name, "type": reg_type, "value": value})
        except Exception:
            continue

    items.sort(key=lambda x: (x.get("source", ""), x.get("name", "")))
    return items
