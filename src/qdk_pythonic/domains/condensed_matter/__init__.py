"""Condensed matter lattice models and simulation.

Example::

    from qdk_pythonic.domains.condensed_matter import (
        Chain, SquareLattice, IsingModel, HeisenbergModel,
    )

    model = IsingModel(Chain(10), J=1.0, h=0.5)
    circuit = model.to_hamiltonian().to_trotter_circuit(dt=0.1, steps=5)
"""

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

__all__ = [
    "Chain",
    "HeisenbergModel",
    "HexagonalLattice",
    "HubbardModel",
    "IsingModel",
    "SquareLattice",
    "simulate_dynamics",
]
