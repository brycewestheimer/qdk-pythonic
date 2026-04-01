"""Classical data encoding into quantum states.

Example::

    from qdk_pythonic.domains.ml.encoding import AngleEncoding

    encoding = AngleEncoding(n_features=4)
    circuit = encoding.to_circuit(data=[0.1, 0.2, 0.3, 0.4])
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class AngleEncoding:
    """Encode classical features as rotation angles.

    Each feature x_i is encoded as Ry(x_i) on qubit i.
    Requires one qubit per feature.

    Attributes:
        n_features: Number of classical features to encode.
    """

    n_features: int

    def __post_init__(self) -> None:
        if self.n_features < 1:
            raise ValueError(
                f"n_features must be >= 1, got {self.n_features}"
            )

    def to_circuit(self, data: Sequence[float]) -> Circuit:
        """Encode classical data into a quantum circuit.

        Args:
            data: Feature vector of length ``n_features``.

        Returns:
            A circuit encoding the data.

        Raises:
            ValueError: If *data* has wrong length.
        """
        if len(data) != self.n_features:
            raise ValueError(
                f"Expected {self.n_features} features, got {len(data)}"
            )

        from qdk_pythonic.core.circuit import Circuit

        circ = Circuit()
        q = circ.allocate(self.n_features)
        for i, x in enumerate(data):
            circ.ry(x, q[i])
        return circ


@dataclass(frozen=True)
class AmplitudeEncoding:
    """Encode classical data as quantum amplitudes.

    Encodes a normalized vector of 2^n values into n qubits using
    Ry rotations (simplified encoding).

    Attributes:
        n_qubits: Number of qubits.
    """

    n_qubits: int

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise ValueError(
                f"n_qubits must be >= 1, got {self.n_qubits}"
            )

    def to_circuit(self, data: Sequence[float]) -> Circuit:
        """Encode amplitude data into a quantum circuit.

        Args:
            data: Data vector of length 2^n_qubits. Must be normalized.

        Returns:
            A circuit encoding the data.

        Raises:
            ValueError: If *data* has wrong length or is not normalized.
        """
        expected_len = 2**self.n_qubits
        if len(data) != expected_len:
            raise ValueError(
                f"Expected {expected_len} values, got {len(data)}"
            )
        norm = sum(x * x for x in data)
        if abs(norm - 1.0) > 1e-6:
            raise ValueError(
                f"Data must be normalized (|data|^2 = 1), got {norm:.6f}"
            )

        from qdk_pythonic.core.circuit import Circuit

        circ = Circuit()
        q = circ.allocate(self.n_qubits)

        # Simplified encoding: compute marginal |1> probability per qubit
        for i in range(self.n_qubits):
            p_one = 0.0
            for j in range(expected_len):
                if (j >> i) & 1:
                    p_one += data[j] * data[j]
            p_one = min(max(p_one, 0.0), 1.0)
            if p_one > 1e-15:
                theta = 2.0 * math.asin(math.sqrt(p_one))
                circ.ry(theta, q[i])

        return circ
