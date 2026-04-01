"""Tests for symbolic Parameter type."""

from __future__ import annotations

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.instruction import Instruction
from qdk_pythonic.core.parameter import Parameter
from qdk_pythonic.exceptions import CodegenError


@pytest.mark.unit
def test_parameter_creation() -> None:
    p = Parameter("theta")
    assert p.name == "theta"


@pytest.mark.unit
def test_parameter_equality() -> None:
    assert Parameter("a") == Parameter("a")
    assert Parameter("a") != Parameter("b")


@pytest.mark.unit
def test_parameter_in_circuit() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.params == (theta,)


@pytest.mark.unit
def test_parameters_property() -> None:
    a, b, c = Parameter("a"), Parameter("b"), Parameter("c")
    circ = Circuit()
    q = circ.allocate(2)
    circ.rx(a, q[0]).ry(b, q[1]).rz(c, q[0])
    assert circ.parameters == [a, b, c]


@pytest.mark.unit
def test_parameters_deduplicates() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(2)
    circ.rx(theta, q[0]).ry(theta, q[1])
    assert circ.parameters == [theta]


@pytest.mark.unit
def test_parameters_empty() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(0.5, q[0])
    assert circ.parameters == []


@pytest.mark.unit
def test_bind_parameters() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0])

    bound = circ.bind_parameters({"theta": 1.23})
    inst = bound.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.params == (1.23,)
    assert bound.parameters == []


@pytest.mark.unit
def test_bind_preserves_original() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0])

    circ.bind_parameters({"theta": 0.5})
    # Original unchanged
    assert circ.parameters == [theta]


@pytest.mark.unit
def test_bind_missing_raises() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0])

    with pytest.raises(ValueError, match="No binding for parameter 'theta'"):
        circ.bind_parameters({})


@pytest.mark.unit
def test_bind_mixed_params() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(2)
    circ.rx(0.5, q[0])  # concrete
    circ.ry(theta, q[1])  # symbolic

    bound = circ.bind_parameters({"theta": 1.0})
    insts = bound.instructions
    assert isinstance(insts[0], Instruction) and insts[0].params == (0.5,)
    assert isinstance(insts[1], Instruction) and insts[1].params == (1.0,)


@pytest.mark.unit
def test_unbound_to_qsharp_raises() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0])

    with pytest.raises(CodegenError, match="unbound parameter"):
        circ.to_qsharp()


@pytest.mark.unit
def test_unbound_to_openqasm_raises() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0])

    with pytest.raises(CodegenError, match="unbound parameter"):
        circ.to_openqasm()


@pytest.mark.unit
def test_bound_circuit_to_qsharp() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0])

    bound = circ.bind_parameters({"theta": 1.57})
    qs = bound.to_qsharp()
    assert "Rx" in qs
    assert "1.57" in qs


@pytest.mark.unit
def test_gate_count_works_with_params() -> None:
    theta = Parameter("theta")
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(theta, q[0]).h(q[0])
    assert circ.gate_count() == {"H": 1, "Rx": 1}
    assert circ.total_gate_count() == 2
    assert circ.depth() == 2


@pytest.mark.unit
def test_eq_with_parameters() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c1.rx(Parameter("a"), q1[0])

    c2 = Circuit()
    q2 = c2.allocate(1)
    c2.rx(Parameter("a"), q2[0])

    assert c1 == c2


@pytest.mark.unit
def test_eq_different_parameters() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c1.rx(Parameter("a"), q1[0])

    c2 = Circuit()
    q2 = c2.allocate(1)
    c2.rx(Parameter("b"), q2[0])

    assert c1 != c2
