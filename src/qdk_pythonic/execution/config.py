"""Configuration dataclasses for execution backends."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunConfig:
    """Configuration for circuit simulation.

    Attributes:
        shots: Number of simulation shots to run.
    """

    shots: int = 1000
