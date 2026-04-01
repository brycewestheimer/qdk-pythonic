"""Tests for TrotterEvolution."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.common.evolution import TrotterEvolution
from qdk_pythonic.domains.common.operators import PauliHamiltonian, X, Z


@pytest.mark.unit
def test_to_circuit_delegates() -> None:
    h = PauliHamiltonian()
    h += -1.0 * Z(0) * Z(1)
    h += -0.5 * X(0)
    evo = TrotterEvolution(hamiltonian=h, time=1.0, steps=10)
    circ = evo.to_circuit()
    assert circ.qubit_count() == 2
    assert circ.total_gate_count() > 0


@pytest.mark.unit
def test_frozen() -> None:
    h = PauliHamiltonian([Z(0)])
    evo = TrotterEvolution(hamiltonian=h, time=1.0)
    with pytest.raises(AttributeError):
        evo.time = 2.0  # type: ignore[misc]


@pytest.mark.unit
def test_steps_multiplies_gates() -> None:
    h = PauliHamiltonian([Z(0)])
    evo1 = TrotterEvolution(hamiltonian=h, time=1.0, steps=1)
    evo5 = TrotterEvolution(hamiltonian=h, time=1.0, steps=5)
    assert evo5.to_circuit().total_gate_count() == (
        5 * evo1.to_circuit().total_gate_count()
    )


@pytest.mark.unit
def test_second_order() -> None:
    h = PauliHamiltonian([Z(0), X(1)])
    evo = TrotterEvolution(hamiltonian=h, time=1.0, steps=1, order=2)
    circ = evo.to_circuit()
    # Second-order doubles the gates
    assert circ.total_gate_count() == 4  # 2 terms * 2 (forward+reverse)
