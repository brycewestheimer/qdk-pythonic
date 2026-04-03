"""Tests for FermionTerm, FermionOperator, and builder functions."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.common.fermion import (
    FermionOperator,
    FermionTerm,
    annihilation,
    creation,
    from_integrals,
    hopping,
    number_operator,
)


# ------------------------------------------------------------------
# FermionTerm
# ------------------------------------------------------------------


@pytest.mark.unit
def test_creation_annihilation() -> None:
    c = creation(0)
    assert c.operators == ((0, True),)
    assert c.coeff == 1.0

    a = annihilation(1)
    assert a.operators == ((1, False),)
    assert a.coeff == 1.0


@pytest.mark.unit
def test_fermion_term_scalar_multiply() -> None:
    t = 0.5 * creation(0)
    assert t.coeff == pytest.approx(0.5)
    assert t.operators == ((0, True),)

    t2 = creation(0) * 0.3
    assert t2.coeff == pytest.approx(0.3)


@pytest.mark.unit
def test_fermion_term_multiply() -> None:
    # a†_0 * a_1 should concatenate operators
    t = creation(0) * annihilation(1)
    assert t.operators == ((0, True), (1, False))
    assert t.coeff == pytest.approx(1.0)


@pytest.mark.unit
def test_fermion_term_adjoint() -> None:
    # (a†_0 a_1)† = a†_1 a_0
    t = FermionTerm(operators=((0, True), (1, False)), coeff=1.0 + 0.5j)
    adj = t.adjoint()
    assert adj.operators == ((1, True), (0, False))
    assert adj.coeff == pytest.approx(1.0 - 0.5j)


@pytest.mark.unit
def test_fermion_term_num_modes() -> None:
    t = FermionTerm(operators=((0, True), (3, False)))
    assert t.num_modes == 4
    empty = FermionTerm(operators=())
    assert empty.num_modes == 0


# ------------------------------------------------------------------
# FermionOperator
# ------------------------------------------------------------------


@pytest.mark.unit
def test_fermion_operator_iadd() -> None:
    op = FermionOperator()
    op += creation(0) * annihilation(1)
    op += creation(1) * annihilation(0)
    assert len(op) == 2


@pytest.mark.unit
def test_fermion_operator_add() -> None:
    op1 = FermionOperator([creation(0) * annihilation(1)])
    op2 = FermionOperator([creation(1) * annihilation(0)])
    op3 = op1 + op2
    assert len(op3) == 2
    assert len(op1) == 1  # original unchanged


@pytest.mark.unit
def test_fermion_operator_num_modes() -> None:
    op = FermionOperator([
        FermionTerm(operators=((0, True), (3, False))),
        FermionTerm(operators=((2, True), (5, False))),
    ])
    assert op.num_modes == 6


@pytest.mark.unit
def test_fermion_operator_adjoint() -> None:
    op = FermionOperator([
        FermionTerm(operators=((0, True), (1, False)), coeff=1.0),
    ])
    adj = op.adjoint()
    assert len(adj) == 1
    assert adj.terms[0].operators == ((1, True), (0, False))


@pytest.mark.unit
def test_fermion_operator_repr() -> None:
    op = FermionOperator([creation(0)])
    assert repr(op) == "FermionOperator(n_terms=1)"


# ------------------------------------------------------------------
# Builder functions
# ------------------------------------------------------------------


@pytest.mark.unit
def test_number_operator() -> None:
    n = number_operator(2)
    assert len(n) == 1
    assert n.terms[0].operators == ((2, True), (2, False))
    assert n.terms[0].coeff == pytest.approx(1.0)


@pytest.mark.unit
def test_hopping() -> None:
    h = hopping(0, 1, coeff=-1.0)
    assert len(h) == 2
    # a†_0 a_1
    assert h.terms[0].operators == ((0, True), (1, False))
    assert h.terms[0].coeff == pytest.approx(-1.0)
    # a†_1 a_0
    assert h.terms[1].operators == ((1, True), (0, False))
    assert h.terms[1].coeff == pytest.approx(-1.0)


@pytest.mark.unit
def test_from_integrals_one_body() -> None:
    # Simple 2-mode system with only one-body terms
    h1e = [[1.0, 0.5], [0.5, 2.0]]
    h2e = [[[[0.0] * 2] * 2] * 2] * 2
    op = from_integrals(h1e, h2e)
    # 2x2 = 4 one-body terms (filtering zeros)
    # h1e has 4 non-zero entries (diagonal + off-diagonal)
    non_zero = [t for t in op.terms if abs(t.coeff) > 1e-15]
    assert len(non_zero) == 4


@pytest.mark.unit
def test_from_integrals_filters_zeros() -> None:
    h1e = [[0.0, 0.0], [0.0, 0.0]]
    h2e = [[[[0.0] * 2] * 2] * 2] * 2
    op = from_integrals(h1e, h2e)
    assert len(op) == 0


@pytest.mark.unit
def test_from_integrals_nuclear_repulsion() -> None:
    h1e = [[0.0]]
    h2e = [[[[0.0]]]]
    op = from_integrals(h1e, h2e, nuclear_repulsion=0.7)
    assert len(op) == 1
    assert op.terms[0].operators == ()
    assert op.terms[0].coeff == pytest.approx(0.7)
