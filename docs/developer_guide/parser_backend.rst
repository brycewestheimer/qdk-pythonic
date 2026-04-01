Writing a Parser Backend
========================

This guide explains how to add a new source language parser (e.g., for
QASM 2.0 or another circuit format).

The Parser Protocol
-------------------

A parser implements the :class:`~qdk_pythonic.parser.base.Parser`
protocol defined in ``src/qdk_pythonic/parser/base.py``:

.. code-block:: python

   class Parser(Protocol):
       def parse(self, source: str) -> Circuit: ...

Any class with a ``parse(source: str) -> Circuit`` method satisfies the
protocol.

Implementation Pattern
----------------------

The general approach is:

1. Tokenize or parse the source string.
2. Create a ``Circuit`` instance.
3. Call ``circuit.allocate()`` for each qubit declaration.
4. Build ``Instruction`` and ``Measurement`` dataclasses and add them
   via ``circuit.add_instruction()``.

.. code-block:: python

   from qdk_pythonic.core.circuit import Circuit
   from qdk_pythonic.core.gates import GATE_CATALOG
   from qdk_pythonic.core.instruction import Instruction, Measurement
   from qdk_pythonic.core.qubit import Qubit
   from qdk_pythonic.exceptions import ParserError, UnsupportedConstructError


   class MyFormatParser:
       def parse(self, source: str) -> Circuit:
           circ = Circuit()
           tokens = self._tokenize(source)

           for token in tokens:
               if token.type == "qubit_decl":
                   circ.allocate(token.size, label=token.label)
               elif token.type == "gate":
                   self._add_gate(circ, token)
               elif token.type == "measure":
                   self._add_measurement(circ, token)
               else:
                   raise UnsupportedConstructError(
                       f"Unsupported construct: {token.type}"
                   )

           return circ

       def _add_gate(self, circ: Circuit, token) -> None:
           gate_name = token.gate_name
           if gate_name not in GATE_CATALOG:
               raise UnsupportedConstructError(
                   f"Unknown gate: {gate_name}"
               )
           gate = GATE_CATALOG[gate_name]
           qubit_by_index = {q.index: q for q in circ.qubits}
           targets = tuple(qubit_by_index[i] for i in token.targets)
           params = tuple(float(p) for p in token.params)
           inst = Instruction(gate=gate, targets=targets, params=params)
           circ.add_instruction(inst)

Key Points
----------

**Use ``GATE_CATALOG``** to look up ``GateDefinition`` instances by
canonical name. This ensures consistency with the rest of the system.

**Use ``add_instruction()``** rather than calling gate methods like
``h()`` or ``cx()``. The low-level ``add_instruction()`` method skips
qubit ownership validation, which is appropriate for parsers that
construct the circuit and its qubits together.

**Expression evaluation.** The existing ``parser/_expr_eval.py`` module
provides helpers for evaluating parameter expressions. Study it as a
reference for handling expressions in your parser.

Error Handling
--------------

- Raise :class:`~qdk_pythonic.exceptions.ParserError` for syntax errors
  (malformed source, unexpected tokens).
- Raise :class:`~qdk_pythonic.exceptions.UnsupportedConstructError` for
  constructs the parser recognizes but cannot convert (custom gates,
  loops, conditionals, etc.).

Registration
------------

1. Add the module to ``src/qdk_pythonic/parser/``.
2. Export from ``src/qdk_pythonic/parser/__init__.py``.
3. Optionally, add a ``Circuit.from_<format>(source)`` classmethod in
   ``circuit.py`` following the pattern of ``from_qsharp()`` and
   ``from_openqasm()``.

Testing
-------

Add ``tests/unit/test_parser_<name>.py``. Cover:

- Valid source with standard gates
- Rotation gates with numeric parameters
- Controlled and adjoint modifiers
- Measurements
- Syntax errors (expect ``ParserError``)
- Unsupported constructs (expect ``UnsupportedConstructError``)
- Round-trip: parse source, generate code with the matching code
  generator, verify circuit metrics match.
