from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from shona_core.cli import cmd_web_start, cmd_web_open, cmd_web_stop, _ensure_runtime, URL_FILE


def _icon_image() -> Image.Image:
    # Simple “girly vibe” icon: neon heart-ish dot
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 54, 54), fill=(255, 107, 214, 255))
    d.ellipse((20, 20, 44, 44), fill=(155, 107, 255, 255))
    d.ellipse((28, 28, 36, 36), fill=(98, 255, 182, 255))
    return img


def run_tray() -> None:
    _ensure_runtime()

    def open_ui(_icon, _item):
        # ensure started
        cmd_web_start("127.0.0.1", 7860)
        cmd_web_open()
        if URL_FILE.exists():
            webbrowser.open(URL_FILE.read_text(encoding="utf-8").strip())

    def start(_icon, _item):
        cmd_web_start("127.0.0.1", 7860)

    def stop(_icon, _item):
        cmd_web_stop()

    def quit_app(icon, _item):
        try:
            cmd_web_stop()
        finally:
            icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Open SHONA", open_ui),
        pystray.MenuItem("Start Web", start),
        pystray.MenuItem("Stop Web", stop),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )

    icon = pystray.Icon("SHONA", _icon_image(), "SHONA", menu)
    icon.run()
