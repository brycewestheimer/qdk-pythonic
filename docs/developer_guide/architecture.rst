Architecture
============

This page describes the internal code organization and key design
decisions for contributors.

Source Layout
-------------

::

    src/qdk_pythonic/
        __init__.py          # Public API re-exports
        _version.py          # Version string
        builders.py          # Factory functions (bell_state, qft, etc.)
        exceptions.py        # Exception hierarchy
        py.typed             # PEP 561 marker
        core/                # Data model
            circuit.py       # Circuit builder class
            gates.py         # GateDefinition instances + GATE_CATALOG
            instruction.py   # Instruction, Measurement, RawQSharp
            parameter.py     # Parameter dataclass
            protocols.py     # CircuitProducer protocol
            qubit.py         # Qubit, QubitRegister
            result.py        # MeasurementResult
        codegen/             # Code generation backends
            base.py          # CodeGenerator protocol
            _helpers.py      # build_qubit_map()
            qsharp.py        # QSharpCodeGenerator
            openqasm.py      # OpenQASMCodeGenerator
        parser/              # Parsing backends
            base.py          # Parser protocol
            _expr_eval.py    # Expression evaluator for parsed parameters
            qsharp_parser.py # QSharpParser
            openqasm_parser.py # OpenQASMParser
        execution/           # Runtime wrappers
            _compat.py       # Lazy qsharp import helper
            config.py        # RunConfig dataclass
            runner.py        # run_circuit()
            estimator.py     # estimate_circuit(), estimate_circuit_batch()
        analysis/            # Metrics and visualization
            _helpers.py      # involved_indices()
            metrics.py       # Depth, gate count, serialization
            visualization.py # ASCII diagram renderer
        domains/             # Application domain modules
            common/          # PauliHamiltonian, TrotterEvolution, ansatz, states
            condensed_matter/ # Lattice models and dynamics simulation
            optimization/    # MaxCut, QUBO, TSP, QAOA
            finance/         # Amplitude estimation and option pricing
            ml/              # Feature encoding, kernels, classifiers

Design Decisions
----------------

**Frozen dataclasses for IR types.** ``Qubit``, ``Instruction``,
``Measurement``, ``RawQSharp``, ``GateDefinition``, and ``Parameter`` are
all ``@dataclass(frozen=True)``. This ensures the instruction list is
append-only and instructions cannot be mutated after creation.

**Mutable Circuit.** The ``Circuit`` class is the one mutable type in the
core. Gate methods modify ``self._instructions`` in place and return
``self`` for fluent chaining. This is a deliberate trade-off: ergonomic
builder API over pure immutability.

**PEP 544 protocols.** ``CodeGenerator``, ``Parser``, and
``CircuitProducer`` are structural typing protocols, not abstract base
classes. This means implementors do not need to inherit from them; any
class with matching method signatures satisfies the protocol. This keeps
the coupling loose and avoids import-time dependencies between packages.

**Lazy imports for optional dependencies.** The ``qsharp`` package is
optional. It is never imported at module level. Instead, ``execution/``
modules use ``_compat.import_qsharp()`` which raises a clear
``ImportError`` when the package is missing. Similarly, ``Circuit``
methods like ``to_qsharp()`` and ``run()`` import the relevant modules
inside the method body.

Data Flow Trace
---------------

Here is what happens when you call ``circ.run(shots=100)``:

1. ``Circuit.run()`` creates a ``RunConfig(shots=100)`` and calls
   ``run_circuit(self, config)``.
2. ``run_circuit()`` calls ``import_qsharp()`` to get the ``qsharp``
   module.
3. A ``QSharpCodeGenerator`` generates a named Q# operation via
   ``generate_operation(op_name, circuit)``.
4. ``generate_operation()`` calls ``build_qubit_map(registers)`` to map
   qubit indices to reference strings (e.g., ``q[0]``), then
   ``_build_body()`` to serialize each instruction.
5. The generated Q# string is compiled with ``qsharp.eval(qsharp_code)``.
6. The operation is executed with ``qsharp.run(f"{op_name}()", shots=100)``.
7. Results are returned as a list.

For resource estimation, the flow is similar but measurements and raw
Q# fragments are stripped (via ``circuit.without_measurements_and_raw()``)
before code generation, and ``qsharp.estimate()`` is called instead of
``qsharp.run()``.
