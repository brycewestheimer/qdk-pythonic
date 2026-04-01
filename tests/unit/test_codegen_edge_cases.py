"""Edge case tests for both Q# and OpenQASM code generators."""

import math

import pytest

from qdk_pythonic.codegen.openqasm import OpenQASMCodeGenerator
from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator
from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.exceptions import CodegenError


# ------------------------------------------------------------------
# 1. Empty circuit (both generators)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_empty_circuit_qsharp() -> None:
    circ = Circuit()
    assert QSharpCodeGenerator().generate(circ) == "{ }"


@pytest.mark.unit
def test_empty_circuit_openqasm() -> None:
    circ = Circuit()
    result = OpenQASMCodeGenerator().generate(circ)
    assert "OPENQASM 3.0;" in result
    assert "qubit" not in result


# ------------------------------------------------------------------
# 2. Single gate, no measurement
# ------------------------------------------------------------------


@pytest.mark.unit
def test_single_gate_no_measurement_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "H(q[0]);" in result
    assert "MResetZ" not in result


@pytest.mark.unit
def test_single_gate_no_measurement_openqasm() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "h q[0];" in result
    # No classical bit declarations (only qubit declarations)
    lines = result.strip().split("\n")
    assert not any(line.strip().startswith("bit[") for line in lines)
    assert "measure" not in result


# ------------------------------------------------------------------
# 3. Measurements only (allocate + measure_all, no gates)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_measurements_only_qsharp() -> None:
    circ = Circuit()
    circ.allocate(2)
    circ.measure_all()
    result = QSharpCodeGenerator().generate(circ)
    assert "use q = Qubit[2];" in result
    assert "let r0 = MResetZ(q[0]);" in result
    assert "let r1 = MResetZ(q[1]);" in result
    assert "[r0, r1]" in result


@pytest.mark.unit
def test_measurements_only_openqasm() -> None:
    circ = Circuit()
    circ.allocate(2)
    circ.measure_all()
    result = OpenQASMCodeGenerator().generate(circ)
    assert "qubit[2] q;" in result
    assert "bit[2] c;" in result
    assert "c[0] = measure q[0];" in result
    assert "c[1] = measure q[1];" in result


# ------------------------------------------------------------------
# 4. Large circuit (50 qubits, 200 gates) — no crash
# ------------------------------------------------------------------


@pytest.mark.unit
def test_large_circuit_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(50)
    for i in range(200):
        circ.h(q[i % 50])
    result = QSharpCodeGenerator().generate(circ)
    assert "use q = Qubit[50];" in result
    assert result.count("H(") == 200


@pytest.mark.unit
def test_large_circuit_openqasm() -> None:
    circ = Circuit()
    q = circ.allocate(50)
    for i in range(200):
        circ.h(q[i % 50])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "qubit[50] q;" in result
    assert result.count("h q[") == 200


# ------------------------------------------------------------------
# 5. Mixed raw Q# with regular gates
# ------------------------------------------------------------------


@pytest.mark.unit
def test_mixed_raw_qsharp_with_gates() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    circ.raw_qsharp("let x = 42;")
    circ.x(q[0])
    result = QSharpCodeGenerator().generate(circ)
    lines = result.split("\n")
    # Find gate and raw lines
    h_idx = next(i for i, l in enumerate(lines) if "H(q[0])" in l)
    raw_idx = next(i for i, l in enumerate(lines) if "let x = 42;" in l)
    x_idx = next(i for i, l in enumerate(lines) if "X(q[0])" in l)
    assert h_idx < raw_idx < x_idx


@pytest.mark.unit
def test_mixed_raw_qsharp_openqasm_becomes_comment() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    circ.raw_qsharp("let x = 42;")
    circ.x(q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "// [raw Q# fragment omitted]" in result
    assert "h q[0];" in result
    assert "x q[0];" in result


# ------------------------------------------------------------------
# 6. All 14 gates in one circuit
# ------------------------------------------------------------------


@pytest.mark.unit
def test_all_14_gates_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0])
    circ.x(q[0])
    circ.y(q[0])
    circ.z(q[0])
    circ.s(q[0])
    circ.t(q[0])
    circ.rx(1.0, q[0])
    circ.ry(1.0, q[0])
    circ.rz(1.0, q[0])
    circ.r1(1.0, q[0])
    circ.cx(q[0], q[1])
    circ.cz(q[0], q[1])
    circ.swap(q[0], q[1])
    circ.ccx(q[0], q[1], q[2])
    result = QSharpCodeGenerator().generate(circ)
    for gate_name in ["H", "X", "Y", "Z", "S", "T", "Rx", "Ry", "Rz", "R1",
                      "CNOT", "CZ", "SWAP", "CCNOT"]:
        assert gate_name + "(" in result


