# SHONA v0.3.0 — Local-First Cybersecurity Assistant (Friend Mode, Opt-In Voice)

> **SHONA** is a **local-first cybersecurity assistant** for Windows PCs (works cross-platform where possible) that helps you **see what changed**, detect **persistence tactics**, and take **safe owner-verified actions** — with a modern Web UI + CLI, and **opt-in voice** in v0.3.0.

✅ **No cloud required**  
✅ **Stores data locally** (`.shona/`)  
✅ **Read-only by default** (safe actions require owner verification)  
✅ **Opt-in voice** (no always-on mic)

---

## Why SHONA exists

Most “security tools” either:
- spam logs with noise, or  
- require deep expertise to interpret.

SHONA sits in the middle:
- **Snapshots** your system state
- **Diffs** what changed
- Flags **persistence surfaces** (startup, tasks, services)
- Lets you **baseline** good states and **ignore** noise
- Provides **owner-verified safe actions** (disable/stop) — with an audit trail
- Adds **Friend Mode** (v0.3.0): friendly responses + optional offline voice

---

## What’s new in v0.3.0

### 🩷 Friend Mode (without being creepy)
- **Opt-in Text-to-Speech (TTS)**: SHONA can speak (offline)
- **Optional Push-to-Talk STT** (offline) if you install Vosk + a local model
- Web UI can **speak responses** (only if you enable it)

**Privacy rule:** no always-on mic, and no recordings saved.

---

## Core Features

### ✅ Snapshot + Diff (baseline security)
- `shona scan` → create a snapshot
- `shona diff` → compare latest two snapshots
- `shona diff --baseline` → compare against a trusted baseline

### 🛡 Defender surfaces (Windows)
- `shona startup list` → startup folder + Run keys
- `shona tasks list` → scheduled tasks
- `shona services list` → services
- `shona services suspicious` → heuristic flags (non-judgemental)

### 🧠 Retention (reduce noise)
- `shona baseline accept <snapshot.json>` → mark a snapshot as “trusted”
- `shona ignore add processes <name>` → ignore known processes
- `shona ignore add ports <proto:addr>` → ignore known ports
- `shona ignore list` → show ignore list

### 🔐 Safe Actions (Owner Verified)
Sensitive actions are **token gated**:
- `shona owner init --pin 1234`
- `shona owner verify --pin 1234` → get token (short-lived)
- `shona startup disable "<name>" --token <TOKEN>` → safe rename to `.disabled`
- `shona tasks disable "<taskname>" --token <TOKEN>` → disables scheduled task
- `shona services stop "<service>" --token <TOKEN>` → requests stop

### 🧾 Audit log (local)
- `shona audit show --tail 50` → last actions + verifies

### 🌐 Web UI + Tray
- `shona web start` / `shona web open` / `shona web stop`
- Modern UI, command chat, and optional voice replies
- Tray support (if enabled in your build)

---

## Installation (Developer / Local)

### 1) Create a venv
**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
````

**Git Bash:**

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 2) Install editable

```bash
python -m pip install -e .
```

### 3) Verify CLI

```bash
shona status
shona scan
shona scan
shona diff
```

---

## Web UI

```bash
shona web start
shona web open
```

If your browser says “refused to connect”, run foreground server to debug:

```bash
python -m uvicorn shona_core.web.app:app --host 127.0.0.1 --port 7860
```

---

## Friend Mode (Voice)

### Enable voice (TTS)

```bash
shona config set voice_enabled true
shona voice status
shona voice say "Hi. I'm Shona."
```

### Optional: Push-to-Talk Speech-to-Text (offline)

Install STT deps:

```bash
pip install vosk sounddevice
```

Place a Vosk model locally (example path):

```
.shona/models/vosk
```

Then:

```bash
shona voice talk --seconds 5
```

> STT is optional. SHONA remains fully functional without it.

---

## Quick Command Cheat Sheet

| Goal                | Command                                            |
| ------------------- | -------------------------------------------------- |
| New snapshot        | `shona scan`                                       |
| Diff latest two     | `shona diff`                                       |
| Diff vs baseline    | `shona diff --baseline`                            |
| Process list        | `shona ps --limit 40`                              |
| Listening ports     | `shona ports`                                      |
| Startup persistence | `shona startup list`                               |
| Scheduled tasks     | `shona tasks list --limit 50`                      |
| Services            | `shona services list --limit 50`                   |
| Suspicious services | `shona services suspicious`                        |
| Accept baseline     | `shona baseline accept <snapshot.json>`            |
| Ignore item         | `shona ignore add processes OneDrive.exe`          |
| Owner token         | `shona owner verify --pin 1234`                    |
| Disable startup     | `shona startup disable "OneDrive" --token <TOKEN>` |
| Audit log           | `shona audit show --tail 50`                       |
| Enable voice        | `shona config set voice_enabled true`              |
| Speak text          | `shona voice say "..."`                            |

---

## Data & Privacy

SHONA is designed as **local-first**:

* All snapshots, state, settings, and audit logs are stored under:

  * `.shona/`
* No telemetry by default
* No cloud dependencies required
* Voice is **opt-in**
* No always-on microphone behavior
* No audio recording storage

---

## Project Structure (high level)

```
shona_core/
  cli.py
  scan.py
  diff.py
  risk.py
  retention.py
  owner.py
  audit.py
  settings.py
  voice.py
  modules/
    processes.py
    ports.py
    startup_win.py
    tasks_win.py
    services_win.py
    actions_win.py
  web/
    app.py
    templates/
    static/
```

---

## Roadmap

### v0.3.1 (polish)

* Web UI voice toggle switch
* Better formatting for persistence results (tables + filters)
* “Explain this change” helper summaries

### v0.4.0 (security depth)

* Startup + tasks risk heuristics improved
* Signed binary packaging (Windows)
* Optional rule packs (local)

### v1.0.0 (product)

* Installer + auto updates
* Full tray-first workflow
* Plug-in system for detection modules

---

## License

Choose a license that matches your goals (MIT / Apache-2.0 recommended for open source).

---

## Disclaimer

SHONA provides **defensive visibility and safe actions**, not guarantees.
Always verify critical changes before disabling system components.

---

**Built with:** Python + FastAPI + Uvicorn + local storage + optional offline voice
**Philosophy:** Calm, local, explainable, owner-verified.


