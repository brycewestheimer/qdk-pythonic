"""Tests for analysis: metrics, serialization, and visualization."""

from __future__ import annotations

import pytest

from qdk_pythonic.analysis.metrics import compute_qubit_count
from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.instruction import Instruction, Measurement, RawQSharp
from qdk_pythonic.exceptions import CircuitError

# ------------------------------------------------------------------
# compute_depth
# ------------------------------------------------------------------


@pytest.mark.unit
def test_depth_empty_circuit() -> None:
    circ = Circuit()
    assert circ.depth() == 0


@pytest.mark.unit
def test_depth_no_instructions() -> None:
    circ = Circuit()
    circ.allocate(2)
    assert circ.depth() == 0


@pytest.mark.unit
def test_depth_single_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    assert circ.depth() == 1


@pytest.mark.unit
def test_depth_bell_state() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    assert circ.depth() == 2


@pytest.mark.unit
def test_depth_ghz_5() -> None:
    circ = Circuit()
    q = circ.allocate(5)
    circ.h(q[0])
    for i in range(4):
        circ.cx(q[i], q[i + 1])
    assert circ.depth() == 5


@pytest.mark.unit
def test_depth_parallel_gates() -> None:
    """Gates on disjoint qubits share the same time step."""
    circ = Circuit()
    q = circ.allocate(4)
    circ.h(q[0]).h(q[1]).h(q[2]).h(q[3])
    assert circ.depth() == 1


@pytest.mark.unit
def test_depth_with_measurement() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0]).measure(q[0])
    assert circ.depth() == 2


@pytest.mark.unit
def test_depth_with_controlled_modifier() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0])
    circ.controlled(circ.x, [q[0], q[1]], q[2])
    assert circ.depth() == 2


@pytest.mark.unit
def test_depth_skips_raw_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0]).raw_qsharp("// noop")
    assert circ.depth() == 1


@pytest.mark.unit
def test_depth_ccnot() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).ccx(q[0], q[1], q[2])
    assert circ.depth() == 2


# ------------------------------------------------------------------
# compute_gate_count
# ------------------------------------------------------------------


@pytest.mark.unit
def test_gate_count_empty() -> None:
    circ = Circuit()
    assert circ.gate_count() == {}


@pytest.mark.unit
def test_gate_count_bell() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    assert circ.gate_count() == {"CNOT": 1, "H": 1}


@pytest.mark.unit
def test_gate_count_ghz_5() -> None:
    circ = Circuit()
    q = circ.allocate(5)
    circ.h(q[0])
    for i in range(4):
        circ.cx(q[i], q[i + 1])
    assert circ.gate_count() == {"CNOT": 4, "H": 1}


@pytest.mark.unit
def test_gate_count_ignores_measurements() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    assert circ.gate_count() == {"CNOT": 1, "H": 1}


@pytest.mark.unit
def test_gate_count_sorted_alphabetically() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.z(q[0]).x(q[0]).h(q[0])
    assert list(circ.gate_count().keys()) == ["H", "X", "Z"]


@pytest.mark.unit
def test_gate_count_multiple_same_gate() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).h(q[1]).h(q[2])
    assert circ.gate_count() == {"H": 3}


@pytest.mark.unit
def test_gate_count_ignores_raw_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0]).raw_qsharp("let x = 1;")
    assert circ.gate_count() == {"H": 1}


# ------------------------------------------------------------------
# compute_qubit_count (standalone function)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_compute_qubit_count_empty() -> None:
    assert compute_qubit_count([]) == 0


@pytest.mark.unit
def test_compute_qubit_count_bell() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    assert compute_qubit_count(circ.instructions) == 2


@pytest.mark.unit
def test_compute_qubit_count_ghz_5() -> None:
    circ = Circuit()
    q = circ.allocate(5)
    circ.h(q[0])
    for i in range(4):
        circ.cx(q[i], q[i + 1])
    assert compute_qubit_count(circ.instructions) == 5


# ------------------------------------------------------------------
# Serialization: to_dict / from_dict / to_json / from_json
# ------------------------------------------------------------------


@pytest.mark.unit
def test_to_dict_roundtrip() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure(q[0])
    d = circ.to_dict()
    restored = Circuit.from_dict(d)
    assert restored.qubit_count() == 2
    assert restored.depth() == circ.depth()
    assert restored.gate_count() == circ.gate_count()


@pytest.mark.unit
def test_to_json_roundtrip() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    j = circ.to_json()
    restored = Circuit.from_json(j)
    assert restored.qubit_count() == circ.qubit_count()
    assert restored.gate_count() == circ.gate_count()


@pytest.mark.unit
def test_to_dict_with_name() -> None:
    circ = Circuit()
    circ.allocate(1)
    d = circ.to_dict(name="my_circuit")
    assert d["name"] == "my_circuit"


@pytest.mark.unit
def test_to_dict_contains_expected_keys() -> None:
    circ = Circuit()
    circ.allocate(1)
    d = circ.to_dict()
    assert "name" in d
    assert "num_qubits" in d
    assert "qubits" in d
    assert "registers" in d
    assert "instructions" in d
    assert "metadata" in d


@pytest.mark.unit
def test_serialization_all_gate_types() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).x(q[0]).y(q[0]).z(q[0]).s(q[0]).t(q[0])
    circ.rx(1.0, q[0]).ry(2.0, q[0]).rz(3.0, q[0]).r1(0.5, q[0])
    circ.cx(q[0], q[1]).cz(q[0], q[1]).swap(q[0], q[1])
    circ.ccx(q[0], q[1], q[2])
    d = circ.to_dict()
    restored = Circuit.from_dict(d)
    assert restored.gate_count() == circ.gate_count()


