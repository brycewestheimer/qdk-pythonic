"""Quantum kernel estimation circuits.

Example::

    from qdk_pythonic.domains.ml import AngleEncoding, QuantumKernel

    encoding = AngleEncoding(n_features=4)
    kernel = QuantumKernel(encoding)
    circuit = kernel.to_circuit(x=[0.1, 0.2, 0.3, 0.4],
                                 y=[0.5, 0.6, 0.7, 0.8])
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qdk_pythonic.domains.ml.encoding import AmplitudeEncoding, AngleEncoding

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class QuantumKernel:
    """Quantum kernel via compute-uncompute circuit.

    Computes ``k(x, y) = |<phi(x)|phi(y)>|^2`` using the compute-uncompute
    method: apply U(x), then U_dagger(y), then measure.

    Attributes:
        encoding: The feature encoding scheme.
    """

    encoding: AngleEncoding | AmplitudeEncoding

    def to_circuit(
        self,
        x: Sequence[float],
        y: Sequence[float],
    ) -> Circuit:
        """Build the kernel estimation circuit.

        Args:
            x: First feature vector.
            y: Second feature vector.

        Returns:
            A circuit whose measurement outcome estimates the kernel
            value.
        """
        from qdk_pythonic.core.circuit import Circuit

        circ_x = self.encoding.to_circuit(x)
        circ_y = self.encoding.to_circuit(y)

        circ = Circuit()
        n = circ_x.qubit_count()
        circ.allocate(n)

        # Apply U(x)
        for inst in circ_x.instructions:
            circ.add_instruction(inst)

        # Apply U_dagger(y) via adjoint of each gate in reverse
        y_insts = list(reversed(circ_y.instructions))
        for inst in y_insts:
            circ.add_instruction(inst)

        # Measure all
        circ.measure_all()

        return circ
