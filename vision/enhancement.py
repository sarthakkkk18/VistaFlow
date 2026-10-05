"""Brightness/contrast, custom histogram and cumulative equalization."""

import numpy as np

from vision.preprocessing import gray


def adjust(image, contrast=1.2, brightness=15):
    return np.clip(image.astype(float) * contrast + brightness, 0, 255).astype(np.uint8)


def histogram(image):
    return np.bincount(gray(image).ravel(), minlength=256)


def equalize(image):
    image = gray(image)
    counts = histogram(image)
    cdf = counts.cumsum()
    low = cdf[counts > 0][0]
    if image.size == low:
        return image.copy()
    lookup = np.rint((cdf - low) * 255 / (image.size - low)).clip(0, 255).astype(np.uint8)
    return lookup[image]
