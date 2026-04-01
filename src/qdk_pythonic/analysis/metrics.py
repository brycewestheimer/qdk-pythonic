"""Circuit metrics: depth, gate count, qubit count, serialization."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from qdk_pythonic.analysis._helpers import involved_indices
from qdk_pythonic.core.gates import GATE_CATALOG
from qdk_pythonic.core.instruction import (
    Instruction,
    InstructionLike,
    Measurement,
    RawQSharp,
)
from qdk_pythonic.core.parameter import Parameter
from qdk_pythonic.core.qubit import Qubit

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


def compute_depth(instructions: list[InstructionLike]) -> int:
    """Compute circuit depth via time-step scheduling.

    Each instruction occupies one time step. The assigned step is the
    earliest step at which all involved qubits are available. RawQSharp
    instructions are skipped.

    Args:
        instructions: The instruction list to analyze.

    Returns:
        The circuit depth (0 for empty circuits).
    """
    qubit_time: dict[int, int] = {}
    for inst in instructions:
        indices = involved_indices(inst)
        if not indices:
            continue
        step = max(qubit_time.get(idx, 0) for idx in indices)
        for idx in indices:
            qubit_time[idx] = step + 1
    return max(qubit_time.values(), default=0)


def compute_gate_count(
    instructions: list[InstructionLike],
) -> dict[str, int]:
    """Count gates by type name.

    Only ``Instruction`` types are counted; ``Measurement`` and
    ``RawQSharp`` are ignored.

    Args:
        instructions: The instruction list to analyze.

    Returns:
        A dict mapping gate name to count, sorted alphabetically.
    """
    counts: dict[str, int] = {}
    for inst in instructions:
        if isinstance(inst, Instruction):
            counts[inst.gate.name] = counts.get(inst.gate.name, 0) + 1
    return dict(sorted(counts.items()))


def compute_qubit_count(instructions: list[InstructionLike]) -> int:
    """Count distinct qubits referenced across all instructions.

    Examines targets and controls of ``Instruction`` types and the
    target of ``Measurement`` types. ``RawQSharp`` is skipped.

    Args:
        instructions: The instruction list to analyze.

    Returns:
        The number of distinct qubit indices.
    """
    seen: set[int] = set()
    for inst in instructions:
        seen.update(involved_indices(inst))
    return len(seen)


def _serialize_param(p: float | Parameter) -> float | dict[str, str]:
    """Serialize a parameter value for JSON compatibility."""
    if isinstance(p, Parameter):
        return {"kind": "symbolic", "name": p.name}
    return p


def _deserialize_param(p: Any) -> float | Parameter:
    """Deserialize a parameter value from a dict or numeric literal."""
    if isinstance(p, dict) and p.get("kind") == "symbolic":
        return Parameter(name=p["name"])
    if isinstance(p, int):
        return float(p)
    return float(p)


def _serialize_instruction(inst: InstructionLike) -> dict[str, Any]:
    """Convert a single instruction to a plain dict.

    Args:
        inst: The instruction to serialize.

    Returns:
        A dict representation of the instruction.
    """
    if isinstance(inst, Instruction):
        return {
            "type": "gate",
            "gate": inst.gate.name,
            "targets": [q.index for q in inst.targets],
            "params": [_serialize_param(p) for p in inst.params],
            "controls": [q.index for q in inst.controls],
            "is_adjoint": inst.is_adjoint,
        }
    if isinstance(inst, Measurement):
        return {
            "type": "measurement",
            "target": inst.target.index,
            "label": inst.label,
        }
    # RawQSharp
    assert isinstance(inst, RawQSharp)
    return {
        "type": "raw_qsharp",
        "code": inst.code,
    }


def circuit_to_dict(
    circuit: Circuit,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize a Circuit to a plain dict.

    Args:
        circuit: The Circuit to serialize.
        name: Optional circuit name.
        metadata: Optional metadata dict.

    Returns:
        A dict with keys: name, num_qubits, qubits, registers,
        instructions, metadata.
    """
    return {
        "name": name,
        "num_qubits": circuit.qubit_count(),
        "qubits": [
            {"index": q.index, "label": q.label} for q in circuit.qubits
        ],
        "registers": [
            {"size": len(reg), "label": reg.label}
            for reg in circuit.registers
        ],
        "instructions": [
            _serialize_instruction(inst) for inst in circuit.instructions
        ],
        "metadata": metadata,
    }


def circuit_from_dict(data: dict[str, Any]) -> Circuit:
    """Reconstruct a Circuit from a plain dict.

    Args:
        data: A dict previously produced by ``circuit_to_dict``.

    Returns:
        A reconstructed Circuit.

    Raises:
        CircuitError: If the dict is missing required keys.
    """
    from qdk_pythonic.core.circuit import Circuit as _Circuit
    from qdk_pythonic.exceptions import CircuitError

    for key in ("registers", "instructions"):
        if key not in data:
            raise CircuitError(
                f"Invalid circuit dict: missing required key {key!r}"
            )

    circ = _Circuit()

    # Allocate registers to recreate qubits in the original order.
    for reg_info in data["registers"]:
        if "size" not in reg_info:
            raise CircuitError(
                f"Invalid register entry: missing 'size' key in {reg_info!r}"
            )
        circ.allocate(reg_info["size"], label=reg_info.get("label"))

    qubit_by_index: dict[int, Qubit] = {q.index: q for q in circ.qubits}

    for entry in data["instructions"]:
        if "type" not in entry:
            raise CircuitError(
                f"Invalid instruction entry: missing 'type' key in {entry!r}"
            )
        if entry["type"] == "gate":
            gate = GATE_CATALOG[entry["gate"]]
            targets = tuple(qubit_by_index[i] for i in entry["targets"])
            params = tuple(
                _deserialize_param(p)
                for p in entry.get("params", [])
            )
            controls = tuple(
                qubit_by_index[i] for i in entry.get("controls", [])
            )
            is_adjoint = entry.get("is_adjoint", False)
            inst = Instruction(
                gate=gate,
                targets=targets,
                params=params,
                controls=controls,
                is_adjoint=is_adjoint,
            )
            circ.add_instruction(inst)
        elif entry["type"] == "measurement":
            target = qubit_by_index[entry["target"]]
            meas = Measurement(target=target, label=entry.get("label"))
            circ.add_instruction(meas)
        elif entry["type"] == "raw_qsharp":
            raw = RawQSharp(code=entry["code"])
            circ.add_instruction(raw)
        else:
            raise CircuitError(
                f"Unknown instruction type: {entry['type']!r}"
            )

    return circ


def circuit_to_json(
    circuit: Circuit,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    indent: int = 2,
) -> str:
    """Serialize a Circuit to a JSON string.

    Args:
        circuit: The Circuit to serialize.
        name: Optional circuit name.
        metadata: Optional metadata dict.
        indent: JSON indentation level.

    Returns:
        A JSON string.
    """
    return json.dumps(
        circuit_to_dict(circuit, name=name, metadata=metadata),
        indent=indent,
    )


def circuit_from_json(json_str: str) -> Circuit:
    """Reconstruct a Circuit from a JSON string.

    Args:
        json_str: A JSON string previously produced by
            ``circuit_to_json``.

    Returns:
        A reconstructed Circuit.
    """
    return circuit_from_dict(json.loads(json_str))
