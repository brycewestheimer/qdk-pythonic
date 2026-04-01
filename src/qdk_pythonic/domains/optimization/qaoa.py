"""Quantum Approximate Optimization Algorithm (QAOA) circuit builder.

Example::

    from qdk_pythonic.domains.optimization.problem import MaxCut
    from qdk_pythonic.domains.optimization.qaoa import QAOA

    problem = MaxCut(edges=[(0,1), (1,2), (2,0)], n_nodes=3)
    qaoa = QAOA(problem.to_hamiltonian(), p=2)
    circuit = qaoa.to_circuit(gamma=[0.5, 0.3], beta=[0.7, 0.2])
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from qdk_pythonic.domains.common.operators import PauliHamiltonian
from qdk_pythonic.domains.optimization.mixer import x_mixer

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class QAOA:
    """QAOA circuit builder.

    Constructs a QAOA circuit from a cost Hamiltonian and optional
    mixer. Defaults to the standard X-mixer.

    Attributes:
        cost_hamiltonian: The cost function as a PauliHamiltonian.
        p: Number of QAOA layers.
        mixer: Mixer Hamiltonian. Defaults to X-mixer.
    """

    cost_hamiltonian: PauliHamiltonian
    p: int = 1
    mixer: PauliHamiltonian = field(default_factory=PauliHamiltonian)

    def __post_init__(self) -> None:
        if self.p < 1:
            raise ValueError(f"p must be >= 1, got {self.p}")
        # Auto-populate mixer if empty
        if len(self.mixer) == 0:
            n = self.cost_hamiltonian.qubit_count()
            object.__setattr__(self, "mixer", x_mixer(n))

    @property
    def num_parameters(self) -> int:
        """Total number of variational parameters (2 * p)."""
        return 2 * self.p

    def to_circuit(
        self,
        gamma: Sequence[float],
        beta: Sequence[float],
    ) -> Circuit:
        """Build the QAOA circuit with given angles.

        Args:
            gamma: Cost-layer angles, length *p*.
            beta: Mixer-layer angles, length *p*.

        Returns:
            The QAOA circuit.

        Raises:
            ValueError: If gamma or beta has wrong length.
        """
        if len(gamma) != self.p:
            raise ValueError(
                f"gamma must have length {self.p}, got {len(gamma)}"
            )
        if len(beta) != self.p:
            raise ValueError(
                f"beta must have length {self.p}, got {len(beta)}"
            )

        from qdk_pythonic.core.circuit import Circuit

        n_qubits = self.cost_hamiltonian.qubit_count()
        circ = Circuit()
        q = circ.allocate(n_qubits)

        # Initial uniform superposition
        for i in range(n_qubits):
            circ.h(q[i])

        # QAOA layers
        for k in range(self.p):
            # Cost unitary: exp(-i * gamma[k] * C)
            cost_circ = self.cost_hamiltonian.to_trotter_circuit(
                dt=gamma[k], steps=1,
            )
            for inst in cost_circ.instructions:
                circ.add_instruction(inst)

            # Mixer unitary: exp(-i * beta[k] * B)
            mixer_circ = self.mixer.to_trotter_circuit(
                dt=beta[k], steps=1,
            )
            for inst in mixer_circ.instructions:
                circ.add_instruction(inst)

        return circ

    def estimate_resources(
        self,
        gamma: Sequence[float],
        beta: Sequence[float],
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Build the circuit and run resource estimation.

        Args:
            gamma: Cost-layer angles.
            beta: Mixer-layer angles.
            params: Optional estimator parameters.

        Returns:
            The resource estimation result.
        """
        return self.to_circuit(gamma, beta).estimate(params=params)
