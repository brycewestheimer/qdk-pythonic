Writing a Code Generator Backend
=================================

This guide explains how to add a new code generation target (e.g., Cirq
Python, QASM 2.0, or any other circuit format).

The CodeGenerator Protocol
--------------------------

A code generator implements the
:class:`~qdk_pythonic.codegen.base.CodeGenerator` protocol defined in
``src/qdk_pythonic/codegen/base.py``:

.. code-block:: python

   class CodeGenerator(Protocol):
       def generate(self, circuit: Circuit) -> str: ...
       def generate_operation(self, name: str, circuit: Circuit) -> str: ...

- ``generate()`` produces a standalone code snippet (block expression,
  program, etc.).
- ``generate_operation()`` produces a named callable (operation, function,
  etc.) that can be invoked by the runtime.

No inheritance is needed. Any class with these two methods satisfies the
protocol.

Implementation Pattern
----------------------

Here is the typical structure:

.. code-block:: python

   from qdk_pythonic.codegen._helpers import build_qubit_map
   from qdk_pythonic.core.instruction import Instruction, Measurement, RawQSharp
   from qdk_pythonic.core.parameter import Parameter
   from qdk_pythonic.exceptions import CodegenError


   class MyFormatCodeGenerator:
       def generate(self, circuit):
           registers = circuit.registers
           if not registers:
               return ""

           qubit_map = build_qubit_map(registers)
           lines = []

           for inst in circuit.instructions:
               if isinstance(inst, Instruction):
                   lines.append(self._serialize_instruction(inst, qubit_map))
               elif isinstance(inst, Measurement):
                   lines.append(self._serialize_measurement(inst, qubit_map))
               elif isinstance(inst, RawQSharp):
                   raise CodegenError(
                       "Raw Q# fragments are not supported by this backend"
                   )

           return "\n".join(lines)

       def generate_operation(self, name, circuit):
           body = self.generate(circuit)
           return f"def {name}():\n    {body}"

       def _serialize_instruction(self, inst, qubit_map):
           # Check for unbound parameters
           for p in inst.params:
               if isinstance(p, Parameter):
                   raise CodegenError(
                       f"Unbound parameter '{p.name}'; "
                       f"call bind_parameters() first"
                   )

           # Access gate metadata
           gate_name = inst.gate.name        # canonical name
           targets = inst.targets             # tuple of Qubit
           params = inst.params               # tuple of float | Parameter
           controls = inst.controls           # tuple of Qubit
           is_adjoint = inst.is_adjoint       # bool

           # Map qubits to reference strings
           target_refs = [qubit_map[q.index] for q in targets]
           # ... build the output string ...

The ``build_qubit_map`` Helper
------------------------------

The :func:`~qdk_pythonic.codegen._helpers.build_qubit_map` function
(from ``codegen/_helpers.py``) maps qubit indices to reference strings
like ``"q[0]"``, ``"q[1]"``, etc., based on register labels and sizes.
Reuse this unless your format requires a different referencing scheme.

Error Handling
--------------

Raise :class:`~qdk_pythonic.exceptions.CodegenError` for:

- Unbound ``Parameter`` instances (check ``isinstance(p, Parameter)``
  in the params tuple)
- Qubits not found in the qubit map (use ``try/except KeyError``)
- Unsupported constructs (e.g., ``RawQSharp`` if your format has no
  equivalent)

Registration
------------

1. Add the module to ``src/qdk_pythonic/codegen/``.
2. Export from ``src/qdk_pythonic/codegen/__init__.py``.
3. Optionally, add a ``Circuit.to_<format>()`` convenience method in
   ``circuit.py`` that imports and calls the generator (following the
   pattern of ``to_qsharp()`` and ``to_openqasm()``).

Testing
-------

Add ``tests/unit/test_codegen_<name>.py`` mirroring the structure of
``test_codegen_qsharp.py`` or ``test_codegen_openqasm.py``. Cover:

- Empty circuit
- Single-qubit gates
- Rotation gates with parameters
- Multi-qubit gates
- Controlled and adjoint modifiers
- Measurements
- Error cases (unbound parameters, unsupported constructs)
