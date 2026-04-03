"""Tests for VQE."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz
from qdk_pythonic.domains.chemistry.vqe import VQE, VQEResult
from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz
from qdk_pythonic.domains.common.operators import PauliHamiltonian, Z
from qdk_pythonic.exceptions import CircuitError


def _h2_hamiltonian() -> PauliHamiltonian:
    """Trivial diagonal Hamiltonian for testing."""
    h = PauliHamiltonian()
    h += -1.0 * Z(0)
    h += 0.5 * Z(1)
    return h


@pytest.mark.unit
def test_vqe_result_frozen() -> None:
    result = VQEResult(
        optimal_energy=-1.0,
        optimal_params=(0.1, 0.2),
        history=(-0.5, -0.8, -1.0),
        n_iterations=3,
        converged=True,
    )
    with pytest.raises(AttributeError):
        result.optimal_energy = -2.0  # type: ignore[misc]


@pytest.mark.unit
def test_vqe_result_fields() -> None:
    result = VQEResult(
        optimal_energy=-1.0,
        optimal_params=(0.1,),
        history=(-0.5, -1.0),
        n_iterations=2,
        converged=True,
    )
    assert result.optimal_energy == -1.0
    assert result.optimal_params == (0.1,)
    assert len(result.history) == 2
    assert result.converged is True


@pytest.mark.unit
def test_to_circuit_uccsd() -> None:
    h = _h2_hamiltonian()
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    vqe = VQE(hamiltonian=h, ansatz=ansatz, n_electrons=2)
    params = [0.1] * ansatz.num_parameters
    circ = vqe.to_circuit(params)
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_to_circuit_hardware_efficient() -> None:
    h = _h2_hamiltonian()
    ansatz = HardwareEfficientAnsatz(n_qubits=2, depth=1)
    vqe = VQE(hamiltonian=h, ansatz=ansatz)
    params = [0.1] * ansatz.num_parameters
    circ = vqe.to_circuit(params)
    assert circ.qubit_count() == 2


@pytest.mark.unit
def test_to_circuit_hardware_efficient_with_hf() -> None:
    """HF state should be prepended when n_electrons is set."""
    h = _h2_hamiltonian()
    ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=1)
    vqe = VQE(hamiltonian=h, ansatz=ansatz, n_electrons=2)
    params = [0.1] * ansatz.num_parameters
    circ = vqe.to_circuit(params)
    assert circ.qubit_count() == 4
    # Should have X gates from HF state
    assert circ.gate_count().get("X", 0) >= 2


@pytest.mark.unit
def test_wrong_initial_params_length() -> None:
    """VQE.run() should reject wrong-length initial params."""
    pytest.importorskip("scipy")
    h = PauliHamiltonian([Z(0)])
    ansatz = HardwareEfficientAnsatz(n_qubits=1, depth=1)
    vqe = VQE(hamiltonian=h, ansatz=ansatz)
    with pytest.raises(CircuitError, match="Expected"):
        vqe.run(initial_params=[0.1, 0.2, 0.3, 0.4, 0.5])


@pytest.mark.unit
def test_estimate_resources_returns_circuit() -> None:
    """estimate_resources should build a circuit (execution requires qsharp)."""
    h = PauliHamiltonian([Z(0)])
    ansatz = HardwareEfficientAnsatz(n_qubits=1, depth=1)
    vqe = VQE(hamiltonian=h, ansatz=ansatz)
    # Just verify to_circuit works with default params
    circ = vqe.to_circuit([0.0] * ansatz.num_parameters)
    assert circ.qubit_count() == 1
