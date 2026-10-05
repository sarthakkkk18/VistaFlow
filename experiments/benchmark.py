"""Real filter/component measurements. Camera is explicit opt-in; no frames saved."""

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path
from queue import Empty
from time import perf_counter

import numpy as np

from core.config import Config
from core.runtime import VisionRuntime
from vision.live_filters import FILTERS, FilterSettings, apply_filter
from vision.operations import synthetic_image


def stats(samples):
    return (
        {
            "count": len(samples),
            "median": float(np.median(samples)),
            "p95": float(np.percentile(samples, 95)),
        }
        if samples
        else {}
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", action="store_true")
    args = parser.parse_args()
    result = {
        "environment": platform.platform(),
        "python": platform.python_version(),
        "scope": "Synthetic 256x256 BGR image; 2 warmups, 10 timed iterations per filter",
    }
    if args.camera:
        runtime = VisionRuntime(Config())
        runtime.settings = FilterSettings(operation="canny")
        runtime.compare = True
        runtime.start(tracking=True)
        samples = []
        deadline = perf_counter() + 45
        try:
            while len(samples) < 60 and perf_counter() < deadline:
                try:
                    runtime.frames.get(timeout=0.5)
                except Empty:
                    if not runtime.thread.is_alive():
                        break
                    continue
                samples.append(dict(runtime.metrics))
        finally:
            stopped = runtime.close(timeout=8)
        result.update(
            scope="Physical camera + MediaPipe + Canny, requested 640x480/30 FPS, at most 60 frames; no gesture accuracy or UI timing",
            frames=len(samples),
            worker_stopped=stopped,
            tracking_active=runtime.tracking,
            frames_saved=False,
            metrics={
                k: stats([s[k] for s in samples[10:]])
                for k in ("capture_fps", "processed_fps", "processing_ms")
            },
            messages=list(runtime.messages.queue),
        )
        filename = "live_camera.json"
    else:
        source = synthetic_image()
        rows = []
        for name in FILTERS:
            if name == "motion":
                continue
            settings = FilterSettings(operation=name)
            for _ in range(2):
                apply_filter(source, settings)
            samples = []
            for _ in range(10):
                start = perf_counter()
                apply_filter(source, settings)
                samples.append((perf_counter() - start) * 1000)
            rows.append(
                {"settings": asdict(settings), "milliseconds": stats(samples), "raw_ms": samples}
            )
        result["filters"] = rows
        filename = "filters.json"
    path = Path("docs/evidence") / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            result if args.camera else {"filters": len(rows), "evidence": str(path)}, indent=2
        )
    )
    if args.camera and (len(samples) < 60 or not stopped):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
