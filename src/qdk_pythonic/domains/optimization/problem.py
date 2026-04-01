"""Combinatorial optimization problem definitions.

Each problem class converts to a :class:`PauliHamiltonian` representing
the cost function in Ising form.

Example::

    from qdk_pythonic.domains.optimization.problem import MaxCut

    problem = MaxCut(edges=[(0,1), (1,2), (2,0)], n_nodes=3)
    hamiltonian = problem.to_hamiltonian()
"""

from __future__ import annotations

from dataclasses import dataclass

from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm


@dataclass(frozen=True)
class MaxCut:
    """Maximum Cut problem on a graph.

    The cost Hamiltonian is:
        C = sum_{(i,j) in E} (1 - Z_i Z_j) / 2

    Since constant offsets don't affect optimization, we encode only
    the ZZ terms with coefficient -0.5.

    Attributes:
        edges: List of edges as (node_i, node_j) pairs.
        n_nodes: Total number of nodes in the graph.
    """

    edges: list[tuple[int, int]]
    n_nodes: int

    def __post_init__(self) -> None:
        if self.n_nodes < 2:
            raise ValueError(
                f"MaxCut requires n_nodes >= 2, got {self.n_nodes}"
            )

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert to a cost Hamiltonian in Ising form."""
        ham = PauliHamiltonian()
        for i, j in self.edges:
            ham += PauliTerm(pauli_ops={i: "Z", j: "Z"}, coeff=-0.5)
        return ham


@dataclass(frozen=True)
class QUBO:
    """Quadratic Unconstrained Binary Optimization.

    Minimizes x^T Q x where x is a binary vector. Converts to an
    Ising Hamiltonian via the substitution x_i = (1 - Z_i) / 2.

    Attributes:
        Q: Upper-triangular weight matrix as a dict mapping
            (i, j) pairs to weights.
        n_vars: Number of binary variables.
    """

    Q: dict[tuple[int, int], float]
    n_vars: int

    def __post_init__(self) -> None:
        if self.n_vars < 1:
            raise ValueError(
                f"QUBO requires n_vars >= 1, got {self.n_vars}"
            )

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert QUBO to an Ising Hamiltonian.

        Uses x_i = (1 - Z_i) / 2 to map binary variables to spins.
        Constant terms are dropped.
        """
        ham = PauliHamiltonian()
        for (i, j), w in self.Q.items():
            if abs(w) < 1e-15:
                continue
            if i == j:
                # Diagonal: w * x_i = w * (1 - Z_i) / 2
                # -> -w/2 * Z_i (dropping constant w/2)
                ham += PauliTerm(pauli_ops={i: "Z"}, coeff=-w / 2)
            else:
                # Off-diagonal: w * x_i * x_j
                # = w * (1 - Z_i)(1 - Z_j) / 4
                # = w/4 * (1 - Z_i - Z_j + Z_i Z_j)
                # -> w/4 * Z_i Z_j - w/4 * Z_i - w/4 * Z_j
                ham += PauliTerm(
                    pauli_ops={i: "Z", j: "Z"}, coeff=w / 4,
                )
                ham += PauliTerm(pauli_ops={i: "Z"}, coeff=-w / 4)
                ham += PauliTerm(pauli_ops={j: "Z"}, coeff=-w / 4)
        return ham
