"""Synthetic rule/property/integration tests; no human accuracy claims."""

import ast
from dataclasses import replace
from pathlib import Path
from time import perf_counter, sleep

import numpy as np
import pytest

from core.config import Config
from core.control import FilterController, gesture_command
from core.models import Command
from core.runtime import VisionRuntime
from gesture.features import classify, extract
from gesture.gesture_recognition import GestureEvent, GestureRecognizer
from gesture.hand_tracking import Landmarks
from gesture.swipe import SwipeDetector
from vision.camera import Frame
from vision.live_filters import FILTERS, FilterSettings, apply_filter
from vision.operations import synthetic_image

PATTERNS = {
    "OPEN_PALM": (1, 1, 1, 1),
    "FIST": (0, 0, 0, 0),
    "INDEX_POINTER": (1, 0, 0, 0),
    "V_SIGN": (1, 1, 0, 0),
    "THREE_FINGERS": (1, 1, 1, 0),
    "ROCK_SIGN": (1, 0, 0, 1),
    "PINKY_POINTER": (0, 0, 0, 1),
    "PINCH": (0, 0, 0, 0),
}


def hand(name):
    p = np.zeros((21, 3))
    p[0, :2] = (0.5, 0.9)
    p[9, :2] = (0.5, 0.6)
    p[4, :2] = (0.1, 0.7)
    for extended, (tip, pip, x) in zip(
        PATTERNS[name], ((8, 6, 0.3), (12, 10, 0.45), (16, 14, 0.6), (20, 18, 0.75)), strict=True
    ):
        p[pip, :2] = (x, 0.5)
        p[tip, :2] = (x, 0.2 if extended else 0.8)
    if name == "PINCH":
        p[4] = p[8]
    return Landmarks("Left:0", p, "Left", 0.95)


@pytest.mark.parametrize("name", PATTERNS)
@pytest.mark.parametrize("mirror", [False, True])
def test_eight_pose_geometry_scale_translation_and_handedness(name, mirror):
    h = hand(name)
    p = h.points * 0.45 + [0.2, 0.1, 0]
    if mirror:
        p[:, 0] = 1 - p[:, 0]
    h = Landmarks("Right:0" if mirror else h.hand_id, p, "Right" if mirror else "Left", 0.95)
    assert classify(extract(h), Config().gesture)[0] == name


@pytest.mark.parametrize("name", PATTERNS)
def test_temporal_confirmation_held_pose_release_and_rearm(name):
    r = GestureRecognizer()
    h = hand(name)
    assert not r.update([h], 0)
    assert not r.update([h], 0.06)
    assert [e.name for e in r.update([h], 0.12)] == [name]
    assert name not in [e.name for e in r.update([h], 1)]
    assert [e.name for e in r.update([], 1.3)] == ["TRACKING_LOST"]
    events = []
    for t in (1.4, 1.46, 1.52):
        events += r.update([h], t)
    assert [e.name for e in events] == [name]


@pytest.mark.parametrize(
    "x,y,name",
    [
        (0.6, 0.3, "swipe_right"),
        (0, 0.3, "swipe_left"),
        (0.3, 0, "swipe_up"),
        (0.3, 0.6, "swipe_down"),
    ],
)
def test_four_direction_swipes(x, y, name):
    detector = SwipeDetector(vertical=True)
    assert detector.update(0.3, 0.3, 0) is None
    assert detector.update(x, y, 0.2) == name


def test_pinch_hysteresis_and_quality():
    f = extract(hand("PINCH"))
    config = Config().gesture
    assert classify(replace(f, pinch=0.36), config, False)[0] != "PINCH"
    assert classify(replace(f, pinch=0.36), config, True)[0] == "PINCH"
    assert classify(replace(f, quality=0.2), config)[0] == "UNKNOWN"


@pytest.mark.parametrize("name", FILTERS)
def test_filters_are_finite_detached_and_preserve_source(name):
    source = synthetic_image(64)
    copy = source.copy()
    result = apply_filter(source, FilterSettings(operation=name))
    assert result.dtype == np.uint8 and result.shape[:2] == source.shape[:2]
    assert np.isfinite(result).all() and np.array_equal(source, copy)
    assert not np.shares_memory(result, source)


