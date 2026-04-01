"""Instruction dataclass binding gates to qubit targets."""

from __future__ import annotations

from dataclasses import dataclass

from qdk_pythonic.core.gates import GateDefinition
from qdk_pythonic.core.parameter import Parameter
from qdk_pythonic.core.qubit import Qubit


@dataclass(frozen=True)
class Instruction:
    """A single quantum instruction: gate + targets + parameters.

    Attributes:
        gate: The gate definition for this instruction.
        targets: The qubit operands.
        params: Parameters (concrete floats or symbolic
            :class:`Parameter` instances).
        controls: Additional control qubits.
        is_adjoint: Whether to apply the adjoint of the gate.
    """

    gate: GateDefinition
    targets: tuple[Qubit, ...]
    params: tuple[float | Parameter, ...] = ()
    controls: tuple[Qubit, ...] = ()
    is_adjoint: bool = False


@dataclass(frozen=True)
class Measurement:
    """A measurement instruction.

    Attributes:
        target: The qubit to measure.
        label: An optional label for the measurement result.
    """

    target: Qubit
    label: str | None = None


@dataclass(frozen=True)
class RawQSharp:
    """A raw Q# code fragment embedded in the circuit.

    Attributes:
        code: The Q# source code string.
    """

    code: str


InstructionLike = Instruction | Measurement | RawQSharp
