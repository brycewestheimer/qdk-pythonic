"""Tests for qubit tapering via Z2 symmetries."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm, X, Y, Z
from qdk_pythonic.domains.common.tapering import (
    TaperingInfo,
    find_z2_symmetries,
    taper_hamiltonian,
)


def _h2_like_hamiltonian() -> PauliHamiltonian:
    """A simplified H2-like Hamiltonian with known Z2 symmetries.

    H = -0.5 Z0 Z1 + 0.3 Z0 + 0.3 Z1 + 0.2 X0 X1
    Symmetry: Z0 Z1 commutes with all terms.
    """
    h = PauliHamiltonian()
    h += PauliTerm(pauli_ops={0: "Z", 1: "Z"}, coeff=-0.5)
    h += PauliTerm(pauli_ops={0: "Z"}, coeff=0.3)
    h += PauliTerm(pauli_ops={1: "Z"}, coeff=0.3)
    h += PauliTerm(pauli_ops={0: "X", 1: "X"}, coeff=0.2)
    return h


def _diagonal_hamiltonian() -> PauliHamiltonian:
    """All-Z Hamiltonian: every Z-string is a symmetry."""
    h = PauliHamiltonian()
    h += -1.0 * Z(0)
    h += 0.5 * Z(1)
    h += PauliTerm(pauli_ops={0: "Z", 1: "Z"}, coeff=-0.3)
    return h


# ── find_z2_symmetries ──


@pytest.mark.unit
def test_find_symmetries_h2_like() -> None:
    h = _h2_like_hamiltonian()
    syms = find_z2_symmetries(h)
    # X0 X1 has X on qubits 0,1; so a Z-string symmetry must have
    # even overlap with {0,1}. Z0 Z1 has overlap 2 (even) -> commutes.
    # Z0 alone has overlap 1 (odd) with X0 X1 -> doesn't commute.
    # So Z0 Z1 should be a symmetry.
    assert len(syms) >= 1
    # Check that at least one symmetry involves both qubits
    has_z0z1 = any(
        set(s.pauli_ops.keys()) == {0, 1}
        and all(op == "Z" for op in s.pauli_ops.values())
        for s in syms
    )
    assert has_z0z1


@pytest.mark.unit
def test_find_symmetries_diagonal() -> None:
    """All-Z Hamiltonian should have many symmetries."""
    h = _diagonal_hamiltonian()
    syms = find_z2_symmetries(h)
    # Every Z-string commutes with an all-Z Hamiltonian
    assert len(syms) >= 1


@pytest.mark.unit
def test_find_symmetries_no_symmetry() -> None:
    """A Hamiltonian with X,Y,Z on the same qubit has no Z symmetry."""
    h = PauliHamiltonian()
    h += X(0)
    h += Y(0)
    h += Z(0)
    syms = find_z2_symmetries(h)
    # X on qubit 0 means any Z-string on qubit 0 anticommutes
    # Y on qubit 0 same. So no single-qubit Z symmetry exists.
    # No multi-qubit symmetry either (only 1 qubit).
    assert len(syms) == 0


@pytest.mark.unit
def test_find_symmetries_empty() -> None:
    h = PauliHamiltonian()
    syms = find_z2_symmetries(h)
    assert syms == []


# ── taper_hamiltonian ──


@pytest.mark.unit
def test_taper_reduces_qubits() -> None:
    h = _h2_like_hamiltonian()
    tapered_h, info = taper_hamiltonian(h)
    assert info.n_symmetries >= 1
    assert info.tapered_qubits < info.original_qubits
    assert tapered_h.qubit_count() < h.qubit_count()


@pytest.mark.unit
def test_taper_preserves_terms() -> None:
    """Tapered Hamiltonian should still have terms."""
    h = _h2_like_hamiltonian()
    tapered_h, _ = taper_hamiltonian(h)
    assert len(tapered_h) > 0


@pytest.mark.unit
def test_taper_diagonal_reduces_maximally() -> None:
    """All-Z Hamiltonian should taper down significantly."""
    h = _diagonal_hamiltonian()
    tapered_h, info = taper_hamiltonian(h)
    assert info.tapered_qubits < info.original_qubits


@pytest.mark.unit
def test_taper_no_symmetry_unchanged() -> None:
    """No symmetry means no reduction."""
    h = PauliHamiltonian()
    h += X(0)
    h += Y(0)
    h += Z(0)
    tapered_h, info = taper_hamiltonian(h)
    assert info.n_symmetries == 0
    assert info.tapered_qubits == info.original_qubits
    assert len(tapered_h) == len(h)


@pytest.mark.unit
def test_taper_with_eigenvalues() -> None:
    """Different eigenvalue sectors should give different results."""
    h = _h2_like_hamiltonian()
    syms = find_z2_symmetries(h)
    n = len(syms)

    h_plus, _ = taper_hamiltonian(h, symmetry_eigenvalues=[1] * n)
    h_minus, _ = taper_hamiltonian(h, symmetry_eigenvalues=[-1] * n)

    # Different sectors should give different Hamiltonians
    # (at least different coefficients)
    plus_coeffs = sorted([t.coeff.real for t in h_plus.terms])
    minus_coeffs = sorted([t.coeff.real for t in h_minus.terms])
    assert plus_coeffs != minus_coeffs


@pytest.mark.unit
def test_taper_wrong_eigenvalue_count() -> None:
    h = _h2_like_hamiltonian()
    with pytest.raises(ValueError, match="Expected"):
        taper_hamiltonian(h, symmetry_eigenvalues=[1, 1, 1, 1, 1])


@pytest.mark.unit
def test_taper_info_fields() -> None:
    h = _h2_like_hamiltonian()
    _, info = taper_hamiltonian(h)
    assert isinstance(info, TaperingInfo)
    assert info.original_qubits == h.qubit_count()
    assert len(info.pivot_qubits) == info.n_symmetries
    assert len(info.eigenvalues) == info.n_symmetries


@pytest.mark.unit
def test_taper_info_frozen() -> None:
    h = _h2_like_hamiltonian()
    _, info = taper_hamiltonian(h)
    with pytest.raises(AttributeError):
        info.n_symmetries = 0  # type: ignore[misc]


@pytest.mark.unit
def test_taper_compacts_indices() -> None:
    """Tapered qubits should have contiguous indices starting at 0."""
    h = _h2_like_hamiltonian()
    tapered_h, info = taper_hamiltonian(h)
    if tapered_h.qubit_count() > 0:
        indices = tapered_h.qubit_indices()
        assert indices[0] == 0
        assert indices[-1] == tapered_h.qubit_count() - 1


@pytest.mark.unit
def test_taper_identity_term_preserved() -> None:
    """Identity (constant) terms should survive tapering."""
    h = PauliHamiltonian()
    h += PauliTerm(pauli_ops={}, coeff=1.5)  # identity
    h += -1.0 * Z(0) * Z(1)
    h += 0.5 * Z(0)
    tapered_h, _ = taper_hamiltonian(h)
    # Identity should still be present
    has_identity = any(not t.pauli_ops for t in tapered_h.terms)
    assert has_identity
