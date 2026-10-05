"""VistaFlow camera and gesture configuration. No audio or external services."""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GestureConfig:
    """Tunable geometry and temporal validation; times are milliseconds."""

    smoothing_alpha: float = 0.45
    smoothing_window: int = 3
    hold_frames: int = 3
    hold_ms: float = 120
    release_frames: int = 3
    release_ms: float = 80
    pinch_threshold: float = 0.30
    pinch_release_threshold: float = 0.43
    minimum_confidence: float = 0.70
    extension_ratio: float = 1.15
    cooldown_ms: float = 350
    tracking_loss_ms: float = 180
    swipe_distance_threshold: float = 0.20
    swipe_velocity_threshold: float = 0.55
    swipe_window_ms: float = 500

    def __post_init__(self):
        from dataclasses import fields

        for item in fields(self):
            value = getattr(self, item.name)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid gesture parameter: {item.name}")
        if any(
            type(v) is not int
            for v in (self.hold_frames, self.release_frames, self.smoothing_window)
        ):
            raise ValueError("Frame counts must be integers")
        if not 0 < self.smoothing_alpha <= 1 or not 0 < self.minimum_confidence <= 1:
            raise ValueError("Confidence and smoothing must be in (0,1]")
        if self.pinch_release_threshold <= self.pinch_threshold or self.extension_ratio <= 1:
            raise ValueError("Invalid geometry hysteresis")


@dataclass(frozen=True)
class Config:
    gesture: GestureConfig = field(default_factory=GestureConfig)
    camera_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    hand_model: str = str(Path(__file__).resolve().parents[1] / "data" / "hand_landmarker.task")

    def __post_init__(self):
        if isinstance(self.gesture, dict):
            object.__setattr__(self, "gesture", GestureConfig(**self.gesture))
        if not isinstance(self.gesture, GestureConfig):
            raise ValueError("Invalid gesture profile")
        if type(self.camera_index) is not int or self.camera_index < 0:
            raise ValueError("Camera index must be nonnegative")
        for name in ("width", "height", "fps"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.hand_model, str) or not self.hand_model.strip():
            raise ValueError("Hand model path required")

    @classmethod
    def load(cls, path=None):
        if path is None:
            return cls()
        path = Path(path).resolve()
        data = json.loads(path.read_text(encoding="utf-8"))
        if "hand_model" in data:
            model = Path(data["hand_model"])
            data["hand_model"] = str(model if model.is_absolute() else path.parent / model)
        return cls(**data)
