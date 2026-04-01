"""Tests for the Q# code generator."""

import math

import pytest

from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator
from qdk_pythonic.core.circuit import Circuit


@pytest.mark.unit
def test_empty_circuit() -> None:
    circ = Circuit()
    gen = QSharpCodeGenerator()
    assert gen.generate(circ) == "{ }"


@pytest.mark.unit
def test_empty_circuit_operation() -> None:
    circ = Circuit()
    gen = QSharpCodeGenerator()
    assert gen.generate_operation("Foo", circ) == "operation Foo() : Unit { }"


@pytest.mark.unit
def test_single_h_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "use q = Qubit[1];" in result
    assert "H(q[0]);" in result


@pytest.mark.unit
def test_bell_state() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "use q = Qubit[2];" in result
    assert "H(q[0]);" in result
    assert "CNOT(q[0], q[1]);" in result
    assert "let r0 = MResetZ(q[0]);" in result
    assert "let r1 = MResetZ(q[1]);" in result
    assert "[r0, r1]" in result


@pytest.mark.unit
def test_ghz_three_qubits() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2]).measure_all()
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "use q = Qubit[3];" in result
    assert "H(q[0]);" in result
    assert "CNOT(q[0], q[1]);" in result
    assert "CNOT(q[1], q[2]);" in result
    assert "[r0, r1, r2]" in result


@pytest.mark.unit
@pytest.mark.parametrize("method,expected", [
    ("h", "H(q[0]);"),
    ("x", "X(q[0]);"),
    ("y", "Y(q[0]);"),
    ("z", "Z(q[0]);"),
    ("s", "S(q[0]);"),
    ("t", "T(q[0]);"),
])
def test_single_qubit_gate_qsharp(method: str, expected: str) -> None:
    circ = Circuit()
    q = circ.allocate(1)
    getattr(circ, method)(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert expected in result


@pytest.mark.unit
@pytest.mark.parametrize("method,angle,gate_name", [
    ("rx", 1.5707963267948966, "Rx"),
    ("ry", 0.5, "Ry"),
    ("rz", math.pi, "Rz"),
    ("r1", math.pi / 4, "R1"),
])
def test_rotation_gate_qsharp(
    method: str, angle: float, gate_name: str
) -> None:
    circ = Circuit()
    q = circ.allocate(1)
    getattr(circ, method)(angle, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert f"{gate_name}(" in result
    assert "q[0]);" in result


@pytest.mark.unit
@pytest.mark.parametrize("method,expected", [
    ("cx", "CNOT(q[0], q[1]);"),
    ("cz", "CZ(q[0], q[1]);"),
    ("swap", "SWAP(q[0], q[1]);"),
])
def test_two_qubit_gate_qsharp(method: str, expected: str) -> None:
    circ = Circuit()
    q = circ.allocate(2)
    getattr(circ, method)(q[0], q[1])
    result = QSharpCodeGenerator().generate(circ)
    assert expected in result


@pytest.mark.unit
def test_ccnot_gate_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.ccx(q[0], q[1], q[2])
    result = QSharpCodeGenerator().generate(circ)
    assert "CCNOT(q[0], q[1], q[2]);" in result


@pytest.mark.unit
def test_parameterized_rotation() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    angle = math.pi / 2
    circ.rx(angle, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert f"Rx({angle!r}, q[0]);" in result


@pytest.mark.unit
def test_controlled_gate() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.controlled(circ.x, [q[0]], q[1])
    result = QSharpCodeGenerator().generate(circ)
    assert "Controlled X([q[0]], q[1]);" in result


@pytest.mark.unit
def test_adjoint_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.s, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "Adjoint S(q[0]);" in result


@pytest.mark.unit
def test_controlled_adjoint_gate() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    # First apply adjoint, then wrap with controlled
    circ.controlled(circ.adjoint, [q[0]], circ.s, q[1])
    result = QSharpCodeGenerator().generate(circ)
    assert "Controlled Adjoint S([q[0]], q[1]);" in result


@pytest.mark.unit
def test_single_measurement() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    circ.measure(q[0])
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "let r0 = MResetZ(q[0]);" in result
    # Single measurement returns bare variable
    assert result.strip().endswith("r0\n}")


@pytest.mark.unit
def test_multi_measurement() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    circ.measure(q[0])
    circ.measure(q[1])
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "let r0 = MResetZ(q[0]);" in result
    assert "let r1 = MResetZ(q[1]);" in result
    assert "[r0, r1]" in result


@pytest.mark.unit
def test_measure_all() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0])
    circ.measure_all()
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "let r0 = MResetZ(q[0]);" in result
    assert "let r1 = MResetZ(q[1]);" in result
    assert "let r2 = MResetZ(q[2]);" in result
    assert "[r0, r1, r2]" in result


@pytest.mark.unit
def test_no_measurement_unit_return() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    # No return line, no measurement variables
    assert "MResetZ" not in result
    # Should not have a return array
    assert "[r" not in result


@pytest.mark.unit
def test_generate_operation_with_name() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    gen = QSharpCodeGenerator()
    result = gen.generate_operation("BellPair", circ)
    assert result.startswith("operation BellPair() : Result[] {")
    assert "use q = Qubit[2];" in result
    assert "H(q[0]);" in result


@pytest.mark.unit
def test_generate_operation_unit_return() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    gen = QSharpCodeGenerator()
    result = gen.generate_operation("MyOp", circ)
    assert "operation MyOp() : Unit {" in result


@pytest.mark.unit
def test_generate_operation_single_result() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0]).measure(q[0])
    gen = QSharpCodeGenerator()
    result = gen.generate_operation("Measure1", circ)
    assert "operation Measure1() : Result {" in result


@pytest.mark.unit
def test_raw_qsharp_fragment() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    circ.raw_qsharp("let x = 42;")
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "let x = 42;" in result


@pytest.mark.unit
def test_multiple_registers() -> None:
    circ = Circuit()
    a = circ.allocate(2, label="a")
    b = circ.allocate(1, label="b")
    circ.h(a[0]).cx(a[0], b[0])
    gen = QSharpCodeGenerator()
    result = gen.generate(circ)
    assert "use a = Qubit[2];" in result
    assert "use b = Qubit[1];" in result
    assert "H(a[0]);" in result
    assert "CNOT(a[0], b[0]);" in result
