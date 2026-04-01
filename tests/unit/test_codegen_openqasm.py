"""Tests for the OpenQASM 3.0 code generator."""

import math

import pytest

from qdk_pythonic.codegen.openqasm import OpenQASMCodeGenerator
from qdk_pythonic.core.circuit import Circuit


@pytest.mark.unit
def test_empty_circuit() -> None:
    circ = Circuit()
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "OPENQASM 3.0;" in result
    assert 'include "stdgates.inc";' in result


@pytest.mark.unit
def test_empty_circuit_no_gates() -> None:
    circ = Circuit()
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    # Should only have header, no qubit declarations
    assert "qubit" not in result


@pytest.mark.unit
def test_single_h_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "qubit[1] q;" in result
    assert "h q[0];" in result


@pytest.mark.unit
def test_bell_state() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "qubit[2] q;" in result
    assert "h q[0];" in result
    assert "cx q[0], q[1];" in result
    assert "bit[2] c;" in result
    assert "c[0] = measure q[0];" in result
    assert "c[1] = measure q[1];" in result


@pytest.mark.unit
def test_ghz_three_qubits() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2]).measure_all()
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "qubit[3] q;" in result
    assert "h q[0];" in result
    assert "cx q[0], q[1];" in result
    assert "cx q[1], q[2];" in result
    assert "bit[3] c;" in result


@pytest.mark.unit
def test_h_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "h q[0];" in result


@pytest.mark.unit
def test_x_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.x(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "x q[0];" in result


@pytest.mark.unit
def test_y_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.y(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "y q[0];" in result


@pytest.mark.unit
def test_z_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.z(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "z q[0];" in result


@pytest.mark.unit
def test_s_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.s(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "s q[0];" in result


@pytest.mark.unit
def test_t_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.t(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "t q[0];" in result


@pytest.mark.unit
def test_rx_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(1.5707963267948966, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "rx(1.5707963267948966) q[0];" in result


@pytest.mark.unit
def test_ry_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.ry(0.5, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "ry(0.5) q[0];" in result


@pytest.mark.unit
def test_rz_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rz(math.pi, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "rz(" in result
    assert "q[0];" in result


@pytest.mark.unit
def test_r1_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.r1(math.pi / 4, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    # R1 maps to "p" in OpenQASM
    assert "p(" in result
    assert "q[0];" in result


@pytest.mark.unit
def test_cx_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.cx(q[0], q[1])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "cx q[0], q[1];" in result


@pytest.mark.unit
def test_cz_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.cz(q[0], q[1])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "cz q[0], q[1];" in result


@pytest.mark.unit
def test_swap_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.swap(q[0], q[1])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "swap q[0], q[1];" in result


@pytest.mark.unit
def test_ccnot_gate_individually() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.ccx(q[0], q[1], q[2])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "ccx q[0], q[1], q[2];" in result


@pytest.mark.unit
def test_parameterized_rotation() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    angle = math.pi / 2
    circ.rx(angle, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert f"rx({angle!r}) q[0];" in result


@pytest.mark.unit
def test_controlled_gate() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.controlled(circ.x, [q[0]], q[1])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "ctrl @ x q[0], q[1];" in result


@pytest.mark.unit
def test_adjoint_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.s, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "inv @ s q[0];" in result


@pytest.mark.unit
def test_controlled_adjoint_gate() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.controlled(circ.adjoint, [q[0]], circ.s, q[1])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "ctrl @ inv @ s q[0], q[1];" in result


@pytest.mark.unit
def test_measurements() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    circ.measure(q[0])
    circ.measure(q[1])
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "bit[2] c;" in result
    assert "c[0] = measure q[0];" in result
    assert "c[1] = measure q[1];" in result


@pytest.mark.unit
def test_measure_all() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.measure_all()
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "bit[3] c;" in result
    assert "c[0] = measure q[0];" in result
    assert "c[1] = measure q[1];" in result
    assert "c[2] = measure q[2];" in result


@pytest.mark.unit
def test_raw_qsharp_becomes_comment() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    circ.raw_qsharp("let x = 42;")
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "// [raw Q# fragment omitted]" in result


@pytest.mark.unit
def test_multiple_registers() -> None:
    circ = Circuit()
    a = circ.allocate(2, label="a")
    b = circ.allocate(1, label="b")
    circ.h(a[0]).cx(a[0], b[0])
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "qubit[2] a;" in result
    assert "qubit[1] b;" in result
    assert "h a[0];" in result
    assert "cx a[0], b[0];" in result


@pytest.mark.unit
def test_generate_operation_same_as_generate() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    gen = OpenQASMCodeGenerator()
    assert gen.generate(circ) == gen.generate_operation("Foo", circ)


@pytest.mark.unit
def test_header_always_present() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    lines = result.strip().split("\n")
    assert lines[0] == "OPENQASM 3.0;"
    assert lines[1] == 'include "stdgates.inc";'
