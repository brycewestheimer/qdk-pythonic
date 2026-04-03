"""Tests for the NetworkX adapter.

Tests that need a live ``networkx`` import use ``pytest.importorskip``
so the suite still runs (with those tests skipped) on machines without
NetworkX installed.
"""

from __future__ import annotations

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.domains.optimization.problem import MaxCut

# ------------------------------------------------------------------
# Pure logic tests (no networkx required)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_maxcut_weighted_hamiltonian() -> None:
    """Weighted MaxCut produces correct per-edge coefficients."""
    mc = MaxCut(
        edges=[(0, 1), (1, 2)],
        n_nodes=3,
        weights=[2.0, 3.0],
    )
    ham = mc.to_hamiltonian()
    coeffs = sorted([t.coeff.real for t in ham.terms])
    assert coeffs[0] == pytest.approx(-1.5)
    assert coeffs[1] == pytest.approx(-1.0)


# ------------------------------------------------------------------
# Tests requiring networkx
# ------------------------------------------------------------------


@pytest.mark.unit
def test_maxcut_from_networkx_triangle() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import maxcut_from_networkx

    G = nx.cycle_graph(3)
    mc = maxcut_from_networkx(G)
    assert mc.n_nodes == 3
    assert len(mc.edges) == 3
    assert mc.weights is None  # unweighted


@pytest.mark.unit
def test_maxcut_from_networkx_weighted() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import maxcut_from_networkx

    G = nx.Graph()
    G.add_weighted_edges_from([(0, 1, 2.0), (1, 2, 3.0)])
    mc = maxcut_from_networkx(G)
    assert mc.n_nodes == 3
    assert mc.weights is not None
    assert sorted(mc.weights) == [2.0, 3.0]


@pytest.mark.unit
def test_maxcut_from_networkx_node_remapping() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import maxcut_from_networkx

    G = nx.Graph()
    G.add_edges_from([("a", "b"), ("b", "c")])
    mc = maxcut_from_networkx(G)
    assert mc.n_nodes == 3
    # Nodes should be remapped to 0, 1, 2
    for i, j in mc.edges:
        assert 0 <= i < 3
        assert 0 <= j < 3


@pytest.mark.unit
def test_solve_maxcut_triangle() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import solve_maxcut

    result = solve_maxcut(nx.cycle_graph(3), p=1)

    expected_keys = {
        "problem", "cost_hamiltonian", "circuit", "n_qubits",
        "gate_count", "total_gates", "depth", "n_edges",
        "max_possible_cut",
    }
    assert expected_keys.issubset(set(result.keys()))
    assert result["n_qubits"] == 3
    assert result["n_edges"] == 3
    assert result["total_gates"] > 0
    assert isinstance(result["circuit"], Circuit)


@pytest.mark.unit
def test_solve_maxcut_p2_more_gates() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import solve_maxcut

    G = nx.path_graph(4)
    r1 = solve_maxcut(G, p=1)
    r2 = solve_maxcut(G, p=2)
    assert r2["total_gates"] > r1["total_gates"]


@pytest.mark.unit
def test_compare_qaoa_depths_structure() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import compare_qaoa_depths

    results = compare_qaoa_depths(nx.cycle_graph(4), p_values=[1, 2, 3])
    assert len(results) == 3
    assert [r["p"] for r in results] == [1, 2, 3]
    # Gates should increase with p
    gates = [r["total_gates"] for r in results]
    assert gates == sorted(gates)


@pytest.mark.unit
def test_build_qaoa_circuit_returns_circuit() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import build_qaoa_circuit

    circ = build_qaoa_circuit(nx.cycle_graph(4), p=1)
    assert isinstance(circ, Circuit)
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_graph_coloring_to_hamiltonian() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import (
        graph_coloring_to_hamiltonian,
    )

    G = nx.cycle_graph(3)  # triangle, 3 edges
    n_colors = 2
    ham = graph_coloring_to_hamiltonian(G, n_colors=n_colors)
    # 3 edges * 2 colors = 6 ZZ terms
    assert len(ham.terms) == 6


@pytest.mark.unit
def test_solve_maxcut_weighted() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import solve_maxcut

    G = nx.Graph()
    G.add_weighted_edges_from([(0, 1, 2.0), (1, 2, 3.0)])
    result = solve_maxcut(G, p=1)
    assert result["max_possible_cut"] == pytest.approx(5.0)


@pytest.mark.unit
def test_maxcut_from_networkx_single_node_error() -> None:
    nx = pytest.importorskip("networkx")
    from qdk_pythonic.adapters.networkx_adapter import maxcut_from_networkx

    G = nx.Graph()
    G.add_node(0)
    with pytest.raises(ValueError, match="n_nodes >= 2"):
        maxcut_from_networkx(G)
