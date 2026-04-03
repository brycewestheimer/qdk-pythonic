"""Tests for ChemistryQPE."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.domains.chemistry.qpe import ChemistryQPE
from qdk_pythonic.domains.common.operators import PauliHamiltonian, X, Z
from qdk_pythonic.exceptions import CircuitError


def _simple_hamiltonian() -> PauliHamiltonian:
    """A 2-qubit Hamiltonian for testing."""
    h = PauliHamiltonian()
    h += -1.0 * Z(0) * Z(1)
    h += -0.5 * X(0)
    return h


@pytest.mark.unit
def test_qubit_count() -> None:
    h = _simple_hamiltonian()
    qpe = ChemistryQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=4)
    circ = qpe.to_circuit()
    # 2 system + 4 estimation = 6
    assert circ.qubit_count() == 6


@pytest.mark.unit
def test_single_qubit_hamiltonian() -> None:
    h = PauliHamiltonian([Z(0)])
    qpe = ChemistryQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=3)
    circ = qpe.to_circuit()
    # 1 system + 3 estimation = 4
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_circuit_has_hf_x_gates() -> None:
    """HF state preparation should add X gates."""
    h = _simple_hamiltonian()
    qpe = ChemistryQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=2)
    circ = qpe.to_circuit()
    gates = circ.gate_count()
    assert gates.get("X", 0) >= 1


@pytest.mark.unit
def test_circuit_has_h_gates() -> None:
    """Estimation register needs Hadamard gates."""
    h = _simple_hamiltonian()
    m = 4
    qpe = ChemistryQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=m)
    circ = qpe.to_circuit()
    gates = circ.gate_count()
    # At least m H gates from estimation + more from inverse QFT
    assert gates.get("H", 0) >= m


@pytest.mark.unit
def test_circuit_has_controlled_gates() -> None:
    """Controlled Trotter evolution should produce controlled gates."""
    h = PauliHamiltonian([Z(0)])
    qpe = ChemistryQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=2)
    circ = qpe.to_circuit()
    # Should have controlled rotation gates
    has_controlled = any(
        hasattr(inst, "controls") and inst.controls
        for inst in circ.instructions
    )
    assert has_controlled


@pytest.mark.unit
def test_energy_from_phase_zero() -> None:
    e = ChemistryQPE.energy_from_phase(0.0, 1.0)
    assert e == 0.0


@pytest.mark.unit
def test_energy_from_phase_half() -> None:
    e = ChemistryQPE.energy_from_phase(0.5, 1.0)
    assert abs(e - (-math.pi)) < 1e-10


@pytest.mark.unit
def test_energy_from_phase_with_time() -> None:
    """E = -2*pi*phi / t."""
    e = ChemistryQPE.energy_from_phase(0.25, 2.0)
    expected = -2.0 * math.pi * 0.25 / 2.0
    assert abs(e - expected) < 1e-10


@pytest.mark.unit
def test_frozen() -> None:
    h = PauliHamiltonian([Z(0)])
    qpe = ChemistryQPE(hamiltonian=h, n_electrons=1)
    with pytest.raises(AttributeError):
        qpe.n_electrons = 2  # type: ignore[misc]


@pytest.mark.unit
def test_invalid_estimation_qubits() -> None:
    h = PauliHamiltonian([Z(0)])
    with pytest.raises(CircuitError, match="n_estimation_qubits"):
        ChemistryQPE(hamiltonian=h, n_electrons=1, n_estimation_qubits=0)


@pytest.mark.unit
def test_invalid_n_electrons() -> None:
    h = PauliHamiltonian([Z(0)])
    with pytest.raises(CircuitError, match="n_electrons"):
        ChemistryQPE(hamiltonian=h, n_electrons=-1)


@pytest.mark.unit
def test_empty_hamiltonian() -> None:
    h = PauliHamiltonian()
    qpe = ChemistryQPE(hamiltonian=h, n_electrons=0, n_estimation_qubits=2)
    with pytest.raises(CircuitError, match="no qubit terms"):
        qpe.to_circuit()


@pytest.mark.unit
def test_more_estimation_qubits_more_gates() -> None:
    """More estimation qubits should produce a deeper circuit."""
    h = PauliHamiltonian([Z(0)])
    circ_2 = ChemistryQPE(
        hamiltonian=h, n_electrons=1, n_estimation_qubits=2,
    ).to_circuit()
    circ_4 = ChemistryQPE(
        hamiltonian=h, n_electrons=1, n_estimation_qubits=4,
    ).to_circuit()
    assert circ_4.total_gate_count() > circ_2.total_gate_count()
