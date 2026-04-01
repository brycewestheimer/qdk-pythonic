"""Tests for the Circuit class."""

import math

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.gates import CCNOT, CNOT, CZ, H, R1, RX, RY, RZ, S, SWAP, T, X, Y, Z
from qdk_pythonic.core.instruction import Instruction, Measurement, RawQSharp
from qdk_pythonic.core.qubit import Qubit, QubitRegister
from qdk_pythonic.exceptions import CircuitError


# ------------------------------------------------------------------
# Allocation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_allocate_creates_qubits() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    assert len(q) == 2
    assert circ.qubit_count() == 2


@pytest.mark.unit
def test_allocate_with_label() -> None:
    circ = Circuit()
    q = circ.allocate(3, label="reg")
    assert q[0].label == "reg_0"
    assert q[1].label == "reg_1"
    assert q[2].label == "reg_2"


@pytest.mark.unit
def test_allocate_zero_raises() -> None:
    circ = Circuit()
    with pytest.raises(CircuitError):
        circ.allocate(0)


@pytest.mark.unit
def test_allocate_negative_raises() -> None:
    circ = Circuit()
    with pytest.raises(CircuitError):
        circ.allocate(-1)


@pytest.mark.unit
def test_multiple_allocations_non_overlapping() -> None:
    circ = Circuit()
    q1 = circ.allocate(2)
    q2 = circ.allocate(3)
    indices = [q.index for q in q1] + [q.index for q in q2]
    assert indices == [0, 1, 2, 3, 4]


@pytest.mark.unit
def test_qubit_count_returns_total() -> None:
    circ = Circuit()
    circ.allocate(2)
    circ.allocate(3)
    assert circ.qubit_count() == 5


# ------------------------------------------------------------------
# Gate methods
# ------------------------------------------------------------------


@pytest.mark.unit
def test_h_gate_appends_instruction() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    assert len(circ.instructions) == 1
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is H
    assert inst.targets == (q[0],)


