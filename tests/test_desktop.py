import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.config import Config
from core.runtime import VisionRuntime
from ui.main_window import MainWindow


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.show()
    app.processEvents()
    yield w
    w.close()
    for _ in range(100):
        app.processEvents()
        if not w.isVisible():
            break
        QTest.qWait(10)


def settle(w):
    for _ in range(200):
        w.poll()
        QApplication.processEvents()
        if not w.requested and w.future is None:
            return
        QTest.qWait(10)
    pytest.fail("Sample job failed to finish")


def test_filter_controls_compare_freeze_and_reset(window):
    w = window
    settle(w)
    assert not w.processed.pixmap().isNull()
    w.operation.setCurrentIndex(w.operation.findData("CLAHE"))
    settle(w)
    assert w.runtime.settings.operation == "CLAHE" and "Clahe" in w.caption.text()
    w.controls["brightness"].setValue(25)
    settle(w)
    assert w.controller.settings.brightness == 25
    w.compare.click()
    assert not w.original_box.isVisible()
    w.freeze.click()
    assert w.controller.frozen
    w.dispatch("RESET")
    settle(w)
    assert w.controller.settings.operation == "original" and not w.controller.frozen
    assert not hasattr(w, "voice") and not hasattr(w, "canvas") and not hasattr(w, "media")


def test_camera_failure_keeps_filters_usable(window):
    class MissingCamera:
        def __init__(self, config):
            raise RuntimeError("fixture failure")

    w = window
    w.runtime = VisionRuntime(Config(), MissingCamera)
    w.toggle_camera()
    for _ in range(100):
        w.poll()
        QApplication.processEvents()
        QTest.qWait(10)
        if not w.runtime.thread.is_alive():
            break
    w.poll()
    assert "unavailable" in w.feedback.text().lower()
    w.dispatch("SET_FILTER", {"operation": "canny"})
    settle(w)
    assert "Canny" in w.caption.text()


def test_preview_sizes(window):
    w = window
    w.dispatch("SET_FILTER", {"operation": "canny"})
    settle(w)
    folder = Path("docs/evidence")
    folder.mkdir(parents=True, exist_ok=True)
    for width, height in ((1380, 860), (1080, 720)):
        w.resize(width, height)
        QApplication.processEvents()
        assert w.grab().save(str(folder / f"preview_{width}.png"))


def test_open_image_worker_and_invalid_file(window, tmp_path, monkeypatch):
    import cv2
    import numpy as np
    from PySide6.QtWidgets import QFileDialog

    w = window
    path = tmp_path / "sample.png"
    source = np.full((48, 64, 3), (10, 20, 30), np.uint8)
    assert cv2.imwrite(str(path), source)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), ""))
    w.open_image()
    for _ in range(100):
        w.poll()
        QApplication.processEvents()
        QTest.qWait(10)
        if w.load_future is None:
            break
    settle(w)
    assert np.array_equal(w.sample, source) and "Loaded image" in w.caption.text()
    path.write_bytes(b"invalid image")
    w.open_image()
    for _ in range(100):
        w.poll()
        QApplication.processEvents()
        QTest.qWait(10)
        if w.load_future is None:
            break
    assert "Could not open" in w.feedback.text()
    assert np.array_equal(w.sample, source)
