Parsing and Interoperability
============================

qdk-pythonic can parse Q# and OpenQASM 3.0 source code into
:class:`~qdk_pythonic.core.circuit.Circuit` objects. This enables
round-tripping and cross-framework workflows.

Parsing Q#
----------

Parse Q# source code with
:meth:`~qdk_pythonic.core.circuit.Circuit.from_qsharp`:

.. code-block:: python

   from qdk_pythonic import Circuit

   qsharp_source = """
   {
       use q = Qubit[2];
       H(q[0]);
       CNOT(q[0], q[1]);
       let r0 = MResetZ(q[0]);
       let r1 = MResetZ(q[1]);
       [r0, r1]
   }
   """

   circ = Circuit.from_qsharp(qsharp_source)
   print(circ.gate_count())   # {'CNOT': 1, 'H': 1}
   print(circ.qubit_count())  # 2

**Supported constructs:**

- ``use`` statements (single and array allocation)
- Standard gates (H, X, Y, Z, S, T, Rx, Ry, Rz, R1, CNOT, CZ, SWAP, CCNOT)
- ``Controlled`` and ``Adjoint`` prefixes
- ``MResetZ`` measurements
- Numeric parameter expressions

**Unsupported constructs** raise ``UnsupportedConstructError``:

- Custom gate/operation definitions
- Classical control flow (if, for, while)
- Repeat-until-success loops
- Library function calls

Parsing OpenQASM
----------------

Parse OpenQASM 3.0 source code with
:meth:`~qdk_pythonic.core.circuit.Circuit.from_openqasm`:

.. code-block:: python

   qasm_source = """
   OPENQASM 3.0;
   include "stdgates.inc";

   qubit[2] q;

   h q[0];
   cx q[0], q[1];

   bit[2] c;
   c[0] = measure q[0];
   c[1] = measure q[1];
   """

   circ = Circuit.from_openqasm(qasm_source)
   print(circ.draw())

**Supported constructs:**

- ``OPENQASM 3.0;`` header
- ``qubit[n]`` declarations
- Standard gates (h, x, y, z, s, t, rx, ry, rz, p, cx, cz, swap, ccx)
- ``ctrl @`` and ``inv @`` modifiers
- ``measure`` statements

**Unsupported constructs** raise ``UnsupportedConstructError``:

- Custom gate definitions (``gate ... { }``)
- Classical variables and conditionals
- Loops
- Subroutines

Round-Trip Fidelity
-------------------

You can generate code from a circuit and parse it back:

.. code-block:: python

   original = Circuit()
   q = original.allocate(2)
   original.h(q[0]).cx(q[0], q[1]).measure_all()

   # Q# round-trip
   qsharp = original.to_qsharp()
   restored = Circuit.from_qsharp(qsharp)
   print(restored.gate_count() == original.gate_count())  # True

   # OpenQASM round-trip
   qasm = original.to_openqasm()
   restored = Circuit.from_openqasm(qasm)
   print(restored.gate_count() == original.gate_count())  # True

The circuit structure (gates, qubits, measurements) is preserved.
Formatting, comments, and variable names are not preserved.

Cross-Format Workflows
----------------------

Parse from one format and export to another:

.. code-block:: python

   # Q# to OpenQASM
   circ = Circuit.from_qsharp(qsharp_source)
   print(circ.to_openqasm())

   # OpenQASM to Q#
   circ = Circuit.from_openqasm(qasm_source)
   print(circ.to_qsharp())

This can serve as a bridge between tools that use different formats.
Note that circuits containing ``raw_qsharp()`` fragments cannot be
exported to OpenQASM.

Error Handling
--------------

- ``ParserError``: raised for syntax errors in the source code.
- ``UnsupportedConstructError``: raised for constructs the parser
  recognizes but cannot convert to the circuit IR.

.. code-block:: python

   from qdk_pythonic.exceptions import ParserError, UnsupportedConstructError

   try:
       circ = Circuit.from_qsharp("invalid source")
   except ParserError as e:
       print(f"Syntax error: {e}")

   try:
       circ = Circuit.from_qsharp("{ for i in 0..3 { H(q[i]); } }")
   except UnsupportedConstructError as e:
       print(f"Unsupported: {e}")
