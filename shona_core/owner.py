from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

STATE_DIR = Path(".shona/state")
OWNER_FILE = STATE_DIR / "owner.json"
TOKEN_FILE = STATE_DIR / "owner_token.json"


def _ensure() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _hash_pin(pin: str, salt: bytes) -> str:
    # PBKDF2 for local PIN hashing (not perfect, but solid enough for local-only)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 120_000)
    return base64.b64encode(dk).decode("ascii")


def owner_init(pin: str) -> dict:
    _ensure()
    if len(pin) < 4 or len(pin) > 32:
        return {"ok": False, "message": "PIN must be 4–32 characters."}

    salt = os.urandom(16)
    data = {
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "pin_hash": _hash_pin(pin, salt),
        "created_utc": int(time.time()),
    }
    OWNER_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"ok": True, "message": "Owner PIN set.", "owner_file": str(OWNER_FILE)}


def owner_verify(pin: str, ttl_seconds: int = 300) -> dict:
    _ensure()
    if not OWNER_FILE.exists():
        return {"ok": False, "message": "Owner not initialized. Run: shona owner init"}

    data = json.loads(OWNER_FILE.read_text(encoding="utf-8"))
    salt = base64.b64decode(data["salt_b64"])
    expected = data["pin_hash"]
    got = _hash_pin(pin, salt)

    if not hmac.compare_digest(expected, got):
        return {"ok": False, "message": "Invalid PIN."}

    token = secrets.token_urlsafe(24)
    exp = int(time.time()) + int(ttl_seconds)
    TOKEN_FILE.write_text(json.dumps({"token": token, "exp": exp}, indent=2), encoding="utf-8")
    return {"ok": True, "token": token, "expires_in": ttl_seconds}


def require_token(token: str) -> dict:
    _ensure()
    if not TOKEN_FILE.exists():
        return {"ok": False, "message": "No active token. Run: shona owner verify"}

    data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    exp = int(data.get("exp", 0))
    stored = str(data.get("token", ""))

    if int(time.time()) > exp:
        TOKEN_FILE.unlink(missing_ok=True)
        return {"ok": False, "message": "Token expired. Run: shona owner verify"}

    if not hmac.compare_digest(stored, token):
        return {"ok": False, "message": "Invalid token."}

    return {"ok": True}
