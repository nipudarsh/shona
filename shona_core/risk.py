from __future__ import annotations


def score_diff(diff: dict) -> dict:
    if not diff.get("ok"):
        return {"severity": "info", "score": 0, "explain": diff.get("message", "No diff")}

    score = 0
    notes: list[str] = []

    sys_changes = diff.get("changes", {})
    if sys_changes:
        score += 5 * len(sys_changes)
        notes.append(f"{len(sys_changes)} system identity change(s)")

    proc_added = diff.get("processes", {}).get("added", [])
    proc_removed = diff.get("processes", {}).get("removed", [])
    if proc_added or proc_removed:
        score += min(30, 2 * (len(proc_added) + len(proc_removed)))
        notes.append(f"process changes (+{len(proc_added)}/-{len(proc_removed)})")

    ports_added = diff.get("ports", {}).get("added", [])
    ports_removed = diff.get("ports", {}).get("removed", [])
    if ports_added or ports_removed:
        score += min(40, 5 * (len(ports_added) + len(ports_removed)))
        notes.append(f"listening port changes (+{len(ports_added)}/-{len(ports_removed)})")

    if score >= 60:
        severity = "high"
    elif score >= 20:
        severity = "medium"
    else:
        severity = "low"

    explain = "Detected: " + (", ".join(notes) if notes else "no notable changes")
    return {"severity": severity, "score": score, "explain": explain}
