import sqlite3

import numpy as np
from experiments.benchmarks import measure, save

from vision.motion import TemporalMotion, block_match, phase_translation


def test_known_translation():
    a = np.random.default_rng(42).integers(0, 256, (64, 64), dtype=np.uint8)
    b = np.roll(a, (2, 3), (0, 1))
    vectors = block_match(a, b)
    inner = [v for v in vectors if 8 < v.x < 56 and 8 < v.y < 56]
    assert all((v.dx, v.dy, v.error) == (3, 2, 0) for v in inner)
    displacement, confidence = phase_translation(a, b)
    assert np.allclose(displacement, (3, 2), atol=0.05) and confidence > 0.9


def test_static_and_temporal():
    image = np.ones((16, 16), np.uint8)
    assert all(v.dx == v.dy == 0 for v in block_match(image, image))
    temporal = TemporalMotion()
    assert temporal.update(image) is None
    temporal.reset()
    assert temporal.previous is None


def test_benchmark_persistence(tmp_path):
    result = measure("sum", lambda: sum(range(100)), (100,), repeats=3)
    assert len(result.samples_ms) == 3 and result.fps > 0
    path = tmp_path / "results.sqlite3"
    save(result, path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM benchmarks").fetchone()[0] == 1
