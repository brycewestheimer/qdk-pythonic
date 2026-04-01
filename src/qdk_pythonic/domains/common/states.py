"""Quantum state preparation abstractions.

Example::

    from qdk_pythonic.domains.common.states import BasisState, UniformSuperposition

    circ = BasisState("1010").to_circuit()
    circ = UniformSuperposition(4).to_circuit()
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit
    from qdk_pythonic.core.qubit import Qubit, QubitRegister


@dataclass(frozen=True)
class BasisState:
    """Prepare a computational basis state.

    Applies X gates to qubits corresponding to ``'1'`` bits in the
    bitstring.

    Attributes:
        bitstring: Target state as ``'0'``/``'1'`` characters
            (leftmost = qubit 0).
    """

    bitstring: str

    def __post_init__(self) -> None:
        if not self.bitstring or not all(c in "01" for c in self.bitstring):
            raise ValueError(
                f"bitstring must be non-empty and contain only '0'/'1', "
                f"got {self.bitstring!r}"
            )

    def to_circuit(self) -> Circuit:
        """Build a circuit that prepares this basis state."""
        from qdk_pythonic.core.circuit import Circuit

        circ = Circuit()
        q = circ.allocate(len(self.bitstring))
        for i, bit in enumerate(self.bitstring):
            if bit == "1":
                circ.x(q[i])
        return circ


@dataclass(frozen=True)
class UniformSuperposition:
    """Prepare a uniform superposition ``|+>^n`` via Hadamard on all qubits.

    Attributes:
        n_qubits: Number of qubits.
    """

    n_qubits: int

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise ValueError(
                f"n_qubits must be >= 1, got {self.n_qubits}"
            )

    def to_circuit(self) -> Circuit:
        """Build a circuit that prepares the uniform superposition."""
        from qdk_pythonic.core.circuit import Circuit

        circ = Circuit()
        q = circ.allocate(self.n_qubits)
        for i in range(self.n_qubits):
            circ.h(q[i])
        return circ


@dataclass(frozen=True)
class DiscreteProbabilityDistribution:
    """Encode a discrete probability distribution into qubit amplitudes.

    Uses a binary tree of controlled Ry rotations to exactly load the
    probability vector into *n* qubits, where
    *n* = ceil(log2(len(probabilities))).

    Attributes:
        probabilities: List of probabilities summing to 1.
    """

    probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.probabilities:
            raise ValueError("probabilities must be non-empty")
        total = sum(self.probabilities)
        if abs(total - 1.0) > 1e-8:
            raise ValueError(
                f"probabilities must sum to 1, got {total:.8f}"
            )

    def to_circuit(self) -> Circuit:
        """Build an exact state-preparation circuit.

        Uses the Mottonen et al. decomposition: a top-down binary tree
        of controlled-Ry rotations that prepares the state
        ``sum_k sqrt(p_k) |k>``.
        """
        from qdk_pythonic.core.circuit import Circuit

        n_qubits = math.ceil(math.log2(len(self.probabilities)))
        n_qubits = max(n_qubits, 1)

        # Pad probabilities to 2^n and compute amplitudes
        n_bins = 2**n_qubits
        padded = list(self.probabilities) + [0.0] * (n_bins - len(self.probabilities))
        amplitudes = [math.sqrt(max(p, 0.0)) for p in padded]

        circ = Circuit()
        q = circ.allocate(n_qubits)
        rotations = _compute_rotation_angles(amplitudes, n_qubits)
        _apply_rotations(circ, q, rotations)
        return circ


def _compute_rotation_angles(
    amplitudes: list[float], n_qubits: int,
) -> list[tuple[int, float, str]]:
    """Compute controlled-Ry angles for exact state preparation.

    Uses a top-down decomposition: for each qubit (target), compute
    the conditional rotation angle given every possible bitstring on
    the qubits above it.

    Returns:
        List of ``(target_qubit, theta, control_pattern)`` triples
        where ``control_pattern`` is a bitstring over qubits
        ``0..target-1`` (empty string for no controls).
    """
    rotations: list[tuple[int, float, str]] = []
    for target in range(n_qubits):
        n_controls = target
        n_groups = 2**n_controls
        for group in range(n_groups):
            ctrl_bits = format(group, f"0{n_controls}b") if n_controls > 0 else ""
            # Sum squared amplitudes for indices matching ctrl_bits
            # with target bit = 0 vs 1
            p_zero = 0.0
            p_one = 0.0
            for k, amp in enumerate(amplitudes):
                matches = True
                for b in range(n_controls):
                    bit_val = (k >> b) & 1
                    pattern_val = int(ctrl_bits[n_controls - 1 - b])
                    if bit_val != pattern_val:
                        matches = False
                        break
                if not matches:
                    continue
                if (k >> target) & 1:
                    p_one += amp * amp
                else:
                    p_zero += amp * amp
            total = p_zero + p_one
            if total < 1e-15:
                continue
            theta = 2.0 * math.atan2(math.sqrt(p_one), math.sqrt(p_zero))
            if abs(theta) < 1e-15:
                continue
            rotations.append((target, theta, ctrl_bits))
    return rotations


def _apply_rotations(
    circ: Circuit,
    qubits: QubitRegister,
    rotations: list[tuple[int, float, str]],
) -> None:
    """Apply computed rotation angles as (controlled-)Ry gates.

    For each rotation ``(target, theta, ctrl_bits)``:
    - No controls: ``Ry(theta, q[target])``
    - With controls: X-gate conditioning on ``|0>`` control bits,
      then multi-controlled Ry, then undo X gates.
    """
    for target, theta, ctrl_bits in rotations:
        q_target = qubits[target]
        if not ctrl_bits:
            circ.ry(theta, q_target)
        else:
            controls: list[Qubit] = []
            flip_indices: list[int] = []
            for b, bit in enumerate(reversed(ctrl_bits)):
                q_ctrl = qubits[b]
                controls.append(q_ctrl)
                if bit == "0":
                    flip_indices.append(b)
                    circ.x(q_ctrl)

            circ.controlled(circ.ry, controls, theta, q_target)

            for b in flip_indices:
                circ.x(qubits[b])
