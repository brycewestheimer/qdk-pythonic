"""Q# code generator: Circuit IR to Q# source strings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qdk_pythonic.codegen._helpers import build_qubit_map
from qdk_pythonic.codegen.base import CodeGenerator
from qdk_pythonic.core.instruction import Instruction, Measurement, RawQSharp

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit
    from qdk_pythonic.core.qubit import Qubit


class QSharpCodeGenerator(CodeGenerator):
    """Generates Q# source code from a Circuit."""

    def generate(self, circuit: Circuit) -> str:
        """Generate a Q# block expression for the given circuit.

        Args:
            circuit: The circuit to serialize.

        Returns:
            A Q# block expression string.
        """
        registers = circuit.registers
        if not registers:
            return "{ }"

        qubit_map = build_qubit_map(registers)
        body_lines = self._build_body(circuit, qubit_map)

        if not body_lines:
            return "{ }"

        lines = ["{"]
        for line in body_lines:
            lines.append(f"    {line}")
        lines.append("}")
        return "\n".join(lines)

    def generate_operation(self, name: str, circuit: Circuit) -> str:
        """Generate a named Q# operation for the given circuit.

        Args:
            name: The operation name.
            circuit: The circuit to serialize.

        Returns:
            A Q# operation definition string.
        """
        registers = circuit.registers
        if not registers:
            return f"operation {name}() : Unit {{ }}"

        qubit_map = build_qubit_map(registers)
        body_lines = self._build_body(circuit, qubit_map)

        if not body_lines:
            return f"operation {name}() : Unit {{ }}"

        return_type = self._infer_return_type(circuit)

        lines = [f"operation {name}() : {return_type} {{"]
        for line in body_lines:
            lines.append(f"    {line}")
        lines.append("}")
        return "\n".join(lines)

    def _qubit_ref(self, qubit: Qubit, qubit_map: dict[int, str]) -> str:
        """Get the Q# reference string for a qubit.

        Args:
            qubit: The qubit to look up.
            qubit_map: The qubit-to-reference mapping.

        Returns:
            The Q# reference string.
        """
        return qubit_map[qubit.index]

    def _build_body(
        self,
        circuit: Circuit,
        qubit_map: dict[int, str],
    ) -> list[str]:
        """Build the body lines (use statements, gates, measurements, return).

        Args:
            circuit: The circuit to serialize.
            qubit_map: The qubit-to-reference mapping.

        Returns:
            A list of Q# source lines (without indentation).
        """
        lines: list[str] = []

        # Use statements for each register
        for reg in circuit.registers:
            reg_label = reg.label if reg.label else "q"
            lines.append(f"use {reg_label} = Qubit[{len(reg)}];")

        # Process instructions
        measurement_count = 0
        measurement_vars: list[str] = []

        for inst in circuit.instructions:
            if isinstance(inst, Instruction):
                lines.append(self._serialize_instruction(inst, qubit_map))
            elif isinstance(inst, Measurement):
                var_name = f"r{measurement_count}"
                ref = self._qubit_ref(inst.target, qubit_map)
                lines.append(f"let {var_name} = MResetZ({ref});")
                measurement_vars.append(var_name)
                measurement_count += 1
            elif isinstance(inst, RawQSharp):
                for raw_line in inst.code.splitlines():
                    lines.append(raw_line)

        # Return expression
        if len(measurement_vars) == 1:
            lines.append(measurement_vars[0])
        elif len(measurement_vars) > 1:
            joined = ", ".join(measurement_vars)
            lines.append(f"[{joined}]")

        return lines

    def _serialize_instruction(
        self, inst: Instruction, qubit_map: dict[int, str]
    ) -> str:
        """Serialize a single gate instruction to Q#.

        Args:
            inst: The instruction to serialize.
            qubit_map: The qubit-to-reference mapping.

        Returns:
            A Q# gate invocation string.
        """
        gate_name = inst.gate.qsharp_name
        target_refs = [self._qubit_ref(q, qubit_map) for q in inst.targets]

        has_controls = len(inst.controls) > 0
        is_adjoint = inst.is_adjoint

        # Build prefix
        prefix = ""
        if has_controls and is_adjoint:
            prefix = "Controlled Adjoint "
        elif has_controls:
            prefix = "Controlled "
        elif is_adjoint:
            prefix = "Adjoint "

        # Build argument list
        if has_controls:
            control_refs = [self._qubit_ref(q, qubit_map) for q in inst.controls]
            controls_str = ", ".join(control_refs)

            # For controlled gates, the args are ([controls], (params..., targets...))
            # But Q# syntax varies:
            # - Controlled H([c], t)
            # - Controlled Rx([c], (angle, t))
            # For multi-qubit gates with controls:
            # - Controlled SWAP([c], (t0, t1))
            if inst.params:
                params_str = ", ".join(repr(p) for p in inst.params)
                targets_str = ", ".join(target_refs)
                inner = f"{params_str}, {targets_str}"
                return f"{prefix}{gate_name}([{controls_str}], ({inner}));"
            elif len(target_refs) == 1:
                return f"{prefix}{gate_name}([{controls_str}], {target_refs[0]});"
            else:
                targets_str = ", ".join(target_refs)
                return f"{prefix}{gate_name}([{controls_str}], ({targets_str}));"
        else:
            # Non-controlled
            if inst.params:
                params_str = ", ".join(repr(p) for p in inst.params)
                targets_str = ", ".join(target_refs)
                args = f"{params_str}, {targets_str}"
            else:
                args = ", ".join(target_refs)

            return f"{prefix}{gate_name}({args});"

    def _infer_return_type(self, circuit: Circuit) -> str:
        """Infer the Q# return type from measurements.

        Args:
            circuit: The circuit to inspect.

        Returns:
            The Q# return type string.
        """
        measurement_count = sum(
            1 for inst in circuit.instructions if isinstance(inst, Measurement)
        )
        if measurement_count == 0:
            return "Unit"
        elif measurement_count == 1:
            return "Result"
        else:
            return "Result[]"