@pytest.mark.unit
def test_serialization_preserves_adjoint() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.s, q[0])
    d = circ.to_dict()
    restored = Circuit.from_dict(d)
    inst = restored.instructions[0]
    assert isinstance(inst, Instruction)
    assert inst.is_adjoint is True


@pytest.mark.unit
def test_serialization_preserves_controls() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.controlled(circ.h, [q[0]], q[1])
    d = circ.to_dict()
    restored = Circuit.from_dict(d)
    inst = restored.instructions[0]
    assert isinstance(inst, Instruction)
    assert len(inst.controls) == 1


@pytest.mark.unit
def test_serialization_preserves_raw_qsharp() -> None:
    circ = Circuit()
    circ.allocate(1)
    circ.raw_qsharp("let x = 42;")
    d = circ.to_dict()
    restored = Circuit.from_dict(d)
    inst = restored.instructions[0]
    assert isinstance(inst, RawQSharp)
    assert inst.code == "let x = 42;"


@pytest.mark.unit
def test_serialization_preserves_measurement_label() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.measure(q[0], label="result")
    d = circ.to_dict()
    restored = Circuit.from_dict(d)
    inst = restored.instructions[0]
    assert isinstance(inst, Measurement)
    assert inst.label == "result"


# ------------------------------------------------------------------
# circuit_from_dict validation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_from_dict_missing_registers_raises() -> None:
    with pytest.raises(CircuitError, match="missing required key 'registers'"):
        Circuit.from_dict({"instructions": []})


@pytest.mark.unit
def test_from_dict_missing_instructions_raises() -> None:
    with pytest.raises(CircuitError, match="missing required key 'instructions'"):
        Circuit.from_dict({"registers": []})


@pytest.mark.unit
def test_from_dict_missing_register_size_raises() -> None:
    data = {"registers": [{"label": "q"}], "instructions": []}
    with pytest.raises(CircuitError, match="missing 'size'"):
        Circuit.from_dict(data)


@pytest.mark.unit
def test_from_dict_missing_instruction_type_raises() -> None:
    data = {"registers": [{"size": 1}], "instructions": [{"gate": "H"}]}
    with pytest.raises(CircuitError, match="missing 'type'"):
        Circuit.from_dict(data)


# ------------------------------------------------------------------
# draw_circuit (ASCII visualization)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_draw_empty_circuit() -> None:
    circ = Circuit()
    assert circ.draw() == "(empty circuit)"


@pytest.mark.unit
def test_draw_no_gates() -> None:
    circ = Circuit()
    circ.allocate(2)
    assert circ.draw() == "(empty circuit)"


@pytest.mark.unit
def test_draw_single_h_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0])
    result = circ.draw()
    assert "H" in result
    assert "q[0]:" in result


@pytest.mark.unit
def test_draw_bell_state() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    result = circ.draw()
    assert "H" in result
    assert "*" in result
    assert "X" in result
    lines = [ln for ln in result.strip().split("\n") if "q[" in ln]
    assert len(lines) == 2


@pytest.mark.unit
def test_draw_with_measurement() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.h(q[0]).measure(q[0])
    result = circ.draw()
    assert "M" in result


@pytest.mark.unit
def test_draw_parameterized_gate() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(1.5707, q[0])
    result = circ.draw()
    assert "Rx" in result


@pytest.mark.unit
def test_draw_returns_string() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    assert isinstance(circ.draw(), str)


@pytest.mark.unit
def test_draw_truncation_many_qubits() -> None:
    circ = Circuit()
    q = circ.allocate(15)
    for i in range(15):
        circ.h(q[i])
    result = circ.draw()
    assert "more qubits" in result


@pytest.mark.unit
def test_draw_ghz_3() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2])
    result = circ.draw()
    assert "H" in result
    assert result.count("*") >= 2
    assert result.count("X") >= 2


# ------------------------------------------------------------------
# Cross-cutting: build -> analyze -> codegen -> parse -> re-analyze
# ------------------------------------------------------------------


@pytest.mark.unit
def test_cross_cutting_qsharp_roundtrip() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2])
    depth_before = circ.depth()
    count_before = circ.gate_count()
    qsharp = circ.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    assert parsed.depth() == depth_before
    assert parsed.gate_count() == count_before


@pytest.mark.unit
def test_cross_cutting_openqasm_roundtrip() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    depth_before = circ.depth()
    count_before = circ.gate_count()
    oq = circ.to_openqasm()
    parsed = Circuit.from_openqasm(oq)
    assert parsed.depth() == depth_before
    assert parsed.gate_count() == count_before


@pytest.mark.unit
def test_cross_cutting_json_roundtrip() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2]).measure_all()
    depth_before = circ.depth()
    count_before = circ.gate_count()
    j = circ.to_json()
    restored = Circuit.from_json(j)
    assert restored.depth() == depth_before
    assert restored.gate_count() == count_before


@pytest.mark.unit
def test_cross_cutting_dict_to_qsharp() -> None:
    """Build -> to_dict -> from_dict -> to_qsharp -> from_qsharp."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    d = circ.to_dict()
    restored = Circuit.from_dict(d)
    qsharp = restored.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    assert parsed.depth() == circ.depth()
    assert parsed.gate_count() == circ.gate_count()
