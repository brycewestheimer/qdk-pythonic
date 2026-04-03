"""Tests for Jordan-Wigner and Bravyi-Kitaev qubit mappings."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.common.fermion import (
    FermionOperator,
    FermionTerm,
    hopping,
    number_operator,
)
from qdk_pythonic.domains.common.mapping import (
    BravyiKitaevMapping,
    JordanWignerMapping,
    QubitMapping,
    bravyi_kitaev,
    jordan_wigner,
)
from qdk_pythonic.registry import _factories, available, create


@pytest.fixture(autouse=True)
def _clean_registry():  # type: ignore[no-untyped-def]
    """Save and restore registry between tests."""
    original = list(_factories)
    yield
    _factories.clear()
    _factories.extend(original)


# ------------------------------------------------------------------
# Jordan-Wigner mapping
# ------------------------------------------------------------------


@pytest.mark.unit
def test_jw_number_operator() -> None:
    """n_0 -> (I - Z_0) / 2 = 0.5*I - 0.5*Z_0."""
    n0 = number_operator(0)
    h = jordan_wigner(n0)
    # Should have 2 terms: identity (coeff 0.5) and Z_0 (coeff -0.5)
    coeffs = {}
    for t in h.terms:
        key = tuple(sorted(t.pauli_ops.items()))
        coeffs[key] = coeffs.get(key, 0) + t.coeff
    # Filter near-zero
    coeffs = {k: v for k, v in coeffs.items() if abs(v) > 1e-10}
    # Identity term
    assert coeffs.get((), 0) == pytest.approx(0.5)
    # Z_0 term
    assert coeffs.get(((0, "Z"),), 0) == pytest.approx(-0.5)


@pytest.mark.unit
def test_jw_single_hopping() -> None:
    """a†_0 a_1 + h.c. -> 0.5*(X_0 X_1 + Y_0 Y_1)."""
    hop = hopping(0, 1, coeff=1.0)
    h = jordan_wigner(hop)
    # Collect terms by Pauli string
    coeffs: dict[tuple[tuple[int, str], ...], complex] = {}
    for t in h.terms:
        key = tuple(sorted(t.pauli_ops.items()))
        coeffs[key] = coeffs.get(key, 0) + t.coeff
    coeffs = {k: v for k, v in coeffs.items() if abs(v) > 1e-10}
    xx = ((0, "X"), (1, "X"))
    yy = ((0, "Y"), (1, "Y"))
    assert coeffs.get(xx, 0) == pytest.approx(0.5)
    assert coeffs.get(yy, 0) == pytest.approx(0.5)


@pytest.mark.unit
def test_jw_hopping_with_gap() -> None:
    """a†_0 a_2 + h.c. should include Z_1 string."""
    hop = hopping(0, 2, coeff=1.0)
    h = jordan_wigner(hop)
    # Terms should involve qubit 1 as Z
    all_qubits: set[int] = set()
    for t in h.terms:
        all_qubits.update(t.pauli_ops.keys())
    assert 1 in all_qubits  # Z string passes through qubit 1


@pytest.mark.unit
def test_jw_onsite_interaction() -> None:
    """n_0 * n_1 -> known ZZ + Z terms."""
    # Build n_0 * n_1 as a FermionOperator
    n0 = number_operator(0)
    n1 = number_operator(1)
    op = FermionOperator()
    for t0 in n0.terms:
        for t1 in n1.terms:
            op += t0 * t1
    h = jordan_wigner(op)
    assert h.qubit_count() <= 2
    assert len(h.terms) > 0


@pytest.mark.unit
def test_jw_hermitian_output() -> None:
    """JW of a Hermitian fermionic operator has real coefficients."""
    hop = hopping(0, 1, coeff=1.0)
    h = jordan_wigner(hop)
    coeffs: dict[tuple[tuple[int, str], ...], complex] = {}
    for t in h.terms:
        key = tuple(sorted(t.pauli_ops.items()))
        coeffs[key] = coeffs.get(key, 0) + t.coeff
    for v in coeffs.values():
        if abs(v) > 1e-10:
            assert abs(v.imag) < 1e-10


@pytest.mark.unit
def test_jw_identity_term() -> None:
    """A constant (identity) FermionTerm maps to a Pauli identity."""
    op = FermionOperator([FermionTerm(operators=(), coeff=0.7)])
    h = jordan_wigner(op)
    assert len(h.terms) == 1
    assert h.terms[0].pauli_ops == {}
    assert h.terms[0].coeff == pytest.approx(0.7)


# ------------------------------------------------------------------
# Bravyi-Kitaev mapping
# ------------------------------------------------------------------


@pytest.mark.unit
def test_bk_number_operator() -> None:
    """BK of n_0 should give same physical result as JW."""
    n0 = number_operator(0)
    h_jw = jordan_wigner(n0)
    h_bk = bravyi_kitaev(n0)
    # Both should have the same 1-norm (same expectation values)
    s_jw = h_jw.summary()
    s_bk = h_bk.summary()
    assert s_jw["one_norm"] == pytest.approx(s_bk["one_norm"])


@pytest.mark.unit
def test_bk_single_hopping() -> None:
    """BK of hopping(0, 1) should produce valid Pauli Hamiltonian."""
    hop = hopping(0, 1, coeff=1.0)
    h = bravyi_kitaev(hop)
    assert len(h.terms) > 0
    # Coefficients for Hermitian input should be real after combining
    coeffs: dict[tuple[tuple[int, str], ...], complex] = {}
    for t in h.terms:
        key = tuple(sorted(t.pauli_ops.items()))
        coeffs[key] = coeffs.get(key, 0) + t.coeff
    for v in coeffs.values():
        if abs(v) > 1e-10:
            assert abs(v.imag) < 1e-10


@pytest.mark.unit
def test_bk_identity_term() -> None:
    """A constant FermionTerm maps to Pauli identity under BK too."""
    op = FermionOperator([FermionTerm(operators=(), coeff=0.7)])
    h = bravyi_kitaev(op)
    assert len(h.terms) == 1
    assert h.terms[0].pauli_ops == {}
    assert h.terms[0].coeff == pytest.approx(0.7)


@pytest.mark.unit
def test_mapping_protocol() -> None:
    """Both implementations satisfy the QubitMapping protocol."""
    assert isinstance(JordanWignerMapping(), QubitMapping)
    assert isinstance(BravyiKitaevMapping(), QubitMapping)


@pytest.mark.unit
def test_jordan_wigner_convenience() -> None:
    """Standalone function matches class method."""
    n0 = number_operator(0)
    h1 = jordan_wigner(n0)
    h2 = JordanWignerMapping().map(n0)
    assert len(h1.terms) == len(h2.terms)


@pytest.mark.unit
def test_bravyi_kitaev_convenience() -> None:
    """Standalone function matches class method."""
    n0 = number_operator(0)
    h1 = bravyi_kitaev(n0)
    h2 = BravyiKitaevMapping().map(n0)
    assert len(h1.terms) == len(h2.terms)


# ------------------------------------------------------------------
# Registry integration
# ------------------------------------------------------------------


@pytest.mark.unit
def test_create_jordan_wigner_mapper() -> None:
    from qdk_pythonic.domains.common.mapping import load_mappings
    load_mappings()
    algo = create("qubit_mapper", "jw")
    assert algo.name() == "jordan_wigner"


@pytest.mark.unit
def test_create_bravyi_kitaev_mapper() -> None:
    from qdk_pythonic.domains.common.mapping import load_mappings
    load_mappings()
    algo = create("qubit_mapper", "bk")
    assert algo.name() == "bravyi_kitaev"


@pytest.mark.unit
def test_available_qubit_mappers() -> None:
    from qdk_pythonic.domains.common.mapping import load_mappings
    load_mappings()
    avail = available("qubit_mapper")
    assert "qubit_mapper" in avail
    names = avail["qubit_mapper"]
    assert "jordan_wigner" in names
    assert "jw" in names
    assert "bravyi_kitaev" in names
    assert "bk" in names
