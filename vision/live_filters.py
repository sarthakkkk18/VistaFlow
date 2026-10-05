"""Validated immutable filter snapshots; parameterized CPU reference pipeline."""

import math
from dataclasses import dataclass

import cv2
import numpy as np

from vision.operations import OPERATIONS, display_image

FILTERS = (*OPERATIONS, "grayscale", "CLAHE", "bilateral", "colour map", "motion")


@dataclass(frozen=True)
class FilterSettings:
    operation: str = "original"
    brightness: int = 0
    contrast: float = 1.0
    kernel: int = 5
    canny_low: int = 60
    canny_high: int = 150
    strength: float = 2.0

    def __post_init__(self):
        if self.operation not in FILTERS:
            raise ValueError("Unknown filter")
        for name in ("brightness", "contrast", "kernel", "canny_low", "canny_high", "strength"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Finite filter values required")
        if type(self.kernel) is not int or self.kernel not in range(3, 16, 2):
            raise ValueError("Kernel must be odd, 3 to 15")
        if not (-100 <= self.brightness <= 100 and 0.2 <= self.contrast <= 3):
            raise ValueError("Brightness/contrast out of range")
        if not 0 <= self.canny_low < self.canny_high <= 255:
            raise ValueError("Canny low must be below high")
        if not 0.1 <= self.strength <= 8:
            raise ValueError("Strength out of range")


def apply_filter(image, settings):
    """Brightness/contrast preprocessing followed by the selected algorithm.

    Always returns a detached uint8 array. Input remains available for exact comparison.
    Motion's consecutive-frame logic belongs to the runtime, not this single-frame API.
    """
    if image is None or image.dtype != np.uint8 or image.ndim not in (2, 3):
        raise ValueError("Expected a uint8 image")
    s = settings
    image = np.clip(image.astype(np.float32) * s.contrast + s.brightness, 0, 255).astype(np.uint8)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    name = s.operation
    if name in ("original", "brightness contrast", "motion"):
        return image
    if name == "grayscale":
        return gray
    if name == "mean":
        return cv2.blur(image, (s.kernel, s.kernel))
    if name == "gaussian":
        return cv2.GaussianBlur(image, (s.kernel, s.kernel), 0)
    if name == "median":
        return cv2.medianBlur(image, s.kernel)
    if name == "canny":
        return cv2.Canny(gray, s.canny_low, s.canny_high)
    if name == "sharpen":
        blur = cv2.GaussianBlur(image, (s.kernel, s.kernel), 0)
        return cv2.addWeighted(image, 1 + s.strength, blur, -s.strength, 0)
    if name == "CLAHE":
        clahe = cv2.createCLAHE(clipLimit=s.strength, tileGridSize=(8, 8))
        if image.ndim == 2:
            return clahe.apply(image)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    if name == "bilateral":
        return cv2.bilateralFilter(image, s.kernel, 20 * s.strength, 20 * s.strength)
    if name == "colour map":
        return cv2.applyColorMap(gray, cv2.COLORMAP_TURBO)
    return display_image(OPERATIONS[name](image)).copy()


def load_image(path):
    """Decode a local Unicode path on a worker; never save user imagery."""
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode this image")
    return image
