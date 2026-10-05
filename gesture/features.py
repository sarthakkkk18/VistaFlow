"""Palm-relative, orientation-independent deterministic hand features."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HandFeatures:
    normalized: np.ndarray
    pinch: float
    extension: np.ndarray
    quality: float


def extract(hand):
    p = hand.points.astype(float).copy()
    p[:, [0, 2]] *= getattr(hand, "aspect", 1.0)
    origin = p[0]
    axis = p[9] - origin
    scale = np.linalg.norm(axis)
    if scale < 1e-5:
        return HandFeatures(np.zeros_like(p), float("inf"), np.zeros(4), 0)
    vertical = axis / scale
    lateral = p[5] - p[17]
    lateral -= np.dot(lateral, vertical) * vertical
    if np.linalg.norm(lateral) < 1e-6:
        lateral = np.cross(vertical, [0, 0, 1])
    lateral /= max(np.linalg.norm(lateral), 1e-6)
    normal = np.cross(lateral, vertical)
    normalized = (p - origin) @ np.stack((lateral, vertical, normal), axis=1) / scale
    ratios = []
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        ratios.append(np.linalg.norm(normalized[tip]) / max(np.linalg.norm(normalized[pip]), 1e-6))
    return HandFeatures(
        normalized,
        float(np.linalg.norm(p[4] - p[8]) / scale),
        np.array(ratios),
        float(np.clip(hand.confidence, 0, 1)),
    )


def classify(features, settings, pinching=False):
    if features.quality < settings.minimum_confidence:
        return "UNKNOWN", 0.0
    threshold = settings.pinch_release_threshold if pinching else settings.pinch_threshold
    if features.pinch < threshold:
        score = features.quality * (0.8 + 0.2 * max(0, 1 - features.pinch / threshold))
        return "PINCH", score
    extended = features.extension > settings.extension_ratio
    margin = np.min(abs(features.extension - settings.extension_ratio))
    score = features.quality * (0.75 + 0.25 * min(1, margin / 0.25))
    if all(extended):
        return "OPEN_PALM", score
    if not any(extended):
        return "FIST", score
    patterns = {
        (True, False, False, False): "INDEX_POINTER",
        (True, True, False, False): "V_SIGN",
        (True, True, True, False): "THREE_FINGERS",
        (True, False, False, True): "ROCK_SIGN",
        (False, False, False, True): "PINKY_POINTER",
    }
    if tuple(extended) in patterns:
        return patterns[tuple(extended)], score
    return "UNKNOWN", 0.0
