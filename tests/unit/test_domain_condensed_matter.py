"""Tests for condensed matter lattices, models, and simulation."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.condensed_matter.lattice import (
    Chain,
    HexagonalLattice,
    SquareLattice,
)
from qdk_pythonic.domains.condensed_matter.models import (
    HeisenbergModel,
    HubbardModel,
    IsingModel,
)
from qdk_pythonic.domains.condensed_matter.simulation import simulate_dynamics

# ------------------------------------------------------------------
# Lattice tests
# ------------------------------------------------------------------


@pytest.mark.unit
def test_chain_open() -> None:
    c = Chain(4)
    assert c.num_sites == 4
    assert c.edges == [(0, 1), (1, 2), (2, 3)]


@pytest.mark.unit
def test_chain_periodic() -> None:
    c = Chain(4, periodic=True)
    assert len(c.edges) == 4
    assert (3, 0) in c.edges


@pytest.mark.unit
def test_chain_too_small_raises() -> None:
    with pytest.raises(ValueError, match="n >= 2"):
        Chain(1)


@pytest.mark.unit
def test_square_lattice_2x2() -> None:
    sq = SquareLattice(2, 2)
    assert sq.num_sites == 4
    # 2x2 grid has 4 edges: (0,1), (0,2), (1,3), (2,3)
    assert len(sq.edges) == 4


@pytest.mark.unit
def test_square_lattice_3x3() -> None:
    sq = SquareLattice(3, 3)
    assert sq.num_sites == 9
    # 3x3: 6 horizontal + 6 vertical = 12 edges
    assert len(sq.edges) == 12


@pytest.mark.unit
def test_square_lattice_invalid() -> None:
    with pytest.raises(ValueError, match="rows >= 1"):
        SquareLattice(0, 3)


@pytest.mark.unit
def test_hexagonal_lattice_2x2() -> None:
    h = HexagonalLattice(2, 2)
    assert h.num_sites == 8
    assert len(h.edges) > 0


@pytest.mark.unit
def test_hexagonal_lattice_invalid() -> None:
    with pytest.raises(ValueError, match="rows >= 1"):
        HexagonalLattice(0, 1)


# ------------------------------------------------------------------
# Model tests
# ------------------------------------------------------------------


@pytest.mark.unit
def test_ising_chain_hamiltonian() -> None:
    model = IsingModel(Chain(4), J=1.0, h=0.5)
    ham = model.to_hamiltonian()
    # 3 ZZ terms + 4 X terms = 7
    assert len(ham) == 7
    assert ham.qubit_count() == 4


@pytest.mark.unit
def test_ising_square_lattice() -> None:
    model = IsingModel(SquareLattice(2, 2), J=1.0, h=0.5)
    ham = model.to_hamiltonian()
    # 4 edges -> 4 ZZ terms + 4 X terms = 8
    assert len(ham) == 8


@pytest.mark.unit
def test_heisenberg_chain() -> None:
    model = HeisenbergModel(Chain(3))
    ham = model.to_hamiltonian()
    # 2 edges * 3 (XX, YY, ZZ) = 6 terms
    assert len(ham) == 6
    assert ham.qubit_count() == 3


@pytest.mark.unit
def test_hubbard_not_implemented() -> None:
    model = HubbardModel(Chain(4))
    with pytest.raises(NotImplementedError, match="Jordan-Wigner"):
        model.to_hamiltonian()


# ------------------------------------------------------------------
# Simulation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_simulate_dynamics_ising() -> None:
    circ = simulate_dynamics(
        IsingModel(Chain(4), J=1.0, h=0.5),
        time=1.0,
        steps=5,
    )
    assert circ.qubit_count() == 4
    assert circ.total_gate_count() > 0


@pytest.mark.unit
def test_simulate_dynamics_heisenberg() -> None:
    circ = simulate_dynamics(
        HeisenbergModel(Chain(3), Jx=1.0, Jy=1.0, Jz=1.0),
        time=0.5,
        steps=2,
    )
    assert circ.qubit_count() == 3
    assert circ.total_gate_count() > 0