@pytest.mark.unit
def test_x_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.x(q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is X


@pytest.mark.unit
def test_y_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.y(q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is Y


@pytest.mark.unit
def test_z_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.z(q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is Z


@pytest.mark.unit
def test_s_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.s(q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is S


@pytest.mark.unit
def test_t_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.t(q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is T


@pytest.mark.unit
def test_rx_gate_stores_param() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(math.pi / 4, q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is RX
    assert inst.params == (math.pi / 4,)


@pytest.mark.unit
def test_ry_gate_stores_param() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.ry(1.23, q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is RY
    assert inst.params == (1.23,)


@pytest.mark.unit
def test_rz_gate_stores_param() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rz(0.5, q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is RZ
    assert inst.params == (0.5,)


@pytest.mark.unit
def test_r1_gate_stores_param() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.r1(math.pi, q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is R1
    assert inst.params == (math.pi,)


@pytest.mark.unit
def test_cx_creates_two_qubit_instruction() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.cx(q[0], q[1])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is CNOT
    assert inst.targets == (q[0], q[1])


@pytest.mark.unit
def test_cz_gate() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.cz(q[0], q[1])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is CZ


@pytest.mark.unit
def test_swap_gate() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.swap(q[0], q[1])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is SWAP


@pytest.mark.unit
def test_ccx_creates_three_qubit_instruction() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.ccx(q[0], q[1], q[2])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is CCNOT
    assert inst.targets == (q[0], q[1], q[2])


@pytest.mark.unit
def test_gate_on_unowned_qubit_raises() -> None:
    circ = Circuit()
    circ.allocate(1)
    foreign = Qubit(index=99, label="foreign")
    with pytest.raises(CircuitError):
        circ.h(foreign)


# ------------------------------------------------------------------
# Fluent chaining
# ------------------------------------------------------------------


@pytest.mark.unit
def test_fluent_chaining_returns_same_instance() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    result = circ.h(q[0]).x(q[1])
    assert result is circ


@pytest.mark.unit
def test_bell_state_circuit() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    assert len(circ.instructions) == 4  # H, CNOT, Measure, Measure


# ------------------------------------------------------------------
# Controlled / Adjoint
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_adds_control_qubit() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.controlled(circ.x, [q[0]], q[1])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.controls == (q[0],)
    assert inst.targets == (q[1],)


@pytest.mark.unit
def test_adjoint_sets_flag() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.s, q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.is_adjoint is True


# ------------------------------------------------------------------
# Measurement
# ------------------------------------------------------------------


@pytest.mark.unit
def test_measure_single_qubit() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.measure(q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Measurement)
    assert inst.target == q[0]
    assert inst.label is None


@pytest.mark.unit
def test_measure_all_creates_measurement_per_qubit() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.measure_all()
    measurements = circ.instructions
    assert len(measurements) == 3
    for i, m in enumerate(measurements):
        assert isinstance(m, Measurement)
        assert m.target == q[i]


@pytest.mark.unit
def test_measure_with_label() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.measure(q[0], label="result")
    inst = circ.instructions[0]
    assert isinstance(inst, Measurement)
    assert inst.label == "result"


# ------------------------------------------------------------------
# Raw Q#
# ------------------------------------------------------------------


@pytest.mark.unit
def test_raw_qsharp_stores_code() -> None:
    circ = Circuit()
    circ.raw_qsharp("let x = 1;")
    inst = circ.instructions[0]
    assert isinstance(inst, RawQSharp)
    assert inst.code == "let x = 1;"


# ------------------------------------------------------------------
# Stubs
# ------------------------------------------------------------------


@pytest.mark.unit
def test_to_qsharp_returns_string() -> None:
    circ = Circuit()
    result = circ.to_qsharp()
    assert isinstance(result, str)


@pytest.mark.unit
def test_to_openqasm_returns_string() -> None:
    circ = Circuit()
    result = circ.to_openqasm()
    assert isinstance(result, str)


@pytest.mark.unit
def test_run_requires_qsharp() -> None:
    circ = Circuit()
    with pytest.raises(ImportError, match="qsharp is required"):
        circ.run()


@pytest.mark.unit
def test_estimate_requires_qsharp() -> None:
    circ = Circuit()
    with pytest.raises(ImportError, match="qsharp is required"):
        circ.estimate()


@pytest.mark.unit
def test_from_qsharp_returns_circuit() -> None:
    source = """
{
    use q = Qubit[2];
    H(q[0]);
    CNOT(q[0], q[1]);
}
"""
    circ = Circuit.from_qsharp(source)
    assert circ.qubit_count() == 2
    assert len([i for i in circ.instructions if isinstance(i, Instruction)]) == 2


@pytest.mark.unit
def test_from_openqasm_returns_circuit() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""
    circ = Circuit.from_openqasm(source)
    assert circ.qubit_count() == 2
    assert len([i for i in circ.instructions if isinstance(i, Instruction)]) == 2


# ------------------------------------------------------------------
# Properties
# ------------------------------------------------------------------


@pytest.mark.unit
def test_instructions_property_returns_copy() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    insts = circ.instructions
    assert len(insts) == 1
    insts.clear()
    assert len(circ.instructions) == 1  # original unmodified


@pytest.mark.unit
def test_qubits_property_returns_copy() -> None:
    circ = Circuit()
    circ.allocate(2)
    qubits = circ.qubits
    assert len(qubits) == 2
    qubits.clear()
    assert len(circ.qubits) == 2


@pytest.mark.unit
def test_registers_property_returns_copy() -> None:
    circ = Circuit()
    circ.allocate(2)
    circ.allocate(3)
    regs = circ.registers
    assert len(regs) == 2
    assert isinstance(regs[0], QubitRegister)
    regs.clear()
    assert len(circ.registers) == 2
