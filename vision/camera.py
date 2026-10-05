"""Camera ownership, monotonic timestamps, measured acquisition FPS."""

from dataclasses import dataclass
from time import perf_counter

import cv2
import numpy as np


@dataclass(frozen=True)
class Frame:
    image: np.ndarray
    timestamp: float
    fps: float

    @property
    def width(self):
        return self.image.shape[1]

    @property
    def height(self):
        return self.image.shape[0]


class Camera:
    def __init__(self, config, factory=cv2.VideoCapture):
        self.config, self.factory = config, factory
        self.capture = None
        self.previous_time = None

    def open(self):
        self.close()
        self.capture = self.factory(self.config.camera_index)
        if not self.capture.isOpened():
            self.close()
            raise RuntimeError("Camera unavailable")
        for key, value in (
            (cv2.CAP_PROP_FRAME_WIDTH, self.config.width),
            (cv2.CAP_PROP_FRAME_HEIGHT, self.config.height),
            (cv2.CAP_PROP_FPS, self.config.fps),
        ):
            self.capture.set(key, value)
        return self

    def read(self):
        if self.capture is None:
            raise RuntimeError("Camera inactive")
        ok, pixels = self.capture.read()
        if not ok or pixels is None:
            self.close()
            raise RuntimeError("Camera frame unavailable")
        now = perf_counter()
        fps = 1 / (now - self.previous_time) if self.previous_time is not None else 0
        self.previous_time = now
        return Frame(pixels, now, fps)

    def close(self):
        if self.capture is not None:
            self.capture.release()
        self.capture = None
        self.previous_time = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *args):
        self.close()
