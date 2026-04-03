"""Unitary Coupled Cluster Singles and Doubles (UCCSD) ansatz.

Generates single and double excitation operators from the
Hartree-Fock reference, maps them to qubit operators, and
Trotterizes to build a variational circuit.

Example::

    from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz

    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    circuit = ansatz.to_circuit([0.1] * ansatz.num_parameters)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qdk_pythonic.domains.common import operators
from qdk_pythonic.domains.common.fermion import FermionOperator, FermionTerm
from qdk_pythonic.domains.common.mapping import (
    BravyiKitaevMapping,
    JordanWignerMapping,
)
from qdk_pythonic.exceptions import CircuitError

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class UCCSDAnsatz:
    """Unitary Coupled Cluster Singles and Doubles ansatz.

    Builds a variational circuit of the form:

        |HF> -> prod_k exp(theta_k (T_k - T_k^dag)) |HF>

    where T_k are single and double excitation operators.

    Attributes:
        n_spatial_orbitals: Number of spatial orbitals.
        n_electrons: Number of electrons.
        mapping: Qubit mapping (``"jordan_wigner"`` or
            ``"bravyi_kitaev"``).
        include_singles: Include single excitations.
        include_doubles: Include double excitations.
    """

    n_spatial_orbitals: int
    n_electrons: int
    mapping: str = "jordan_wigner"
    include_singles: bool = True
    include_doubles: bool = True

    def __post_init__(self) -> None:
        if self.n_spatial_orbitals < 1:
            raise CircuitError(
                f"n_spatial_orbitals must be >= 1, "
                f"got {self.n_spatial_orbitals}"
            )
        if self.n_electrons < 0:
            raise CircuitError(
                f"n_electrons must be >= 0, got {self.n_electrons}"
            )
        if self.n_electrons > 2 * self.n_spatial_orbitals:
            raise CircuitError(
                f"n_electrons ({self.n_electrons}) cannot exceed "
                f"2 * n_spatial_orbitals ({2 * self.n_spatial_orbitals})"
            )
        if self.mapping not in ("jordan_wigner", "bravyi_kitaev"):
            raise CircuitError(
                f"Unknown mapping '{self.mapping}'"
            )

    @property
    def n_qubits(self) -> int:
        """Number of qubits (spin-orbitals)."""
        return 2 * self.n_spatial_orbitals

    def singles(self) -> list[tuple[int, int]]:
        """Enumerate single excitation pairs (occupied, virtual).

        Spin-orbital indexing: spatial orbital *p* maps to
        spin-orbitals ``2*p`` (alpha) and ``2*p + 1`` (beta).
        Excitations preserve spin.

        Returns:
            List of (i, a) pairs where i is occupied, a is virtual.
        """
        n_so = self.n_qubits
        occupied = list(range(self.n_electrons))
        virtual = list(range(self.n_electrons, n_so))
        pairs: list[tuple[int, int]] = []
        for i in occupied:
            for a in virtual:
                # Preserve spin: alpha->alpha, beta->beta
                if i % 2 == a % 2:
                    pairs.append((i, a))
        return pairs

    def doubles(self) -> list[tuple[int, int, int, int]]:
        """Enumerate double excitation quadruples.

        Returns:
            List of (i, j, a, b) tuples where i<j are occupied
            and a<b are virtual spin-orbitals with matching spin.
        """
        n_so = self.n_qubits
        occupied = list(range(self.n_electrons))
        virtual = list(range(self.n_electrons, n_so))
        quads: list[tuple[int, int, int, int]] = []
        for idx_i, i in enumerate(occupied):
            for j in occupied[idx_i + 1:]:
                for idx_a, a in enumerate(virtual):
                    for b in virtual[idx_a + 1:]:
                        # Spin conservation: total spin of (i,j)
                        # must equal total spin of (a,b)
                        spin_occ = (i % 2) + (j % 2)
                        spin_virt = (a % 2) + (b % 2)
                        if spin_occ == spin_virt:
                            quads.append((i, j, a, b))
        return quads

    @property
    def num_parameters(self) -> int:
        """Total number of variational parameters."""
        count = 0
        if self.include_singles:
            count += len(self.singles())
        if self.include_doubles:
            count += len(self.doubles())
        return count

    def excitation_operators(self) -> list[FermionOperator]:
        """Build the anti-Hermitian excitation generators.

        For each excitation, returns ``T_k - T_k^dag`` as a
        FermionOperator.

        Returns:
            List of FermionOperator generators, one per parameter.
        """
        generators: list[FermionOperator] = []

        if self.include_singles:
            for i, a in self.singles():
                # T = a†_a a_i
                t_term = FermionTerm(
                    operators=((a, True), (i, False)), coeff=1.0,
                )
                # T† = a†_i a_a
                t_dag = FermionTerm(
                    operators=((i, True), (a, False)), coeff=-1.0,
                )
                generators.append(FermionOperator([t_term, t_dag]))

        if self.include_doubles:
            for i, j, a, b in self.doubles():
                # T = a†_a a†_b a_j a_i
                t_term = FermionTerm(
                    operators=(
                        (a, True), (b, True), (j, False), (i, False),
                    ),
                    coeff=1.0,
                )
                # T† = a†_i a†_j a_b a_a
                t_dag = FermionTerm(
                    operators=(
                        (i, True), (j, True), (b, False), (a, False),
                    ),
                    coeff=-1.0,
                )
                generators.append(FermionOperator([t_term, t_dag]))

        return generators

    def to_circuit(self, params: Sequence[float]) -> Circuit:
        """Build the UCCSD circuit with given amplitudes.

        The circuit prepends the Hartree-Fock state, then applies
        Trotterized excitation rotations.

        Args:
            params: Variational parameters, one per excitation.
                Length must equal :attr:`num_parameters`.

        Returns:
            The parameterized UCCSD circuit.

        Raises:
            CircuitError: If *params* has the wrong length.
        """
        from qdk_pythonic.core.circuit import Circuit
        from qdk_pythonic.domains.chemistry.hartree_fock import (
            HartreeFockState,
        )

        expected = self.num_parameters
        if len(params) != expected:
            raise CircuitError(
                f"Expected {expected} parameters, got {len(params)}"
            )

        n_q = self.n_qubits

        # Map excitation generators to Pauli Hamiltonians
        mapper: JordanWignerMapping | BravyiKitaevMapping
        if self.mapping == "bravyi_kitaev":
            mapper = BravyiKitaevMapping()
        else:
            mapper = JordanWignerMapping()

        generators = self.excitation_operators()

        # Start with HF state
        hf = HartreeFockState(
            n_qubits=n_q,
            n_electrons=self.n_electrons,
            mapping=self.mapping,
        )
        circ = Circuit()
        q = circ.allocate(n_q)

        # Compose HF state preparation
        hf_circ = hf.to_circuit()
        hf_map = {
            src.index: q[i]
            for i, src in enumerate(hf_circ.qubits)
        }
        circ.compose_into(hf_circ, qubit_map=hf_map)

        # Apply each excitation as a Trotter rotation.
        #
        # The JW/BK-mapped generator G has imaginary Pauli coefficients
        # (because G = T - T† is anti-Hermitian). We want exp(theta * G).
        #
        # to_trotter_circuit(dt) computes exp(-i * H * dt) with real H.
        # If G = sum_k (i * r_k) P_k, then exp(theta * G) =
        # exp(-i * sum_k (-r_k) P_k * theta), so we build H with
        # real coefficients -Im(c_k) and use dt=theta.
        for theta, gen in zip(params, generators):
            if abs(theta) < 1e-15:
                continue
            pauli_gen = mapper.map(gen)
            # Convert imaginary coefficients to real Hamiltonian
            real_ham = _to_real_hamiltonian(pauli_gen)
            trotter_circ = real_ham.to_trotter_circuit(
                dt=theta, order=1, steps=1,
            )
            if trotter_circ.qubit_count() == 0:
                continue
            # Map trotter circuit qubits into our register
            trotter_map = {
                src.index: q[src.index]
                for src in trotter_circ.qubits
                if src.index < n_q
            }
            circ.compose_into(trotter_circ, qubit_map=trotter_map)

        return circ


def _to_real_hamiltonian(
    pauli_ham: operators.PauliHamiltonian,
) -> operators.PauliHamiltonian:
    """Convert an anti-Hermitian Pauli operator to a real Hamiltonian.

    For an operator ``G = sum_k c_k P_k`` with purely imaginary
    coefficients ``c_k = i * r_k``, returns ``H = sum_k (-r_k) P_k``
    so that ``exp(theta * G) = exp(-i * H * theta)``.

    Real parts of coefficients are kept as-is.
    """
    real_terms: list[operators.PauliTerm] = []
    for term in pauli_ham.terms:
        # For c_k = i*b_k: exp(theta * i*b_k * P) = exp(-i*(-b_k)*theta*P)
        # So the real Hamiltonian coefficient is -Im(c_k).
        real_coeff = -term.coeff.imag
        if abs(real_coeff) < 1e-15:
            continue
        real_terms.append(operators.PauliTerm(
            pauli_ops=dict(term.pauli_ops),
            coeff=real_coeff,
        ))
    return operators.PauliHamiltonian(real_terms)
