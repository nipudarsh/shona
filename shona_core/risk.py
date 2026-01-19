from __future__ import annotations

def score_diff(diff: dict):
    if not diff.get("ok"):
        return {"severity": "info", "score": 0}
    c = len(diff.get("changes", {}))
    score = min(20, c * 5)
    return {
        "severity": "medium" if score >= 10 else "low",
        "score": score,
    }
