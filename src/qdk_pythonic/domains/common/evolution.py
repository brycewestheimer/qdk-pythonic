"""Trotterized time evolution from Pauli Hamiltonians.

Example::

    from qdk_pythonic.domains.common.operators import PauliHamiltonian, Z, X
    from qdk_pythonic.domains.common.evolution import TrotterEvolution

    H = PauliHamiltonian()
    H += -1.0 * Z(0) * Z(1)
    H += -0.5 * X(0)
    H += -0.5 * X(1)

    evo = TrotterEvolution(hamiltonian=H, time=1.0, steps=10)
    circuit = evo.to_circuit()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qdk_pythonic.domains.common.operators import PauliHamiltonian

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class TrotterEvolution:
    """Time evolution via Trotter-Suzuki decomposition.

    Wraps a :class:`PauliHamiltonian` and provides convenient circuit
    generation and resource estimation.

    Attributes:
        hamiltonian: The Hamiltonian to evolve under.
        time: Total evolution time.
        steps: Number of Trotter steps (higher = more accurate).
        order: Trotter order (1 or 2).
    """

    hamiltonian: PauliHamiltonian
    time: float
    steps: int = 1
    order: int = 1

    def to_circuit(self) -> Circuit:
        """Build the Trotterized time-evolution circuit.

        Returns:
            A Circuit approximating exp(-i H t).
        """
        dt = self.time / self.steps
        return self.hamiltonian.to_trotter_circuit(
            dt, order=self.order, steps=self.steps,
        )

    def estimate_resources(
        self, params: dict[str, Any] | None = None,
    ) -> Any:
        """Build the circuit and run resource estimation.

        Args:
            params: Optional estimator parameters passed to
                ``Circuit.estimate()``.

        Returns:
            The resource estimation result.
        """
        return self.to_circuit().estimate(params=params)
