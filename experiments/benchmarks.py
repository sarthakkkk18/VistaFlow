"""Measured timings persisted to SQLite; no frame/audio persistence."""

import json
import platform
import sqlite3
import statistics
from dataclasses import asdict, dataclass
from time import perf_counter, process_time


@dataclass(frozen=True)
class BenchmarkResult:
    algorithm: str
    input_size: tuple
    parameters: dict
    samples_ms: list
    median_ms: float
    fps: float
    environment: str
    cpu_ms: float


def measure(name, operation, input_size, parameters=None, repeats=5):
    if repeats < 1:
        raise ValueError("At least one repeat required")
    operation()  # warm-up excluded
    durations = []
    cpu_start = process_time()
    for _ in range(repeats):
        start = perf_counter()
        operation()
        durations.append((perf_counter() - start) * 1000)
    median = statistics.median(durations)
    return BenchmarkResult(
        name,
        tuple(input_size),
        parameters or {},
        durations,
        median,
        1000 / median,
        platform.platform() + "; Python " + platform.python_version(),
        (process_time() - cpu_start) * 1000 / repeats,
    )


def save(result, path):
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS benchmarks (id INTEGER PRIMARY KEY, result TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO benchmarks(result) VALUES (?)", (json.dumps(asdict(result)),)
        )
