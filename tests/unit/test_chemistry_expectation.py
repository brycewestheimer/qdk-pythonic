"""Tests for expectation value measurement utilities."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.chemistry.expectation import (
    group_commuting_terms,
)
from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm, X, Y, Z


@pytest.mark.unit
def test_group_single_term() -> None:
    h = PauliHamiltonian([Z(0)])
    groups = group_commuting_terms(h)
    assert len(groups) == 1
    assert len(groups[0]) == 1


@pytest.mark.unit
def test_group_commuting_zz_and_z() -> None:
    """Z(0)*Z(1) and Z(0) are qubit-wise commuting (both Z on qubit 0)."""
    h = PauliHamiltonian()
    h += Z(0) * Z(1)
    h += Z(0)
    groups = group_commuting_terms(h)
    # Both should be in the same group
    assert len(groups) == 1
    assert len(groups[0]) == 2


@pytest.mark.unit
def test_group_non_commuting_z_and_x() -> None:
    """Z(0) and X(0) do not qubit-wise commute."""
    h = PauliHamiltonian()
    h += Z(0)
    h += X(0)
    groups = group_commuting_terms(h)
    assert len(groups) == 2


@pytest.mark.unit
def test_group_identity_term() -> None:
    """Identity term commutes with everything."""
    identity = PauliTerm(pauli_ops={}, coeff=1.5)
    h = PauliHamiltonian([identity, Z(0)])
    groups = group_commuting_terms(h)
    # Identity should group with Z(0)
    assert len(groups) == 1


@pytest.mark.unit
def test_group_complex_hamiltonian() -> None:
    """A typical molecular Hamiltonian has multiple groups."""
    h = PauliHamiltonian()
    h += -0.5 * Z(0) * Z(1)
    h += 0.3 * X(0) * X(1)
    h += 0.3 * Y(0) * Y(1)
    h += -0.2 * Z(0)
    h += -0.2 * Z(1)
    groups = group_commuting_terms(h)
    # ZZ, Z(0), Z(1) should group together; XX in another; YY in another
    total_terms = sum(len(g) for g in groups)
    assert total_terms == 5
    assert len(groups) >= 2


@pytest.mark.unit
def test_group_preserves_all_terms() -> None:
    """All terms should appear exactly once across all groups."""
    h = PauliHamiltonian()
    h += Z(0)
    h += X(0)
    h += Y(0)
    h += Z(1)
    groups = group_commuting_terms(h)
    all_terms = [t for g in groups for t in g]
    assert len(all_terms) == 4


@pytest.mark.unit
def test_group_empty_hamiltonian() -> None:
    h = PauliHamiltonian()
    groups = group_commuting_terms(h)
    assert groups == []


@pytest.mark.unit
def test_group_disjoint_qubits_commute() -> None:
    """Terms on different qubits always commute."""
    h = PauliHamiltonian()
    h += X(0)
    h += Y(1)
    h += Z(2)
    groups = group_commuting_terms(h)
    # All on different qubits -> single group
    assert len(groups) == 1
    assert len(groups[0]) == 3
