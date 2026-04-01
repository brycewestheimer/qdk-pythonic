"""Tests for HardwareEfficientAnsatz."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz


@pytest.mark.unit
def test_num_parameters() -> None:
    ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=2)
    # 4 qubits * 2 rotation gates (ry, rz) * 2 layers = 16
    assert ansatz.num_parameters == 16


@pytest.mark.unit
def test_to_circuit_basic() -> None:
    ansatz = HardwareEfficientAnsatz(n_qubits=3, depth=1)
    params = [0.1] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    assert circ.qubit_count() == 3
    assert circ.total_gate_count() > 0


@pytest.mark.unit
def test_to_circuit_has_rotations_and_cx() -> None:
    ansatz = HardwareEfficientAnsatz(n_qubits=3, depth=1)
    params = [0.1] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    gates = circ.gate_count()
    # 3 qubits * 2 rotations = 6 rotation gates
    assert gates.get("Ry", 0) == 3
    assert gates.get("Rz", 0) == 3
    # linear entanglement: 2 CX gates for 3 qubits
    assert gates.get("CNOT", 0) == 2


@pytest.mark.unit
def test_full_entanglement() -> None:
    ansatz = HardwareEfficientAnsatz(
        n_qubits=3, depth=1, entanglement="full",
    )
    params = [0.1] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    # Full entanglement: C(3,2) = 3 CX gates
    assert circ.gate_count().get("CNOT", 0) == 3


@pytest.mark.unit
def test_wrong_param_count_raises() -> None:
    ansatz = HardwareEfficientAnsatz(n_qubits=2, depth=1)
    with pytest.raises(ValueError, match="Expected"):
        ansatz.to_circuit([0.1])


@pytest.mark.unit
def test_invalid_rotation_gate_raises() -> None:
    with pytest.raises(ValueError, match="Unknown rotation gate"):
        HardwareEfficientAnsatz(n_qubits=2, rotation_gates=("bad",))


@pytest.mark.unit
def test_invalid_entanglement_raises() -> None:
    with pytest.raises(ValueError, match="entanglement"):
        HardwareEfficientAnsatz(n_qubits=2, entanglement="star")


@pytest.mark.unit
def test_single_qubit_no_cx() -> None:
    ansatz = HardwareEfficientAnsatz(n_qubits=1, depth=2)
    params = [0.1] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    assert circ.gate_count().get("CNOT", 0) == 0
