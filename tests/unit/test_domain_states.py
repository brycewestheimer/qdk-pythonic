"""Tests for state preparation abstractions."""

from __future__ import annotations

import pytest

from qdk_pythonic.core.instruction import Instruction
from qdk_pythonic.domains.common.states import (
    BasisState,
    DiscreteProbabilityDistribution,
    UniformSuperposition,
)


@pytest.mark.unit
def test_basis_state_all_zeros() -> None:
    circ = BasisState("0000").to_circuit()
    assert circ.qubit_count() == 4
    assert circ.total_gate_count() == 0


@pytest.mark.unit
def test_basis_state_all_ones() -> None:
    circ = BasisState("111").to_circuit()
    assert circ.qubit_count() == 3
    assert circ.total_gate_count() == 3
    assert circ.gate_count()["X"] == 3


@pytest.mark.unit
def test_basis_state_mixed() -> None:
    circ = BasisState("1010").to_circuit()
    assert circ.qubit_count() == 4
    assert circ.gate_count()["X"] == 2


@pytest.mark.unit
def test_basis_state_invalid() -> None:
    with pytest.raises(ValueError, match="'0'/'1'"):
        BasisState("012")


@pytest.mark.unit
def test_basis_state_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        BasisState("")


@pytest.mark.unit
def test_uniform_superposition() -> None:
    circ = UniformSuperposition(4).to_circuit()
    assert circ.qubit_count() == 4
    assert circ.gate_count()["H"] == 4


@pytest.mark.unit
def test_uniform_superposition_invalid() -> None:
    with pytest.raises(ValueError, match="n_qubits must be >= 1"):
        UniformSuperposition(0)


@pytest.mark.unit
def test_discrete_distribution() -> None:
    probs = (0.25, 0.25, 0.25, 0.25)
    circ = DiscreteProbabilityDistribution(probs).to_circuit()
    assert circ.qubit_count() == 2
    # Should have Ry rotations
    gate_insts = [i for i in circ.instructions if isinstance(i, Instruction)]
    assert len(gate_insts) > 0


@pytest.mark.unit
def test_discrete_distribution_invalid_sum() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        DiscreteProbabilityDistribution((0.5, 0.3))


@pytest.mark.unit
def test_discrete_distribution_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        DiscreteProbabilityDistribution(())
