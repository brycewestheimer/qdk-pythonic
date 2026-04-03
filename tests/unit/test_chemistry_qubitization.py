"""Tests for ChemistryQubitization wrapper."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.chemistry.qubitization import (
    ChemistryQubitization,
)
from qdk_pythonic.domains.common.operators import PauliHamiltonian, X, Z
from qdk_pythonic.exceptions import CircuitError


def _simple_hamiltonian() -> PauliHamiltonian:
    h = PauliHamiltonian()
    h += -1.0 * Z(0) * Z(1)
    h += -0.5 * X(0)
    return h


@pytest.mark.unit
def test_gate_level_circuit_builds() -> None:
    h = _simple_hamiltonian()
    cq = ChemistryQubitization(
        hamiltonian=h, n_electrons=1,
        n_estimation_qubits=2, gate_level=True,
    )
    circ = cq.to_circuit()
    # system(2) + ancilla(1) + estimation(2) = 5
    assert circ.qubit_count() == 5


@pytest.mark.unit
def test_gate_level_false_rejects_to_circuit() -> None:
    h = _simple_hamiltonian()
    cq = ChemistryQubitization(
        hamiltonian=h, n_electrons=1, gate_level=False,
    )
    with pytest.raises(CircuitError, match="gate_level=True"):
        cq.to_circuit()


@pytest.mark.unit
def test_bridge_mode_rejects_pauli_hamiltonian() -> None:
    """Bridge mode needs DF or FCIDUMP, not raw Pauli."""
    h = _simple_hamiltonian()
    cq = ChemistryQubitization(
        hamiltonian=h, n_electrons=1, gate_level=False,
    )
    with pytest.raises((CircuitError, ImportError)):
        cq.estimate_resources()


@pytest.mark.unit
def test_frozen() -> None:
    h = _simple_hamiltonian()
    cq = ChemistryQubitization(
        hamiltonian=h, n_electrons=1,
    )
    with pytest.raises(AttributeError):
        cq.n_electrons = 2  # type: ignore[misc]


@pytest.mark.unit
def test_invalid_estimation_qubits() -> None:
    h = _simple_hamiltonian()
    with pytest.raises(CircuitError, match="n_estimation_qubits"):
        ChemistryQubitization(
            hamiltonian=h, n_electrons=1, n_estimation_qubits=0,
        )


@pytest.mark.unit
def test_invalid_electrons() -> None:
    h = _simple_hamiltonian()
    with pytest.raises(CircuitError, match="n_electrons"):
        ChemistryQubitization(hamiltonian=h, n_electrons=-1)


@pytest.mark.unit
def test_gate_level_with_df_hamiltonian() -> None:
    """DF Hamiltonian should be converted to Pauli for gate-level."""
    np = pytest.importorskip("numpy")
    from qdk_pythonic.domains.common.double_factorization import (
        double_factorize,
    )

    h1e = np.array([[-1.0, 0.0], [0.0, -0.5]])
    h2e = np.zeros((2, 2, 2, 2))
    h2e[0, 0, 0, 0] = 0.5
    df = double_factorize(h1e, h2e, 0.7, n_electrons=2, threshold=1e-10)

    cq = ChemistryQubitization(
        hamiltonian=df, n_electrons=2,
        n_estimation_qubits=2, gate_level=True,
    )
    circ = cq.to_circuit()
    assert circ.qubit_count() > 0
