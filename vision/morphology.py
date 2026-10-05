"""Flat square grayscale morphology with OpenCV reference implementation."""

import cv2
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from vision.preprocessing import gray


def apply(image, operation="opening", size=3, custom=True):
    if size <= 0 or size % 2 == 0:
        raise ValueError("Positive odd size required")
    image = gray(image)
    codes = {
        "erosion": cv2.MORPH_ERODE,
        "dilation": cv2.MORPH_DILATE,
        "opening": cv2.MORPH_OPEN,
        "closing": cv2.MORPH_CLOSE,
    }
    if operation not in codes:
        raise ValueError("Unknown morphology")
    if not custom:
        return cv2.morphologyEx(
            image,
            codes[operation],
            np.ones((size, size), np.uint8),
            borderType=cv2.BORDER_REPLICATE,
        )

    def primitive(pixels, dilate):
        windows = sliding_window_view(np.pad(pixels, size // 2, mode="edge"), (size, size))
        return windows.max(axis=(-2, -1)) if dilate else windows.min(axis=(-2, -1))

    if operation == "erosion":
        return primitive(image, False)
    if operation == "dilation":
        return primitive(image, True)
    return primitive(primitive(image, operation == "closing"), operation == "opening")
