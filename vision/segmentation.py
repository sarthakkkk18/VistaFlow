"""Global, Otsu and adaptive threshold segmentation."""

import cv2

from vision.preprocessing import gray


def segment(image, method="otsu", threshold=127):
    image = gray(image)
    if method == "adaptive":
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    if method not in ("otsu", "global"):
        raise ValueError("Unknown segmentation")
    return cv2.threshold(
        image,
        threshold,
        255,
        cv2.THRESH_BINARY | (cv2.THRESH_OTSU if method == "otsu" else 0),
    )[1]
