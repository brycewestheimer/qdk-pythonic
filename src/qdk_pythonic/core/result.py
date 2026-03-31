"""Result wrapper types for simulation and estimation output."""

from __future__ import annotations

from dataclasses import dataclass

from qdk_pythonic.core.qubit import Qubit


@dataclass(frozen=True)
class MeasurementResult:
    """Result of a single measurement.

    Attributes:
        qubit: The qubit that was measured.
        label: An optional label for this result.
    """

    qubit: Qubit
    label: str | None = None
