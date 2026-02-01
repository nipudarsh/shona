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

app = FastAPI(title="SHONA", version="0.1.1")

# ✅ Serve static files correctly: /static/styles.css, /static/app.js
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/api/health")
def api_health():
    return JSONResponse({"ok": True, "name": "shona", "version": "0.1.1"})


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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


@app.get("/api/friendline")
def api_friendline():
    lines = [
        "Hey Nipun. I’m here. Want a quick scan?",
        "All quiet. I can stay in the background while you work.",
        "If something changes, I’ll explain it clearly—no panic.",
        "Tell me what you need: scan, diff, ports, or processes.",
    ]
    return JSONResponse({"lines": lines})
