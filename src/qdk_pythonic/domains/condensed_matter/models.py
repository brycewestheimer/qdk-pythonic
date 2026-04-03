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

from qdk_pythonic.domains.common.fermion import (
    FermionOperator,
    hopping,
    number_operator,
)
from qdk_pythonic.domains.common.operators import PauliHamiltonian


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
    """Fermi-Hubbard model with configurable qubit mapping.

    H = -t sum_{<i,j>,s} (c^dag_is c_js + h.c.) + U sum_i n_i↑ n_i↓

    Uses 2N qubits for N lattice sites (N spin-up + N spin-down).
    Qubit ordering: sites 0..N-1 for spin-up, N..2N-1 for spin-down.

    Attributes:
        lattice: The lattice geometry.
        t: Hopping parameter.
        U: On-site interaction strength.
        mapping: Qubit mapping name (``"jordan_wigner"`` or
            ``"bravyi_kitaev"``).
    """

    lattice: Lattice
    t: float = 1.0
    U: float = 1.0
    mapping: str = "jordan_wigner"

    def to_fermion_operator(self) -> FermionOperator:
        """Build the second-quantized fermionic Hamiltonian.

        Uses 2N modes for N sites (N spin-up + N spin-down).
        Mode ordering: 0..N-1 for spin-up, N..2N-1 for spin-down.
        """
        n = self.lattice.num_sites
        op = FermionOperator()

        # Hopping: -t * (a†_is a_js + h.c.) for each edge, each spin
        for i, j in self.lattice.edges:
            for spin_offset in (0, n):
                op += hopping(
                    i + spin_offset, j + spin_offset, coeff=-self.t,
                )

        # On-site: U * n_i↑ n_i↓
        for i in range(n):
            n_up = number_operator(i)
            n_dn = number_operator(n + i)
            for t_up in n_up.terms:
                for t_dn in n_dn.terms:
                    op += t_up * t_dn * self.U

        return op

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert to a Pauli Hamiltonian via qubit mapping."""
        from qdk_pythonic.domains.common.mapping import (
            BravyiKitaevMapping,
            JordanWignerMapping,
        )

        fermion_op = self.to_fermion_operator()
        if self.mapping == "bravyi_kitaev":
            return BravyiKitaevMapping().map(fermion_op)
        return JordanWignerMapping().map(fermion_op)
