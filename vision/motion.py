"""Consecutive-frame motion: exhaustive SAD block matching and phase correlation."""

from dataclasses import dataclass

import cv2
import numpy as np

from vision.preprocessing import gray


@dataclass(frozen=True)
class MotionVector:
    x: int
    y: int
    dx: int
    dy: int
    error: float


def block_match(previous, current, block_size=8, search_radius=4):
    previous, current = gray(previous), gray(current)
    if previous.shape != current.shape:
        raise ValueError("Frame sizes differ")
    if block_size <= 0 or search_radius < 0:
        raise ValueError("Invalid search parameters")
    h, w = previous.shape
    vectors = []
    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            block = previous[y : y + block_size, x : x + block_size].astype(float)
            best = None
            for dy in range(-search_radius, search_radius + 1):
                for dx in range(-search_radius, search_radius + 1):
                    yy, xx = y + dy, x + dx
                    if yy < 0 or xx < 0 or yy + block_size > h or xx + block_size > w:
                        continue
                    sad = float(
                        np.mean(np.abs(block - current[yy : yy + block_size, xx : xx + block_size]))
                    )
                    candidate = (sad, dx * dx + dy * dy, dy, dx)
                    if best is None or candidate < best:
                        best = candidate
            error, _, dy, dx = best
            vectors.append(MotionVector(x + block_size // 2, y + block_size // 2, dx, dy, error))
    return vectors


def phase_translation(previous, current):
    a, b = gray(previous).astype(np.float32), gray(current).astype(np.float32)
    if a.shape != b.shape:
        raise ValueError("Frame sizes differ")
    return cv2.phaseCorrelate(a, b)


def overlay(image, vectors):
    output = image.copy()
    if output.ndim == 2:
        output = cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)
    for v in vectors:
        cv2.arrowedLine(output, (v.x, v.y), (v.x + v.dx, v.y + v.dy), (0, 0, 255), 1, tipLength=0.3)
    return output


class TemporalMotion:
    def __init__(self):
        self.previous = None

    def update(self, image):
        result = None if self.previous is None else phase_translation(self.previous, image)
        self.previous = image.copy()
        return result

    def reset(self):
        self.previous = None
