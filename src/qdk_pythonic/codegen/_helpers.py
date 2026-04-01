"""Shared helpers for code generators."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdk_pythonic.core.qubit import QubitRegister


def build_qubit_map(registers: list[QubitRegister]) -> dict[int, str]:
    """Map qubit index to code-gen reference string (e.g. ``"q[0]"``)."""
    qubit_map: dict[int, str] = {}
    for reg in registers:
        reg_label = reg.label if reg.label else "q"
        for i, qubit in enumerate(reg):
            qubit_map[qubit.index] = f"{reg_label}[{i}]"
    return qubit_map
