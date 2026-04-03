"""Tests for LCU and qubitization gate-level framework."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.domains.common.lcu import (
    PrepareOracle,
    QubitizationQPE,
    QubitizationWalkOperator,
    SelectOracle,
)
from qdk_pythonic.domains.common.operators import PauliHamiltonian, X, Z
from qdk_pythonic.exceptions import CircuitError


def _simple_hamiltonian() -> PauliHamiltonian:
    """2-qubit, 3-term Hamiltonian for testing."""
    h = PauliHamiltonian()
    h += -1.0 * Z(0) * Z(1)
    h += -0.5 * X(0)
    h += -0.5 * X(1)
    return h


def _single_term_hamiltonian() -> PauliHamiltonian:
    return PauliHamiltonian([Z(0)])


# ── PrepareOracle ──


@pytest.mark.unit
def test_prepare_n_ancilla_3_terms() -> None:
    h = _simple_hamiltonian()
    prep = PrepareOracle(h)
    assert prep.n_terms == 3
    assert prep.n_ancilla_qubits == 2  # ceil(log2(3)) = 2


@pytest.mark.unit
def test_prepare_n_ancilla_single_term() -> None:
    prep = PrepareOracle(_single_term_hamiltonian())
    assert prep.n_ancilla_qubits == 1


@pytest.mark.unit
def test_prepare_n_ancilla_4_terms() -> None:
    h = PauliHamiltonian([Z(0), X(0), Z(1), X(1)])
    prep = PrepareOracle(h)
    assert prep.n_ancilla_qubits == 2  # ceil(log2(4)) = 2


@pytest.mark.unit
def test_prepare_circuit_builds() -> None:
    prep = PrepareOracle(_simple_hamiltonian())
    circ = prep.to_circuit()
    assert circ.qubit_count() == prep.n_ancilla_qubits


@pytest.mark.unit
def test_prepare_frozen() -> None:
    prep = PrepareOracle(_simple_hamiltonian())
    with pytest.raises(AttributeError):
        prep.hamiltonian = PauliHamiltonian()  # type: ignore[misc]


# ── SelectOracle ──


@pytest.mark.unit
def test_select_qubit_counts() -> None:
    select = SelectOracle(_simple_hamiltonian())
    assert select.n_system_qubits == 2
    assert select.n_ancilla_qubits == 2


@pytest.mark.unit
def test_select_circuit_builds() -> None:
    select = SelectOracle(_simple_hamiltonian())
    circ = select.to_circuit()
    assert circ.qubit_count() == select.n_system_qubits + select.n_ancilla_qubits


@pytest.mark.unit
def test_select_has_gates() -> None:
    select = SelectOracle(_simple_hamiltonian())
    circ = select.to_circuit()
    assert circ.total_gate_count() > 0


@pytest.mark.unit
def test_select_frozen() -> None:
    select = SelectOracle(_simple_hamiltonian())
    with pytest.raises(AttributeError):
        select.hamiltonian = PauliHamiltonian()  # type: ignore[misc]


# ── QubitizationWalkOperator ──


@pytest.mark.unit
def test_walk_qubit_counts() -> None:
    walk = QubitizationWalkOperator(_simple_hamiltonian())
    assert walk.n_system_qubits == 2
    assert walk.n_ancilla_qubits == 2


@pytest.mark.unit
def test_walk_circuit_builds() -> None:
    walk = QubitizationWalkOperator(_simple_hamiltonian())
    circ = walk.to_circuit()
    total = walk.n_system_qubits + walk.n_ancilla_qubits
    assert circ.qubit_count() == total


@pytest.mark.unit
def test_walk_has_gates() -> None:
    walk = QubitizationWalkOperator(_simple_hamiltonian())
    circ = walk.to_circuit()
    assert circ.total_gate_count() > 0


@pytest.mark.unit
def test_walk_frozen() -> None:
    walk = QubitizationWalkOperator(_simple_hamiltonian())
    with pytest.raises(AttributeError):
        walk.hamiltonian = PauliHamiltonian()  # type: ignore[misc]


# ── QubitizationQPE ──


@pytest.mark.unit
def test_qpe_qubit_count() -> None:
    h = _simple_hamiltonian()
    qpe = QubitizationQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=3)
    circ = qpe.to_circuit()
    # system(2) + ancilla(2) + estimation(3) = 7
    assert circ.qubit_count() == 7


@pytest.mark.unit
def test_qpe_single_term() -> None:
    h = _single_term_hamiltonian()
    qpe = QubitizationQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=2)
    circ = qpe.to_circuit()
    # system(1) + ancilla(1) + estimation(2) = 4
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_qpe_has_controlled_gates() -> None:
    h = _single_term_hamiltonian()
    qpe = QubitizationQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=2)
    circ = qpe.to_circuit()
    has_controlled = any(
        hasattr(inst, "controls") and inst.controls
        for inst in circ.instructions
    )
    assert has_controlled


@pytest.mark.unit
def test_qpe_more_estimation_qubits_more_gates() -> None:
    h = _single_term_hamiltonian()
    c2 = QubitizationQPE(
        hamiltonian=h, n_electrons=1, n_estimation_qubits=2,
    ).to_circuit()
    c3 = QubitizationQPE(
        hamiltonian=h, n_electrons=1, n_estimation_qubits=3,
    ).to_circuit()
    assert c3.total_gate_count() > c2.total_gate_count()


@pytest.mark.unit
def test_qpe_energy_from_phase_zero() -> None:
    e = QubitizationQPE.energy_from_phase(0.0, 1.0)
    # sin(-pi/2) = -1.0
    assert abs(e - (-1.0)) < 1e-10


@pytest.mark.unit
def test_qpe_energy_from_phase_quarter() -> None:
    e = QubitizationQPE.energy_from_phase(0.25, 2.0)
    # sin(2*pi*0.25 - pi/2) = sin(0) = 0
    assert abs(e) < 1e-10


@pytest.mark.unit
def test_qpe_energy_from_phase_half() -> None:
    e = QubitizationQPE.energy_from_phase(0.5, 1.0)
    # sin(2*pi*0.5 - pi/2) = sin(pi - pi/2) = sin(pi/2) = 1.0
    assert abs(e - 1.0) < 1e-10


@pytest.mark.unit
def test_qpe_frozen() -> None:
    h = _single_term_hamiltonian()
    qpe = QubitizationQPE(hamiltonian=h, n_electrons=1)
    with pytest.raises(AttributeError):
        qpe.n_electrons = 2  # type: ignore[misc]


@pytest.mark.unit
def test_qpe_invalid_estimation_qubits() -> None:
    h = _single_term_hamiltonian()
    with pytest.raises(CircuitError, match="n_estimation_qubits"):
        QubitizationQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=0)


@pytest.mark.unit
def test_qpe_invalid_electrons() -> None:
    h = _single_term_hamiltonian()
    with pytest.raises(CircuitError, match="n_electrons"):
        QubitizationQPE(hamiltonian=h, n_electrons=-1)


@pytest.mark.unit
def test_qpe_empty_hamiltonian() -> None:
    h = PauliHamiltonian()
    qpe = QubitizationQPE(hamiltonian=h, n_electrons=0, n_estimation_qubits=2)
    with pytest.raises(CircuitError, match="no qubit terms"):
        qpe.to_circuit()
