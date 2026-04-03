"""Adapter for NetworkX graph-based optimization problems.

Converts NetworkX graphs into QAOA circuits via the existing
:class:`~qdk_pythonic.domains.optimization.problem.MaxCut` and
:class:`~qdk_pythonic.domains.optimization.qaoa.QAOA` classes.

The core conversion function :func:`maxcut_from_networkx` requires
NetworkX; pure-logic helpers that build on existing domain objects
do not.

Example::

    import networkx as nx
    from qdk_pythonic.adapters.networkx_adapter import solve_maxcut

    result = solve_maxcut(nx.cycle_graph(6), p=2)
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm
from qdk_pythonic.domains.optimization.problem import MaxCut
from qdk_pythonic.domains.optimization.qaoa import QAOA


def _require_networkx() -> Any:
    """Lazily import networkx, raising a clear error if missing."""
    try:
        import networkx  # type: ignore[import-untyped]  # noqa: F811
        return networkx
    except ImportError:
        raise ImportError(
            "NetworkX is required for this function. "
            "Install it with: pip install qdk-pythonic[networkx]"
        ) from None


# ═══════════════════════════════════════════════════════════
# Graph-to-Problem Translators
# ═══════════════════════════════════════════════════════════


def maxcut_from_networkx(graph: Any) -> MaxCut:
    """Convert a NetworkX graph to a :class:`MaxCut` problem.

    Nodes are remapped to contiguous integers ``0..n-1``.  Edge
    weights are read from the ``"weight"`` attribute (default 1.0).

    Args:
        graph: A ``networkx.Graph`` instance.

    Returns:
        A MaxCut problem instance with optional weights.

    Raises:
        ImportError: If NetworkX is not installed.
    """
    _require_networkx()

    node_list = sorted(graph.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(node_list)}

    edges: list[tuple[int, int]] = []
    weights: list[float] = []
    all_unit = True

    for u, v, data in graph.edges(data=True):
        w = float(data.get("weight", 1.0))
        edges.append((node_to_idx[u], node_to_idx[v]))
        weights.append(w)
        if w != 1.0:
            all_unit = False

    return MaxCut(
        edges=edges,
        n_nodes=len(node_list),
        weights=None if all_unit else weights,
    )


def graph_coloring_to_hamiltonian(
    graph: Any,
    n_colors: int,
    penalty: float = 2.0,
) -> PauliHamiltonian:
    """Build a cost Hamiltonian for graph coloring via one-hot encoding.

    Uses ``n_nodes * n_colors`` qubits.  Qubit ``(i * n_colors + c)``
    represents node *i* having color *c*.  The Hamiltonian penalises
    adjacent nodes sharing the same color.

    Args:
        graph: A ``networkx.Graph`` instance.
        n_colors: Number of available colors.
        penalty: Penalty weight for constraint violations.

    Returns:
        A PauliHamiltonian encoding the graph coloring cost.

    Raises:
        ImportError: If NetworkX is not installed.
    """
    _require_networkx()

    node_list = sorted(graph.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(node_list)}

    hamiltonian = PauliHamiltonian()

    for u, v in graph.edges():
        i = node_to_idx[u]
        j = node_to_idx[v]
        for c in range(n_colors):
            qi = i * n_colors + c
            qj = j * n_colors + c
            hamiltonian += PauliTerm(
                pauli_ops={qi: "Z", qj: "Z"},
                coeff=penalty / 4,
            )

    return hamiltonian


# ═══════════════════════════════════════════════════════════
# Circuit Construction
# ═══════════════════════════════════════════════════════════


def build_qaoa_circuit(
    graph: Any,
    p: int = 1,
    gammas: Sequence[float] | None = None,
    betas: Sequence[float] | None = None,
) -> Any:
    """Build a QAOA MaxCut circuit from a NetworkX graph.

    Thin wrapper around :func:`maxcut_from_networkx` and
    :class:`~qdk_pythonic.domains.optimization.qaoa.QAOA`.

    Args:
        graph: A ``networkx.Graph`` instance.
        p: Number of QAOA layers.
        gammas: Cost-layer angles (length *p*).  Defaults to pi/4.
        betas: Mixer-layer angles (length *p*).  Defaults to pi/8.

    Returns:
        A :class:`~qdk_pythonic.core.circuit.Circuit`.
    """
    if gammas is None:
        gammas = [math.pi / 4] * p
    if betas is None:
        betas = [math.pi / 8] * p

    problem = maxcut_from_networkx(graph)
    cost_h = problem.to_hamiltonian()
    qaoa = QAOA(cost_hamiltonian=cost_h, p=p)
    return qaoa.to_circuit(gamma=list(gammas), beta=list(betas))


# ═══════════════════════════════════════════════════════════
# High-Level Convenience Functions
# ═══════════════════════════════════════════════════════════


def solve_maxcut(
    graph: Any,
    p: int = 1,
    gammas: Sequence[float] | None = None,
    betas: Sequence[float] | None = None,
    estimate_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One-call NetworkX graph to QAOA MaxCut resource estimation.

    Args:
        graph: A ``networkx.Graph`` instance (optionally weighted).
        p: Number of QAOA layers.
        gammas: Cost-layer angles (length *p*).  Defaults to pi/4.
        betas: Mixer-layer angles (length *p*).  Defaults to pi/8.
        estimate_params: Hardware configuration for resource estimation.
            If ``None``, estimation is skipped.

    Returns:
        A dict with keys ``problem``, ``cost_hamiltonian``, ``circuit``,
        ``n_qubits``, ``gate_count``, ``total_gates``, ``depth``,
        ``n_edges``, ``max_possible_cut``, and optionally
        ``estimate_result``.
    """
    if gammas is None:
        gammas = [math.pi / 4] * p
    if betas is None:
        betas = [math.pi / 8] * p

    problem = maxcut_from_networkx(graph)
    cost_h = problem.to_hamiltonian()
    qaoa = QAOA(cost_hamiltonian=cost_h, p=p)
    circuit = qaoa.to_circuit(gamma=list(gammas), beta=list(betas))

    # Compute max possible cut from weights
    if problem.weights:
        max_cut_val = sum(problem.weights)
    else:
        max_cut_val = float(len(problem.edges))

    result: dict[str, Any] = {
        "problem": problem,
        "cost_hamiltonian": cost_h,
        "circuit": circuit,
        "n_qubits": problem.n_nodes,
        "gate_count": circuit.gate_count(),
        "total_gates": circuit.total_gate_count(),
        "depth": circuit.depth(),
        "n_edges": len(problem.edges),
        "max_possible_cut": max_cut_val,
    }

    if estimate_params is not None:
        result["estimate_result"] = circuit.estimate(params=estimate_params)

    return result


def compare_qaoa_depths(
    graph: Any,
    p_values: list[int] | None = None,
    estimate_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Compare QAOA resource requirements across different depths.

    Args:
        graph: A ``networkx.Graph`` instance.
        p_values: QAOA layer counts to compare.  Defaults to
            ``[1, 2, 3, 4, 5]``.
        estimate_params: Hardware configuration for resource estimation.

    Returns:
        A list of result dicts, one per *p* value.  Each dict includes
        a ``"p"`` key.
    """
    if p_values is None:
        p_values = [1, 2, 3, 4, 5]

    results: list[dict[str, Any]] = []
    for p in p_values:
        r = solve_maxcut(graph, p=p, estimate_params=estimate_params)
        r["p"] = p
        results.append(r)

    return results
