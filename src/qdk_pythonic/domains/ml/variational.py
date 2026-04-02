"""Variational quantum classifiers.

Example::

    from qdk_pythonic.domains.ml import AngleEncoding, VariationalClassifier
    from qdk_pythonic.domains.common import HardwareEfficientAnsatz

    encoding = AngleEncoding(n_features=4)
    ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=2)
    classifier = VariationalClassifier(encoding, ansatz)
    circuit = classifier.to_circuit(data=[0.1, 0.2, 0.3, 0.4],
                                      params=[0.1] * ansatz.num_parameters)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz
from qdk_pythonic.domains.ml.encoding import AngleEncoding

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class VariationalClassifier:
    """Parameterized quantum classifier.

    Combines data encoding with a variational ansatz and measurement
    to form a quantum classifier circuit.

    Attributes:
        encoding: The feature encoding scheme.
        ansatz: The variational ansatz.
    """

    encoding: AngleEncoding
    ansatz: HardwareEfficientAnsatz

    def __post_init__(self) -> None:
        if self.encoding.n_features != self.ansatz.n_qubits:
            raise ValueError(
                f"Encoding features ({self.encoding.n_features}) must "
                f"match ansatz qubits ({self.ansatz.n_qubits})"
            )

    def to_circuit(
        self,
        data: Sequence[float],
        params: Sequence[float],
    ) -> Circuit:
        """Build the classifier circuit.

        Args:
            data: Feature vector.
            params: Ansatz parameters.

        Returns:
            A circuit combining encoding, ansatz, and measurement.
        """
        from qdk_pythonic.core.circuit import Circuit

        enc_circ = self.encoding.to_circuit(data)
        ans_circ = self.ansatz.to_circuit(params)

        circ = Circuit()
        n = self.encoding.n_features
        q = circ.allocate(n)

        # Encoding layer
        circ.compose_into(enc_circ)

        # Ansatz layer
        circ.compose_into(ans_circ)

        # Measure first qubit as classification output
        circ.measure(q[0])

        return circ
