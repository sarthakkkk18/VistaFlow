"""Custom Sobel/Prewitt gradients compared with OpenCV Canny/Laplacian."""

import cv2
import numpy as np

from vision.filtering import correlate
from vision.preprocessing import gray


def gradients(image, method="sobel"):
    if method not in ("sobel", "prewitt"):
        raise ValueError("Unknown gradient")
    kernel = (
        np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        if method == "sobel"
        else np.array([[-1, 0, 1]] * 3)
    )
    image = gray(image)
    return correlate(image, kernel), correlate(image, kernel.T)


def detect(image, method="sobel", low=60, high=150):
    image = gray(image)
    if method == "canny":
        return cv2.Canny(image, low, high)
    if method == "laplacian":
        return cv2.convertScaleAbs(cv2.Laplacian(image, cv2.CV_64F))
    gx, gy = gradients(image, method)
    return np.clip(np.hypot(gx, gy), 0, 255).astype(np.uint8)
