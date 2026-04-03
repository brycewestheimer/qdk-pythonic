"""Tests for the QuSpin adapter.

All tests are pure Python and do not require QuSpin to be installed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from qdk_pythonic.adapters.quspin_adapter import (
    _expand_ladder_operators,
    _parse_quspin_operator_string,
    from_quspin_hamiltonian,
    from_quspin_static_list,
    simulate_quspin_model,
)

# ------------------------------------------------------------------
# _parse_quspin_operator_string
# ------------------------------------------------------------------


@pytest.mark.unit
def test_parse_operator_string_basic() -> None:
    assert _parse_quspin_operator_string("zz") == ["Z", "Z"]
    assert _parse_quspin_operator_string("x") == ["X"]
    assert _parse_quspin_operator_string("xyz") == ["X", "Y", "Z"]


@pytest.mark.unit
def test_parse_operator_string_ladder() -> None:
    assert _parse_quspin_operator_string("+-") == ["+", "-"]
    assert _parse_quspin_operator_string("-+") == ["-", "+"]


@pytest.mark.unit
def test_parse_operator_string_identity() -> None:
    assert _parse_quspin_operator_string("I") == ["I"]
    assert _parse_quspin_operator_string("zI") == ["Z", "I"]


@pytest.mark.unit
def test_parse_operator_string_invalid() -> None:
    with pytest.raises(ValueError, match="Unknown QuSpin operator"):
        _parse_quspin_operator_string("q")


# ------------------------------------------------------------------
# _expand_ladder_operators
# ------------------------------------------------------------------


@pytest.mark.unit
def test_expand_ladder_no_ladders() -> None:
    result = _expand_ladder_operators(["Z", "Z"], [0, 1], 1.0)
    assert len(result) == 1
    coeff, ops = result[0]
    assert coeff == pytest.approx(1.0)
    assert ops == {0: "Z", 1: "Z"}


@pytest.mark.unit
def test_expand_ladder_single_plus() -> None:
    # S+ = (X + iY) / 2
    result = _expand_ladder_operators(["+"], [0], 1.0)
    assert len(result) == 2
    by_ops = {tuple(sorted(ops.items())): coeff for coeff, ops in result}
    assert by_ops[((0, "X"),)] == pytest.approx(0.5)
    assert by_ops[((0, "Y"),)] == pytest.approx(0.5j)


@pytest.mark.unit
def test_expand_ladder_single_minus() -> None:
    # S- = (X - iY) / 2
    result = _expand_ladder_operators(["-"], [0], 1.0)
    assert len(result) == 2
    by_ops = {tuple(sorted(ops.items())): coeff for coeff, ops in result}
    assert by_ops[((0, "X"),)] == pytest.approx(0.5)
    assert by_ops[((0, "Y"),)] == pytest.approx(-0.5j)


@pytest.mark.unit
def test_expand_ladder_plus_minus() -> None:
    # S+_0 S-_1 = (X+iY)(X-iY)/4 → (XX + YY + iXY - iYX) / 4
    result = _expand_ladder_operators(["+", "-"], [0, 1], 1.0)
    assert len(result) == 4

    by_ops: dict[tuple[tuple[int, str], ...], complex] = {}
    for coeff, ops in result:
        key = tuple(sorted(ops.items()))
        by_ops[key] = coeff

    xx = ((0, "X"), (1, "X"))
    yy = ((0, "Y"), (1, "Y"))
    xy = ((0, "X"), (1, "Y"))
    yx = ((0, "Y"), (1, "X"))

    assert by_ops[xx] == pytest.approx(0.25)
    assert by_ops[yy] == pytest.approx(0.25)
    assert by_ops[xy] == pytest.approx(-0.25j)
    assert by_ops[yx] == pytest.approx(0.25j)


@pytest.mark.unit
def test_expand_ladder_hermitian_cancellation() -> None:
    """S+S- + S-S+ produces only real-coefficient terms."""
    terms_pm = _expand_ladder_operators(["+", "-"], [0, 1], 1.0)
    terms_mp = _expand_ladder_operators(["-", "+"], [0, 1], 1.0)

    combined: dict[tuple[tuple[int, str], ...], complex] = {}
    for coeff, ops in terms_pm + terms_mp:
        key = tuple(sorted(ops.items()))
        combined[key] = combined.get(key, 0) + coeff

    for key, coeff in combined.items():
        assert abs(coeff.imag) < 1e-14, (
            f"Imaginary residual for {key}: {coeff}"
        )


@pytest.mark.unit
def test_expand_ladder_identity_filtered() -> None:
    """Identity operators are not included in the pauli_ops dict."""
    result = _expand_ladder_operators(["I"], [0], 1.0)
    assert len(result) == 1
    assert result[0][1] == {}  # empty dict, identity term


@pytest.mark.unit
def test_expand_ladder_mixed() -> None:
    """Mix of ladder and regular operators."""
    result = _expand_ladder_operators(["+", "Z"], [0, 1], 2.0)
    assert len(result) == 2
    for coeff, ops in result:
        assert 1 in ops
        assert ops[1] == "Z"


# ------------------------------------------------------------------
# from_quspin_static_list
# ------------------------------------------------------------------


@pytest.mark.unit
def test_from_static_list_ising_1d() -> None:
    """4-site periodic Ising: 4 ZZ + 4 X = 8 terms."""
    L = 4
    J_zz = [[1.0, i, (i + 1) % L] for i in range(L)]
    h_x = [[0.5, i] for i in range(L)]
    static = [["zz", J_zz], ["x", h_x]]

    h = from_quspin_static_list(static, L)
    assert len(h.terms) == 8
    assert h.qubit_count() == 4


@pytest.mark.unit
def test_from_static_list_heisenberg_xx_yy_zz() -> None:
    """XX + YY + ZZ on a single bond → 3 terms."""
    static = [
        ["xx", [[1.0, 0, 1]]],
        ["yy", [[1.0, 0, 1]]],
        ["zz", [[1.0, 0, 1]]],
    ]
    h = from_quspin_static_list(static, 2)
    assert len(h.terms) == 3


@pytest.mark.unit
def test_from_static_list_three_body() -> None:
    """Three-body 'xyz' term produces one Pauli term."""
    static = [["xyz", [[1.0, 0, 1, 2]]]]
    h = from_quspin_static_list(static, 3)
    assert len(h.terms) == 1
    t = h.terms[0]
    assert t.pauli_ops == {0: "X", 1: "Y", 2: "Z"}


@pytest.mark.unit
def test_from_static_list_identity_filtered() -> None:
    """Pure identity 'I' terms are skipped (no pauli_ops)."""
    static = [["I", [[1.0, 0]]]]
    h = from_quspin_static_list(static, 1)
    assert len(h.terms) == 0


@pytest.mark.unit
def test_from_static_list_ladder_operators() -> None:
    """'+-' on one bond expands to multiple Pauli terms."""
    static = [["+-", [[1.0, 0, 1]]]]
    h = from_quspin_static_list(static, 2)
    assert len(h.terms) == 4  # XX, YY, XY, YX


@pytest.mark.unit
def test_from_static_list_site_count_mismatch() -> None:
    with pytest.raises(ValueError, match="expects 2 sites"):
        from_quspin_static_list([["zz", [[1.0, 0]]]], 2)


@pytest.mark.unit
def test_from_static_list_coefficient_signs() -> None:
    """Negative coupling should be preserved."""
    static = [["z", [[-1.5, 0]]]]
    h = from_quspin_static_list(static, 1)
    assert h.terms[0].coeff == pytest.approx(-1.5)


# ------------------------------------------------------------------
# simulate_quspin_model
# ------------------------------------------------------------------


@pytest.mark.unit
def test_simulate_quspin_model_structure() -> None:
    static = [["zz", [[1.0, 0, 1]]], ["x", [[0.5, 0], [0.5, 1]]]]
    result = simulate_quspin_model(static, n_sites=2, time=0.5, trotter_steps=2)

    expected_keys = {
        "hamiltonian", "circuit", "n_qubits", "gate_count",
        "total_gates", "depth", "n_hamiltonian_terms",
    }
    assert set(result.keys()) == expected_keys


@pytest.mark.unit
def test_simulate_quspin_model_circuit_properties() -> None:
    static = [["zz", [[1.0, 0, 1]]], ["x", [[0.5, 0], [0.5, 1]]]]
    result = simulate_quspin_model(static, n_sites=2, time=0.5, trotter_steps=2)

    assert result["n_qubits"] == 2
    assert result["total_gates"] > 0
    assert isinstance(result["depth"], int)
    assert result["n_hamiltonian_terms"] == 3  # 1 ZZ + 2 X


@pytest.mark.unit
def test_simulate_quspin_model_trotter_order() -> None:
    static = [["zz", [[1.0, 0, 1]]]]
    r1 = simulate_quspin_model(
        static, n_sites=2, time=0.5, trotter_steps=1, trotter_order=1,
    )
    r2 = simulate_quspin_model(
        static, n_sites=2, time=0.5, trotter_steps=1, trotter_order=2,
    )
    assert r2["total_gates"] == 2 * r1["total_gates"]


@pytest.mark.unit
def test_simulate_quspin_model_generates_qsharp() -> None:
    static = [["zz", [[1.0, 0, 1]]], ["x", [[0.5, 0], [0.5, 1]]]]
    result = simulate_quspin_model(static, n_sites=2, time=0.5, trotter_steps=2)
    qsharp_code = result["circuit"].to_qsharp()
    assert "Qubit" in qsharp_code


@pytest.mark.unit
def test_from_quspin_hamiltonian_mock() -> None:
    """Test with a mocked QuSpin hamiltonian object."""
    mock_ham = MagicMock()
    mock_ham.static_list = [["zz", [[1.0, 0, 1]]], ["x", [[0.5, 0]]]]
    mock_ham.dynamic_list = []

    # Patch quspin import so it doesn't fail
    import sys
    mock_quspin = MagicMock()
    sys.modules["quspin"] = mock_quspin
    sys.modules["quspin.operators"] = mock_quspin.operators
    try:
        h = from_quspin_hamiltonian(mock_ham, n_sites=2)
        assert len(h.terms) == 2  # 1 ZZ + 1 X
    finally:
        del sys.modules["quspin"]
        del sys.modules["quspin.operators"]