def test_parameter_effect_and_clipping():
    source = np.full((16, 16, 3), 10, np.uint8)
    assert np.all(apply_filter(source, FilterSettings(brightness=-30)) == 0)
    assert np.all(apply_filter(source, FilterSettings(contrast=2, brightness=5)) == 25)
    source = np.random.default_rng(1).integers(0, 256, (64, 64, 3), dtype=np.uint8)
    assert not np.array_equal(
        apply_filter(source, FilterSettings(operation="gaussian", kernel=3)),
        apply_filter(source, FilterSettings(operation="gaussian", kernel=15)),
    )


@pytest.mark.parametrize(
    "params",
    [
        {"kernel": 4},
        {"canny_low": 200},
        {"contrast": float("nan")},
        {"strength": 9},
        {"operation": "invalid"},
    ],
)
def test_invalid_settings_do_not_replace_valid_state(params):
    controller = FilterController()
    original = controller.settings
    with pytest.raises((TypeError, ValueError)):
        controller.dispatch(Command("PARAMETERS", parameters=params))
    assert controller.settings is original


def test_recognizer_to_filter_controller_and_discrete_freeze():
    r = GestureRecognizer()
    c = FilterController()
    for i in range(12):
        for event in r.update([hand("V_SIGN")], i * 0.06):
            command = gesture_command(event)
            if command:
                c.dispatch(command)
    assert c.settings.operation == "canny"
    r.update([], 1)
    for i in range(12):
        for event in r.update([hand("FIST")], 1.2 + i * 0.06):
            command = gesture_command(event)
            if command:
                c.dispatch(command)
    assert c.frozen
    c.dispatch(gesture_command(GestureEvent("SWIPE_UP", 0.95, 3)))
    assert c.settings.brightness == 10
    assert gesture_command(GestureEvent("TRACKING_LOST", 0, 4)) is None


class FakeCamera:
    closed = False

    def __init__(self, config):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def read(self):
        sleep(0.01)
        return Frame(synthetic_image(64), perf_counter(), 30)


def test_runtime_hot_filter_snapshot_and_optional_model_failure():
    camera = FakeCamera(None)
    runtime = VisionRuntime(Config(hand_model="missing.task"), lambda c: camera)
    runtime.settings = FilterSettings(operation="canny", canny_low=40, canny_high=120)
    runtime.compare = True
    runtime.start(tracking=True)
    try:
        packet = runtime.frames.get(timeout=5)
        assert np.array_equal(packet.image, apply_filter(packet.original, packet.settings))
        assert not runtime.tracking and runtime.thread.is_alive()
        runtime.settings = FilterSettings(operation="CLAHE", strength=3)
        for _ in range(10):
            packet = runtime.frames.get(timeout=2)
            if packet.settings.operation == "CLAHE":
                break
        assert packet.settings.operation == "CLAHE"
        assert np.array_equal(packet.image, apply_filter(packet.original, packet.settings))
    finally:
        assert runtime.close(timeout=3)
    assert camera.closed


def test_no_removed_feature_dependencies_or_cross_project_imports():
    root = Path(__file__).resolve().parents[1]
    for module in ("voice", "games"):
        assert not (root / module).exists()
    for path in [
        *(root / "core").glob("*.py"),
        *(root / "gesture").glob("*.py"),
        *(root / "ui").glob("*.py"),
        *(root / "vision").glob("*.py"),
    ]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [n.name for n in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            assert not any(
                n.split(".")[0] in ("voice", "games", "sounddevice", "faster_whisper")
                for n in names
            )
            if path.parent.name == "gesture":
                assert not any(n.split(".")[0] == "ui" for n in names)
    import core.config

    assert Path(core.config.__file__).resolve().is_relative_to(root)


def test_loaded_project_modules_are_all_local():
    import sys

    root = Path(__file__).resolve().parents[1]
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in ("core", "vision", "gesture", "ui", "experiments") and getattr(
            module, "__file__", None
        ):
            assert Path(module.__file__).resolve().is_relative_to(root), (name, module.__file__)
