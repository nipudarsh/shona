from __future__ import annotations


def score_diff(diff: dict) -> dict:
    if not diff.get("ok"):
        return {"severity": "info", "score": 0, "explain": diff.get("message", "No diff")}

    score = 0
    notes: list[str] = []

    def add(cat: str, weight: int, cap: int) -> None:
        nonlocal score
        added = diff.get(cat, {}).get("added", [])
        removed = diff.get(cat, {}).get("removed", [])
        n = len(added) + len(removed)
        if n:
            score += min(cap, weight * n)
            notes.append(f"{cat} changes (+{len(added)}/-{len(removed)})")

    add("processes", weight=2, cap=30)
    add("ports", weight=5, cap=40)

    # Persistence surfaces are higher risk if they change
    add("startup", weight=8, cap=60)
    add("scheduled_tasks", weight=8, cap=60)
    add("services", weight=6, cap=50)

    if score >= 80:
        severity = "high"
    elif score >= 30:
        severity = "medium"
    else:
        severity = "low"

    explain = "Detected: " + (", ".join(notes) if notes else "no notable changes")
    return {"severity": severity, "score": score, "explain": explain}
