import cv2
import numpy as np
import pytest

from vision import (
    color,
    edges,
    enhancement,
    filtering,
    morphology,
    segmentation,
    transforms,
)
from vision.operations import OPERATIONS, synthetic_image


@pytest.mark.parametrize("name", OPERATIONS)
def test_registry(name):
    image = synthetic_image(64)
    original = image.copy()
    result = OPERATIONS[name](image)
    assert result.shape[:2] == image.shape[:2] and np.isfinite(result).all()
    assert np.array_equal(image, original)


def test_convolution_reference():
    image = np.random.default_rng(2).integers(0, 256, (16, 16), dtype=np.uint8)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    assert np.allclose(filtering.correlate(image, kernel), cv2.filter2D(image, cv2.CV_64F, kernel))


def test_histogram_reference():
    image = np.arange(64, dtype=np.uint8).reshape(8, 8)
    assert enhancement.histogram(image).sum() == 64
    assert np.array_equal(enhancement.equalize(image), cv2.equalizeHist(image))
    assert np.all(enhancement.adjust(np.array([[10]], np.uint8), 1, -20) == 0)


def test_median_removes_isolated_impulse_without_mutating_input():
    image = np.full((9, 9, 3), 80, np.uint8)
    image[4, 4] = 255
    output = filtering.median(image)
    assert output.shape == image.shape and np.all(output == 80)
    assert np.all(image[4, 4] == 255)
    with pytest.raises(ValueError):
        filtering.median(image, 4)


@pytest.mark.parametrize("method", ["erosion", "dilation", "opening", "closing"])
def test_morphology_reference(method):
    image = np.random.default_rng(3).integers(0, 256, (16, 16), dtype=np.uint8)
    assert np.array_equal(
        morphology.apply(image, method), morphology.apply(image, method, custom=False)
    )


def test_transform_reconstruction():
    image = np.random.default_rng(1).integers(0, 255, (16, 16), dtype=np.uint8)
    assert np.allclose(transforms.inverse_dct(transforms.dct(image)), image)
    assert np.allclose(transforms.inverse_haar(transforms.haar(image)), image)
    assert np.allclose(transforms.lowpass(np.full((16, 16), 42, np.uint8)), 42)


def test_edges_segmentation_color():
    image = np.zeros((16, 16), np.uint8)
    image[:, 8:] = 255
    gx, gy = edges.gradients(image)
    assert np.max(gx) == 1020 and np.all(gy == 0)
    assert np.array_equal(segmentation.segment(image), image)
    green = np.full((2, 2, 3), (0, 255, 0), np.uint8)
    assert np.all(color.mask_hsv(green) == 255)
