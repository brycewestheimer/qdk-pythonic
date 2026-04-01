"""Tests for optimization problems and QAOA."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.optimization.mixer import x_mixer
from qdk_pythonic.domains.optimization.problem import QUBO, MaxCut
from qdk_pythonic.domains.optimization.qaoa import QAOA

# ------------------------------------------------------------------
# MaxCut
# ------------------------------------------------------------------


@pytest.mark.unit
def test_maxcut_triangle() -> None:
    mc = MaxCut(edges=[(0, 1), (1, 2), (2, 0)], n_nodes=3)
    ham = mc.to_hamiltonian()
    # 3 edges -> 3 ZZ terms
    assert len(ham) == 3
    assert ham.qubit_count() == 3


@pytest.mark.unit
def test_maxcut_coefficients() -> None:
    mc = MaxCut(edges=[(0, 1)], n_nodes=2)
    ham = mc.to_hamiltonian()
    assert len(ham) == 1
    assert ham.terms[0].coeff == pytest.approx(-0.5)


@pytest.mark.unit
def test_maxcut_invalid_nodes() -> None:
    with pytest.raises(ValueError, match="n_nodes >= 2"):
        MaxCut(edges=[], n_nodes=1)


# ------------------------------------------------------------------
# QUBO
# ------------------------------------------------------------------


@pytest.mark.unit
def test_qubo_diagonal() -> None:
    q = QUBO(Q={(0, 0): 2.0, (1, 1): 3.0}, n_vars=2)
    ham = q.to_hamiltonian()
    # 2 diagonal terms -> 2 Z terms
    assert len(ham) == 2


@pytest.mark.unit
def test_qubo_off_diagonal() -> None:
    q = QUBO(Q={(0, 1): 4.0}, n_vars=2)
    ham = q.to_hamiltonian()
    # 1 off-diagonal -> 3 terms (ZZ, Z_i, Z_j)
    assert len(ham) == 3


@pytest.mark.unit
def test_qubo_invalid() -> None:
    with pytest.raises(ValueError, match="n_vars >= 1"):
        QUBO(Q={}, n_vars=0)


# ------------------------------------------------------------------
# QAOA
# ------------------------------------------------------------------


@pytest.mark.unit
def test_qaoa_num_parameters() -> None:
    mc = MaxCut(edges=[(0, 1), (1, 2)], n_nodes=3)
    qaoa = QAOA(mc.to_hamiltonian(), p=3)
    assert qaoa.num_parameters == 6


@pytest.mark.unit
def test_qaoa_circuit_structure() -> None:
    mc = MaxCut(edges=[(0, 1), (1, 2), (2, 0)], n_nodes=3)
    qaoa = QAOA(mc.to_hamiltonian(), p=1)
    circ = qaoa.to_circuit(gamma=[0.5], beta=[0.3])
    assert circ.qubit_count() == 3
    # Should have H gates (initial), cost ZZ gates, and mixer Rx gates
    gates = circ.gate_count()
    assert gates.get("H", 0) >= 3  # initial superposition


@pytest.mark.unit
def test_qaoa_p2_more_gates() -> None:
    mc = MaxCut(edges=[(0, 1)], n_nodes=2)
    circ1 = QAOA(mc.to_hamiltonian(), p=1).to_circuit([0.5], [0.3])
    circ2 = QAOA(mc.to_hamiltonian(), p=2).to_circuit([0.5, 0.3], [0.7, 0.2])
    assert circ2.total_gate_count() > circ1.total_gate_count()


@pytest.mark.unit
def test_qaoa_wrong_gamma_length() -> None:
    mc = MaxCut(edges=[(0, 1)], n_nodes=2)
    qaoa = QAOA(mc.to_hamiltonian(), p=2)
    with pytest.raises(ValueError, match="gamma"):
        qaoa.to_circuit(gamma=[0.5], beta=[0.3, 0.2])


@pytest.mark.unit
def test_qaoa_wrong_beta_length() -> None:
    mc = MaxCut(edges=[(0, 1)], n_nodes=2)
    qaoa = QAOA(mc.to_hamiltonian(), p=2)
    with pytest.raises(ValueError, match="beta"):
        qaoa.to_circuit(gamma=[0.5, 0.3], beta=[0.2])


@pytest.mark.unit
def test_qaoa_invalid_p() -> None:
    mc = MaxCut(edges=[(0, 1)], n_nodes=2)
    with pytest.raises(ValueError, match="p must be >= 1"):
        QAOA(mc.to_hamiltonian(), p=0)


@pytest.mark.unit
def test_qaoa_default_mixer_is_x_mixer() -> None:
    mc = MaxCut(edges=[(0, 1)], n_nodes=2)
    qaoa = QAOA(mc.to_hamiltonian(), p=1)
    # Mixer should have 2 X terms (one per qubit)
    assert len(qaoa.mixer) == 2


# ------------------------------------------------------------------
# x_mixer
# ------------------------------------------------------------------


@pytest.mark.unit
def test_x_mixer() -> None:
    m = x_mixer(4)
    assert len(m) == 4
    assert m.qubit_count() == 4
    for term in m.terms:
        assert list(term.pauli_ops.values()) == ["X"]
