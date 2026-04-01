"""Condensed matter spin models.

Each model produces a :class:`PauliHamiltonian` from a lattice geometry.

Example::

    from qdk_pythonic.domains.condensed_matter.lattice import SquareLattice
    from qdk_pythonic.domains.condensed_matter.models import IsingModel

    model = IsingModel(SquareLattice(4, 4), J=1.0, h=0.5)
    hamiltonian = model.to_hamiltonian()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm


@runtime_checkable
class Lattice(Protocol):
    """Protocol for lattice geometries."""

    @property
    def num_sites(self) -> int: ...

    @property
    def edges(self) -> list[tuple[int, int]]: ...


@dataclass(frozen=True)
class IsingModel:
    """Transverse-field Ising model on an arbitrary lattice.

    H = -J sum_{<i,j>} Z_i Z_j  -  h sum_i X_i

    Attributes:
        lattice: The lattice geometry.
        J: ZZ coupling strength.
        h: Transverse field strength.
    """

    lattice: Lattice
    J: float = 1.0
    h: float = 0.5

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert to a Pauli Hamiltonian."""
        return PauliHamiltonian.from_ising(
            edges=self.lattice.edges,
            n_qubits=self.lattice.num_sites,
            J=self.J,
            h=self.h,
        )


@dataclass(frozen=True)
class HeisenbergModel:
    """Heisenberg XXZ model on an arbitrary lattice.

    H = sum_{<i,j>} [Jx X_i X_j + Jy Y_i Y_j + Jz Z_i Z_j]

    Attributes:
        lattice: The lattice geometry.
        Jx: XX coupling strength.
        Jy: YY coupling strength.
        Jz: ZZ coupling strength.
    """

    lattice: Lattice
    Jx: float = 1.0
    Jy: float = 1.0
    Jz: float = 1.0

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert to a Pauli Hamiltonian."""
        return PauliHamiltonian.from_heisenberg(
            edges=self.lattice.edges,
            Jx=self.Jx,
            Jy=self.Jy,
            Jz=self.Jz,
        )


@dataclass(frozen=True)
class HubbardModel:
    """Fermi-Hubbard model with Jordan-Wigner mapping.

    H = -t sum_{<i,j>,s} (c^dag_is c_js + h.c.) + U sum_i n_i↑ n_i↓

    Uses 2N qubits for N lattice sites (N spin-up + N spin-down).
    Qubit ordering: sites 0..N-1 for spin-up, N..2N-1 for spin-down.

    Attributes:
        lattice: The lattice geometry.
        t: Hopping parameter.
        U: On-site interaction strength.
    """

    lattice: Lattice
    t: float = 1.0
    U: float = 1.0

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert to a Pauli Hamiltonian via Jordan-Wigner transform.

        The hopping term ``c†_i c_j + h.c.`` maps to
        ``0.5 * (X_i X_j + Y_i Y_j) * Z_{i+1} ... Z_{j-1}``
        under JW ordering (for i < j). The on-site interaction
        ``n_i↑ n_i↓`` maps to Z-terms on the two spin qubits.
        """
        n = self.lattice.num_sites
        ham = PauliHamiltonian()

        # Hopping: -t * (c†_is c_js + h.c.) for each edge, each spin
        for i, j in self.lattice.edges:
            lo, hi = min(i, j), max(i, j)
            for spin_offset in (0, n):
                qi = lo + spin_offset
                qj = hi + spin_offset
                # JW string: Z on all qubits between qi and qj
                jw_ops: dict[int, str] = {}
                for k in range(qi + 1, qj):
                    jw_ops[k] = "Z"
                # XX term
                xx_ops = dict(jw_ops)
                xx_ops[qi] = "X"
                xx_ops[qj] = "X"
                ham += PauliTerm(pauli_ops=xx_ops, coeff=-self.t / 2)
                # YY term
                yy_ops = dict(jw_ops)
                yy_ops[qi] = "Y"
                yy_ops[qj] = "Y"
                ham += PauliTerm(pauli_ops=yy_ops, coeff=-self.t / 2)

        # On-site: U * n_i↑ n_i↓
        # n_is = (I - Z_is) / 2, product expands to Z-terms
        for i in range(n):
            qi_up = i
            qi_dn = n + i
            ham += PauliTerm(
                pauli_ops={qi_up: "Z", qi_dn: "Z"}, coeff=self.U / 4,
            )
            ham += PauliTerm(pauli_ops={qi_up: "Z"}, coeff=-self.U / 4)
            ham += PauliTerm(pauli_ops={qi_dn: "Z"}, coeff=-self.U / 4)

        return ham
