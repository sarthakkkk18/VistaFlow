"""Sensor orchestration independent of Qt; latest frame prevents queue buildup."""

from collections import deque
from dataclasses import dataclass
from queue import Empty, Full, Queue
from threading import Event, Thread
from time import perf_counter

import cv2

from gesture.features import extract
from gesture.gesture_recognition import GestureRecognizer
from gesture.hand_tracking import HandTracker, overlay
from vision.camera import Camera
from vision.live_filters import FilterSettings, apply_filter
from vision.motion import phase_translation


@dataclass(frozen=True)
class FrameResult:
    image: object
    events: list
    fps: float
    processing_ms: float
    original: object = None
    settings: object = None

    def __iter__(self):
        return iter((self.image, self.events, self.fps, self.processing_ms))


class VisionRuntime:
    def __init__(self, config, camera_factory=Camera):
        self.config = config
        self.camera_factory = camera_factory
        self.frames = Queue(maxsize=1)
        self.commands = Queue(maxsize=64)
        self.messages = Queue(maxsize=32)
        self.stop_event = Event()
        self.thread = None
        self.settings = FilterSettings()
        self.tracking = False
        self.debug = False
        self.diagnostics = {}
        self.metrics = {}
        self.observation = {}
        self.original = None
        self.compare = False

    def message(self, text):
        try:
            self.messages.put_nowait(text)
        except Full:
            pass

    def start(self, tracking=False):
        if self.thread and self.thread.is_alive():
            return
        self.diagnostics = {}
        self.metrics = {}
        self.observation = {}
        self.tracking = tracking
        self.stop_event.clear()
        for queue in (self.frames, self.commands, self.messages):
            while True:
                try:
                    queue.get_nowait()
                except Empty:
                    break
        self.thread = Thread(target=self.run, daemon=True, name="vistaflow-vision")
        self.thread.start()

    def run(self):
        tracker = None
        previous = None
        completed = deque(maxlen=60)
        recognizer = GestureRecognizer(settings=self.config.gesture)
        try:
            with self.camera_factory(self.config) as camera:
                self.message("CAMERA ACTIVE")
                while not self.stop_event.is_set():
                    if self.tracking and tracker is None:
                        try:
                            tracker = HandTracker(
                                self.config.hand_model,
                                self.config.gesture.smoothing_alpha,
                                self.config.gesture.smoothing_window,
                            ).open()
                        except Exception as error:
                            self.tracking = False
                            self.message(f"Tracking unavailable ({type(error).__name__})")
                    elif not self.tracking and tracker is not None:
                        tracker.close()
                        tracker = None
                        recognizer.reset()
                        self.diagnostics = {}
                        self.observation = {}
                        from gesture.gesture_recognition import GestureEvent

                        try:
                            self.commands.put_nowait(
                                GestureEvent("TRACKING_LOST", 0, perf_counter())
                            )
                        except Full:
                            self.message("Gesture queue full; release pending")
                    started = perf_counter()
                    frame = camera.read()
                    processing_started = perf_counter()
                    events = []
                    hands = []
                    self.original = frame.image if self.compare else None
                    image = frame.image
                    settings = self.settings
                    if tracker:
                        try:
                            hands = tracker.detect(frame)
                            if hands:
                                features = extract(hands[0])
                                self.observation = {
                                    "timestamp": frame.timestamp,
                                    "pinch": features.pinch,
                                    "extension": features.extension.tolist(),
                                    "quality": features.quality,
                                    "handedness": hands[0].handedness,
                                }
                            else:
                                self.observation = {}
                            events = recognizer.update(hands, frame.timestamp)
                            self.diagnostics = dict(recognizer.diagnostics)
                        except Exception as error:
                            self.message(f"Tracking stopped ({type(error).__name__})")
                            tracker.close()
                            tracker = None
                            self.tracking = False
                            self.observation = {}
                            events = recognizer.update([], frame.timestamp)
                    if tracker is None:
                        events = recognizer.update([], frame.timestamp)
                        self.diagnostics = dict(recognizer.diagnostics)
                    try:
                        if settings.operation == "motion":
                            image = apply_filter(frame.image, settings)
                            if previous is not None:
                                (dx, dy), confidence = phase_translation(previous, frame.image)
                                cv2.putText(
                                    image,
                                    f"dx {dx:.1f} dy {dy:.1f} response {confidence:.2f}",
                                    (12, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6,
                                    (0, 255, 0),
                                    2,
                                )
                            previous = frame.image.copy()
                        else:
                            image = apply_filter(image, settings)
                            previous = None
                    except Exception as error:
                        self.message(f"Processing unavailable ({type(error).__name__})")
                    if hands and self.debug:
                        if image.ndim == 2:
                            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                        image = overlay(image, hands)
                    if self.debug and self.diagnostics:
                        cv2.putText(
                            image,
                            f"{self.diagnostics['candidate']} {self.diagnostics['confidence']:.2f} | {self.diagnostics['state']}",
                            (12, 55),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (90, 210, 180),
                            1,
                        )
                    completed.append(perf_counter())
                    self.metrics = {
                        "capture_fps": frame.fps,
                        "processing_ms": (perf_counter() - processing_started) * 1000,
                        "processed_fps": (len(completed) - 1) / (completed[-1] - completed[0])
                        if len(completed) > 1
                        else 0.0,
                    }
                    for event in events:
                        try:
                            self.commands.put_nowait(event)
                        except Full:
                            self.message("Gesture queue full; command ignored")
                    packet = FrameResult(
                        image,
                        [],
                        frame.fps,
                        self.metrics["processing_ms"],
                        frame.image if self.compare else None,
                        settings,
                    )
                    try:
                        self.frames.get_nowait()
                    except Empty:
                        pass
                    self.frames.put_nowait(packet)
                    self.stop_event.wait(max(0, 1 / self.config.fps - (perf_counter() - started)))
        except Exception as error:
            self.message(f"Camera unavailable ({type(error).__name__})")
        finally:
            if tracker:
                tracker.close()
            self.observation = {}
            self.diagnostics = {}
            self.message("CAMERA INACTIVE")

    def stop(self):
        self.stop_event.set()

    def close(self, timeout=2):
        self.stop()
        if self.thread:
            self.thread.join(timeout)
        return not self.thread or not self.thread.is_alive()
