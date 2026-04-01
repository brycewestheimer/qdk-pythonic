"""Tests for the OpenQASM 3.0 code generator."""

import math

import pytest

from qdk_pythonic.codegen.openqasm import OpenQASMCodeGenerator
from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.exceptions import CodegenError


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
@pytest.mark.parametrize("method,expected", [
    ("h", "h q[0];"),
    ("x", "x q[0];"),
    ("y", "y q[0];"),
    ("z", "z q[0];"),
    ("s", "s q[0];"),
    ("t", "t q[0];"),
])
def test_single_qubit_gate_openqasm(method: str, expected: str) -> None:
    circ = Circuit()
    q = circ.allocate(1)
    getattr(circ, method)(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert expected in result


@pytest.mark.unit
@pytest.mark.parametrize("method,angle,gate_name", [
    ("rx", 1.5707963267948966, "rx"),
    ("ry", 0.5, "ry"),
    ("rz", math.pi, "rz"),
    ("r1", math.pi / 4, "p"),
])
def test_rotation_gate_openqasm(
    method: str, angle: float, gate_name: str
) -> None:
    circ = Circuit()
    q = circ.allocate(1)
    getattr(circ, method)(angle, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert f"{gate_name}(" in result
    assert "q[0];" in result


@pytest.mark.unit
@pytest.mark.parametrize("method,expected", [
    ("cx", "cx q[0], q[1];"),
    ("cz", "cz q[0], q[1];"),
    ("swap", "swap q[0], q[1];"),
])
def test_two_qubit_gate_openqasm(method: str, expected: str) -> None:
    circ = Circuit()
    q = circ.allocate(2)
    getattr(circ, method)(q[0], q[1])
    result = OpenQASMCodeGenerator().generate(circ)
    assert expected in result


@pytest.mark.unit
def test_ccnot_gate_openqasm() -> None:
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
    circ.allocate(3)
    circ.measure_all()
    gen = OpenQASMCodeGenerator()
    result = gen.generate(circ)
    assert "bit[3] c;" in result
    assert "c[0] = measure q[0];" in result
    assert "c[1] = measure q[1];" in result
    assert "c[2] = measure q[2];" in result


@pytest.mark.unit
def test_raw_qsharp_raises_codegen_error() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    circ.raw_qsharp("let x = 42;")
    gen = OpenQASMCodeGenerator()
    with pytest.raises(CodegenError, match="Cannot export raw Q#"):
        gen.generate(circ)


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
