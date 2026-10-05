"""MediaPipe Tasks adapter; imports and model loading occur only on activation."""

from collections import deque
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class Landmarks:
    hand_id: str
    points: np.ndarray
    handedness: str
    confidence: float
    aspect: float = 1.0

    def __post_init__(self):
        if (
            not np.isfinite([self.confidence, self.aspect]).all()
            or not 0 <= self.confidence <= 1
            or self.aspect <= 0
        ):
            raise ValueError("Invalid landmark quality or aspect")
        if self.points.shape != (21, 3) or not np.isfinite(self.points).all():
            raise ValueError("Expected 21 finite XYZ landmarks")


class Smoother:
    def __init__(self, alpha=0.45, window=1):
        if not 0 < alpha <= 1:
            raise ValueError("Alpha must be in (0,1]")
        if type(window) is not int or window < 1:
            raise ValueError("Positive window required")
        self.window = window
        self.samples = {}
        self.alpha = alpha
        self.previous = {}

    def update(self, hands):
        result = []
        present = set()
        for hand in hands:
            present.add(hand.hand_id)
            old = self.previous.get(hand.hand_id, hand.points)
            history = self.samples.setdefault(hand.hand_id, deque(maxlen=self.window))
            history.append(hand.points)
            filtered = np.median(np.stack(history), axis=0)
            points = self.alpha * filtered + (1 - self.alpha) * old
            self.previous[hand.hand_id] = points
            result.append(
                Landmarks(hand.hand_id, points, hand.handedness, hand.confidence, hand.aspect)
            )
        self.previous = {key: value for key, value in self.previous.items() if key in present}
        self.samples = {key: value for key, value in self.samples.items() if key in present}
        return result


class HandTracker:
    def __init__(self, model_path, alpha=0.45, window=3):
        self.model_path = Path(model_path)
        self.detector = None
        self.smoother = Smoother(alpha, window)
        self.last_ms = -1

    def open(self):
        if not self.model_path.is_file():
            raise FileNotFoundError("Configure a local MediaPipe hand model")
        import mediapipe as mp

        self.mp = mp
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
        )
        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
        return self

    def detect(self, frame):
        if self.detector is None:
            raise RuntimeError("Tracking inactive")
        image = self.mp.Image(
            image_format=self.mp.ImageFormat.SRGB,
            data=cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB),
        )
        timestamp = max(self.last_ms + 1, int(frame.timestamp * 1000))
        self.last_ms = timestamp
        result = self.detector.detect_for_video(image, timestamp)
        hands = []
        counts = {}
        for points, categories in zip(result.hand_landmarks, result.handedness, strict=True):
            category = categories[0]
            label = category.category_name
            index = counts.get(label, 0)
            counts[label] = index + 1
            hands.append(
                Landmarks(
                    f"{label}:{index}",
                    np.array([[p.x, p.y, p.z] for p in points]),
                    label,
                    category.score,
                    frame.width / frame.height,
                )
            )
        return self.smoother.update(hands)

    def close(self):
        if self.detector is not None:
            self.detector.close()
        self.detector = None
        self.smoother.previous.clear()
        self.smoother.samples.clear()
        self.last_ms = -1


def overlay(image, hands):
    result = image.copy()
    h, w = result.shape[:2]
    for hand in hands:
        for x, y, _z in hand.points:
            cv2.circle(result, (int(x * w), int(y * h)), 3, (0, 255, 255), -1)
        x, y, _ = hand.points[0]
        cv2.putText(
            result,
            f"{hand.handedness} {hand.confidence:.2f}",
            (int(x * w), int(y * h)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
        )
    return result
