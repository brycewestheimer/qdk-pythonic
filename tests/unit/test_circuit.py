"""Tests for the Circuit class."""

import math
from typing import Any

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.gates import CCNOT, CNOT, CZ, R1, RX, RY, RZ, SWAP, H, S, T, X, Y, Z
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
@pytest.mark.parametrize("method_name,gate_def", [
    ("h", H), ("x", X), ("y", Y), ("z", Z), ("s", S), ("t", T),
])
def test_single_qubit_gate_appends_instruction(
    method_name: str, gate_def: object
) -> None:
    circ = Circuit()
    q = circ.allocate(1)
    getattr(circ, method_name)(q[0])
    assert len(circ.instructions) == 1
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is gate_def
    assert inst.targets == (q[0],)


@pytest.mark.unit
@pytest.mark.parametrize("method_name,gate_def,angle", [
    ("rx", RX, math.pi / 4),
    ("ry", RY, 1.23),
    ("rz", RZ, 0.5),
    ("r1", R1, math.pi),
])
def test_rotation_gate_stores_param(
    method_name: str, gate_def: object, angle: float
) -> None:
    circ = Circuit()
    q = circ.allocate(1)
    getattr(circ, method_name)(angle, q[0])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is gate_def
    assert inst.params == (angle,)


@pytest.mark.unit
@pytest.mark.parametrize("method_name,gate_def", [
    ("cx", CNOT), ("cz", CZ), ("swap", SWAP),
])
def test_two_qubit_gate(method_name: str, gate_def: object) -> None:
    circ = Circuit()
    q = circ.allocate(2)
    getattr(circ, method_name)(q[0], q[1])
    inst = circ.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.gate is gate_def
    assert inst.targets == (q[0], q[1])


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


# ------------------------------------------------------------------
# Qubit ownership by circuit provenance (Issue 1)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_qubit_from_other_circuit_rejected() -> None:
    c1 = Circuit()
    c1.allocate(2)
    c2 = Circuit()
    q2 = c2.allocate(1)
    with pytest.raises(CircuitError, match="not owned"):
        c1.h(q2[0])


# ------------------------------------------------------------------
# Qubit distinctness (Issue 4)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_cx_same_qubit_raises() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    with pytest.raises(CircuitError, match="distinct"):
        circ.cx(q[0], q[0])


@pytest.mark.unit
def test_swap_same_qubit_raises() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    with pytest.raises(CircuitError, match="distinct"):
        circ.swap(q[0], q[0])


@pytest.mark.unit
def test_ccx_duplicate_qubit_raises() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    with pytest.raises(CircuitError, match="distinct"):
        circ.ccx(q[0], q[0], q[1])


@pytest.mark.unit
def test_controlled_target_equals_control_raises() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    with pytest.raises(CircuitError, match="distinct"):
        circ.controlled(circ.x, [q[0]], q[0])


# ------------------------------------------------------------------
# Namespace-safe allocation (Issue 2)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_allocate_duplicate_label_raises() -> None:
    circ = Circuit()
    circ.allocate(2, label="r")
    with pytest.raises(CircuitError, match="Duplicate register label"):
        circ.allocate(2, label="r")


@pytest.mark.unit
def test_allocate_unlabeled_unique_labels() -> None:
    circ = Circuit()
    r1 = circ.allocate(2)
    r2 = circ.allocate(3)
    assert r1.label is not None
    assert r2.label is not None
    assert r1.label != r2.label


# ------------------------------------------------------------------
# add_instruction / without_measurements
# ------------------------------------------------------------------


@pytest.mark.unit
def test_add_instruction_appends() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    inst = Instruction(gate=H, targets=(q[0],))
    circ.add_instruction(inst)
    assert len(circ.instructions) == 1
    assert circ.instructions[0] is inst


@pytest.mark.unit
def test_add_instruction_fluent() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    inst = Instruction(gate=H, targets=(q[0],))
    result = circ.add_instruction(inst)
    assert result is circ


@pytest.mark.unit
def test_add_instruction_measurement() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    meas = Measurement(target=q[0])
    circ.add_instruction(meas)
    assert isinstance(circ.instructions[0], Measurement)


@pytest.mark.unit
def test_add_instruction_raw_qsharp() -> None:
    circ = Circuit()
    raw = RawQSharp(code="let x = 1;")
    circ.add_instruction(raw)
    assert isinstance(circ.instructions[0], RawQSharp)


