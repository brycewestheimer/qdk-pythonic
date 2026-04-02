"""Tests for quantum ML domain."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz
from qdk_pythonic.domains.ml.encoding import AmplitudeEncoding, AngleEncoding
from qdk_pythonic.domains.ml.kernels import QuantumKernel
from qdk_pythonic.domains.ml.variational import VariationalClassifier

# ------------------------------------------------------------------
# AngleEncoding
# ------------------------------------------------------------------


@pytest.mark.unit
def test_angle_encoding() -> None:
    enc = AngleEncoding(n_features=3)
    circ = enc.to_circuit([0.1, 0.2, 0.3])
    assert circ.qubit_count() == 3
    assert circ.gate_count().get("Ry", 0) == 3


@pytest.mark.unit
def test_angle_encoding_wrong_length() -> None:
    enc = AngleEncoding(n_features=3)
    with pytest.raises(ValueError, match="Expected 3"):
        enc.to_circuit([0.1, 0.2])


@pytest.mark.unit
def test_angle_encoding_invalid() -> None:
    with pytest.raises(ValueError, match="n_features"):
        AngleEncoding(n_features=0)


# ------------------------------------------------------------------
# AmplitudeEncoding
# ------------------------------------------------------------------


@pytest.mark.unit
def test_amplitude_encoding() -> None:
    enc = AmplitudeEncoding(n_qubits=2)
    data = [0.5, 0.5, 0.5, 0.5]  # normalized: sum of squares = 1
    circ = enc.to_circuit(data)
    assert circ.qubit_count() == 2


@pytest.mark.unit
def test_amplitude_encoding_wrong_length() -> None:
    enc = AmplitudeEncoding(n_qubits=2)
    with pytest.raises(ValueError, match="Expected 4"):
        enc.to_circuit([0.5, 0.5])


@pytest.mark.unit
def test_amplitude_encoding_not_normalized() -> None:
    enc = AmplitudeEncoding(n_qubits=1)
    with pytest.raises(ValueError, match="normalized"):
        enc.to_circuit([0.5, 0.5])  # sum of squares = 0.5, not 1


@pytest.mark.unit
def test_amplitude_encoding_valid_normalized() -> None:
    enc = AmplitudeEncoding(n_qubits=1)
    s = 1.0 / math.sqrt(2)
    circ = enc.to_circuit([s, s])
    assert circ.qubit_count() == 1


# ------------------------------------------------------------------
# QuantumKernel
# ------------------------------------------------------------------


@pytest.mark.unit
def test_quantum_kernel() -> None:
    enc = AngleEncoding(n_features=2)
    kernel = QuantumKernel(enc)
    circ = kernel.to_circuit(x=[0.1, 0.2], y=[0.3, 0.4])
    assert circ.qubit_count() == 2
    # Should have Ry rotations from both x and y encodings
    assert circ.gate_count().get("Ry", 0) == 4
    # Should have measurements
    from qdk_pythonic.core.instruction import Measurement

    n_meas = sum(1 for i in circ.instructions if isinstance(i, Measurement))
    assert n_meas == 2


# ------------------------------------------------------------------
# VariationalClassifier
# ------------------------------------------------------------------


@pytest.mark.unit
def test_variational_classifier() -> None:
    enc = AngleEncoding(n_features=3)
    ansatz = HardwareEfficientAnsatz(n_qubits=3, depth=1)
    clf = VariationalClassifier(enc, ansatz)
    params = [0.1] * ansatz.num_parameters
    circ = clf.to_circuit(data=[0.1, 0.2, 0.3], params=params)
    assert circ.qubit_count() == 3
    # Should have encoding Ry + ansatz gates + measurement
    from qdk_pythonic.core.instruction import Measurement

    n_meas = sum(1 for i in circ.instructions if isinstance(i, Measurement))
    assert n_meas == 1  # measures first qubit


@pytest.mark.unit
def test_variational_classifier_mismatch() -> None:
    enc = AngleEncoding(n_features=3)
    ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=1)
    with pytest.raises(ValueError, match="must match"):
        VariationalClassifier(enc, ansatz)


# ------------------------------------------------------------------
# Exact AmplitudeEncoding tests
# ------------------------------------------------------------------


@pytest.mark.unit
def test_amplitude_encoding_uses_controlled_gates() -> None:
    """Exact encoding for non-product states should use controlled-Ry."""
    enc = AmplitudeEncoding(n_qubits=2)
    # Non-product state: (1/sqrt(2), 0, 0, 1/sqrt(2))
    s = 1.0 / math.sqrt(2)
    circ = enc.to_circuit([s, 0.0, 0.0, s])
    # Should have controlled gates (not just independent Ry)
    from qdk_pythonic.core.instruction import Instruction

    has_controlled = any(
        isinstance(i, Instruction) and len(i.controls) > 0
        for i in circ.instructions
    )
    assert has_controlled


@pytest.mark.unit
def test_amplitude_encoding_basis_state() -> None:
    """Encoding a single basis state should produce a valid circuit."""
    enc = AmplitudeEncoding(n_qubits=2)
    circ = enc.to_circuit([0.0, 1.0, 0.0, 0.0])  # |01>
    assert circ.qubit_count() == 2
    assert circ.total_gate_count() > 0


# ------------------------------------------------------------------
# Codegen roundtrip (regression tests for qubit remapping)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_quantum_kernel_codegen_roundtrip() -> None:
    enc = AngleEncoding(n_features=3)
    kernel = QuantumKernel(enc)
    circ = kernel.to_circuit(x=[0.1, 0.2, 0.3], y=[0.4, 0.5, 0.6])
    qs = circ.to_qsharp()
    assert "Ry" in qs


@pytest.mark.unit
def test_variational_classifier_codegen_roundtrip() -> None:
    enc = AngleEncoding(n_features=3)
    ansatz = HardwareEfficientAnsatz(n_qubits=3, depth=1)
    clf = VariationalClassifier(enc, ansatz)
    params = [0.1] * ansatz.num_parameters
    circ = clf.to_circuit(data=[0.1, 0.2, 0.3], params=params)
    qs = circ.to_qsharp()
    assert "Ry" in qs
