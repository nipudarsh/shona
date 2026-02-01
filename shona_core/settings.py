from __future__ import annotations

import json
from pathlib import Path

STATE_DIR = Path(".shona/state")
SETTINGS_FILE = STATE_DIR / "settings.json"


def _ensure() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    _ensure()
    if not SETTINGS_FILE.exists():
        return {
            "friend_mode": True,
            "voice_enabled": False,
            "voice_rate": 175,
            "voice_volume": 1.0,
            "vosk_model_path": ".shona/models/vosk",
        }
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "friend_mode": True,
            "voice_enabled": False,
            "voice_rate": 175,
            "voice_volume": 1.0,
            "vosk_model_path": ".shona/models/vosk",
        }


def save_settings(data: dict) -> dict:
    _ensure()
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def set_setting(key: str, value) -> dict:
    data = load_settings()
    data[key] = value
    return save_settings(data)