@pytest.mark.unit
def test_without_measurements_filters() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    filtered = circ.without_measurements()
    assert len(filtered.instructions) == 2  # H and CNOT only
    for inst in filtered.instructions:
        assert not isinstance(inst, Measurement)


@pytest.mark.unit
def test_without_measurements_preserves_original() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).measure(q[0])
    original_count = len(circ.instructions)
    circ.without_measurements()
    assert len(circ.instructions) == original_count


# ------------------------------------------------------------------
# controlled() / adjoint() safety (Issue 3)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_measure_raises() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    with pytest.raises(CircuitError, match="gate instructions"):
        circ.controlled(circ.measure, [q[0]], q[1])


@pytest.mark.unit
def test_adjoint_measure_raises() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    with pytest.raises(CircuitError, match="gate instructions"):
        circ.adjoint(circ.measure, q[0])


@pytest.mark.unit
def test_controlled_noop_raises() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    with pytest.raises(CircuitError, match="did not add one"):
        circ.controlled(lambda: None, [q[0]])


@pytest.mark.unit
def test_adjoint_noop_raises() -> None:
    circ = Circuit()
    circ.allocate(1)
    with pytest.raises(CircuitError, match="did not add one"):
        circ.adjoint(lambda: None)


# ------------------------------------------------------------------
# __repr__
# ------------------------------------------------------------------


@pytest.mark.unit
def test_repr_empty_circuit() -> None:
    circ = Circuit()
    assert repr(circ) == "Circuit(qubits=0, gates=0, measurements=0)"


@pytest.mark.unit
def test_repr_with_gates_and_measurements() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    assert repr(circ) == "Circuit(qubits=2, gates=2, measurements=2)"


# ------------------------------------------------------------------
# __eq__
# ------------------------------------------------------------------


@pytest.mark.unit
def test_eq_identical_circuits() -> None:
    c1 = Circuit()
    q1 = c1.allocate(2)
    c1.h(q1[0]).cx(q1[0], q1[1])

    c2 = Circuit()
    q2 = c2.allocate(2)
    c2.h(q2[0]).cx(q2[0], q2[1])

    assert c1 == c2


@pytest.mark.unit
def test_eq_different_gate_types() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c1.h(q1[0])

    c2 = Circuit()
    q2 = c2.allocate(1)
    c2.x(q2[0])

    assert c1 != c2


@pytest.mark.unit
def test_eq_different_params() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c1.rx(0.5, q1[0])

    c2 = Circuit()
    q2 = c2.allocate(1)
    c2.rx(0.6, q2[0])

    assert c1 != c2


@pytest.mark.unit
def test_eq_different_topology() -> None:
    c1 = Circuit()
    q1 = c1.allocate(2)
    c1.cx(q1[0], q1[1])

    c2 = Circuit()
    q2 = c2.allocate(2)
    c2.cx(q2[1], q2[0])

    assert c1 != c2


@pytest.mark.unit
def test_eq_ignores_labels() -> None:
    c1 = Circuit()
    c1.allocate(2, label="a")
    c2 = Circuit()
    c2.allocate(2, label="b")
    assert c1 == c2


@pytest.mark.unit
def test_eq_non_circuit_returns_not_implemented() -> None:
    circ = Circuit()
    assert circ.__eq__("not a circuit") is NotImplemented


@pytest.mark.unit
def test_eq_different_qubit_count() -> None:
    c1 = Circuit()
    c1.allocate(2)
    c2 = Circuit()
    c2.allocate(3)
    assert c1 != c2


@pytest.mark.unit
def test_eq_with_measurements() -> None:
    c1 = Circuit()
    q1 = c1.allocate(2)
    c1.h(q1[0]).measure(q1[0])

    c2 = Circuit()
    q2 = c2.allocate(2)
    c2.h(q2[0]).measure(q2[0])

    assert c1 == c2


@pytest.mark.unit
def test_eq_with_raw_qsharp() -> None:
    c1 = Circuit()
    c1.raw_qsharp("let x = 1;")

    c2 = Circuit()
    c2.raw_qsharp("let x = 1;")

    assert c1 == c2


@pytest.mark.unit
def test_eq_different_raw_qsharp() -> None:
    c1 = Circuit()
    c1.raw_qsharp("let x = 1;")

    c2 = Circuit()
    c2.raw_qsharp("let x = 2;")

    assert c1 != c2


