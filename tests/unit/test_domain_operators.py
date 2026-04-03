"""Tests for PauliTerm, PauliHamiltonian, and Trotter circuit generation."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.core.instruction import Instruction
from qdk_pythonic.domains.common.operators import (
    PauliHamiltonian,
    PauliTerm,
    X,
    Y,
    Z,
)

# ------------------------------------------------------------------
# PauliTerm construction and arithmetic
# ------------------------------------------------------------------


@pytest.mark.unit
def test_pauli_term_single_qubit() -> None:
    t = Z(0)
    assert t.pauli_ops == {0: "Z"}
    assert t.coeff == 1.0


@pytest.mark.unit
def test_pauli_helpers() -> None:
    assert X(1).pauli_ops == {1: "X"}
    assert Y(2).pauli_ops == {2: "Y"}
    assert Z(3).pauli_ops == {3: "Z"}


@pytest.mark.unit
def test_scalar_multiply() -> None:
    t = 0.5 * Z(0)
    assert t.coeff == pytest.approx(0.5)
    assert t.pauli_ops == {0: "Z"}


@pytest.mark.unit
def test_right_scalar_multiply() -> None:
    t = Z(0) * 0.3
    assert t.coeff == pytest.approx(0.3)


@pytest.mark.unit
def test_tensor_product() -> None:
    t = Z(0) * Z(1)
    assert t.pauli_ops == {0: "Z", 1: "Z"}
    assert t.coeff == 1.0


@pytest.mark.unit
def test_tensor_product_with_scalar() -> None:
    t = -0.5 * Z(0) * Z(1)
    assert t.coeff == pytest.approx(-0.5)
    assert t.pauli_ops == {0: "Z", 1: "Z"}


@pytest.mark.unit
def test_overlap_raises() -> None:
    with pytest.raises(ValueError, match="Overlapping"):
        Z(0) * Z(0)


@pytest.mark.unit
def test_invalid_pauli_raises() -> None:
    with pytest.raises(ValueError, match="Invalid Pauli"):
        PauliTerm(pauli_ops={0: "A"})


# ------------------------------------------------------------------
# PauliHamiltonian construction
# ------------------------------------------------------------------


@pytest.mark.unit
def test_hamiltonian_iadd_term() -> None:
    h = PauliHamiltonian()
    h += Z(0)
    h += X(1)
    assert len(h) == 2


@pytest.mark.unit
def test_hamiltonian_add() -> None:
    h1 = PauliHamiltonian([Z(0)])
    h2 = PauliHamiltonian([X(1)])
    h3 = h1 + h2
    assert len(h3) == 2
    assert len(h1) == 1  # original unmodified


@pytest.mark.unit
def test_hamiltonian_qubit_count() -> None:
    h = PauliHamiltonian()
    h += -1.0 * Z(0) * Z(1)
    h += -0.5 * X(0)
    h += -0.5 * X(1)
    assert h.qubit_count() == 2


@pytest.mark.unit
def test_hamiltonian_repr() -> None:
    h = PauliHamiltonian([Z(0), X(1)])
    assert repr(h) == "PauliHamiltonian(n_terms=2)"


# ------------------------------------------------------------------
# from_ising / from_heisenberg
# ------------------------------------------------------------------


@pytest.mark.unit
def test_from_ising_chain_4() -> None:
    edges = [(0, 1), (1, 2), (2, 3)]
    h = PauliHamiltonian.from_ising(edges, n_qubits=4, J=1.0, h=0.5)
    # 3 ZZ terms + 4 X terms = 7
    assert len(h) == 7
    assert h.qubit_count() == 4


@pytest.mark.unit
def test_from_heisenberg_chain_3() -> None:
    edges = [(0, 1), (1, 2)]
    h = PauliHamiltonian.from_heisenberg(edges, Jx=1.0, Jy=1.0, Jz=1.0)
    # 2 edges * 3 terms (XX, YY, ZZ) = 6
    assert len(h) == 6
    assert h.qubit_count() == 3


@pytest.mark.unit
def test_from_heisenberg_zero_coupling_skipped() -> None:
    edges = [(0, 1)]
    h = PauliHamiltonian.from_heisenberg(edges, Jx=0.0, Jy=0.0, Jz=1.0)
    # Only ZZ term
    assert len(h) == 1


# ------------------------------------------------------------------
# Trotter circuit generation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_trotter_single_z_term() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "Z"}, coeff=1.0)])
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    # Single Z term -> one Rz gate
    assert circ.qubit_count() == 1
    assert circ.total_gate_count() == 1
    gates = circ.gate_count()
    assert "Rz" in gates


@pytest.mark.unit
def test_trotter_single_x_term() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "X"}, coeff=1.0)])
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    assert circ.total_gate_count() == 1
    assert "Rx" in circ.gate_count()


@pytest.mark.unit
def test_trotter_single_y_term() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "Y"}, coeff=1.0)])
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    assert circ.total_gate_count() == 1
    assert "Ry" in circ.gate_count()


@pytest.mark.unit
def test_trotter_zz_term() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "Z", 1: "Z"}, coeff=1.0)])
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    # ZZ decomposition: CX, Rz, CX = 3 gates
    assert circ.total_gate_count() == 3
    assert circ.gate_count()["CNOT"] == 2
    assert circ.gate_count()["Rz"] == 1


@pytest.mark.unit
def test_trotter_xx_term() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "X", 1: "X"}, coeff=1.0)])
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    # XX: H, H, CX, Rz, CX, H, H = 7 gates
    gates = circ.gate_count()
    assert gates.get("H", 0) == 4
    assert gates.get("CNOT", 0) == 2
    assert gates.get("Rz", 0) == 1


@pytest.mark.unit
def test_trotter_ising_matches_manual() -> None:
    """Verify gate count matches the manual Ising notebook construction."""
    n = 4
    edges = [(i, i + 1) for i in range(n - 1)]
    h = PauliHamiltonian.from_ising(edges, n_qubits=n, J=1.0, h=0.5)
    circ = h.to_trotter_circuit(dt=0.1, steps=1)

    # Per the Ising notebook:
    # ZZ terms: 3 edges * 3 gates (CX, Rz, CX) = 9
    # X terms: 4 qubits * 1 gate (Rx) = 4
    # Total: 13
    assert circ.total_gate_count() == 13
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_trotter_multiple_steps() -> None:
    h = PauliHamiltonian([Z(0)])
    circ = h.to_trotter_circuit(dt=0.1, steps=5)
    # 1 gate per step * 5 steps
    assert circ.total_gate_count() == 5


@pytest.mark.unit
def test_trotter_second_order() -> None:
    h = PauliHamiltonian([Z(0), X(1)])
    circ1 = h.to_trotter_circuit(dt=0.1, order=1, steps=1)
    circ2 = h.to_trotter_circuit(dt=0.1, order=2, steps=1)
    # Second-order: forward + reverse = 2x gates
    assert circ2.total_gate_count() == 2 * circ1.total_gate_count()


@pytest.mark.unit
def test_trotter_invalid_order_raises() -> None:
    h = PauliHamiltonian([Z(0)])
    with pytest.raises(ValueError, match="order must be 1 or 2"):
        h.to_trotter_circuit(dt=0.1, order=3)


@pytest.mark.unit
def test_trotter_empty_hamiltonian() -> None:
    h = PauliHamiltonian()
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    assert circ.qubit_count() == 0
    assert circ.total_gate_count() == 0


@pytest.mark.unit
def test_trotter_zero_coeff_skipped() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "Z"}, coeff=0.0)])
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    assert circ.total_gate_count() == 0


# ------------------------------------------------------------------
# Complex coefficients
# ------------------------------------------------------------------


@pytest.mark.unit
def test_complex_coeff_construction() -> None:
    t = PauliTerm(pauli_ops={0: "Z"}, coeff=(0.5 + 0.3j))
    assert t.coeff == pytest.approx(0.5 + 0.3j)


@pytest.mark.unit
def test_complex_scalar_multiply() -> None:
    t = (0.5 + 0.5j) * Z(0)
    assert t.coeff == pytest.approx(0.5 + 0.5j)


@pytest.mark.unit
def test_complex_right_scalar_multiply() -> None:
    t = Z(0) * (0.5 + 0.5j)
    assert t.coeff == pytest.approx(0.5 + 0.5j)


@pytest.mark.unit
def test_complex_tensor_product_coeff() -> None:
    t = (0.5j) * X(0) * Y(1)
    assert t.coeff == pytest.approx(0.5j)
    assert t.pauli_ops == {0: "X", 1: "Y"}


@pytest.mark.unit
def test_trotter_complex_coeff_raises() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "Z"}, coeff=(1.0 + 0.5j))])
    with pytest.raises(ValueError, match="real coefficients"):
        h.to_trotter_circuit(dt=0.1, steps=1)


@pytest.mark.unit
def test_trotter_real_complex_coeff_succeeds() -> None:
    h = PauliHamiltonian([PauliTerm(pauli_ops={0: "Z"}, coeff=complex(1.0, 0.0))])
    circ = h.to_trotter_circuit(dt=0.1, steps=1)
    assert circ.total_gate_count() == 1


# ------------------------------------------------------------------
# Hamiltonian summary
# ------------------------------------------------------------------


@pytest.mark.unit
def test_summary_ising() -> None:
    edges = [(0, 1), (1, 2), (2, 3)]
    h = PauliHamiltonian.from_ising(edges, n_qubits=4, J=1.0, h=0.5)
    s = h.summary()
    assert s["n_qubits"] == 4
    assert s["n_terms"] == 7  # 3 ZZ + 4 X
    assert s["max_pauli_weight"] == 2
    assert s["weight_distribution"] == {1: 4, 2: 3}
    assert s["one_norm"] == pytest.approx(5.0)  # 3*1.0 + 4*0.5


@pytest.mark.unit
def test_summary_empty() -> None:
    h = PauliHamiltonian()
    s = h.summary()
    assert s["n_qubits"] == 0
    assert s["n_terms"] == 0
    assert s["max_pauli_weight"] == 0
    assert s["weight_distribution"] == {}
    assert s["one_norm"] == 0.0


@pytest.mark.unit
def test_print_summary(capsys: pytest.CaptureFixture[str]) -> None:
    h = PauliHamiltonian.from_ising([(0, 1)], n_qubits=2, J=1.0, h=0.5)
    h.print_summary()
    captured = capsys.readouterr()
    assert "PauliHamiltonian:" in captured.out
    assert "3 terms" in captured.out
    assert "2 qubits" in captured.out
