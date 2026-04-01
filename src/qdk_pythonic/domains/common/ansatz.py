"""Variational ansatz circuit builders.

Example::

    from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz

    ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=2)
    params = [0.1] * ansatz.num_parameters
    circuit = ansatz.to_circuit(params)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit

_ROTATION_DISPATCH = {
    "rx": "rx",
    "ry": "ry",
    "rz": "rz",
}


@dataclass(frozen=True)
class HardwareEfficientAnsatz:
    """Hardware-efficient variational ansatz.

    Alternates layers of single-qubit rotations with entangling
    (CX) layers.

    Attributes:
        n_qubits: Number of qubits.
        depth: Number of ansatz layers.
        rotation_gates: Rotation gate names per layer (e.g.
            ``("ry", "rz")``).
        entanglement: Entanglement pattern. ``"linear"`` connects
            adjacent qubits; ``"full"`` connects all pairs.
    """

    n_qubits: int
    depth: int = 1
    rotation_gates: tuple[str, ...] = ("ry", "rz")
    entanglement: str = "linear"

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise ValueError(
                f"n_qubits must be >= 1, got {self.n_qubits}"
            )
        if self.depth < 1:
            raise ValueError(
                f"depth must be >= 1, got {self.depth}"
            )
        for gate in self.rotation_gates:
            if gate not in _ROTATION_DISPATCH:
                raise ValueError(
                    f"Unknown rotation gate '{gate}'; "
                    f"valid options: {sorted(_ROTATION_DISPATCH)}"
                )
        if self.entanglement not in ("linear", "full"):
            raise ValueError(
                f"entanglement must be 'linear' or 'full', "
                f"got '{self.entanglement}'"
            )

    @property
    def num_parameters(self) -> int:
        """Total number of variational parameters."""
        return self.n_qubits * len(self.rotation_gates) * self.depth

    def to_circuit(self, params: Sequence[float]) -> Circuit:
        """Build the ansatz circuit with concrete parameter values.

        Args:
            params: Parameter values, length must equal
                :attr:`num_parameters`.

        Returns:
            The parameterized circuit.

        Raises:
            ValueError: If *params* has the wrong length.
        """
        if len(params) != self.num_parameters:
            raise ValueError(
                f"Expected {self.num_parameters} parameters, "
                f"got {len(params)}"
            )

        from qdk_pythonic.core.circuit import Circuit

        circ = Circuit()
        q = circ.allocate(self.n_qubits)
        idx = 0

        for _layer in range(self.depth):
            # Rotation layer
            for gate_name in self.rotation_gates:
                method_name = _ROTATION_DISPATCH[gate_name]
                for i in range(self.n_qubits):
                    getattr(circ, method_name)(params[idx], q[i])
                    idx += 1

            # Entangling layer
            if self.entanglement == "linear":
                for i in range(self.n_qubits - 1):
                    circ.cx(q[i], q[i + 1])
            else:  # full
                for i in range(self.n_qubits):
                    for j in range(i + 1, self.n_qubits):
                        circ.cx(q[i], q[j])

        return circ