# ------------------------------------------------------------------
# total_gate_count
# ------------------------------------------------------------------


@pytest.mark.unit
def test_total_gate_count_empty() -> None:
    circ = Circuit()
    assert circ.total_gate_count() == 0


@pytest.mark.unit
def test_total_gate_count_bell_state() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    assert circ.total_gate_count() == 2


@pytest.mark.unit
def test_total_gate_count_ignores_measurements() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    assert circ.total_gate_count() == 2


# ------------------------------------------------------------------
# without_measurements deep copy safety
# ------------------------------------------------------------------


@pytest.mark.unit
def test_without_measurements_does_not_share_registers() -> None:
    circ = Circuit()
    circ.allocate(2)
    circ.allocate(3)
    filtered = circ.without_measurements()
    # Verify the register objects are distinct
    for orig, copied in zip(circ.registers, filtered.registers):
        assert orig is not copied


# ------------------------------------------------------------------
# without_measurements_and_raw
# ------------------------------------------------------------------


@pytest.mark.unit
def test_without_measurements_and_raw_filters_both() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).raw_qsharp("M(q[0]);").measure(q[0])
    filtered = circ.without_measurements_and_raw()
    assert len(filtered.instructions) == 1
    assert isinstance(filtered.instructions[0], Instruction)


@pytest.mark.unit
def test_without_measurements_and_raw_preserves_original() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0]).raw_qsharp("let x = 1;").measure(q[0])
    original_count = len(circ.instructions)
    circ.without_measurements_and_raw()
    assert len(circ.instructions) == original_count


# ------------------------------------------------------------------
# __add__ composition
# ------------------------------------------------------------------


@pytest.mark.unit
def test_add_combines_circuits() -> None:
    c1 = Circuit()
    q1 = c1.allocate(2)
    c1.h(q1[0])

    c2 = Circuit()
    q2 = c2.allocate(2)
    c2.x(q2[0])

    result = c1 + c2
    assert result.qubit_count() == 4
    assert result.total_gate_count() == 2


@pytest.mark.unit
def test_add_preserves_instruction_order() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c1.h(q1[0])

    c2 = Circuit()
    q2 = c2.allocate(1)
    c2.x(q2[0])

    result = c1 + c2
    insts = result.instructions
    assert isinstance(insts[0], Instruction) and insts[0].gate is H
    assert isinstance(insts[1], Instruction) and insts[1].gate is X


@pytest.mark.unit
def test_add_remaps_qubit_indices() -> None:
    c1 = Circuit()
    q1 = c1.allocate(2)
    c1.cx(q1[0], q1[1])

    c2 = Circuit()
    q2 = c2.allocate(2)
    c2.cx(q2[0], q2[1])

    result = c1 + c2
    insts = result.instructions
    assert isinstance(insts[0], Instruction)
    assert isinstance(insts[1], Instruction)
    # First circuit's qubits: 0, 1. Second circuit's qubits: 2, 3.
    assert tuple(q.index for q in insts[0].targets) == (0, 1)
    assert tuple(q.index for q in insts[1].targets) == (2, 3)


@pytest.mark.unit
def test_add_with_measurements() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c1.h(q1[0]).measure(q1[0])

    c2 = Circuit()
    q2 = c2.allocate(1)
    c2.x(q2[0])

    result = c1 + c2
    assert result.qubit_count() == 2
    assert len(result.instructions) == 3


@pytest.mark.unit
def test_add_raw_qsharp_raises() -> None:
    c1 = Circuit()
    c1.raw_qsharp("let x = 1;")

    c2 = Circuit()
    c2.allocate(1)

    with pytest.raises(CircuitError, match="raw Q#"):
        c1 + c2


@pytest.mark.unit
def test_add_non_circuit_returns_not_implemented() -> None:
    circ = Circuit()
    assert circ.__add__("nope") is NotImplemented


@pytest.mark.unit
def test_add_three_way_composition() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c1.h(q1[0])

    c2 = Circuit()
    q2 = c2.allocate(1)
    c2.x(q2[0])

    c3 = Circuit()
    q3 = c3.allocate(1)
    c3.z(q3[0])

    result = c1 + c2 + c3
    assert result.qubit_count() == 3
    assert result.total_gate_count() == 3


