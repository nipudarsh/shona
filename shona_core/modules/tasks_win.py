from __future__ import annotations

import platform
import subprocess


def _not_supported() -> list[dict]:
    return [{"error": "scheduled tasks not supported on this OS"}]


def list_scheduled_tasks(limit: int = 200) -> list[dict]:
    """
    Windows scheduled tasks (common persistence).
    Uses schtasks /Query /FO CSV /V
    """
    if platform.system().lower() != "windows":
        return _not_supported()

    try:
        out = subprocess.check_output(["schtasks", "/Query", "/FO", "CSV", "/V"], text=True, errors="ignore")  # noqa: S603,S607
    except Exception:
        return [{"error": "failed to query scheduled tasks"}]

    lines = out.splitlines()
    if len(lines) < 2:
        return []

    # CSV parsing without importing csv to keep minimal? We'll do safe split via csv module.
    import csv
    from io import StringIO

    reader = csv.DictReader(StringIO(out))
    items = []
    for i, row in enumerate(reader):
        if i >= limit:
            break
        # Normalize key names (Windows uses localized headers sometimes; keep raw row too)
        items.append({
            "TaskName": row.get("TaskName") or row.get("Task Name") or row.get("Task"),
            "Status": row.get("Status"),
            "Author": row.get("Author"),
            "Task To Run": row.get("Task To Run") or row.get("TaskToRun"),
            "Schedule": row.get("Schedule") or row.get("Schedule Type"),
            "Run As User": row.get("Run As User") or row.get("RunAsUser"),
        })

    # keep only rows with a task name
    items = [x for x in items if x.get("TaskName")]
    items.sort(key=lambda x: (x.get("TaskName") or ""))
    return items
