"""Image inputs use OpenCV BGR uint8 conventions unless documented otherwise."""

import cv2
import numpy as np


def gray(image):
    if image.ndim == 2:
        return image.copy()
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def resize(image, width, height):
    if width <= 0 or height <= 0:
        raise ValueError("Positive dimensions required")
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def normalize(image):
    return image.astype(np.float32) / 255.0
