"""Shared helpers for analysis modules."""

from __future__ import annotations

from qdk_pythonic.core.instruction import Instruction, InstructionLike, Measurement


def involved_indices(inst: InstructionLike) -> list[int]:
    """Return qubit indices touched by an instruction."""
    if isinstance(inst, Instruction):
        return [q.index for q in inst.targets] + [
            q.index for q in inst.controls
        ]
    if isinstance(inst, Measurement):
        return [inst.target.index]
    return []
