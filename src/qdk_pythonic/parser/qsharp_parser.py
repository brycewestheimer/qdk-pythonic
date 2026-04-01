"""Q# source string parser: Q# to Circuit IR."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.gates import GATE_CATALOG, GateDefinition
from qdk_pythonic.core.qubit import Qubit, QubitRegister
from qdk_pythonic.exceptions import ParserError, UnsupportedConstructError
from qdk_pythonic.parser._expr_eval import eval_math_expr

_QSHARP_CONSTANTS: dict[str, float] = {
    "Std.Math.PI()": math.pi,
    "PI()": math.pi,
}

# Keywords that signal unsupported control flow / constructs.
_UNSUPPORTED_KEYWORDS = frozenset({
    "for", "if", "elif", "else", "repeat", "until",
    "while", "function", "internal", "newtype", "open", "return",
})

_RE_UNSUPPORTED = re.compile(
    r"\b(" + "|".join(sorted(_UNSUPPORTED_KEYWORDS)) + r")\b"
)

# Regex for array qubit allocation: use <name> = Qubit[<n>];
_RE_ALLOC_ARRAY = re.compile(
    r"use\s+(\w+)\s*=\s*Qubit\[\s*(\d+)\s*\]\s*;",
)
# Regex for single qubit allocation: use <name> = Qubit();
_RE_ALLOC_SINGLE = re.compile(
    r"use\s+(\w+)\s*=\s*Qubit\(\)\s*;",
)

# Measurement patterns
_RE_MEASURE_LET = re.compile(
    r"let\s+\w+\s*=\s*(?:MResetZ|M)\(\s*([^)]+)\s*\)\s*;",
)
_RE_MEASURE_BARE = re.compile(
    r"(?:MResetZ|M)\(\s*([^)]+)\s*\)\s*;",
)

# Controlled Adjoint gate: Controlled Adjoint <Gate>([<controls>], <rest>);
_RE_CTRL_ADJ = re.compile(
    r"Controlled\s+Adjoint\s+(\w+)\((\[.*?\]),\s*(.+)\)\s*;",
)
# Controlled gate: Controlled <Gate>([<controls>], <rest>);
_RE_CTRL = re.compile(
    r"Controlled\s+(\w+)\((\[.*?\]),\s*(.+)\)\s*;",
)
# Adjoint gate: Adjoint <Gate>(<args>);
_RE_ADJOINT = re.compile(
    r"Adjoint\s+(\w+)\((.+)\)\s*;",
)
# Regular gate with parenthesized args: <Gate>(<args>);
_RE_GATE = re.compile(
    r"(\w+)\((.+)\)\s*;",
)


def _build_qsharp_name_to_gate() -> dict[str, GateDefinition]:
    """Build a mapping from Q# gate name to GateDefinition."""
    result: dict[str, GateDefinition] = {}
    for gate_def in GATE_CATALOG.values():
        result[gate_def.qsharp_name] = gate_def
    return result


_QSHARP_GATE_MAP = _build_qsharp_name_to_gate()


def _build_gate_to_method_name() -> dict[str, str]:
    """Map gate canonical name to Circuit method name."""
    return {
        "H": "h",
        "X": "x",
        "Y": "y",
        "Z": "z",
        "S": "s",
        "T": "t",
        "Rx": "rx",
        "Ry": "ry",
        "Rz": "rz",
        "R1": "r1",
        "CNOT": "cx",
        "CZ": "cz",
        "SWAP": "swap",
        "CCNOT": "ccx",
    }


_GATE_METHOD_MAP = _build_gate_to_method_name()


