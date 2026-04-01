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
    """Prepare a uniform superposition |+>^n via Hadamard on all qubits.

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

    Uses controlled Ry rotations to load a probability vector into the
    amplitudes of *n* qubits, where *n* = ceil(log2(len(probabilities))).

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
        """Build a state-preparation circuit.

        Uses a simplified Ry-rotation encoding: for each amplitude,
        apply Ry(2 * arcsin(sqrt(p))) on the corresponding qubit.
        This is an approximation suitable for resource estimation.
        """
        from qdk_pythonic.core.circuit import Circuit

        n_qubits = math.ceil(math.log2(len(self.probabilities)))
        n_qubits = max(n_qubits, 1)

        circ = Circuit()
        q = circ.allocate(n_qubits)

        # Simple product-state approximation: encode marginal
        # probabilities as Ry rotations on each qubit.
        n_bins = 2**n_qubits
        for i in range(n_qubits):
            # Probability that qubit i is |1>
            p_one = 0.0
            for j in range(n_bins):
                if j < len(self.probabilities) and (j >> i) & 1:
                    p_one += self.probabilities[j]
            p_one = min(max(p_one, 0.0), 1.0)
            if p_one > 1e-15:
                theta = 2.0 * math.asin(math.sqrt(p_one))
                circ.ry(theta, q[i])

        return circ
