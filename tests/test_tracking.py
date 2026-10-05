import numpy as np
import pytest

from gesture.hand_tracking import HandTracker, Landmarks, Smoother


def test_smoothing_and_loss():
    smooth = Smoother(0.5)

    def make(value):
        return Landmarks("left", np.full((21, 3), value, dtype=float), "Left", 0.9)

    smooth.update([make(0)])
    assert np.all(smooth.update([make(1)])[0].points == 0.5)
    smooth.update([])
    assert np.all(smooth.update([make(1)])[0].points == 1)


def test_invalid_and_missing(tmp_path):
    with pytest.raises(ValueError):
        Landmarks("x", np.zeros((2, 3)), "Left", 1)
    with pytest.raises(FileNotFoundError):
        HandTracker(tmp_path / "absent.task").open()
    HandTracker(tmp_path / "absent.task").close()


def test_actual_model_when_available():
    from pathlib import Path
    from time import perf_counter

    from vision.camera import Frame

    path = Path("data/hand_landmarker.task")
    if not path.exists():
        pytest.skip("Local model not downloaded")
    pytest.importorskip("mediapipe")
    tracker = HandTracker(path).open()
    try:
        assert tracker.detect(Frame(np.zeros((64, 64, 3), np.uint8), perf_counter(), 0)) == []
    finally:
        tracker.close()