class QSharpParser:
    """Parses common Q# circuit patterns into a Circuit object.

    Supports a subset of Q# that covers standard gate operations,
    measurements, controlled gates, and adjoint gates. Control flow
    and other advanced constructs raise UnsupportedConstructError.
    """

    def parse(self, source: str) -> Circuit:
        """Parse a Q# source string into a Circuit.

        Args:
            source: Q# source code (typically a block expression).

        Returns:
            A Circuit populated with the parsed gates and measurements.

        Raises:
            ParserError: If the source contains unknown gates or invalid references.
            UnsupportedConstructError: If the source uses unsupported constructs.
        """
        stripped = source.strip()
        if not stripped:
            return Circuit()

        circuit = Circuit()
        qubit_map: dict[str, QubitRegister] = {}

        statements = self._extract_statements(stripped)
        non_alloc: list[str] = []

        # First pass: extract qubit allocations
        for stmt in statements:
            alloc_arr = _RE_ALLOC_ARRAY.search(stmt)
            if alloc_arr:
                reg_name = alloc_arr.group(1)
                count = int(alloc_arr.group(2))
                reg = circuit.allocate(count, label=reg_name)
                qubit_map[reg_name] = reg
                continue

            alloc_single = _RE_ALLOC_SINGLE.search(stmt)
            if alloc_single:
                reg_name = alloc_single.group(1)
                reg = circuit.allocate(1, label=reg_name)
                qubit_map[reg_name] = reg
                continue

            non_alloc.append(stmt)

        # Second pass: process remaining statements
        for stmt in non_alloc:
            self._process_line(stmt, circuit, qubit_map)

        return circuit

    @staticmethod
    def _extract_statements(source: str) -> list[str]:
        """Split Q# source into individual statements.

        Handles both multi-line and single-line formats by splitting
        on semicolons and normalizing whitespace.

        Args:
            source: The raw source string.

        Returns:
            A list of stripped statement strings (with trailing semicolons).
        """
        # Remove braces and split on semicolons
        cleaned = source.replace("{", " ").replace("}", " ")
        parts = cleaned.split(";")
        statements: list[str] = []
        for part in parts:
            trimmed = part.strip()
            if trimmed:
                # Re-add the semicolon since our regexes expect it
                statements.append(trimmed + ";")
        return statements

    def _resolve_qubit(
        self,
        ref: str,
        qubit_map: dict[str, QubitRegister],
    ) -> Qubit:
        """Resolve a qubit reference like 'q[0]' or 'reg[2]' to a Qubit.

        Args:
            ref: The qubit reference string.
            qubit_map: Mapping from register name to QubitRegister.

        Returns:
            The resolved Qubit object.

        Raises:
            ParserError: If the reference is invalid.
        """
        ref = ref.strip()
        m = re.match(r"(\w+)\[(\d+)\]", ref)
        if m:
            reg_name = m.group(1)
            idx = int(m.group(2))
            reg = qubit_map.get(reg_name)
            if reg is None:
                raise ParserError(f"Unknown qubit register: {reg_name}")
            if idx >= len(reg):
                raise ParserError(
                    f"Qubit index {idx} out of range for register "
                    f"'{reg_name}' (size {len(reg)})"
                )
            qubit = reg[idx]
            assert isinstance(qubit, Qubit)
            return qubit

        # Bare name (single qubit allocation)
        reg = qubit_map.get(ref)
        if reg is not None and len(reg) == 1:
            qubit = reg[0]
            assert isinstance(qubit, Qubit)
            return qubit

        raise ParserError(f"Invalid qubit reference: {ref}")

    def _resolve_qubits(
        self,
        refs_str: str,
        qubit_map: dict[str, QubitRegister],
    ) -> list[Qubit]:
        """Resolve a comma-separated list of qubit references.

        Args:
            refs_str: Comma-separated qubit references.
            qubit_map: Mapping from register name to QubitRegister.

        Returns:
            A list of resolved Qubit objects.
        """
        parts = [p.strip() for p in refs_str.split(",") if p.strip()]
        return [self._resolve_qubit(p, qubit_map) for p in parts]

    def _get_gate_method(
        self,
        gate_name: str,
        circuit: Circuit,
    ) -> tuple[GateDefinition, Callable[..., Any]]:
        """Look up a gate definition and circuit method by Q# gate name.

        Args:
            gate_name: The Q# gate name (e.g. "H", "CNOT", "Rx").
            circuit: The circuit to look up the method on.

        Returns:
            A tuple of (GateDefinition, bound method).

        Raises:
            ParserError: If the gate name is unknown.
        """
        gate_def = _QSHARP_GATE_MAP.get(gate_name)
        if gate_def is None:
            raise ParserError(f"Unknown Q# gate: {gate_name}")
        method_name = _GATE_METHOD_MAP.get(gate_def.name)
        if method_name is None:
            raise ParserError(f"No circuit method for gate: {gate_def.name}")
        method = getattr(circuit, method_name)
        return gate_def, method

    def _parse_controlled_args(
        self,
        rest: str,
        qubit_map: dict[str, QubitRegister],
        gate_def: GateDefinition,
    ) -> tuple[tuple[float, ...], list[Qubit]]:
        """Parse the arguments part of a Controlled gate call.

        For Controlled gates, the rest after controls is either:
        - A single qubit: ``q[1]``
        - A tuple: ``(angle, q[1])`` or ``(q[0], q[1])``

        Args:
            rest: The string after ``[controls],``.
            qubit_map: Mapping from register name to QubitRegister.
            gate_def: The gate definition for parameter count.

        Returns:
            A tuple of (params, target_qubits).
        """
        rest = rest.strip()
        # Strip outer parentheses if present
        if rest.startswith("(") and rest.endswith(")"):
            rest = rest[1:-1].strip()

        parts = [p.strip() for p in rest.split(",")]

        if gate_def.num_params > 0:
            # First N parts are params, rest are qubits
            param_parts = parts[:gate_def.num_params]
            qubit_parts = parts[gate_def.num_params:]
            params = tuple(
                eval_math_expr(p, _QSHARP_CONSTANTS) for p in param_parts
            )
            targets = [self._resolve_qubit(q, qubit_map) for q in qubit_parts]
            return params, targets
        else:
            targets = [self._resolve_qubit(q, qubit_map) for q in parts]
            return (), targets

    def _check_unsupported(self, line: str) -> None:
        """Raise UnsupportedConstructError if the line uses unsupported keywords.

        Args:
            line: The source line to check.

        Raises:
            UnsupportedConstructError: If an unsupported keyword is found.
        """
        if _RE_UNSUPPORTED.search(line):
            raise UnsupportedConstructError(
                f"Unsupported Q# construct: {line}"
            )

    def _process_line(
        self,
        line: str,
        circuit: Circuit,
        qubit_map: dict[str, QubitRegister],
    ) -> None:
        """Process a single non-allocation line.

        Args:
            line: The stripped source line.
            circuit: The circuit being built.
            qubit_map: Mapping from register name to QubitRegister.
        """
        # Skip comments and return expressions like "[r0, r1]" or "r0"
        if line.startswith("//") or line.startswith("[") or line.startswith("}"):
            return
        # Skip bare variable references (return expressions)
        if re.match(r"^r\d+$", line):
            return

        # Check unsupported constructs
        self._check_unsupported(line)

        # Measurement with let binding
        m = _RE_MEASURE_LET.match(line)
        if m:
            qubit = self._resolve_qubit(m.group(1), qubit_map)
            circuit.measure(qubit)
            return

        # Bare measurement
        m = _RE_MEASURE_BARE.match(line)
        if m:
            qubit = self._resolve_qubit(m.group(1), qubit_map)
            circuit.measure(qubit)
            return

        # Controlled Adjoint gate
        m = _RE_CTRL_ADJ.match(line)
        if m:
            gate_name = m.group(1)
            controls_str = m.group(2).strip()[1:-1]  # strip outer [ ]
            rest = m.group(3)
            gate_def, _ = self._get_gate_method(gate_name, circuit)
            controls = self._resolve_qubits(controls_str, qubit_map)
            params, targets = self._parse_controlled_args(
                rest, qubit_map, gate_def,
            )
            from qdk_pythonic.core.instruction import Instruction as Inst
            inst = Inst(
                gate=gate_def,
                targets=tuple(targets),
                params=params,
                controls=tuple(controls),
                is_adjoint=True,
            )
            circuit.add_instruction(inst)
            return

        # Controlled gate
        m = _RE_CTRL.match(line)
        if m:
            gate_name = m.group(1)
            controls_str = m.group(2).strip()[1:-1]  # strip outer [ ]
            rest = m.group(3)
            gate_def, method = self._get_gate_method(gate_name, circuit)
            controls = self._resolve_qubits(controls_str, qubit_map)
            params, targets = self._parse_controlled_args(
                rest, qubit_map, gate_def,
            )
            circuit.controlled(method, controls, *params, *targets)
            return

        # Adjoint gate
        m = _RE_ADJOINT.match(line)
        if m:
            gate_name = m.group(1)
            args_str = m.group(2)
            gate_def, method = self._get_gate_method(gate_name, circuit)
            if gate_def.num_params > 0:
                parts = [p.strip() for p in args_str.split(",")]
                params = tuple(
                    eval_math_expr(p, _QSHARP_CONSTANTS)
                    for p in parts[:gate_def.num_params]
                )
                targets = [
                    self._resolve_qubit(p, qubit_map)
                    for p in parts[gate_def.num_params:]
                ]
                circuit.adjoint(method, *params, *targets)
            else:
                targets = self._resolve_qubits(args_str, qubit_map)
                circuit.adjoint(method, *targets)
            return

        # Regular gate
        m = _RE_GATE.match(line)
        if m:
            gate_name = m.group(1)
            args_str = m.group(2)
            # Skip measurement-like patterns that slipped through
            if gate_name in ("MResetZ", "M", "let"):
                qubit = self._resolve_qubit(args_str.strip(), qubit_map)
                circuit.measure(qubit)
                return

            gate_def, method = self._get_gate_method(gate_name, circuit)
            if gate_def.num_params > 0:
                parts = [p.strip() for p in args_str.split(",")]
                param_vals = [
                    eval_math_expr(p, _QSHARP_CONSTANTS)
                    for p in parts[:gate_def.num_params]
                ]
                qubit_parts = parts[gate_def.num_params:]
                qubit_targets = [
                    self._resolve_qubit(q, qubit_map) for q in qubit_parts
                ]
                method(*param_vals, *qubit_targets)
            else:
                qubit_targets = self._resolve_qubits(args_str, qubit_map)
                method(*qubit_targets)
            return

        raise ParserError(f"Unrecognized Q# statement: {line}")
