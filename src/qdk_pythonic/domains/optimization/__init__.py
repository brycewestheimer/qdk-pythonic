"""Combinatorial optimization problems and QAOA.

Example::

    from qdk_pythonic.domains.optimization import MaxCut, QAOA

    problem = MaxCut(edges=[(0,1), (1,2), (2,0)], n_nodes=3)
    qaoa = QAOA(problem.to_hamiltonian(), p=2)
    circuit = qaoa.to_circuit(gamma=[0.5, 0.3], beta=[0.7, 0.2])
"""

from qdk_pythonic.domains.optimization.mixer import x_mixer
from qdk_pythonic.domains.optimization.problem import (
    QUBO,
    TSP,
    MaxCut,
)
from qdk_pythonic.domains.optimization.qaoa import QAOA

__all__ = [
    "MaxCut",
    "QAOA",
    "QUBO",
    "TSP",
    "x_mixer",
]
