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
def test_h_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "H(q[0]);" in result


@pytest.mark.unit
def test_x_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.x(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "X(q[0]);" in result


@pytest.mark.unit
def test_y_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.y(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "Y(q[0]);" in result


@pytest.mark.unit
def test_z_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.z(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "Z(q[0]);" in result


@pytest.mark.unit
def test_s_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.s(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "S(q[0]);" in result


@pytest.mark.unit
def test_t_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.t(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "T(q[0]);" in result


@pytest.mark.unit
def test_rx_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(1.5707963267948966, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "Rx(1.5707963267948966, q[0]);" in result


@pytest.mark.unit
def test_ry_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.ry(0.5, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "Ry(0.5, q[0]);" in result


@pytest.mark.unit
def test_rz_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rz(math.pi, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "Rz(" in result
    assert "q[0]);" in result


@pytest.mark.unit
def test_r1_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.r1(math.pi / 4, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "R1(" in result
    assert "q[0]);" in result


@pytest.mark.unit
def test_cx_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.cx(q[0], q[1])
    result = QSharpCodeGenerator().generate(circ)
    assert "CNOT(q[0], q[1]);" in result


@pytest.mark.unit
def test_cz_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.cz(q[0], q[1])
    result = QSharpCodeGenerator().generate(circ)
    assert "CZ(q[0], q[1]);" in result


@pytest.mark.unit
def test_swap_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.swap(q[0], q[1])
    result = QSharpCodeGenerator().generate(circ)
    assert "SWAP(q[0], q[1]);" in result


@pytest.mark.unit
def test_ccnot_gate_individually() -> None:
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
