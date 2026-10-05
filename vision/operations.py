"""Display registry shared by GUI and reproducible synthetic gallery."""

from functools import partial

import cv2
import numpy as np

from vision import (
    color,
    edges,
    enhancement,
    filtering,
    morphology,
    segmentation,
    transforms,
)

OPERATIONS = {
    "original": lambda image: image.copy(),
    "brightness contrast": enhancement.adjust,
    "mean": filtering.smooth,
    "median": filtering.median,
    "gaussian": filtering.gaussian,
    "sharpen": filtering.sharpen,
    "equalize": enhancement.equalize,
    "FFT spectrum": transforms.spectrum,
    "FFT lowpass": transforms.lowpass,
    "DCT": transforms.dct,
    "Haar": transforms.haar,
    "HSV": color.convert,
    "green mask": color.mask_hsv,
}
OPERATIONS.update(
    {
        method: partial(edges.detect, method=method)
        for method in ("sobel", "prewitt", "canny", "laplacian")
    }
)
OPERATIONS.update(
    {
        method: partial(morphology.apply, operation=method)
        for method in ("erosion", "dilation", "opening", "closing")
    }
)
OPERATIONS.update(
    {
        method: partial(segmentation.segment, method=method)
        for method in ("global", "otsu", "adaptive")
    }
)


def display_image(image):
    if image.dtype == np.uint8:
        return image
    return cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def synthetic_image(size=256):
    image = np.zeros((size, size, 3), np.uint8)
    image[:] = np.arange(size, dtype=np.uint8)[None, :, None]
    cv2.rectangle(image, (size // 8, size // 8), (size // 2, size // 2), (0, 220, 0), -1)
    cv2.circle(image, (size * 3 // 4, size * 3 // 4), size // 8, (240, 80, 30), -1)
    return image


def histogram_plot(image):
    counts = enhancement.histogram(image)
    canvas = np.zeros((256, 256, 3), np.uint8)
    heights = (counts / max(1, counts.max()) * 230).astype(int)
    for x, height in enumerate(heights):
        cv2.line(canvas, (x, 255), (x, 255 - int(height)), (190, 220, 70), 1)
    return cv2.resize(canvas, (image.shape[1], image.shape[0]))


OPERATIONS["histogram"] = histogram_plot
