"""ASCII circuit diagram renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qdk_pythonic.analysis._helpers import involved_indices
from qdk_pythonic.core.instruction import (
    Instruction,
    InstructionLike,
    Measurement,
    RawQSharp,
)

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit

_MAX_QUBITS = 10
_MAX_GATES = 30


def _schedule_instructions(
    instructions: list[InstructionLike],
) -> list[tuple[InstructionLike, int]]:
    """Assign each instruction to a time step.

    Uses greedy scheduling: each instruction is placed at the earliest
    step where all its qubits are available. RawQSharp instructions
    are excluded.

    Args:
        instructions: The instruction list.

    Returns:
        A list of (instruction, time_step) pairs.
    """
    qubit_time: dict[int, int] = {}
    scheduled: list[tuple[InstructionLike, int]] = []

    for inst in instructions:
        indices = involved_indices(inst)
        if not indices:
            continue
        step = max(qubit_time.get(idx, 0) for idx in indices)
        for idx in indices:
            qubit_time[idx] = step + 1
        scheduled.append((inst, step))

    return scheduled


def _gate_symbol(inst: Instruction) -> str:
    """Return the display symbol for a gate on its target qubit.

    Args:
        inst: The gate instruction.

    Returns:
        A string symbol for the gate.
    """
    name = inst.gate.name
    if inst.params:
        param_str = ", ".join(f"{p:.2f}" for p in inst.params)
        return f"[{name}({param_str})]"
    return name


def draw_circuit(circuit: Circuit) -> str:
    """Draw an ASCII representation of a quantum circuit.

    Each qubit is rendered as a horizontal wire with gate symbols
    placed in time-step-aligned columns. Controlled gates show ``*``
    on control qubits with ``|`` vertical connectors to the target.

    Args:
        circuit: The Circuit to draw.

    Returns:
        A multi-line ASCII string. Returns ``(empty circuit)`` if
        the circuit has no qubits or instructions.
    """
    all_qubits = circuit.qubits
    all_instructions: list[InstructionLike] = circuit.instructions

    if not all_qubits or not all_instructions:
        return "(empty circuit)"

    # Filter to renderable instructions (skip RawQSharp).
    renderable: list[InstructionLike] = [
        inst for inst in all_instructions if not isinstance(inst, RawQSharp)
    ]
    if not renderable:
        return "(empty circuit)"

    # Truncation.
    qubit_truncated = len(all_qubits) > _MAX_QUBITS
    gate_truncated = len(renderable) > _MAX_GATES
    qubits = all_qubits[:_MAX_QUBITS]
    renderable = renderable[:_MAX_GATES]

    qubit_indices = {q.index for q in qubits}

    # Schedule the (possibly truncated) instructions.
    scheduled = _schedule_instructions(renderable)
    if not scheduled:
        return "(empty circuit)"

    num_steps = max(step for _, step in scheduled) + 1

    # Build grid: (qubit_index, step) -> symbol string.
    grid: dict[tuple[int, int], str] = {}
    # Track vertical connectors: (qubit_index, step) for '|' lines.
    connectors: set[tuple[int, int]] = set()

    for inst, step in scheduled:
        if isinstance(inst, Measurement):
            if inst.target.index in qubit_indices:
                grid[(inst.target.index, step)] = "M"
            continue

        assert isinstance(inst, Instruction)

        targets = inst.targets
        controls = inst.controls
        gate_name = inst.gate.name

        if gate_name == "SWAP":
            for t in targets:
                if t.index in qubit_indices:
                    grid[(t.index, step)] = "x"
            _add_connectors(
                [t.index for t in targets], step, qubit_indices, connectors
            )
        elif gate_name in ("CNOT", "CZ", "CCNOT"):
            # Built-in multi-qubit gates: first N-1 targets are controls,
            # last target is the gate target.
            control_qubits = list(targets[:-1]) + list(controls)
            target_qubit = targets[-1]
            for cq in control_qubits:
                if cq.index in qubit_indices:
                    grid[(cq.index, step)] = "*"
            if target_qubit.index in qubit_indices:
                symbol = "X" if gate_name in ("CNOT", "CCNOT") else "Z"
                grid[(target_qubit.index, step)] = symbol
            all_involved = [q.index for q in control_qubits] + [
                target_qubit.index
            ]
            _add_connectors(all_involved, step, qubit_indices, connectors)
        elif controls:
            # User-applied controlled modifier.
            for cq in controls:
                if cq.index in qubit_indices:
                    grid[(cq.index, step)] = "*"
            for t in targets:
                if t.index in qubit_indices:
                    grid[(t.index, step)] = _gate_symbol(inst)
            all_involved = [q.index for q in controls] + [
                q.index for q in targets
            ]
            _add_connectors(all_involved, step, qubit_indices, connectors)
        else:
            # Single-qubit gate (or multi-qubit without control semantics).
            for t in targets:
                if t.index in qubit_indices:
                    grid[(t.index, step)] = _gate_symbol(inst)

    # Determine column widths.
    col_widths: list[int] = []
    for s in range(num_steps):
        max_sym = 1
        for q in qubits:
            sym = grid.get((q.index, s), "")
            if len(sym) > max_sym:
                max_sym = len(sym)
        col_widths.append(max_sym)

    # Build qubit labels.
    labels = [f"q[{q.index}]:" for q in qubits]
    label_width = max(len(lb) for lb in labels)

    # Render wire lines and connector lines.
    # For each pair of adjacent qubit rows, we may need a connector line.
    wire_lines: list[str] = []
    sorted_qubits = sorted(qubits, key=lambda q: q.index)

    for qi, q in enumerate(sorted_qubits):
        label = f"q[{q.index}]:".ljust(label_width)
        parts: list[str] = []
        for s in range(num_steps):
            w = col_widths[s]
            sym = grid.get((q.index, s), "")
            if sym:
                padded = sym.center(w)
                parts.append(f" {padded} ")
            else:
                parts.append("-" * (w + 2))
        wire_lines.append(label + "--" + "--".join(parts) + "--")

        # Add connector line between this qubit and the next one.
        if qi < len(sorted_qubits) - 1:
            next_q = sorted_qubits[qi + 1]
            has_connector = False
            for s in range(num_steps):
                if (q.index, s) in connectors or (
                    next_q.index, s
                ) in connectors:
                    has_connector = True
                    break
            if has_connector:
                spacer = " " * label_width
                cparts: list[str] = []
                for s in range(num_steps):
                    w = col_widths[s]
                    if (q.index, s) in connectors or (
                        next_q.index, s
                    ) in connectors:
                        pipe = "|".center(w + 2)
                        cparts.append(pipe)
                    else:
                        cparts.append(" " * (w + 2))
                wire_lines.append(spacer + "  " + "  ".join(cparts))

    # Truncation notes.
    notes: list[str] = []
    if gate_truncated:
        remaining = len(
            [
                i
                for i in all_instructions
                if not isinstance(i, RawQSharp)
            ]
        ) - _MAX_GATES
        notes.append(f"... ({remaining} more gates)")
    if qubit_truncated:
        remaining_q = len(all_qubits) - _MAX_QUBITS
        notes.append(f"... ({remaining_q} more qubits)")

    result = "\n".join(wire_lines)
    if notes:
        result += "\n" + "\n".join(notes)
    return result


def _add_connectors(
    indices: list[int],
    step: int,
    qubit_indices: set[int],
    connectors: set[tuple[int, int]],
) -> None:
    """Add vertical connector entries between the min and max qubit indices.

    Args:
        indices: Qubit indices involved in the gate.
        step: The time step.
        qubit_indices: The set of renderable qubit indices.
        connectors: The set to add connector entries to.
    """
    visible = [i for i in indices if i in qubit_indices]
    if len(visible) < 2:
        return
    lo, hi = min(visible), max(visible)
    for idx in range(lo, hi + 1):
        if idx in qubit_indices:
            connectors.add((idx, step))
