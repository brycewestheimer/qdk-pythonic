"""OpenQASM 3.0 source string parser: OpenQASM to Circuit IR."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.gates import GATE_CATALOG, GateDefinition
from qdk_pythonic.core.instruction import Instruction
from qdk_pythonic.core.qubit import Qubit, QubitRegister
from qdk_pythonic.exceptions import ParserError, UnsupportedConstructError
from qdk_pythonic.parser._expr_eval import eval_math_expr

_OPENQASM_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
}

# Keywords that signal unsupported constructs.
_UNSUPPORTED_KEYWORDS = frozenset({
    "gate", "def", "if", "for", "while", "input", "output", "box", "barrier",
})

# Header pattern
_RE_HEADER = re.compile(r"OPENQASM\s+(\d+\.\d+)\s*;")

# Include pattern
_RE_INCLUDE = re.compile(r'include\s+"[^"]+"\s*;')

# Qubit declaration: qubit[<n>] <name>;
_RE_QUBIT_DECL = re.compile(r"qubit\[\s*(\d+)\s*\]\s+(\w+)\s*;")

# Bit declaration: bit[<n>] <name>;
_RE_BIT_DECL = re.compile(r"bit\[\s*(\d+)\s*\]\s+(\w+)\s*;")

# Measurement assignment: <var>[<i>] = measure <qubit_ref>;
_RE_MEASURE_INDEXED = re.compile(
    r"\w+\[\s*\d+\s*\]\s*=\s*measure\s+(.+?)\s*;",
)
# Measurement assignment: <var> = measure <qubit_ref>;
_RE_MEASURE_BARE = re.compile(
    r"\w+\s*=\s*measure\s+(.+?)\s*;",
)

# Controlled+Adjoint gate: ctrl @ inv @ <gate>...
_RE_CTRL_INV = re.compile(
    r"ctrl\s+@\s+inv\s+@\s+(\w+)(?:\(([^)]*)\))?\s+(.+?)\s*;",
)
# Controlled gate: ctrl @ <gate>...
_RE_CTRL = re.compile(
    r"ctrl\s+@\s+(\w+)(?:\(([^)]*)\))?\s+(.+?)\s*;",
)
# Adjoint gate: inv @ <gate>...
_RE_INV = re.compile(
    r"inv\s+@\s+(\w+)(?:\(([^)]*)\))?\s+(.+?)\s*;",
)
# Regular gate with params: <gate>(<params>) <qubits>;
_RE_GATE_PARAMS = re.compile(
    r"(\w+)\(([^)]+)\)\s+(.+?)\s*;",
)
# Regular gate no params: <gate> <qubits>;
_RE_GATE_BARE = re.compile(
    r"(\w+)\s+(.+?)\s*;",
)


def _build_openqasm_name_to_gate() -> dict[str, GateDefinition]:
    """Build a mapping from OpenQASM gate name to GateDefinition."""
    result: dict[str, GateDefinition] = {}
    for gate_def in GATE_CATALOG.values():
        result[gate_def.openqasm_name] = gate_def
    return result


_OPENQASM_GATE_MAP = _build_openqasm_name_to_gate()

_GATE_METHOD_MAP: dict[str, str] = {
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


class OpenQASMParser:
    """Parses OpenQASM 3.0 circuit strings into Circuit objects.

    Supports a subset of OpenQASM 3.0 covering standard gate operations,
    measurements, controlled (``ctrl @``) and adjoint (``inv @``) modifiers.
    Unsupported constructs raise UnsupportedConstructError.
    """

    def parse(self, source: str) -> Circuit:
        """Parse an OpenQASM 3.0 source string into a Circuit.

        Args:
            source: OpenQASM 3.0 source code.

        Returns:
            A Circuit populated with the parsed gates and measurements.

        Raises:
            ParserError: If the header is missing/wrong or gates are unknown.
            UnsupportedConstructError: If the source uses unsupported constructs.
        """
        lines = [line.strip() for line in source.strip().splitlines()]
        lines = [ln for ln in lines if ln and not ln.startswith("//")]

        if not lines:
            raise ParserError("Empty OpenQASM source: missing OPENQASM header")

        # Validate header
        header_match = _RE_HEADER.match(lines[0])
        if not header_match:
            raise ParserError(
                f"Missing or invalid OPENQASM header: {lines[0]}"
            )
        version = header_match.group(1)
        if version != "3.0":
            raise ParserError(
                f"Unsupported OpenQASM version: {version} (only 3.0 is supported)"
            )

        circuit = Circuit()
        qubit_map: dict[str, QubitRegister] = {}
        process_lines: list[str] = []

        # Process declarations
        for line in lines[1:]:
            if _RE_INCLUDE.match(line):
                continue
            if _RE_QUBIT_DECL.match(line):
                m = _RE_QUBIT_DECL.match(line)
                assert m is not None
                count = int(m.group(1))
                name = m.group(2)
                reg = circuit.allocate(count, label=name)
                qubit_map[name] = reg
                continue
            if _RE_BIT_DECL.match(line):
                continue
            process_lines.append(line)

        # Process gates and measurements
        for line in process_lines:
            self._process_line(line, circuit, qubit_map)

        return circuit

    def _resolve_qubit(
        self,
        ref: str,
        qubit_map: dict[str, QubitRegister],
    ) -> Qubit:
        """Resolve a qubit reference like 'q[0]' to a Qubit.

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
        """Look up a gate definition and circuit method by OpenQASM gate name.

        Args:
            gate_name: The OpenQASM gate name (e.g. "h", "cx", "rx").
            circuit: The circuit to look up the method on.

        Returns:
            A tuple of (GateDefinition, bound method).

        Raises:
            ParserError: If the gate name is unknown.
        """
        gate_def = _OPENQASM_GATE_MAP.get(gate_name)
        if gate_def is None:
            raise ParserError(f"Unknown OpenQASM gate: {gate_name}")
        method_name = _GATE_METHOD_MAP.get(gate_def.name)
        if method_name is None:
            raise ParserError(f"No circuit method for gate: {gate_def.name}")
        method = getattr(circuit, method_name)
        return gate_def, method

    def _check_unsupported(self, line: str) -> None:
        """Raise UnsupportedConstructError if line uses unsupported keywords.

        Args:
            line: The source line to check.

        Raises:
            UnsupportedConstructError: If an unsupported keyword is found.
        """
        # Check if the line starts with an unsupported keyword
        first_word = line.split()[0] if line.split() else ""
        if first_word in _UNSUPPORTED_KEYWORDS:
            raise UnsupportedConstructError(
                f"Unsupported OpenQASM construct: {line}"
            )

    def _process_line(
        self,
        line: str,
        circuit: Circuit,
        qubit_map: dict[str, QubitRegister],
    ) -> None:
        """Process a single non-declaration line.

        Args:
            line: The stripped source line.
            circuit: The circuit being built.
            qubit_map: Mapping from register name to QubitRegister.
        """
        # Check unsupported constructs first
        self._check_unsupported(line)

        # Measurement (indexed)
        m = _RE_MEASURE_INDEXED.match(line)
        if m:
            qubit = self._resolve_qubit(m.group(1), qubit_map)
            circuit.measure(qubit)
            return

        # Measurement (bare)
        m = _RE_MEASURE_BARE.match(line)
        if m:
            qubit = self._resolve_qubit(m.group(1), qubit_map)
            circuit.measure(qubit)
            return

        # Controlled + Adjoint gate: ctrl @ inv @ <gate>
        m = _RE_CTRL_INV.match(line)
        if m:
            gate_name = m.group(1)
            params_str = m.group(2)
            qubits_str = m.group(3)
            gate_def, _ = self._get_gate_method(gate_name, circuit)
            all_qubits = self._resolve_qubits(qubits_str, qubit_map)
            params = self._parse_params(params_str) if params_str else ()
            # First qubit(s) are controls, rest are targets
            num_targets = gate_def.num_qubits
            controls = all_qubits[:-num_targets]
            targets = all_qubits[-num_targets:]
            inst = Instruction(
                gate=gate_def,
                targets=tuple(targets),
                params=params,
                controls=tuple(controls),
                is_adjoint=True,
            )
            circuit.add_instruction(inst)
            return

        # Controlled gate: ctrl @ <gate>
        m = _RE_CTRL.match(line)
        if m:
            gate_name = m.group(1)
            params_str = m.group(2)
            qubits_str = m.group(3)
            gate_def, method = self._get_gate_method(gate_name, circuit)
            all_qubits = self._resolve_qubits(qubits_str, qubit_map)
            params = self._parse_params(params_str) if params_str else ()
            num_targets = gate_def.num_qubits
            controls = all_qubits[:-num_targets]
            targets = all_qubits[-num_targets:]
            circuit.controlled(method, controls, *params, *targets)
            return

        # Adjoint gate: inv @ <gate>
        m = _RE_INV.match(line)
        if m:
            gate_name = m.group(1)
            params_str = m.group(2)
            qubits_str = m.group(3)
            gate_def, method = self._get_gate_method(gate_name, circuit)
            qubits = self._resolve_qubits(qubits_str, qubit_map)
            params = self._parse_params(params_str) if params_str else ()
            circuit.adjoint(method, *params, *qubits)
            return

        # Regular gate with parameters: <gate>(<params>) <qubits>
        m = _RE_GATE_PARAMS.match(line)
        if m:
            gate_name = m.group(1)
            params_str = m.group(2)
            qubits_str = m.group(3)
            gate_def, method = self._get_gate_method(gate_name, circuit)
            params = self._parse_params(params_str)
            qubits = self._resolve_qubits(qubits_str, qubit_map)
            method(*params, *qubits)
            return

        # Regular gate without parameters: <gate> <qubits>
        m = _RE_GATE_BARE.match(line)
        if m:
            gate_name = m.group(1)
            qubits_str = m.group(2)
            # Skip keywords that look like gate calls
            if gate_name in ("measure", "bit", "qubit", "include"):
                return
            gate_def, method = self._get_gate_method(gate_name, circuit)
            qubits = self._resolve_qubits(qubits_str, qubit_map)
            method(*qubits)
            return

    @staticmethod
    def _parse_params(params_str: str) -> tuple[float, ...]:
        """Parse a comma-separated parameter string into floats.

        Supports arithmetic expressions with ``pi`` (e.g. ``pi/2``).

        Args:
            params_str: Comma-separated parameter values.

        Returns:
            A tuple of float parameter values.

        Raises:
            ParserError: If a parameter expression cannot be evaluated.
        """
        parts = [p.strip() for p in params_str.split(",") if p.strip()]
        return tuple(eval_math_expr(p, _OPENQASM_CONSTANTS) for p in parts)
