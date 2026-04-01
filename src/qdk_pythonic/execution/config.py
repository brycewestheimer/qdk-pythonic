"""Configuration dataclasses for execution backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RunConfig:
    """Configuration for circuit simulation.

    Attributes:
        shots: Number of simulation shots to run.
        seed: Optional random seed for reproducibility.
        noise_model: Optional noise model specification.
    """

    shots: int = 1000
    seed: int | None = None
    noise_model: dict[str, Any] | None = None
