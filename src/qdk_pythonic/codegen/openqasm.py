"""OpenQASM 3.0 code generator: Circuit IR to OpenQASM source strings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qdk_pythonic.codegen._helpers import build_qubit_map
from qdk_pythonic.codegen.base import CodeGenerator
from qdk_pythonic.core.instruction import Instruction, Measurement, RawQSharp
from qdk_pythonic.core.parameter import Parameter
from qdk_pythonic.exceptions import CodegenError

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit
    from qdk_pythonic.core.qubit import Qubit


class OpenQASMCodeGenerator(CodeGenerator):
    """Generates OpenQASM 3.0 source code from a Circuit."""

    def generate(self, circuit: Circuit) -> str:
        """Generate an OpenQASM 3.0 program for the given circuit.

        Args:
            circuit: The circuit to serialize.

        Returns:
            An OpenQASM 3.0 program string.
        """
        lines: list[str] = [
            "OPENQASM 3.0;",
            'include "stdgates.inc";',
        ]

        registers = circuit.registers
        if not registers:
            return "\n".join(lines) + "\n"

        qubit_map = build_qubit_map(registers)

        # Qubit declarations
        lines.append("")
        for reg in registers:
            reg_label = reg.label if reg.label else "q"
            lines.append(f"qubit[{len(reg)}] {reg_label};")

        # Gate instructions
        gate_lines: list[str] = []
        measurements: list[Measurement] = []

        for inst in circuit.instructions:
            if isinstance(inst, Instruction):
                gate_lines.append(self._serialize_instruction(inst, qubit_map))
            elif isinstance(inst, Measurement):
                measurements.append(inst)
            elif isinstance(inst, RawQSharp):
                raise CodegenError(
                    "Cannot export raw Q# fragment to OpenQASM. "
                    "Remove raw_qsharp() calls or use to_qsharp() instead."
                )

        if gate_lines:
            lines.append("")
            lines.extend(gate_lines)

        # Measurement declarations and assignments
        if measurements:
            lines.append("")
            lines.append(f"bit[{len(measurements)}] c;")
            for i, m in enumerate(measurements):
                ref = self._qubit_ref(m.target, qubit_map)
                lines.append(f"c[{i}] = measure {ref};")

        lines.append("")
        return "\n".join(lines)

    def generate_operation(self, name: str, circuit: Circuit) -> str:
        """Generate an OpenQASM 3.0 program (same as generate).

        OpenQASM programs are self-contained, so this returns the same
        output as generate().

        Args:
            name: The operation name (unused for OpenQASM).
            circuit: The circuit to serialize.

        Returns:
            An OpenQASM 3.0 program string.
        """
        return self.generate(circuit)

    def _qubit_ref(self, qubit: Qubit, qubit_map: dict[int, str]) -> str:
        """Get the OpenQASM reference string for a qubit.

        Args:
            qubit: The qubit to look up.
            qubit_map: The qubit-to-reference mapping.

        Returns:
            The OpenQASM reference string.
        """
        return qubit_map[qubit.index]

    def _serialize_instruction(
        self, inst: Instruction, qubit_map: dict[int, str]
    ) -> str:
        """Serialize a single gate instruction to OpenQASM.

        Args:
            inst: The instruction to serialize.
            qubit_map: The qubit-to-reference mapping.

        Returns:
            An OpenQASM gate invocation string.
        """
        for p in inst.params:
            if isinstance(p, Parameter):
                raise CodegenError(
                    f"Cannot generate OpenQASM for unbound parameter "
                    f"'{p.name}'; call bind_parameters() first"
                )

        gate_name = inst.gate.openqasm_name
        target_refs = [self._qubit_ref(q, qubit_map) for q in inst.targets]

        has_controls = len(inst.controls) > 0
        is_adjoint = inst.is_adjoint

        # Build modifier prefix
        prefix = ""
        if has_controls and is_adjoint:
            prefix = "ctrl @ inv @ "
        elif has_controls:
            prefix = "ctrl @ "
        elif is_adjoint:
            prefix = "inv @ "

        # Build parameter string
        if inst.params:
            params_str = ", ".join(repr(p) for p in inst.params)
            param_part = f"({params_str})"
        else:
            param_part = ""

        # Build qubit list
        if has_controls:
            control_refs = [self._qubit_ref(q, qubit_map) for q in inst.controls]
            all_refs = control_refs + target_refs
        else:
            all_refs = target_refs

        qubits_str = ", ".join(all_refs)
        return f"{prefix}{gate_name}{param_part} {qubits_str};"
