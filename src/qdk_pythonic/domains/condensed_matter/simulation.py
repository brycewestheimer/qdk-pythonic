"""Convenience functions for condensed matter simulations.

Example::

    from qdk_pythonic.domains.condensed_matter import (
        Chain, IsingModel, simulate_dynamics,
    )

    circuit = simulate_dynamics(
        IsingModel(Chain(10), J=1.0, h=0.5),
        time=1.0, steps=10,
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qdk_pythonic.domains.common.evolution import TrotterEvolution
from qdk_pythonic.domains.condensed_matter.models import (
    HeisenbergModel,
    IsingModel,
)

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


def simulate_dynamics(
    model: IsingModel | HeisenbergModel,
    time: float,
    steps: int = 10,
    order: int = 1,
) -> Circuit:
    """Build a Trotter circuit simulating time evolution of a model.

    Convenience function chaining model -> hamiltonian -> TrotterEvolution
    -> circuit.

    Args:
        model: A condensed matter model with ``to_hamiltonian()``.
        time: Total evolution time.
        steps: Number of Trotter steps.
        order: Trotter order (1 or 2).

    Returns:
        The time-evolution circuit.
    """
    ham = model.to_hamiltonian()
    evo = TrotterEvolution(
        hamiltonian=ham, time=time, steps=steps, order=order,
    )
    return evo.to_circuit()
