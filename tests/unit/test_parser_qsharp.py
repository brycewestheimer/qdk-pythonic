"""Tests for the Q# parser."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.gates import (
    CCNOT,
    CNOT,
    CZ,
    R1,
    RX,
    RY,
    RZ,
    SWAP,
    H,
    S,
    T,
    X,
    Y,
    Z,
)
from qdk_pythonic.core.instruction import Instruction, Measurement
from qdk_pythonic.exceptions import ParserError, UnsupportedConstructError
from qdk_pythonic.parser.qsharp_parser import QSharpParser


def _gate_instructions(circ: Circuit) -> list[Instruction]:
    """Extract only gate instructions from a circuit."""
    return [i for i in circ.instructions if isinstance(i, Instruction)]


def _measurements(circ: Circuit) -> list[Measurement]:
    """Extract only measurements from a circuit."""
    return [i for i in circ.instructions if isinstance(i, Measurement)]


# ------------------------------------------------------------------
# Bell state
# ------------------------------------------------------------------


@pytest.mark.unit
def test_bell_state() -> None:
    source = """
{
    use q = Qubit[2];
    H(q[0]);
    CNOT(q[0], q[1]);
    let r0 = MResetZ(q[0]);
    let r1 = MResetZ(q[1]);
    [r0, r1]
}
"""
    circ = QSharpParser().parse(source)
    assert circ.qubit_count() == 2
    assert len(_gate_instructions(circ)) == 2
    assert len(_measurements(circ)) == 2
    gates = _gate_instructions(circ)
    assert gates[0].gate is H
    assert gates[1].gate is CNOT


# ------------------------------------------------------------------
# GHZ state
# ------------------------------------------------------------------


@pytest.mark.unit
def test_ghz_state() -> None:
    source = """
{
    use q = Qubit[3];
    H(q[0]);
    CNOT(q[0], q[1]);
    CNOT(q[1], q[2]);
}
"""
    circ = QSharpParser().parse(source)
    assert circ.qubit_count() == 3
    gates = _gate_instructions(circ)
    assert len(gates) == 3
    assert gates[0].gate is H
    assert gates[1].gate is CNOT
    assert gates[2].gate is CNOT


# ------------------------------------------------------------------
# Parameterized rotation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_rx_with_angle() -> None:
    source = """
{
    use q = Qubit[1];
    Rx(1.5707, q[0]);
}
"""
    circ = QSharpParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is RX
    assert math.isclose(gates[0].params[0], 1.5707, rel_tol=1e-9)


# ------------------------------------------------------------------
# Controlled gate
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_gate() -> None:
    source = """
{
    use q = Qubit[2];
    Controlled H([q[0]], q[1]);
}
"""
    circ = QSharpParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is H
    assert len(gates[0].controls) == 1
    assert gates[0].is_adjoint is False


# ------------------------------------------------------------------
# Adjoint gate
# ------------------------------------------------------------------


@pytest.mark.unit
def test_adjoint_gate() -> None:
    source = """
{
    use q = Qubit[1];
    Adjoint S(q[0]);
}
"""
    circ = QSharpParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is S
    assert gates[0].is_adjoint is True


# ------------------------------------------------------------------
# Controlled Adjoint gate
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_adjoint_gate() -> None:
    source = """
{
    use q = Qubit[2];
    Controlled Adjoint S([q[0]], q[1]);
}
"""
    circ = QSharpParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is S
    assert len(gates[0].controls) == 1
    assert gates[0].is_adjoint is True


# ------------------------------------------------------------------
# All 14 gate types
# ------------------------------------------------------------------


@pytest.mark.unit
def test_h_gate() -> None:
    source = "{ use q = Qubit[1]; H(q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is H


@pytest.mark.unit
def test_x_gate() -> None:
    source = "{ use q = Qubit[1]; X(q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is X


@pytest.mark.unit
def test_y_gate() -> None:
    source = "{ use q = Qubit[1]; Y(q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is Y


@pytest.mark.unit
def test_z_gate() -> None:
    source = "{ use q = Qubit[1]; Z(q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is Z


@pytest.mark.unit
def test_s_gate() -> None:
    source = "{ use q = Qubit[1]; S(q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is S


@pytest.mark.unit
def test_t_gate() -> None:
    source = "{ use q = Qubit[1]; T(q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is T


@pytest.mark.unit
def test_rx_gate() -> None:
    source = "{ use q = Qubit[1]; Rx(0.5, q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is RX
    assert math.isclose(gates[0].params[0], 0.5)


@pytest.mark.unit
def test_ry_gate() -> None:
    source = "{ use q = Qubit[1]; Ry(0.5, q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is RY


@pytest.mark.unit
def test_rz_gate() -> None:
    source = "{ use q = Qubit[1]; Rz(0.5, q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is RZ


@pytest.mark.unit
def test_r1_gate() -> None:
    source = "{ use q = Qubit[1]; R1(0.5, q[0]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is R1


@pytest.mark.unit
def test_cnot_gate() -> None:
    source = "{ use q = Qubit[2]; CNOT(q[0], q[1]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is CNOT


@pytest.mark.unit
def test_cz_gate() -> None:
    source = "{ use q = Qubit[2]; CZ(q[0], q[1]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is CZ


@pytest.mark.unit
def test_swap_gate() -> None:
    source = "{ use q = Qubit[2]; SWAP(q[0], q[1]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is SWAP


@pytest.mark.unit
def test_ccnot_gate() -> None:
    source = "{ use q = Qubit[3]; CCNOT(q[0], q[1], q[2]); }"
    gates = _gate_instructions(QSharpParser().parse(source))
    assert gates[0].gate is CCNOT


# ------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------


@pytest.mark.unit
def test_unsupported_for_loop() -> None:
    source = """
{
    use q = Qubit[1];
    for i in 0..3 {
        H(q[0]);
    }
}
"""
    with pytest.raises(UnsupportedConstructError, match="for"):
        QSharpParser().parse(source)


@pytest.mark.unit
def test_unsupported_if_statement() -> None:
    source = """
{
    use q = Qubit[1];
    if M(q[0]) == One {
        X(q[0]);
    }
}
"""
    with pytest.raises(UnsupportedConstructError, match="if"):
        QSharpParser().parse(source)


@pytest.mark.unit
def test_unknown_gate_name() -> None:
    source = """
{
    use q = Qubit[1];
    FooBar(q[0]);
}
"""
    with pytest.raises(ParserError, match="Unknown Q# gate"):
        QSharpParser().parse(source)


@pytest.mark.unit
def test_empty_input() -> None:
    circ = QSharpParser().parse("")
    assert circ.qubit_count() == 0
    assert len(circ.instructions) == 0


@pytest.mark.unit
def test_whitespace_only_input() -> None:
    circ = QSharpParser().parse("   \n\n  ")
    assert circ.qubit_count() == 0


# ------------------------------------------------------------------
# Single-qubit allocation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_single_qubit_allocation() -> None:
    source = """
{
    use q = Qubit();
    H(q);
}
"""
    circ = QSharpParser().parse(source)
    assert circ.qubit_count() == 1
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is H


# ------------------------------------------------------------------
# M() measurement variant
# ------------------------------------------------------------------


@pytest.mark.unit
def test_m_measurement() -> None:
    source = """
{
    use q = Qubit[1];
    let r = M(q[0]);
}
"""
    circ = QSharpParser().parse(source)
    assert len(_measurements(circ)) == 1


# ------------------------------------------------------------------
# Controlled rotation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_rx() -> None:
    source = """
{
    use q = Qubit[2];
    Controlled Rx([q[0]], (1.5707, q[1]));
}
"""
    circ = QSharpParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is RX
    assert len(gates[0].controls) == 1
    assert math.isclose(gates[0].params[0], 1.5707, rel_tol=1e-9)


@pytest.mark.unit
def test_rx_with_pi_expression() -> None:
    source = """
{
    use q = Qubit[1];
    Rx(PI() / 2.0, q[0]);
}
"""
    circ = QSharpParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is RX
    assert math.isclose(gates[0].params[0], math.pi / 2.0, rel_tol=1e-9)


@pytest.mark.unit
def test_rx_with_std_math_pi() -> None:
    source = """
{
    use q = Qubit[1];
    Rx(Std.Math.PI() / 4.0, q[0]);
}
"""
    circ = QSharpParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is RX
    assert math.isclose(gates[0].params[0], math.pi / 4.0, rel_tol=1e-9)


@pytest.mark.unit
def test_unrecognized_statement_raises() -> None:
    source = """
{
    use q = Qubit[1];
    SomeWeirdThing;
}
"""
    with pytest.raises(ParserError, match="Unrecognized Q# statement"):
        QSharpParser().parse(source)


# ------------------------------------------------------------------
# Expression evaluator (_expr_eval)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_eval_division_by_zero_raises_parser_error() -> None:
    from qdk_pythonic.parser._expr_eval import eval_math_expr

    with pytest.raises(ParserError, match="Cannot evaluate expression"):
        eval_math_expr("1/0")


@pytest.mark.unit
def test_eval_constant_division_by_zero_raises() -> None:
    from qdk_pythonic.parser._expr_eval import eval_math_expr

    with pytest.raises(ParserError, match="Cannot evaluate expression"):
        eval_math_expr("pi/0", constants={"pi": math.pi})


@pytest.mark.unit
def test_eval_normal_division() -> None:
    from qdk_pythonic.parser._expr_eval import eval_math_expr

    assert eval_math_expr("4/2") == pytest.approx(2.0)
