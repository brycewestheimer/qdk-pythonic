"""Linear Combination of Unitaries (LCU) and qubitization.

Gate-level implementations of PREPARE, SELECT, and walk operator
circuits for qubitization-based Hamiltonian simulation.

Suitable for small systems (< ~16 Hamiltonian terms) where
explicit circuit construction is practical. For production-scale
resource estimation, use the qsharp.chemistry bridge instead.

Example::

    from qdk_pythonic.domains.common.operators import PauliHamiltonian, Z, X
    from qdk_pythonic.domains.common.lcu import QubitizationQPE

    H = PauliHamiltonian()
    H += -1.0 * Z(0) * Z(1)
    H += -0.5 * X(0)

    qpe = QubitizationQPE(hamiltonian=H, n_electrons=1, n_estimation_qubits=4)
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
class PrepareOracle:
    """Encodes Hamiltonian coefficients into an ancilla register.

    Given ``H = sum_k alpha_k P_k`` with ``lambda = sum |alpha_k|``,
    PREPARE produces:

        |0> -> sum_k sqrt(|alpha_k| / lambda) |k>

    Uses ``ceil(log2(n_terms))`` ancilla qubits.

    Attributes:
        hamiltonian: Source PauliHamiltonian.
    """

    hamiltonian: PauliHamiltonian

    @property
    def n_terms(self) -> int:
        """Number of Hamiltonian terms."""
        return len(self.hamiltonian.terms)

    @property
    def n_ancilla_qubits(self) -> int:
        """Ancilla qubits needed: ceil(log2(n_terms)), minimum 1."""
        if self.n_terms <= 1:
            return 1
        return math.ceil(math.log2(self.n_terms))

    def to_circuit(self) -> Circuit:
        """Build the PREPARE circuit.

        Uses amplitude-encoding rotations (tree of controlled-Ry)
        to load the coefficient distribution into ancilla qubits.

        Returns:
            A circuit on ``n_ancilla_qubits`` qubits.
        """
        from qdk_pythonic.core.circuit import Circuit
        from qdk_pythonic.domains.common.states import (
            DiscreteProbabilityDistribution,
        )

        n_a = self.n_ancilla_qubits
        n_bins = 2 ** n_a

        # Compute normalized probabilities
        coeffs = [abs(t.coeff) for t in self.hamiltonian.terms]
        total = sum(coeffs)
        if total < 1e-15:
            circ = Circuit()
            circ.allocate(n_a, label="anc")
            return circ

        probs = [c / total for c in coeffs]
        # Pad to power of 2
        probs += [0.0] * (n_bins - len(probs))

        # Use the existing state preparation machinery
        dist = DiscreteProbabilityDistribution(
            probabilities=tuple(probs),
        )
        return dist.to_circuit()


@dataclass(frozen=True)
class SelectOracle:
    """Applies Pauli unitaries conditioned on ancilla state.

    SELECT |k>|psi> = |k> P_k |psi>

    For each Pauli term P_k, decodes the ancilla state |k> and
    applies the corresponding Pauli gates to the system register.

    Attributes:
        hamiltonian: Source PauliHamiltonian.
    """

    hamiltonian: PauliHamiltonian

    @property
    def n_system_qubits(self) -> int:
        """System qubits from the Hamiltonian."""
        indices = self.hamiltonian.qubit_indices()
        return (max(indices) + 1) if indices else 0

    @property
    def n_ancilla_qubits(self) -> int:
        """Ancilla qubits: ceil(log2(n_terms)), minimum 1."""
        n = len(self.hamiltonian.terms)
        if n <= 1:
            return 1
        return math.ceil(math.log2(n))

    def to_circuit(self) -> Circuit:
        """Build the SELECT circuit.

        For each term k, applies X/Y/Z gates to system qubits
        controlled on the ancilla encoding |k>.

        Returns:
            A circuit on (n_ancilla + n_system) qubits.
        """
        from qdk_pythonic.core.circuit import Circuit

        n_sys = self.n_system_qubits
        n_anc = self.n_ancilla_qubits

        circ = Circuit()
        sys_q = circ.allocate(n_sys, label="sys")
        anc_q = circ.allocate(n_anc, label="anc")

        for k, term in enumerate(self.hamiltonian.terms):
            if not term.pauli_ops:
                continue  # Identity -- no gates needed

            # Encode k in binary; flip ancilla bits that should be |0>
            bits = format(k, f"0{n_anc}b")
            flip_indices: list[int] = []
            for b, bit in enumerate(reversed(bits)):
                if bit == "0":
                    flip_indices.append(b)
                    circ.x(anc_q[b])

            # Apply multi-controlled Pauli gates
            controls = [anc_q[b] for b in range(n_anc)]
            for qi, pauli in sorted(term.pauli_ops.items()):
                if qi >= n_sys:
                    continue
                if pauli == "X":
                    circ.controlled(circ.x, controls, sys_q[qi])
                elif pauli == "Y":
                    circ.controlled(circ.y, controls, sys_q[qi])
                elif pauli == "Z":
                    circ.controlled(circ.z, controls, sys_q[qi])

            # Undo ancilla flips
            for b in flip_indices:
                circ.x(anc_q[b])

        return circ


@dataclass(frozen=True)
class QubitizationWalkOperator:
    """Walk operator for qubitization.

    W = REFLECT_ancilla . PREPARE† . SELECT . PREPARE

    The eigenvalues of W encode ``arcsin(E_k / lambda)`` where
    E_k are Hamiltonian eigenvalues and lambda is the 1-norm.

    Attributes:
        hamiltonian: Source PauliHamiltonian.
    """

    hamiltonian: PauliHamiltonian

    @property
    def n_system_qubits(self) -> int:
        """System qubits from the Hamiltonian."""
        indices = self.hamiltonian.qubit_indices()
        return (max(indices) + 1) if indices else 0

    @property
    def n_ancilla_qubits(self) -> int:
        """Ancilla qubits for the coefficient encoding."""
        n = len(self.hamiltonian.terms)
        if n <= 1:
            return 1
        return math.ceil(math.log2(n))

    def to_circuit(self) -> Circuit:
        """Build one step of the walk operator.

        Structure: PREPARE -> SELECT -> PREPARE† -> REFLECT

        Returns:
            A circuit on (n_system + n_ancilla) qubits.
        """
        from qdk_pythonic.core.circuit import Circuit, remap_instruction

        n_sys = self.n_system_qubits
        n_anc = self.n_ancilla_qubits

        circ = Circuit()
        sys_q = circ.allocate(n_sys, label="sys")
        anc_q = circ.allocate(n_anc, label="anc")

        # PREPARE on ancilla
        prepare = PrepareOracle(self.hamiltonian)
        prep_circ = prepare.to_circuit()
        prep_map = {
            src.index: anc_q[i]
            for i, src in enumerate(prep_circ.qubits)
        }
        circ.compose_into(prep_circ, qubit_map=prep_map)

        # SELECT on (ancilla, system)
        select = SelectOracle(self.hamiltonian)
        select_circ = select.to_circuit()
        # Map select circuit: first n_sys qubits -> sys, next n_anc -> anc
        select_map: dict[int, Any] = {}
        select_qubits = list(select_circ.qubits)
        for i in range(min(n_sys, len(select_qubits))):
            select_map[select_qubits[i].index] = sys_q[i]
        for i in range(min(n_anc, len(select_qubits) - n_sys)):
            select_map[select_qubits[n_sys + i].index] = anc_q[i]
        circ.compose_into(select_circ, qubit_map=select_map)

        # PREPARE† on ancilla (adjoint of each instruction, reversed)
        for inst in reversed(list(prep_circ.instructions)):
            remapped = remap_instruction(inst, prep_map)
            if isinstance(remapped, Instruction):
                adj = dataclasses.replace(
                    remapped, is_adjoint=not remapped.is_adjoint,
                )
                circ._instructions.append(adj)

        # REFLECT = I - 2|0><0| on ancilla
        # Multi-controlled Z on all ancilla qubits
        if n_anc == 1:
            circ.z(anc_q[0])
        else:
            # Apply X to all ancilla, then multi-controlled Z, then X
            for i in range(n_anc):
                circ.x(anc_q[i])
            controls = [anc_q[i] for i in range(n_anc - 1)]
            circ.controlled(circ.z, controls, anc_q[n_anc - 1])
            for i in range(n_anc):
                circ.x(anc_q[i])

        return circ


@dataclass(frozen=True)
class QubitizationQPE:
    """QPE on the qubitization walk operator.

    Combines the walk operator with phase estimation to extract
    Hamiltonian eigenvalues. The energy is related to the phase
    via ``E = lambda * sin(2*pi*phi - pi/2)``.

    Attributes:
        hamiltonian: Source PauliHamiltonian.
        n_electrons: Number of electrons (for HF initial state).
        n_estimation_qubits: Number of phase estimation qubits.
    """

    hamiltonian: PauliHamiltonian
    n_electrons: int
    n_estimation_qubits: int = 8

    def __post_init__(self) -> None:
        if self.n_estimation_qubits < 1:
            raise CircuitError(
                f"n_estimation_qubits must be >= 1, "
                f"got {self.n_estimation_qubits}"
            )
        if self.n_electrons < 0:
            raise CircuitError(
                f"n_electrons must be >= 0, "
                f"got {self.n_electrons}"
            )

    def to_circuit(self) -> Circuit:
        """Build the full qubitization QPE circuit.

        Structure:
        1. HF state on system register
        2. Hadamard on estimation register
        3. Controlled walk^(2^k) for each estimation qubit k
        4. Inverse QFT on estimation register

        Returns:
            The QPE circuit with system, ancilla, and estimation
            registers.
        """
        from qdk_pythonic.builders import inverse_qft
        from qdk_pythonic.core.circuit import Circuit, remap_instruction
        from qdk_pythonic.domains.chemistry.hartree_fock import (
            HartreeFockState,
        )

        walk = QubitizationWalkOperator(self.hamiltonian)
        n_sys = walk.n_system_qubits
        n_anc = walk.n_ancilla_qubits
        m = self.n_estimation_qubits

        if n_sys == 0:
            raise CircuitError("Hamiltonian has no qubit terms")

        circ = Circuit()
        sys_q = circ.allocate(n_sys, label="sys")
        anc_q = circ.allocate(n_anc, label="anc")
        est_q = circ.allocate(m, label="est")

        # 1. HF state on system register
        hf = HartreeFockState(n_qubits=n_sys, n_electrons=self.n_electrons)
        hf_circ = hf.to_circuit()
        hf_map = {
            src.index: sys_q[i]
            for i, src in enumerate(hf_circ.qubits)
        }
        circ.compose_into(hf_circ, qubit_map=hf_map)

        # 2. Hadamard on estimation register
        for i in range(m):
            circ.h(est_q[i])

        # 3. Controlled walk^(2^k)
        walk_circ = walk.to_circuit()
        walk_qubits = list(walk_circ.qubits)
        walk_map: dict[int, Any] = {}
        for i in range(min(n_sys, len(walk_qubits))):
            walk_map[walk_qubits[i].index] = sys_q[i]
        for i in range(min(n_anc, len(walk_qubits) - n_sys)):
            walk_map[walk_qubits[n_sys + i].index] = anc_q[i]

        for k in range(m):
            power = 2 ** k
            for _ in range(power):
                for inst in walk_circ.instructions:
                    remapped = remap_instruction(inst, walk_map)
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
        phase: float, one_norm: float,
    ) -> float:
        """Convert a measured phase to an energy eigenvalue.

        The qubitization walk operator has eigenphases related
        to energies by ``E = lambda * sin(2*pi*phi - pi/2)``.

        Args:
            phase: Measured phase in [0, 1).
            one_norm: The Hamiltonian 1-norm (lambda).

        Returns:
            The corresponding energy in Hartree.
        """
        return one_norm * math.sin(2.0 * math.pi * phase - math.pi / 2)
