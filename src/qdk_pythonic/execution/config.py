"""Configuration dataclasses for execution backends."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunConfig:
    """Configuration for circuit simulation.

    Attributes:
        shots: Number of simulation shots to run. Must be >= 1.
    """

    shots: int = 1000

    def __post_init__(self) -> None:
        if self.shots < 1:
            raise ValueError(f"shots must be >= 1, got {self.shots}")
