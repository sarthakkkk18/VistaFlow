"""VistaFlow entry point; never starts camera automatically."""

import argparse

from core.config import Config


def main():
    parser = argparse.ArgumentParser(description="VistaFlow real-time image/video processing")
    parser.add_argument("--config")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    app = QApplication([])
    try:
        config = Config.load(args.config)
    except (ValueError, OSError, TypeError) as error:
        parser.error(str(error))
    window = MainWindow(config)
    window.show()
    if args.smoke:
        QTimer.singleShot(700, window.close)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
