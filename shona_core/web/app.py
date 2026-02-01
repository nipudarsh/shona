from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from shona_core.scan import run_scan
from shona_core.diff import diff_latest_two
from shona_core.risk import score_diff
from shona_core.modules.processes import list_processes
from shona_core.modules.ports import list_listening_ports

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="SHONA", version="0.2.1")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/api/health")
def api_health():
    return JSONResponse({"ok": True, "name": "shona", "version": "0.2.0"})



@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/friendline")
def api_friendline():
    lines = [
        "Hey Nipun. I’m here. Want a quick scan?",
        "All quiet. I’ll stay calm in the background.",
        "If anything changes, I’ll explain it cleanly—no panic.",
        "Type: scan, diff, ports, ps, find <name>",
    ]
    return JSONResponse({"lines": lines})


@app.post("/api/scan")
def api_scan():
    p = run_scan()
    return JSONResponse({"ok": True, "snapshot": str(p)})


@app.get("/api/diff")
def api_diff():
    d = diff_latest_two()
    r = score_diff(d)
    return JSONResponse({"diff": d, "risk": r})


@app.get("/api/ps")
def api_ps(limit: int = 30):
    procs = list_processes()[: max(1, min(limit, 200))]
    return JSONResponse({"items": procs})


@app.get("/api/ports")
def api_ports():
    return JSONResponse({"items": list_listening_ports()})


def _safe_find_files(query: str, limit: int = 30) -> list[str]:
    query_l = query.lower().strip()
    if not query_l:
        return []

    home = Path.home()
    bases = [home / "Desktop", home / "Downloads", home / "Documents", home]
    seen = set()
    hits: list[str] = []

    for base in bases:
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                if query_l in p.name.lower():
                    s = str(p)
                    if s in seen:
                        continue
                    seen.add(s)
                    hits.append(s)
                    if len(hits) >= limit:
                        return hits
        except Exception:
            continue

    return hits


@app.post("/api/command")
async def api_command(payload: dict):
    """
    Accepts: {"text":"scan"} etc.
    Returns: {"ok":true,"kind":"diff|scan|ports|ps|find|help","data":{...},"say":"..."}
    """
    text = str(payload.get("text", "")).strip()
    cmd = text.lower()

    if not cmd:
        return JSONResponse({"ok": False, "kind": "help", "data": {}, "say": "Type a command like: scan, diff, ports, ps, find <name>."})

    if cmd == "scan":
        p = run_scan()
        return JSONResponse({"ok": True, "kind": "scan", "data": {"snapshot": str(p)}, "say": "Snapshot saved. Want a diff?"})

    if cmd == "diff":
        d = diff_latest_two()
        r = score_diff(d)
        sev = (r.get("severity") or "low").lower()
        if sev == "high":
            say = "Something looks risky. I can explain what changed."
        elif sev == "medium":
            say = "A few things changed. Probably normal, but worth a look."
        else:
            say = "All calm. No meaningful changes detected."
        return JSONResponse({"ok": True, "kind": "diff", "data": {"diff": d, "risk": r}, "say": say})

    if cmd == "ports":
        items = list_listening_ports()
        return JSONResponse({"ok": True, "kind": "ports", "data": {"items": items}, "say": "Here are listening ports. New unexpected ports can matter."})

    if cmd.startswith("ps"):
        # ps or ps 50
        parts = cmd.split()
        limit = 40
        if len(parts) >= 2 and parts[1].isdigit():
            limit = max(1, min(int(parts[1]), 200))
        items = list_processes()[:limit]
        return JSONResponse({"ok": True, "kind": "ps", "data": {"items": items}, "say": f"Here are running processes (top {limit})."})

    if cmd.startswith("find "):
        q = cmd[5:].strip()
        hits = _safe_find_files(q, limit=30)
        return JSONResponse({"ok": True, "kind": "find", "data": {"query": q, "hits": hits}, "say": f"I found {len(hits)} match(es). Want me to open one?"})

    return JSONResponse({"ok": False, "kind": "help", "data": {}, "say": "I can run: scan, diff, ports, ps, find <name>."})
