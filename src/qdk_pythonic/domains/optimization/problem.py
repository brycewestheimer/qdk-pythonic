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
    weights: list[float] | None = None

    def __post_init__(self) -> None:
        if self.n_nodes < 2:
            raise ValueError(
                f"MaxCut requires n_nodes >= 2, got {self.n_nodes}"
            )
        if self.weights is not None and len(self.weights) != len(self.edges):
            raise ValueError(
                f"weights length ({len(self.weights)}) must match "
                f"edges length ({len(self.edges)})"
            )

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert to a cost Hamiltonian in Ising form."""
        ham = PauliHamiltonian()
        for idx, (i, j) in enumerate(self.edges):
            w = self.weights[idx] if self.weights else 1.0
            ham += PauliTerm(pauli_ops={i: "Z", j: "Z"}, coeff=-w / 2)
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


@dataclass(frozen=True)
class TSP:
    """Traveling Salesman Problem.

    Uses one-hot encoding with N^2 binary variables: x_{i,t} = 1 means
    city *i* is visited at time step *t*. Converts to QUBO, then to an
    Ising Hamiltonian.

    The QUBO encodes three sets of terms:

    1. Row constraints (each city visited exactly once):
       ``A * (1 - sum_t x_{i,t})^2`` for each city *i*.
    2. Column constraints (each time step has exactly one city):
       ``A * (1 - sum_i x_{i,t})^2`` for each time step *t*.
    3. Distance objective:
       ``sum_{i,j,t} d_{i,j} * x_{i,t} * x_{j,(t+1) mod N}``

    Attributes:
        distances: N x N distance matrix (list of lists).
        penalty: Constraint penalty weight. Auto-computed if ``None``.
    """

    distances: list[list[float]]
    penalty: float | None = None

    def __post_init__(self) -> None:
        n = len(self.distances)
        if n < 2:
            raise ValueError(
                f"TSP requires at least 2 cities, got {n}"
            )
        for row in self.distances:
            if len(row) != n:
                raise ValueError(
                    f"Distance matrix must be square; got row of "
                    f"length {len(row)} for {n} cities"
                )

    @property
    def n_cities(self) -> int:
        """Number of cities."""
        return len(self.distances)

    def _effective_penalty(self) -> float:
        """Return the penalty weight, auto-computing if needed."""
        if self.penalty is not None:
            return self.penalty
        n = self.n_cities
        max_dist = max(
            self.distances[i][j]
            for i in range(n) for j in range(n) if i != j
        )
        return max_dist * n + 1.0

    def _var(self, city: int, step: int) -> int:
        """Map (city, time step) to QUBO variable index."""
        return city * self.n_cities + step

    def to_qubo(self) -> QUBO:
        """Convert TSP to a QUBO problem.

        Returns:
            A QUBO encoding the TSP constraints and objective.
        """
        n = self.n_cities
        n_vars = n * n
        A = self._effective_penalty()  # noqa: N806
        Q: dict[tuple[int, int], float] = {}

        def _add(i: int, j: int, val: float) -> None:
            key = (min(i, j), max(i, j)) if i != j else (i, j)
            Q[key] = Q.get(key, 0.0) + val

        # Row constraints: A * (1 - sum_t x_{i,t})^2
        # Expanded: A * (sum_t x_{i,t}^2 - 2*sum_t x_{i,t}
        #            + sum_{t1<t2} 2*x_{i,t1}*x_{i,t2} + 1)
        # Diagonal: A * (1 - 2) = -A per variable (from x^2 = x)
        # Off-diagonal: 2A per pair
        for city in range(n):
            for t in range(n):
                v = self._var(city, t)
                _add(v, v, -A)
            for t1 in range(n):
                for t2 in range(t1 + 1, n):
                    v1 = self._var(city, t1)
                    v2 = self._var(city, t2)
                    _add(v1, v2, 2 * A)

        # Column constraints: A * (1 - sum_i x_{i,t})^2
        for t in range(n):
            for city in range(n):
                v = self._var(city, t)
                _add(v, v, -A)
            for c1 in range(n):
                for c2 in range(c1 + 1, n):
                    v1 = self._var(c1, t)
                    v2 = self._var(c2, t)
                    _add(v1, v2, 2 * A)

        # Distance objective: d_{i,j} * x_{i,t} * x_{j,(t+1) mod N}
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                d = self.distances[i][j]
                if abs(d) < 1e-15:
                    continue
                for t in range(n):
                    v1 = self._var(i, t)
                    v2 = self._var(j, (t + 1) % n)
                    _add(v1, v2, d)

        return QUBO(Q=Q, n_vars=n_vars)

    def to_hamiltonian(self) -> PauliHamiltonian:
        """Convert TSP to an Ising Hamiltonian via QUBO."""
        return self.to_qubo().to_hamiltonian()
