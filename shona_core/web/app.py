from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from shona_core.scan import run_scan
from shona_core.diff import diff_latest_two
from shona_core.risk import score_diff
from shona_core.modules.processes import list_processes
from shona_core.modules.ports import list_listening_ports

app = FastAPI(title="SHONA", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


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

@app.get("/api/health")
def api_health():
    return JSONResponse({"ok": True, "name": "shona", "version": "0.1.0"})


@app.get("/api/friendline")
def api_friendline():
    # Friendly “assistant voice” responses (safe, not creepy)
    lines = [
        "Hey Nipun. I’m here. Want a quick scan?",
        "All quiet on the system side. I can stay in the background.",
        "Something changed recently. If you want, I’ll explain it in simple terms.",
        "Tell me what you need—files, ports, processes, anything.",
    ]
    return JSONResponse({"lines": lines})
