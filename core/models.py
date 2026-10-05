"""Shared input-independent contracts. Timestamps use the monotonic clock."""

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass(frozen=True)
class Command:
    intent: str
    source: str = "system"
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=perf_counter)


@dataclass(frozen=True)
class SystemEvent:
    type: str
    source: str
    payload: Any = None
    timestamp: float = field(default_factory=perf_counter)