@pytest.mark.unit
def test_all_14_gates_openqasm() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0])
    circ.x(q[0])
    circ.y(q[0])
    circ.z(q[0])
    circ.s(q[0])
    circ.t(q[0])
    circ.rx(1.0, q[0])
    circ.ry(1.0, q[0])
    circ.rz(1.0, q[0])
    circ.r1(1.0, q[0])
    circ.cx(q[0], q[1])
    circ.cz(q[0], q[1])
    circ.swap(q[0], q[1])
    circ.ccx(q[0], q[1], q[2])
    result = OpenQASMCodeGenerator().generate(circ)
    for gate_name in ["h ", "x ", "y ", "z ", "s ", "t ", "rx(", "ry(", "rz(",
                      "p(", "cx ", "cz ", "swap ", "ccx "]:
        assert gate_name in result


# ------------------------------------------------------------------
# 7. Multiple registers with different labels
# ------------------------------------------------------------------


@pytest.mark.unit
def test_multiple_registers_different_labels_qsharp() -> None:
    circ = Circuit()
    data = circ.allocate(3, label="data")
    anc = circ.allocate(1, label="anc")
    circ.h(data[0]).cx(data[0], anc[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "use data = Qubit[3];" in result
    assert "use anc = Qubit[1];" in result
    assert "H(data[0]);" in result
    assert "CNOT(data[0], anc[0]);" in result


@pytest.mark.unit
def test_multiple_registers_different_labels_openqasm() -> None:
    circ = Circuit()
    data = circ.allocate(3, label="data")
    anc = circ.allocate(1, label="anc")
    circ.h(data[0]).cx(data[0], anc[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "qubit[3] data;" in result
    assert "qubit[1] anc;" in result
    assert "h data[0];" in result
    assert "cx data[0], anc[0];" in result


# ------------------------------------------------------------------
# 8. Adjoint of parameterized gate
# ------------------------------------------------------------------


@pytest.mark.unit
def test_adjoint_parameterized_gate_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.rx, math.pi / 2, q[0])
    result = QSharpCodeGenerator().generate(circ)
    assert "Adjoint Rx(" in result
    assert "q[0]);" in result


@pytest.mark.unit
def test_adjoint_parameterized_gate_openqasm() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.rx, math.pi / 2, q[0])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "inv @ rx(" in result
    assert "q[0];" in result


# ------------------------------------------------------------------
# 9. Controlled gate with multiple controls
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_with_multiple_controls_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.controlled(circ.x, [q[0], q[1]], q[2])
    result = QSharpCodeGenerator().generate(circ)
    assert "Controlled X([q[0], q[1]], q[2]);" in result


@pytest.mark.unit
def test_controlled_with_multiple_controls_openqasm() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.controlled(circ.x, [q[0], q[1]], q[2])
    result = OpenQASMCodeGenerator().generate(circ)
    assert "ctrl @ x q[0], q[1], q[2];" in result


# ------------------------------------------------------------------
# 10. Deterministic output (generate twice, compare)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_deterministic_output_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    gen = QSharpCodeGenerator()
    assert gen.generate(circ) == gen.generate(circ)


@pytest.mark.unit
def test_deterministic_output_openqasm() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    gen = OpenQASMCodeGenerator()
    assert gen.generate(circ) == gen.generate(circ)


# ------------------------------------------------------------------
# 11. to_openqasm("2.0") raises CodegenError
# ------------------------------------------------------------------


@pytest.mark.unit
def test_to_openqasm_unsupported_version() -> None:
    circ = Circuit()
    with pytest.raises(CodegenError, match="Unsupported OpenQASM version: 2.0"):
        circ.to_openqasm("2.0")


# ------------------------------------------------------------------
# Wire-up: to_qsharp() and to_openqasm() work on Circuit
# ------------------------------------------------------------------


@pytest.mark.unit
def test_circuit_to_qsharp_wired_up() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    result = circ.to_qsharp()
    assert "H(q[0]);" in result
    assert "CNOT(q[0], q[1]);" in result


@pytest.mark.unit
def test_circuit_to_openqasm_wired_up() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    result = circ.to_openqasm()
    assert "h q[0];" in result
    assert "cx q[0], q[1];" in result
