"""Quantum Phase Estimation for molecular ground-state energy.

Builds a QPE circuit using Trotterized Hamiltonian simulation,
following the qdk-chemistry workflow.

Example::

    from qdk_pythonic.domains.common.operators import PauliHamiltonian, Z
    from qdk_pythonic.domains.chemistry.qpe import ChemistryQPE

    H = PauliHamiltonian([Z(0)])
    qpe = ChemistryQPE(hamiltonian=H, n_electrons=1, n_estimation_qubits=4)
    circuit = qpe.to_circuit()
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qdk_pythonic.core.instruction import Instruction
from qdk_pythonic.domains.common.operators import PauliHamiltonian
from qdk_pythonic.exceptions import CircuitError

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class ChemistryQPE:
    """Quantum Phase Estimation for molecular energy.

    The circuit structure is:

    1. Prepare Hartree-Fock state on the system register.
    2. Hadamard on all estimation qubits.
    3. For each estimation qubit *k*: apply controlled
       ``exp(-i H t 2^k)`` via Trotterized simulation.
    4. Inverse QFT on the estimation register.

    Attributes:
        hamiltonian: Molecular Hamiltonian as PauliHamiltonian.
        n_electrons: Number of electrons (for HF state).
        n_estimation_qubits: Number of phase estimation qubits
            (determines energy precision).
        evolution_time: Total Hamiltonian evolution time.
        trotter_steps: Trotter steps per controlled evolution.
        trotter_order: Trotter-Suzuki decomposition order (1 or 2).
    """

    hamiltonian: PauliHamiltonian
    n_electrons: int
    n_estimation_qubits: int = 8
    evolution_time: float = 1.0
    trotter_steps: int = 1
    trotter_order: int = 1

    def __post_init__(self) -> None:
        if self.n_estimation_qubits < 1:
            raise CircuitError(
                f"n_estimation_qubits must be >= 1, "
                f"got {self.n_estimation_qubits}"
            )
        if self.n_electrons < 0:
            raise CircuitError(
                f"n_electrons must be >= 0, got {self.n_electrons}"
            )

    def to_circuit(self) -> Circuit:
        """Build the full QPE circuit.

        Returns:
            A circuit with system register, estimation register,
            controlled Hamiltonian evolution, and inverse QFT.
        """
        from qdk_pythonic.builders import inverse_qft
        from qdk_pythonic.core.circuit import Circuit, remap_instruction
        from qdk_pythonic.domains.chemistry.hartree_fock import (
            HartreeFockState,
        )

        n_system = self.hamiltonian.qubit_count()
        if n_system == 0:
            raise CircuitError(
                "Hamiltonian has no qubit terms"
            )
        m = self.n_estimation_qubits

        circ = Circuit()
        sys_q = circ.allocate(n_system, label="sys")
        est_q = circ.allocate(m, label="est")

        # 1. Prepare HF state on system register
        hf = HartreeFockState(
            n_qubits=n_system,
            n_electrons=self.n_electrons,
        )
        hf_circ = hf.to_circuit()
        hf_map = {
            src.index: sys_q[i]
            for i, src in enumerate(hf_circ.qubits)
        }
        circ.compose_into(hf_circ, qubit_map=hf_map)

        # 2. Hadamard on all estimation qubits
        for i in range(m):
            circ.h(est_q[i])

        # 3. Controlled-exp(-iHt * 2^k) for each estimation qubit k
        for k in range(m):
            power = 2 ** k
            t_scaled = self.evolution_time * power

            # Build Trotter circuit for exp(-iHt)
            trotter_circ = self.hamiltonian.to_trotter_circuit(
                dt=t_scaled / self.trotter_steps,
                order=self.trotter_order,
                steps=self.trotter_steps,
            )

            # Remap trotter qubits to system register
            sys_indices = self.hamiltonian.qubit_indices()
            trotter_map = {
                src.index: sys_q[sys_indices.index(src.index)]
                for src in trotter_circ.qubits
                if src.index in sys_indices
            }

            # Apply each gate controlled on est_q[k]
            for inst in trotter_circ.instructions:
                remapped = remap_instruction(inst, trotter_map)
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

    def estimate_resources(
        self, params: dict[str, Any] | None = None,
    ) -> Any:
        """Build the QPE circuit and run resource estimation.

        Args:
            params: Optional estimator parameters.

        Returns:
            The resource estimation result.
        """
        return self.to_circuit().estimate(params=params)

    @staticmethod
    def energy_from_phase(
        phase: float, evolution_time: float,
    ) -> float:
        """Convert a measured phase to an energy eigenvalue.

        The QPE measures a phase ``phi`` such that
        ``exp(-i E t) = exp(2*pi*i*phi)``, giving
        ``E = -2*pi*phi / t``.

        Args:
            phase: Measured phase in [0, 1).
            evolution_time: The evolution time used in QPE.

        Returns:
            The corresponding energy in Hartree.
        """
        return -2.0 * math.pi * phase / evolution_time
