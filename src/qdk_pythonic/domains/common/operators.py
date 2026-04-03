"""Pauli operators and Hamiltonian representations.

Provides :class:`PauliTerm` and :class:`PauliHamiltonian` for building
quantum Hamiltonians from Pauli strings and converting them to Trotter
circuits.

Example::

    from qdk_pythonic.domains.common.operators import X, Y, Z, PauliHamiltonian

    H = PauliHamiltonian()
    H += -1.0 * Z(0) * Z(1)
    H += -0.5 * X(0)
    H += -0.5 * X(1)
    circuit = H.to_trotter_circuit(dt=0.1, steps=5)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit

_VALID_PAULIS = frozenset({"X", "Y", "Z"})


@dataclass(frozen=True)
class PauliTerm:
    """A single Pauli tensor product with a real coefficient.

    Qubits absent from *pauli_ops* are implicitly identity.

    Attributes:
        pauli_ops: Mapping from qubit index to Pauli label
            (``"X"``, ``"Y"``, or ``"Z"``).
        coeff: Real coefficient for this term.
    """

    pauli_ops: dict[int, str]
    coeff: complex = 1.0

    def __post_init__(self) -> None:
        for idx, op in self.pauli_ops.items():
            if op not in _VALID_PAULIS:
                raise ValueError(
                    f"Invalid Pauli operator '{op}' on qubit {idx}; "
                    f"must be one of {sorted(_VALID_PAULIS)}"
                )

    def __mul__(self, other: object) -> PauliTerm:
        """Tensor-product two terms or multiply by a scalar."""
        if isinstance(other, (int, float, complex)):
            return PauliTerm(
                pauli_ops=dict(self.pauli_ops),
                coeff=self.coeff * other,
            )
        if isinstance(other, PauliTerm):
            merged = dict(self.pauli_ops)
            for qi, op in other.pauli_ops.items():
                if qi in merged:
                    raise ValueError(
                        f"Overlapping qubit index {qi} in Pauli product"
                    )
                merged[qi] = op
            return PauliTerm(
                pauli_ops=merged,
                coeff=self.coeff * other.coeff,
            )
        return NotImplemented

    def __rmul__(self, other: object) -> PauliTerm:
        """Scalar multiplication from the left."""
        if isinstance(other, (int, float, complex)):
            return PauliTerm(
                pauli_ops=dict(self.pauli_ops),
                coeff=self.coeff * other,
            )
        return NotImplemented


def X(qubit: int) -> PauliTerm:  # noqa: N802
    """Create a single-qubit Pauli-X term."""
    return PauliTerm(pauli_ops={qubit: "X"})


def Y(qubit: int) -> PauliTerm:  # noqa: N802
    """Create a single-qubit Pauli-Y term."""
    return PauliTerm(pauli_ops={qubit: "Y"})


def Z(qubit: int) -> PauliTerm:  # noqa: N802
    """Create a single-qubit Pauli-Z term."""
    return PauliTerm(pauli_ops={qubit: "Z"})


class PauliHamiltonian:
    """A sum of Pauli tensor product terms.

    Supports incremental construction via ``+=`` and conversion to
    Trotter circuits for time evolution simulation.

    Example::

        H = PauliHamiltonian()
        H += -1.0 * Z(0) * Z(1)
        H += -0.5 * X(0)
        circuit = H.to_trotter_circuit(dt=0.1, steps=5)
    """

    def __init__(self, terms: list[PauliTerm] | None = None) -> None:
        self.terms: list[PauliTerm] = list(terms) if terms else []

    def __iadd__(self, other: PauliHamiltonian | PauliTerm) -> PauliHamiltonian:
        if isinstance(other, PauliTerm):
            self.terms.append(other)
        elif isinstance(other, PauliHamiltonian):
            self.terms.extend(other.terms)
        else:
            return NotImplemented
        return self

    def __add__(self, other: PauliHamiltonian | PauliTerm) -> PauliHamiltonian:
        result = PauliHamiltonian(list(self.terms))
        result += other
        return result

    def __len__(self) -> int:
        return len(self.terms)

    def __repr__(self) -> str:
        return f"PauliHamiltonian(n_terms={len(self.terms)})"

    def qubit_count(self) -> int:
        """Return the number of distinct qubits referenced."""
        indices: set[int] = set()
        for term in self.terms:
            indices.update(term.pauli_ops.keys())
        return len(indices)

    def qubit_indices(self) -> list[int]:
        """Return sorted list of qubit indices referenced."""
        indices: set[int] = set()
        for term in self.terms:
            indices.update(term.pauli_ops.keys())
        return sorted(indices)

    def to_trotter_circuit(
        self,
        dt: float,
        order: int = 1,
        steps: int = 1,
    ) -> Circuit:
        """Build a Trotterized time-evolution circuit.

        Approximates exp(-i H dt) via product formula decomposition.

        Args:
            dt: Time step per Trotter step.
            order: Trotter order (1 for first-order, 2 for second-order
                Suzuki-Trotter).
            steps: Number of Trotter steps.

        Returns:
            A Circuit approximating the time evolution.

        Raises:
            ValueError: If order is not 1 or 2.
        """
        if order not in (1, 2):
            raise ValueError(f"Trotter order must be 1 or 2, got {order}")

        from qdk_pythonic.core.circuit import Circuit

        all_indices = self.qubit_indices()
        n_qubits = max(all_indices) + 1 if all_indices else 0

        circ = Circuit()
        if n_qubits == 0:
            return circ

        q = circ.allocate(n_qubits)

        for _ in range(steps):
            if order == 1:
                for term in self.terms:
                    _apply_pauli_rotation(circ, q, term, dt)
            else:
                # Second-order Suzuki-Trotter: forward dt/2, reverse dt/2
                for term in self.terms:
                    _apply_pauli_rotation(circ, q, term, dt / 2)
                for term in reversed(self.terms):
                    _apply_pauli_rotation(circ, q, term, dt / 2)

        return circ

    @classmethod
    def from_ising(
        cls,
        edges: list[tuple[int, int]],
        n_qubits: int,
        J: float = 1.0,  # noqa: N803
        h: float = 0.5,
    ) -> PauliHamiltonian:
        """Build a transverse-field Ising Hamiltonian.

        H = -J sum_{(i,j)} Z_i Z_j  -  h sum_i X_i

        Args:
            edges: Pairs of interacting qubit indices.
            n_qubits: Total number of qubits (sites).
            J: ZZ coupling strength.
            h: Transverse field strength.
        """
        ham = cls()
        for i, j in edges:
            ham += PauliTerm(pauli_ops={i: "Z", j: "Z"}, coeff=-J)
        for i in range(n_qubits):
            ham += PauliTerm(pauli_ops={i: "X"}, coeff=-h)
        return ham

    @classmethod
    def from_heisenberg(
        cls,
        edges: list[tuple[int, int]],
        Jx: float = 1.0,  # noqa: N803
        Jy: float = 1.0,  # noqa: N803
        Jz: float = 1.0,  # noqa: N803
    ) -> PauliHamiltonian:
        """Build a Heisenberg XXZ Hamiltonian.

        H = sum_{(i,j)} [Jx X_i X_j + Jy Y_i Y_j + Jz Z_i Z_j]

        Args:
            edges: Pairs of interacting qubit indices.
            Jx: XX coupling strength.
            Jy: YY coupling strength.
            Jz: ZZ coupling strength.
        """
        ham = cls()
        for i, j in edges:
            if Jx != 0:
                ham += PauliTerm(pauli_ops={i: "X", j: "X"}, coeff=Jx)
            if Jy != 0:
                ham += PauliTerm(pauli_ops={i: "Y", j: "Y"}, coeff=Jy)
            if Jz != 0:
                ham += PauliTerm(pauli_ops={i: "Z", j: "Z"}, coeff=Jz)
        return ham


def _apply_pauli_rotation(
    circ: Circuit,
    qubits: object,
    term: PauliTerm,
    dt: float,
) -> None:
    """Apply exp(-i * coeff * dt * P) for a single Pauli term.

    Uses the standard diagonalize-CNOT-Rz-CNOT-undiagonalize decomposition
    for arbitrary Pauli strings.
    """
    if abs(term.coeff) < 1e-15:
        return

    if isinstance(term.coeff, complex) and abs(term.coeff.imag) > 1e-15:
        raise ValueError(
            f"Trotter evolution requires real coefficients, "
            f"got {term.coeff} for term on qubits "
            f"{sorted(term.pauli_ops.keys())}"
        )
    angle = 2.0 * term.coeff.real * dt
    sorted_qubits = sorted(term.pauli_ops.keys())

    if len(sorted_qubits) == 1:
        qi = sorted_qubits[0]
        op = term.pauli_ops[qi]
        q = qubits[qi]  # type: ignore[index]
        if op == "X":
            circ.rx(angle, q)
        elif op == "Y":
            circ.ry(angle, q)
        else:  # Z
            circ.rz(angle, q)
        return

    # Multi-qubit Pauli string: diagonalize -> CNOT ladder -> Rz -> undo
    # Step 1: Change basis (diagonalize non-Z paulis to Z)
    for qi in sorted_qubits:
        op = term.pauli_ops[qi]
        q = qubits[qi]  # type: ignore[index]
        if op == "X":
            circ.h(q)
        elif op == "Y":
            circ.rx(math.pi / 2, q)

    # Step 2: CNOT ladder
    for k in range(len(sorted_qubits) - 1):
        circ.cx(
            qubits[sorted_qubits[k]],  # type: ignore[index]
            qubits[sorted_qubits[k + 1]],  # type: ignore[index]
        )

    # Step 3: Rz on last qubit
    last_q = qubits[sorted_qubits[-1]]  # type: ignore[index]
    circ.rz(angle, last_q)

    # Step 4: Reverse CNOT ladder
    for k in range(len(sorted_qubits) - 2, -1, -1):
        circ.cx(
            qubits[sorted_qubits[k]],  # type: ignore[index]
            qubits[sorted_qubits[k + 1]],  # type: ignore[index]
        )

    # Step 5: Undo basis change
    for qi in sorted_qubits:
        op = term.pauli_ops[qi]
        q = qubits[qi]  # type: ignore[index]
        if op == "X":
            circ.h(q)
        elif op == "Y":
            circ.rx(-math.pi / 2, q)
