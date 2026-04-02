"""Quantum Amplitude Estimation (QAE) circuit builder.

Implements the canonical QAE algorithm (Brassard, Hoyer, Mosca, Tapp
2002): QPE applied to the Grover iterate to extract the amplitude of
a marked state.

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

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qdk_pythonic.core.circuit import remap_instruction
from qdk_pythonic.core.instruction import Instruction

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class QuantumAmplitudeEstimation:
    """Quantum Amplitude Estimation circuit builder.

    Wraps a state preparation circuit and a Grover oracle into a
    QPE-based amplitude estimation circuit.

    The circuit structure is:

    1. Hadamard on all estimation qubits.
    2. State preparation *A* on the state register.
    3. For each estimation qubit *k*: apply the Grover iterate
       *Q* = *oracle* a total of 2^k times, with each gate
       controlled on estimation qubit *k*.
    4. Inverse QFT on the estimation register.

    Attributes:
        state_prep: Circuit preparing the state whose amplitude
            we want to estimate.
        oracle: Grover oracle circuit (the Grover iterate *Q*).
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
        """Build the full amplitude estimation circuit.

        Returns:
            The QAE circuit with state register, estimation register,
            controlled oracle applications, and inverse QFT.
        """
        from qdk_pythonic.builders import inverse_qft
        from qdk_pythonic.core.circuit import Circuit

        n_prep = self.state_prep.qubit_count()
        n_oracle = self.oracle.qubit_count()
        n_state = max(n_prep, n_oracle)
        m = self.n_estimation_qubits

        circ = Circuit()
        state_q = circ.allocate(n_state, label="state")
        est_q = circ.allocate(m, label="est")

        # 1. Hadamard on estimation register
        for i in range(m):
            circ.h(est_q[i])

        # 2. State preparation A on state register
        prep_map = {
            src.index: state_q[i]
            for i, src in enumerate(self.state_prep.qubits)
        }
        circ.compose_into(self.state_prep, qubit_map=prep_map)

        # 3. Controlled-Q^(2^k) for each estimation qubit k
        oracle_map = {
            src.index: state_q[i]
            for i, src in enumerate(self.oracle.qubits)
        }
        for k in range(m):
            power = 2**k
            for _ in range(power):
                for inst in self.oracle.instructions:
                    remapped = remap_instruction(inst, oracle_map)
                    if isinstance(remapped, Instruction):
                        controlled = dataclasses.replace(
                            remapped,
                            controls=remapped.controls + (est_q[k],),
                        )
                        circ._instructions.append(controlled)
                    else:
                        circ._instructions.append(remapped)

        # 4. Inverse QFT on estimation register
        iqft = inverse_qft(m)
        iqft_map = {
            src.index: est_q[i]
            for i, src in enumerate(iqft.qubits)
        }
        circ.compose_into(iqft, qubit_map=iqft_map)

        return circ
