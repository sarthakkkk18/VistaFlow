"""Temporal confirmation, release hysteresis and normalized gesture events."""

from collections import deque
from dataclasses import dataclass, field, replace

from core.config import GestureConfig
from gesture.features import classify, extract
from gesture.swipe import SwipeDetector


@dataclass(frozen=True)
class GestureEvent:
    name: str
    confidence: float
    timestamp: float
    payload: dict = field(default_factory=dict)


def pose(hand, pinch_threshold=0.3):
    name, _ = classify(
        extract(hand),
        GestureConfig(
            pinch_threshold=pinch_threshold,
            pinch_release_threshold=max(0.43, pinch_threshold + 0.1),
        ),
    )
    return {"INDEX_POINTER": "point"}.get(name, name.lower())


class GestureRecognizer:
    def __init__(self, cooldown=None, pinch_threshold=None, stable_frames=None, settings=None):
        self.settings = settings or GestureConfig()
        overrides = {}
        if cooldown is not None:
            overrides["cooldown_ms"] = max(1, cooldown * 1000)
        if pinch_threshold is not None:
            overrides["pinch_threshold"] = pinch_threshold
        if stable_frames is not None:
            overrides["hold_frames"] = stable_frames
        self.settings = replace(self.settings, **overrides)
        s = self.settings
        self.swipe = SwipeDetector(
            s.swipe_distance_threshold,
            s.swipe_window_ms / 1000,
            s.swipe_velocity_threshold,
            vertical=True,
        )
        self.reset()

    def reset(self):
        self.candidate = "UNKNOWN"
        self.active = "UNKNOWN"
        self.count = 0
        self.since = None
        self.release_count = 0
        self.release_since = None
        self.last_seen = None
        self.last_time = None
        self.last_emit = -float("inf")
        self.hand_id = None
        self.history = deque(maxlen=30)
        self.swipe.reset()
        self.diagnostics = {
            "state": "IDLE",
            "current": "UNKNOWN",
            "candidate": "UNKNOWN",
            "confidence": 0.0,
            "hold_ms": 0.0,
            "cooldown_ms": 0.0,
            "landmark_confidence": 0.0,
        }

    def update(self, hands, timestamp):
        s = self.settings
        events = []
        if self.last_time is not None and timestamp <= self.last_time:
            return []
        self.last_time = timestamp
        valid = [h for h in hands if h.confidence >= s.minimum_confidence]
        hand = next((h for h in valid if h.hand_id == self.hand_id), None)
        if hand is None and self.hand_id is not None:
            if (
                self.last_seen is not None
                and (timestamp - self.last_seen) * 1000 < s.tracking_loss_ms
            ):
                self.diagnostics["state"] = "OCCLUDED"
                return []
            self.reset()
            self.last_time = timestamp
            events.append(GestureEvent("TRACKING_LOST", 0, timestamp))
        if not valid:
            return events
        hand = hand or sorted(valid, key=lambda h: h.hand_id)[0]
        self.hand_id = hand.hand_id
        self.last_seen = timestamp
        name, confidence = classify(extract(hand), s, self.active == "PINCH")
        self.history.append((timestamp, name, confidence))
        if name != self.candidate:
            self.candidate = name
            self.count = 1
            self.since = timestamp
        else:
            self.count += 1
        hold = (timestamp - self.since) * 1000
        if self.active != "UNKNOWN" and name != self.active:
            if self.release_since is None:
                self.release_since = timestamp
            self.release_count += 1
            if (
                self.release_count >= s.release_frames
                and (timestamp - self.release_since) * 1000 + 1e-6 >= s.release_ms
            ):
                events.append(GestureEvent("RELEASE", confidence, timestamp, {"pose": self.active}))
                self.active = "UNKNOWN"
        else:
            self.release_count = 0
            self.release_since = None
        stable = (
            self.count >= s.hold_frames
            and hold + 1e-6 >= s.hold_ms
            and confidence >= s.minimum_confidence
        )
        if (
            stable
            and name != "UNKNOWN"
            and self.active == "UNKNOWN"
            and (timestamp - self.last_emit) * 1000 >= s.cooldown_ms
        ):
            self.active = name
            self.last_emit = timestamp
            events.append(
                GestureEvent(
                    name,
                    confidence,
                    timestamp,
                    {"point": hand.points[8, :2].tolist(), "phase": "CONFIRMED", "hold_ms": hold},
                )
            )
        if self.active == name and stable and name == "OPEN_PALM":
            swipe = self.swipe.update(*hand.points[0, :2], timestamp)
            if swipe and (timestamp - self.last_emit) * 1000 >= s.cooldown_ms:
                events.append(GestureEvent(swipe.upper(), confidence, timestamp))
                self.last_emit = timestamp
        else:
            self.swipe.reset()
        self.diagnostics = {
            "current": self.active,
            "candidate": name,
            "confidence": confidence,
            "hold_ms": hold,
            "cooldown_ms": max(0, s.cooldown_ms - (timestamp - self.last_emit) * 1000),
            "landmark_confidence": hand.confidence,
            "handedness": hand.handedness,
            "state": "CONFIRMED" if self.active == name and stable else "CANDIDATE",
        }
        return events
