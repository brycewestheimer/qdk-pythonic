Architecture Overview
=====================

qdk-pythonic is a circuit-builder library that generates Q# and OpenQASM
source strings from a Python-level intermediate representation, then feeds
those strings to the ``qsharp`` runtime for simulation and resource
estimation.

Data Flow
---------

The path from Python to execution looks like this::

    Circuit (Python)
        |
        v
    [Instruction, Measurement, RawQSharp, ...]   (in-memory IR)
        |
        v
    CodeGenerator.generate()
        |
        v
    Q# source string    or    OpenQASM 3.0 source string
        |
        v
    qsharp.eval() / qsharp.run() / qsharp.estimate()

You build a circuit in Python using the :class:`~qdk_pythonic.core.circuit.Circuit`
class. Each gate method appends a frozen :class:`~qdk_pythonic.core.instruction.Instruction`
dataclass to an internal list. When you call ``to_qsharp()`` or ``to_openqasm()``,
a :class:`~qdk_pythonic.codegen.base.CodeGenerator` walks the instruction list
and produces a source string. For execution, that string is compiled and run
by the ``qsharp`` package.

Core Types
----------

**Circuit**
    The mutable builder class and primary entry point. Gate methods
    (``h()``, ``cx()``, etc.) return ``self`` for fluent chaining.
    See :doc:`circuits` for full details.

**Qubit / QubitRegister**
    Frozen handles returned by :meth:`~qdk_pythonic.core.circuit.Circuit.allocate`.
    ``Qubit`` is a dataclass with an ``index`` and ``label``.
    ``QubitRegister`` supports integer indexing, slicing, iteration, and
    ``len()``.

**Instruction / Measurement / RawQSharp**
    The three IR element types, all frozen dataclasses:

    - ``Instruction`` binds a ``GateDefinition`` to target qubits, parameters,
      optional control qubits, and an ``is_adjoint`` flag.
    - ``Measurement`` records a qubit target and optional label.
    - ``RawQSharp`` holds a verbatim Q# code fragment.

    The union type ``InstructionLike = Instruction | Measurement | RawQSharp``
    represents any element in the instruction list.

**GateDefinition**
    A frozen dataclass holding metadata for a gate type: canonical name,
    number of qubits, number of parameters, Q# name, and OpenQASM name.
    All built-in gates are defined in :mod:`qdk_pythonic.core.gates` and
    collected in the ``GATE_CATALOG`` dict.

**Parameter**
    A frozen dataclass with a single ``name`` field. Use ``Parameter``
    instances as rotation angles to build parameterized circuit templates.
    See :doc:`parameters`.

Protocols
---------

qdk-pythonic uses `PEP 544 <https://peps.python.org/pep-0544/>`_ structural
typing protocols instead of abstract base classes:

**CodeGenerator**
    Two methods: ``generate(circuit) -> str`` and
    ``generate_operation(name, circuit) -> str``. Implemented by
    ``QSharpCodeGenerator`` and ``OpenQASMCodeGenerator``.

**Parser**
    One method: ``parse(source) -> Circuit``. Implemented by
    ``QSharpParser`` and ``OpenQASMParser``.

**CircuitProducer**
    One method: ``to_circuit() -> Circuit``. Satisfied by domain objects
    that produce circuits (lattice models, QAOA instances, etc.).

Because these are protocols, you do not need to inherit from them. Any
class with matching method signatures satisfies the protocol automatically.

Why Code Generation?
--------------------

qdk-pythonic generates Q# strings rather than calling the QDK runtime via
Rust FFI. This means:

- **Full compatibility** with the ``qsharp`` compiler and resource estimator
  without modifications to QDK.
- **The Pythonic API can only express circuits with valid Q# serialization.**
  Constructs that have no Q# equivalent cannot be represented (use
  ``raw_qsharp()`` for those).
- **Debugging is transparent**: call ``to_qsharp()`` to see exactly what
  will be compiled and executed.
