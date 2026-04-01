"""Circuit class: primary user-facing quantum circuit builder."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any

from qdk_pythonic.core.gates import (
    CCNOT,
    CNOT,
    CZ,
    R1,
    RX,
    RY,
    RZ,
    SWAP,
    GateDefinition,
    H,
    S,
    T,
    X,
    Y,
    Z,
)
from qdk_pythonic.core.instruction import (
    Instruction,
    InstructionLike,
    Measurement,
    RawQSharp,
)
from qdk_pythonic.core.qubit import Qubit, QubitRegister
from qdk_pythonic.exceptions import CircuitError


class Circuit:
    """A quantum circuit builder with Pythonic gate methods.

    Example::

        circ = Circuit()
        q = circ.allocate(2)
        circ.h(q[0]).cx(q[0], q[1]).measure_all()
    """

    def __init__(self) -> None:
        self._instructions: list[InstructionLike] = []
        self._qubits: list[Qubit] = []
        self._registers: list[QubitRegister] = []
        self._next_qubit_index: int = 0
        self._used_labels: set[str] = set()
        self._register_counter: int = 0

    # ------------------------------------------------------------------
    # Qubit allocation
    # ------------------------------------------------------------------

    def allocate(self, n: int, label: str | None = None) -> QubitRegister:
        """Allocate n qubits and return them as a QubitRegister.

        Args:
            n: Number of qubits to allocate. Must be >= 1.
            label: Optional label prefix for the qubits.

        Returns:
            A QubitRegister containing the newly allocated qubits.

        Raises:
            CircuitError: If n < 1.
        """
        if n < 1:
            raise CircuitError(f"Cannot allocate {n} qubits; n must be >= 1")

        if label is not None:
            if label in self._used_labels:
                raise CircuitError(f"Duplicate register label: {label!r}")
        else:
            # Auto-assign a unique label: first unlabeled gets "q", then "q1", ...
            if "q" not in self._used_labels:
                label = "q"
            else:
                while f"q{self._register_counter}" in self._used_labels:
                    self._register_counter += 1
                label = f"q{self._register_counter}"
                self._register_counter += 1
        self._used_labels.add(label)

        qubits: list[Qubit] = []
        for i in range(n):
            qubit_label = f"{label}_{i}"
            qubit = Qubit(
                index=self._next_qubit_index,
                label=qubit_label,
                _circuit_id=id(self),
            )
            qubits.append(qubit)
            self._next_qubit_index += 1

        self._qubits.extend(qubits)
        reg = QubitRegister(qubits, label=label)
        self._registers.append(reg)
        return reg

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_qubit_owned(self, qubit: Qubit) -> None:
        """Raise CircuitError if the qubit does not belong to this circuit."""
        if qubit not in self._qubits:
            raise CircuitError(f"Qubit {qubit} is not owned by this circuit")

    def _validate_qubits_owned(self, qubits: tuple[Qubit, ...]) -> None:
        """Raise CircuitError if any qubit does not belong to this circuit."""
        for q in qubits:
            self._validate_qubit_owned(q)

    def _apply_gate(
        self,
        gate: GateDefinition,
        targets: tuple[Qubit, ...],
        params: tuple[float, ...] = (),
    ) -> Circuit:
        """Validate and append a gate instruction.

        Args:
            gate: The gate definition.
            targets: Target qubits.
            params: Gate parameters (rotation angles).

        Returns:
            self, for fluent chaining.

        Raises:
            CircuitError: If arity or ownership checks fail.
        """
        self._validate_qubits_owned(targets)
        if len(targets) > 1 and len({q.index for q in targets}) != len(targets):
            raise CircuitError(
                f"Gate {gate.name} requires distinct target qubits"
            )
        if len(targets) != gate.num_qubits:
            raise CircuitError(
                f"Gate {gate.name} expects {gate.num_qubits} qubits, got {len(targets)}"
            )
        if len(params) != gate.num_params:
            raise CircuitError(
                f"Gate {gate.name} expects {gate.num_params} params, got {len(params)}"
            )
        inst = Instruction(gate=gate, targets=targets, params=params)
        self._instructions.append(inst)
        return self

    # ------------------------------------------------------------------
    # Single-qubit gates (no params)
    # ------------------------------------------------------------------

    def h(self, target: Qubit) -> Circuit:
        """Apply Hadamard gate.

        Args:
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(H, (target,))

    def x(self, target: Qubit) -> Circuit:
        """Apply Pauli-X gate.

        Args:
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(X, (target,))

    def y(self, target: Qubit) -> Circuit:
        """Apply Pauli-Y gate.

        Args:
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(Y, (target,))

    def z(self, target: Qubit) -> Circuit:
        """Apply Pauli-Z gate.

        Args:
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(Z, (target,))

    def s(self, target: Qubit) -> Circuit:
        """Apply S gate.

        Args:
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(S, (target,))

    def t(self, target: Qubit) -> Circuit:
        """Apply T gate.

        Args:
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(T, (target,))

    # ------------------------------------------------------------------
    # Single-qubit rotation gates (one param)
    # ------------------------------------------------------------------

    def rx(self, theta: float, target: Qubit) -> Circuit:
        """Apply Rx rotation gate.

        Args:
            theta: Rotation angle in radians.
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(RX, (target,), (theta,))

    def ry(self, theta: float, target: Qubit) -> Circuit:
        """Apply Ry rotation gate.

        Args:
            theta: Rotation angle in radians.
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(RY, (target,), (theta,))

    def rz(self, theta: float, target: Qubit) -> Circuit:
        """Apply Rz rotation gate.

        Args:
            theta: Rotation angle in radians.
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(RZ, (target,), (theta,))

    def r1(self, theta: float, target: Qubit) -> Circuit:
        """Apply R1 (phase) gate.

        Args:
            theta: Phase angle in radians.
            target: The qubit to apply the gate to.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(R1, (target,), (theta,))

    # ------------------------------------------------------------------
    # Two-qubit gates
    # ------------------------------------------------------------------

    def cx(self, control: Qubit, target: Qubit) -> Circuit:
        """Apply CNOT (controlled-X) gate.

        Args:
            control: The control qubit.
            target: The target qubit.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(CNOT, (control, target))

    def cz(self, control: Qubit, target: Qubit) -> Circuit:
        """Apply CZ (controlled-Z) gate.

        Args:
            control: The control qubit.
            target: The target qubit.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(CZ, (control, target))

    def swap(self, q0: Qubit, q1: Qubit) -> Circuit:
        """Apply SWAP gate.

        Args:
            q0: First qubit.
            q1: Second qubit.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(SWAP, (q0, q1))

    # ------------------------------------------------------------------
    # Three-qubit gates
    # ------------------------------------------------------------------

    def ccx(self, c0: Qubit, c1: Qubit, target: Qubit) -> Circuit:
        """Apply Toffoli (CCNOT) gate.

        Args:
            c0: First control qubit.
            c1: Second control qubit.
            target: The target qubit.

        Returns:
            self, for fluent chaining.
        """
        return self._apply_gate(CCNOT, (c0, c1, target))

    # ------------------------------------------------------------------
    # Controlled / Adjoint modifiers
    # ------------------------------------------------------------------

    def controlled(
        self,
        gate_fn: Callable[..., Circuit],
        controls: list[Qubit],
        *args: Any,
        **kwargs: Any,
    ) -> Circuit:
        """Apply a gate with additional control qubits.

        Calls gate_fn, then patches the resulting instruction to add controls.

        Args:
            gate_fn: A bound gate method (e.g. ``circ.x``).
            controls: Qubits to use as controls.
            *args: Positional arguments forwarded to gate_fn.
            **kwargs: Keyword arguments forwarded to gate_fn.

        Returns:
            self, for fluent chaining.

        Raises:
            CircuitError: If controls are not owned by this circuit.
        """
        for ctrl in controls:
            self._validate_qubit_owned(ctrl)

        count_before = len(self._instructions)
        gate_fn(*args, **kwargs)

        if len(self._instructions) <= count_before:
            raise CircuitError(
                "controlled() requires a gate instruction, but the callable "
                "did not add one"
            )

        last = self._instructions[-1]
        if not isinstance(last, Instruction):
            self._instructions.pop()
            raise CircuitError(
                "controlled() can only wrap gate instructions, not "
                f"{type(last).__name__}"
            )

        control_indices = {q.index for q in controls}
        target_indices = {q.index for q in last.targets}
        if control_indices & target_indices:
            self._instructions.pop()
            raise CircuitError(
                "Control qubits must be distinct from target qubits"
            )

        patched = dataclasses.replace(
            last, controls=last.controls + tuple(controls)
        )
        self._instructions[-1] = patched
        return self

    def adjoint(
        self,
        gate_fn: Callable[..., Circuit],
        *args: Any,
        **kwargs: Any,
    ) -> Circuit:
        """Apply the adjoint (inverse) of a gate.

        Calls gate_fn, then patches the resulting instruction to set is_adjoint.

        Args:
            gate_fn: A bound gate method (e.g. ``circ.s``).
            *args: Positional arguments forwarded to gate_fn.
            **kwargs: Keyword arguments forwarded to gate_fn.

        Returns:
            self, for fluent chaining.
        """
        count_before = len(self._instructions)
        gate_fn(*args, **kwargs)

        if len(self._instructions) <= count_before:
            raise CircuitError(
                "adjoint() requires a gate instruction, but the callable "
                "did not add one"
            )

        last = self._instructions[-1]
        if not isinstance(last, Instruction):
            self._instructions.pop()
            raise CircuitError(
                "adjoint() can only wrap gate instructions, not "
                f"{type(last).__name__}"
            )

        patched = dataclasses.replace(last, is_adjoint=True)
        self._instructions[-1] = patched
        return self

    # ------------------------------------------------------------------
    # Measurement
    # ------------------------------------------------------------------

    def measure(self, target: Qubit, label: str | None = None) -> Circuit:
        """Measure a single qubit.

        Args:
            target: The qubit to measure.
            label: Optional label for the measurement result.

        Returns:
            self, for fluent chaining.
        """
        self._validate_qubit_owned(target)
        self._instructions.append(Measurement(target=target, label=label))
        return self

    def measure_all(self, label: str | None = None) -> Circuit:
        """Measure all allocated qubits.

        Args:
            label: Optional label prefix. Each measurement gets ``{label}_{i}``.

        Returns:
            self, for fluent chaining.
        """
        for i, q in enumerate(self._qubits):
            m_label = f"{label}_{i}" if label else None
            self._instructions.append(Measurement(target=q, label=m_label))
        return self

    # ------------------------------------------------------------------
    # Raw Q# escape hatch
    # ------------------------------------------------------------------

    def raw_qsharp(self, code: str) -> Circuit:
        """Embed a raw Q# code fragment in the circuit.

        Args:
            code: The Q# source code string.

        Returns:
            self, for fluent chaining.
        """
        self._instructions.append(RawQSharp(code=code))
        return self

    # ------------------------------------------------------------------
    # Qubit count
    # ------------------------------------------------------------------

    def qubit_count(self) -> int:
        """Return the total number of allocated qubits."""
        return len(self._qubits)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def instructions(self) -> list[InstructionLike]:
        """Return a copy of the instruction list."""
        return list(self._instructions)

    @property
    def qubits(self) -> list[Qubit]:
        """Return a copy of the qubit list."""
        return list(self._qubits)

    @property
    def registers(self) -> list[QubitRegister]:
        """Return a copy of the register list."""
        return list(self._registers)

    # ------------------------------------------------------------------
    # Stub methods (to be implemented in later phases)
    # ------------------------------------------------------------------

    def to_qsharp(self) -> str:
        """Generate Q# source code for this circuit.

        Returns:
            A Q# block expression string.
        """
        from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator

        return QSharpCodeGenerator().generate(self)

    def to_openqasm(self, version: str = "3.0") -> str:
        """Generate OpenQASM source code for this circuit.

        Args:
            version: The OpenQASM version. Only "3.0" is supported.

        Returns:
            An OpenQASM program string.

        Raises:
            CodegenError: If the requested version is not supported.
        """
        if version != "3.0":
            from qdk_pythonic.exceptions import CodegenError

            raise CodegenError(f"Unsupported OpenQASM version: {version}")
        from qdk_pythonic.codegen.openqasm import OpenQASMCodeGenerator

        return OpenQASMCodeGenerator().generate(self)

    def run(self, shots: int = 1000) -> list[Any]:
        """Execute this circuit on the qsharp simulator.

        Args:
            shots: Number of simulation shots. Defaults to 1000.

        Returns:
            A list of measurement results, one per shot.

        Raises:
            ExecutionError: If Q# compilation or simulation fails.
            ImportError: If qsharp is not installed.
        """
        from qdk_pythonic.execution.config import RunConfig
        from qdk_pythonic.execution.runner import run_circuit

        config = RunConfig(shots=shots)
        return run_circuit(self, config)

    def estimate(self, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """Run resource estimation on this circuit.

        Args:
            params: Optional estimator parameters (e.g. qubit model, QEC scheme).
            **kwargs: Reserved for future use.

        Returns:
            The resource estimation result from qsharp.estimate.

        Raises:
            ExecutionError: If Q# compilation or estimation fails.
            ImportError: If qsharp is not installed.
        """
        from qdk_pythonic.execution.estimator import estimate_circuit

        return estimate_circuit(self, params=params)

    def depth(self) -> int:
        """Calculate the circuit depth (number of time steps)."""
        from qdk_pythonic.analysis.metrics import compute_depth

        return compute_depth(self._instructions)

    def gate_count(self) -> dict[str, int]:
        """Count gates by type.

        Returns:
            A dict mapping gate name to count, sorted alphabetically.
        """
        from qdk_pythonic.analysis.metrics import compute_gate_count

        return compute_gate_count(self._instructions)

    def draw(self) -> str:
        """Draw an ASCII representation of the circuit.

        Returns:
            A multi-line ASCII string.
        """
        from qdk_pythonic.analysis.visualization import draw_circuit

        return draw_circuit(self)

    def to_dict(
        self,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Serialize this circuit to a plain dict.

        Args:
            name: Optional circuit name.
            metadata: Optional metadata dict.

        Returns:
            A dict representation of this circuit.
        """
        from qdk_pythonic.analysis.metrics import circuit_to_dict

        return circuit_to_dict(self, name=name, metadata=metadata)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Circuit:
        """Reconstruct a Circuit from a plain dict.

        Args:
            data: A dict previously produced by ``to_dict``.

        Returns:
            A reconstructed Circuit.
        """
        from qdk_pythonic.analysis.metrics import circuit_from_dict

        return circuit_from_dict(data)

    def to_json(
        self,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        indent: int = 2,
    ) -> str:
        """Serialize this circuit to a JSON string.

        Args:
            name: Optional circuit name.
            metadata: Optional metadata dict.
            indent: JSON indentation level.

        Returns:
            A JSON string representation of this circuit.
        """
        from qdk_pythonic.analysis.metrics import circuit_to_json

        return circuit_to_json(
            self, name=name, metadata=metadata, indent=indent,
        )

    @classmethod
    def from_json(cls, json_str: str) -> Circuit:
        """Reconstruct a Circuit from a JSON string.

        Args:
            json_str: A JSON string previously produced by ``to_json``.

        Returns:
            A reconstructed Circuit.
        """
        from qdk_pythonic.analysis.metrics import circuit_from_json

        return circuit_from_json(json_str)

    @classmethod
    def from_qsharp(cls, source: str) -> Circuit:
        """Parse a Q# source string into a Circuit.

        Args:
            source: Q# source code.

        Returns:
            A Circuit built from the parsed Q# source.
        """
        from qdk_pythonic.parser.qsharp_parser import QSharpParser

        return QSharpParser().parse(source)

    @classmethod
    def from_openqasm(cls, source: str) -> Circuit:
        """Parse an OpenQASM 3.0 source string into a Circuit.

        Args:
            source: OpenQASM source code.

        Returns:
            A Circuit built from the parsed OpenQASM source.
        """
        from qdk_pythonic.parser.openqasm_parser import OpenQASMParser

        return OpenQASMParser().parse(source)
