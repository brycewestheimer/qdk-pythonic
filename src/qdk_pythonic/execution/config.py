"""Configuration dataclasses for execution backends."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunConfig:
    """Configuration for circuit simulation.

    Attributes:
        shots: Number of simulation shots to run. Must be >= 1.
        seed: Optional RNG seed for reproducible simulation.
        noise: Optional noise model as (depolarizing, dephasing, bitflip)
            probabilities, each in [0, 1].
    """

    shots: int = 1000
    seed: int | None = None
    noise: tuple[float, float, float] | None = None

    def __post_init__(self) -> None:
        if self.shots < 1:
            raise ValueError(f"shots must be >= 1, got {self.shots}")
        if self.seed is not None and self.seed < 0:
            raise ValueError(f"seed must be non-negative, got {self.seed}")
        if self.noise is not None:
            if len(self.noise) != 3:
                raise ValueError("noise must be a 3-tuple (px, py, pz)")
            if any(p < 0 or p > 1 for p in self.noise):
                raise ValueError("noise probabilities must be in [0, 1]")
