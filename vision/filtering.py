"""NumPy spatial correlation (reflect-101 boundary) and library references."""

import cv2
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def correlate(image, kernel):
    kernel = np.asarray(kernel, dtype=float)
    if kernel.ndim != 2 or any(s % 2 == 0 for s in kernel.shape):
        raise ValueError("Kernel dimensions must be odd")
    if image.ndim == 3:
        return np.stack([correlate(image[:, :, i], kernel) for i in range(image.shape[2])], axis=-1)
    padding = tuple((s // 2, s // 2) for s in kernel.shape)
    windows = sliding_window_view(
        np.pad(image.astype(float), padding, mode="reflect"), kernel.shape
    )
    return np.einsum("ijkl,kl->ij", windows, kernel)


def smooth(image, size=3):
    if size <= 0 or size % 2 == 0:
        raise ValueError("Positive odd size required")
    return np.clip(correlate(image, np.ones((size, size)) / (size * size)), 0, 255).astype(np.uint8)


def sharpen(image):
    return np.clip(correlate(image, [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]), 0, 255).astype(np.uint8)


def gaussian(image, size=5, sigma=1.0):
    return cv2.GaussianBlur(image, (size, size), sigma)


def median(image, size=5):
    """OpenCV reference median filter; odd neighborhood preserves image dimensions."""
    if type(size) is not int or size < 3 or size % 2 == 0:
        raise ValueError("Odd kernel size >=3 required")
    return cv2.medianBlur(image, size)
