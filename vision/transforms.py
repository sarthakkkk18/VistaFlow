"""FFT low-pass, orthonormal DCT and custom separable one-level Haar."""

import numpy as np
from scipy.fft import dctn, idctn

from vision.preprocessing import gray


def spectrum(image):
    return np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(gray(image)))))


def lowpass(image, radius=20):
    if radius < 0:
        raise ValueError("Nonnegative radius required")
    pixels = gray(image)
    yy, xx = np.indices(pixels.shape)
    mask = (xx - pixels.shape[1] // 2) ** 2 + (yy - pixels.shape[0] // 2) ** 2 <= radius**2
    return np.fft.ifft2(np.fft.ifftshift(np.fft.fftshift(np.fft.fft2(pixels)) * mask)).real


def dct(image):
    return dctn(gray(image).astype(float), norm="ortho")


def inverse_dct(coefficients):
    return idctn(coefficients, norm="ortho")


def haar(image):
    pixels = gray(image).astype(float)
    if any(s % 2 for s in pixels.shape):
        raise ValueError("Haar requires even dimensions")
    rows = np.concatenate(
        (
            (pixels[:, 0::2] + pixels[:, 1::2]) / np.sqrt(2),
            (pixels[:, 0::2] - pixels[:, 1::2]) / np.sqrt(2),
        ),
        axis=1,
    )
    return np.concatenate(
        (
            (rows[0::2] + rows[1::2]) / np.sqrt(2),
            (rows[0::2] - rows[1::2]) / np.sqrt(2),
        ),
        axis=0,
    )


def inverse_haar(coefficients):
    h, w = coefficients.shape
    rows = np.empty_like(coefficients, dtype=float)
    rows[0::2] = (coefficients[: h // 2] + coefficients[h // 2 :]) / np.sqrt(2)
    rows[1::2] = (coefficients[: h // 2] - coefficients[h // 2 :]) / np.sqrt(2)
    pixels = np.empty_like(rows)
    pixels[:, 0::2] = (rows[:, : w // 2] + rows[:, w // 2 :]) / np.sqrt(2)
    pixels[:, 1::2] = (rows[:, : w // 2] - rows[:, w // 2 :]) / np.sqrt(2)
    return pixels
