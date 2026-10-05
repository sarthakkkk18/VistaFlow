"""OpenCV BGR conversions and HSV colour-range segmentation."""

import cv2
import numpy as np


def convert(image, space="hsv"):
    codes = {
        "hsv": cv2.COLOR_BGR2HSV,
        "gray": cv2.COLOR_BGR2GRAY,
        "lab": cv2.COLOR_BGR2LAB,
        "rgb": cv2.COLOR_BGR2RGB,
    }
    return cv2.cvtColor(image, codes[space])


def mask_hsv(image, lower=(35, 50, 50), upper=(85, 255, 255)):
    return cv2.inRange(convert(image), np.array(lower, np.uint8), np.array(upper, np.uint8))
