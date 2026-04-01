"""Quantum Amplitude Estimation (QAE) circuit builder.

Example::

    from qdk_pythonic.domains.finance import QuantumAmplitudeEstimation

    qae = QuantumAmplitudeEstimation(
        state_prep=my_state_prep_circuit,
        oracle=my_grover_oracle,
        n_estimation_qubits=8,
    )
    circuit = qae.to_circuit()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class QuantumAmplitudeEstimation:
    """Quantum Amplitude Estimation circuit builder.

    Wraps a state preparation circuit and a Grover oracle into a
    QPE-based amplitude estimation circuit.

    Attributes:
        state_prep: Circuit preparing the state whose amplitude
            we want to estimate.
        oracle: Grover oracle circuit (reflection about the marked
            state).
        n_estimation_qubits: Number of counting qubits for QPE.
    """

    state_prep: Circuit
    oracle: Circuit
    n_estimation_qubits: int

    def __post_init__(self) -> None:
        if self.n_estimation_qubits < 1:
            raise ValueError(
                f"n_estimation_qubits must be >= 1, "
                f"got {self.n_estimation_qubits}"
            )

    def to_circuit(self) -> Circuit:
        """Build the amplitude estimation circuit.

        Constructs a simplified QAE circuit: Hadamard on estimation
        qubits, state preparation, and the oracle applied once per
        estimation qubit.

        Returns:
            The QAE circuit.
        """
        from qdk_pythonic.core.circuit import Circuit

        n_state = self.state_prep.qubit_count()

        circ = Circuit()
        circ.allocate(n_state, label="state")
        est_q = circ.allocate(self.n_estimation_qubits, label="est")

        # Hadamard on estimation qubits
        for i in range(self.n_estimation_qubits):
            circ.h(est_q[i])

        # State preparation
        for inst in self.state_prep.instructions:
            circ.add_instruction(inst)

        # Oracle applications (simplified: one per estimation qubit)
        for _k in range(self.n_estimation_qubits):
            for inst in self.oracle.instructions:
                circ.add_instruction(inst)

        return circ