# ------------------------------------------------------------------
# controlled() / adjoint() atomicity (Issues 1+2)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_multi_instruction_rollback() -> None:
    """If gate_fn adds multiple instructions, controlled() rolls back all."""
    circ = Circuit()
    q = circ.allocate(3)

    def multi_gate(*_args: Any, **_kwargs: Any) -> Circuit:
        circ.h(q[1])
        circ.x(q[2])
        return circ

    with pytest.raises(CircuitError, match="exactly one"):
        circ.controlled(multi_gate, [q[0]], q[1])

    assert len(circ.instructions) == 0


@pytest.mark.unit
def test_adjoint_multi_instruction_rollback() -> None:
    """If gate_fn adds multiple instructions, adjoint() rolls back all."""
    circ = Circuit()
    q = circ.allocate(2)

    def multi_gate(*_args: Any, **_kwargs: Any) -> Circuit:
        circ.h(q[0])
        circ.x(q[1])
        return circ

    with pytest.raises(CircuitError, match="exactly one"):
        circ.adjoint(multi_gate)

    assert len(circ.instructions) == 0


@pytest.mark.unit
def test_controlled_duplicate_controls_raises() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    with pytest.raises(CircuitError, match="distinct"):
        circ.controlled(circ.x, [q[0], q[0]], q[2])


@pytest.mark.unit
def test_controlled_error_leaves_circuit_clean() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    with pytest.raises(CircuitError):
        circ.controlled(circ.measure, [q[0]], q[1])
    assert len(circ.instructions) == 0


@pytest.mark.unit
def test_adjoint_error_leaves_circuit_clean() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    with pytest.raises(CircuitError):
        circ.adjoint(circ.measure, q[0])
    assert len(circ.instructions) == 0


# ------------------------------------------------------------------
# add_instruction() qubit ownership (Issue 6)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_add_instruction_foreign_qubit_raises() -> None:
    c1 = Circuit()
    c1.allocate(1)
    c2 = Circuit()
    q2 = c2.allocate(1)
    inst = Instruction(gate=H, targets=(q2[0],))
    with pytest.raises(CircuitError, match="not owned"):
        c1.add_instruction(inst)


@pytest.mark.unit
def test_add_instruction_foreign_measurement_raises() -> None:
    c1 = Circuit()
    c1.allocate(1)
    c2 = Circuit()
    q2 = c2.allocate(1)
    meas = Measurement(target=q2[0])
    with pytest.raises(CircuitError, match="not owned"):
        c1.add_instruction(meas)


@pytest.mark.unit
def test_add_instruction_foreign_control_raises() -> None:
    c1 = Circuit()
    q1 = c1.allocate(1)
    c2 = Circuit()
    q2 = c2.allocate(1)
    inst = Instruction(gate=H, targets=(q1[0],), controls=(q2[0],))
    with pytest.raises(CircuitError, match="not owned"):
        c1.add_instruction(inst)


@pytest.mark.unit
def test_add_instruction_raw_qsharp_accepted() -> None:
    circ = Circuit()
    circ.allocate(1)
    raw = RawQSharp(code="Message(\"hello\");")
    circ.add_instruction(raw)
    assert len(circ.instructions) == 1


# ------------------------------------------------------------------
# Register label validation (Issue 7)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_allocate_invalid_label_hyphen() -> None:
    circ = Circuit()
    with pytest.raises(CircuitError, match="Invalid register label"):
        circ.allocate(1, label="bad-name")


@pytest.mark.unit
def test_allocate_invalid_label_space() -> None:
    circ = Circuit()
    with pytest.raises(CircuitError, match="Invalid register label"):
        circ.allocate(1, label="my reg")


@pytest.mark.unit
def test_allocate_invalid_label_starts_digit() -> None:
    circ = Circuit()
    with pytest.raises(CircuitError, match="Invalid register label"):
        circ.allocate(1, label="1reg")


@pytest.mark.unit
def test_allocate_valid_label_underscore_prefix() -> None:
    circ = Circuit()
    reg = circ.allocate(1, label="_r")
    assert reg.label == "_r"


@pytest.mark.unit
def test_allocate_valid_label_alphanumeric() -> None:
    circ = Circuit()
    reg = circ.allocate(1, label="my_reg_2")
    assert reg.label == "my_reg_2"
