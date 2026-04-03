"""Second-quantized fermionic operators.

Provides :class:`FermionTerm` and :class:`FermionOperator` for
representing fermionic Hamiltonians before qubit mapping.

Example::

    from qdk_pythonic.domains.common.fermion import (
        creation, annihilation, number_operator, hopping,
    )

    # Build a two-site Hubbard hopping term
    op = hopping(0, 1, coeff=-1.0)

    # Map to qubits
    from qdk_pythonic.domains.common.mapping import jordan_wigner
    pauli_h = jordan_wigner(op)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FermionTerm:
    """A product of fermionic creation/annihilation operators.

    Attributes:
        operators: Sequence of (mode_index, is_creation) pairs,
            ordered left to right. ``(3, True)`` means a-dagger_3.
        coeff: Complex coefficient.
    """

    operators: tuple[tuple[int, bool], ...]
    coeff: complex = 1.0

    def __mul__(self, other: object) -> FermionTerm:
        """Concatenate operators or multiply by a scalar."""
        if isinstance(other, (int, float, complex)):
            return FermionTerm(
                operators=self.operators,
                coeff=self.coeff * other,
            )
        if isinstance(other, FermionTerm):
            return FermionTerm(
                operators=self.operators + other.operators,
                coeff=self.coeff * other.coeff,
            )
        return NotImplemented

    def __rmul__(self, other: object) -> FermionTerm:
        """Scalar multiplication from the left."""
        if isinstance(other, (int, float, complex)):
            return FermionTerm(
                operators=self.operators,
                coeff=self.coeff * other,
            )
        return NotImplemented

    @property
    def num_modes(self) -> int:
        """Minimum number of modes to represent this term."""
        if not self.operators:
            return 0
        return max(idx for idx, _ in self.operators) + 1

    def adjoint(self) -> FermionTerm:
        """Return the Hermitian conjugate.

        Reverses operator order, flips creation/annihilation,
        and conjugates the coefficient.
        """
        adj_ops = tuple(
            (idx, not is_creation)
            for idx, is_creation in reversed(self.operators)
        )
        return FermionTerm(
            operators=adj_ops,
            coeff=self.coeff.conjugate(),
        )


class FermionOperator:
    """A sum of fermionic operator products.

    Supports incremental construction via ``+=`` and conversion
    to qubit operators via a :class:`QubitMapping`.
    """

    def __init__(self, terms: list[FermionTerm] | None = None) -> None:
        self.terms: list[FermionTerm] = list(terms) if terms else []

    def __iadd__(
        self, other: FermionOperator | FermionTerm,
    ) -> FermionOperator:
        if isinstance(other, FermionTerm):
            self.terms.append(other)
        elif isinstance(other, FermionOperator):
            self.terms.extend(other.terms)
        else:
            return NotImplemented
        return self

    def __add__(
        self, other: FermionOperator | FermionTerm,
    ) -> FermionOperator:
        result = FermionOperator(list(self.terms))
        result += other
        return result

    def __len__(self) -> int:
        return len(self.terms)

    def __repr__(self) -> str:
        return f"FermionOperator(n_terms={len(self.terms)})"

    @property
    def num_modes(self) -> int:
        """Minimum number of modes across all terms."""
        if not self.terms:
            return 0
        return max(t.num_modes for t in self.terms)

    def adjoint(self) -> FermionOperator:
        """Return the Hermitian conjugate of the full operator."""
        return FermionOperator([t.adjoint() for t in self.terms])


# ── Builder functions ──


def creation(mode: int) -> FermionTerm:
    """Create a single creation operator a-dagger on *mode*."""
    return FermionTerm(operators=((mode, True),))


def annihilation(mode: int) -> FermionTerm:
    """Create a single annihilation operator a on *mode*."""
    return FermionTerm(operators=((mode, False),))


def number_operator(mode: int) -> FermionOperator:
    """Return the number operator n = a-dagger a on *mode*."""
    return FermionOperator([
        FermionTerm(operators=((mode, True), (mode, False))),
    ])


def hopping(
    i: int, j: int, coeff: complex = -1.0,
) -> FermionOperator:
    """Return a Hermitian hopping term.

    ``coeff * a†_i a_j + conj(coeff) * a†_j a_i``
    """
    return FermionOperator([
        FermionTerm(operators=((i, True), (j, False)), coeff=coeff),
        FermionTerm(
            operators=((j, True), (i, False)),
            coeff=coeff.conjugate() if isinstance(coeff, complex) else coeff,
        ),
    ])


def from_integrals(
    h1e: Any,
    h2e: Any,
    nuclear_repulsion: float = 0.0,
) -> FermionOperator:
    """Build a molecular Hamiltonian from electron integrals.

    Args:
        h1e: One-electron integrals, shape (n, n), MO basis.
        h2e: Two-electron integrals, shape (n, n, n, n),
            **physicist** notation: h2e[p,q,r,s] = <pq|rs>.
        nuclear_repulsion: Scalar nuclear repulsion energy,
            stored as a constant (identity) term.

    Returns:
        FermionOperator representing the electronic Hamiltonian.
    """
    n = len(h1e)
    op = FermionOperator()

    # One-body: Σ_{pq} h1e[p,q] a†_p a_q
    for p in range(n):
        for q in range(n):
            c = complex(h1e[p][q])
            if abs(c) < 1e-15:
                continue
            op += FermionTerm(
                operators=((p, True), (q, False)), coeff=c,
            )

    # Two-body: 0.5 * Σ_{pqrs} h2e[p,q,r,s] a†_p a†_q a_s a_r
    for p in range(n):
        for q in range(n):
            for r in range(n):
                for s in range(n):
                    c = 0.5 * complex(h2e[p][q][r][s])
                    if abs(c) < 1e-15:
                        continue
                    op += FermionTerm(
                        operators=(
                            (p, True), (q, True), (s, False), (r, False),
                        ),
                        coeff=c,
                    )

    # Nuclear repulsion as an empty-operator (identity) term
    if abs(nuclear_repulsion) > 1e-15:
        op += FermionTerm(operators=(), coeff=nuclear_repulsion)

    return op
