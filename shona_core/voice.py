from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from shona_core.settings import load_settings


@dataclass
class VoiceStatus:
    tts_ok: bool
    stt_ok: bool
    message: str


def voice_status() -> VoiceStatus:
    # TTS check
    try:
        import pyttsx3  # noqa: F401
        tts_ok = True
    except Exception:
        tts_ok = False

    # STT check (optional)
    stt_ok = False
    msg = []
    if tts_ok:
        msg.append("TTS: ok")
    else:
        msg.append("TTS: missing (install pyttsx3)")

    try:
        import vosk  # noqa: F401
        import sounddevice  # noqa: F401
        stt_ok = True
        msg.append("STT: ok (vosk+sounddevice)")
    except Exception:
        msg.append("STT: optional (install vosk + sounddevice for offline voice input)")

    return VoiceStatus(tts_ok=tts_ok, stt_ok=stt_ok, message=" | ".join(msg))


def speak(text: str) -> dict:
    """
    Offline TTS. Does NOT store audio.
    Voice depends on OS voices available.
    """
    cfg = load_settings()
    if not cfg.get("voice_enabled", False):
        return {"ok": False, "message": "Voice is disabled. Enable: shona config set voice_enabled true"}

    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", int(cfg.get("voice_rate", 175)))
        engine.setProperty("volume", float(cfg.get("voice_volume", 1.0)))

        # Attempt to pick a more "feminine" voice if available (Windows voices vary)
        try:
            voices = engine.getProperty("voices")
            preferred = None
            for v in voices:
                name = (getattr(v, "name", "") or "").lower()
                if any(k in name for k in ["zira", "female", "woman", "susan", "eva", "hazel"]):
                    preferred = v.id
                    break
            if preferred:
                engine.setProperty("voice", preferred)
        except Exception:
            pass

        engine.say(text)
        engine.runAndWait()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def listen_ptt(seconds: int = 5) -> dict:
    """
    Optional offline STT using Vosk + sounddevice.
    Requires a local Vosk model path in settings.
    Push-to-talk concept: record for fixed seconds.
    Does NOT save recordings to disk.
    """
    cfg = load_settings()
    model_path = Path(str(cfg.get("vosk_model_path", ".shona/models/vosk")))

    try:
        import json
        import queue
        import vosk
        import sounddevice as sd
    except Exception:
        return {"ok": False, "message": "Offline STT not installed. Install: pip install vosk sounddevice"}

    if not model_path.exists():
        return {
            "ok": False,
            "message": f"Vosk model not found at: {model_path}. Download a Vosk model and place it there.",
            "hint": "Example: Vosk 'small' English model (offline). Keep it local.",
        }

    q: queue.Queue[bytes] = queue.Queue()

    def callback(indata, frames, time, status):  # noqa: ANN001
        if status:
            pass
        q.put(bytes(indata))

    model = vosk.Model(str(model_path))
    rec = vosk.KaldiRecognizer(model, 16000)

    # record mono 16k
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=callback):
        # collect for N seconds
        import time as _t
        end = _t.time() + max(1, min(seconds, 20))
        while _t.time() < end:
            data = q.get()
            rec.AcceptWaveform(data)

    result = rec.FinalResult()
    try:
        obj = json.loads(result)
        text = (obj.get("text") or "").strip()
    except Exception:
        text = ""
    return {"ok": True, "text": text}
