"""Load a system font when headless Qt cannot enumerate native Windows fonts."""

import os
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


def ensure_font():
    app = QApplication.instance()
    if app is None or QFontDatabase.families():
        return
    candidates = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/segoeui.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            identifier = QFontDatabase.addApplicationFont(str(path))
            families = QFontDatabase.applicationFontFamilies(identifier)
            if families:
                app.setFont(QFont(families[0], 10))
                return
