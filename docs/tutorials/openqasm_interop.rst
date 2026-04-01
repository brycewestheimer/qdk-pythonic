OpenQASM Interoperability
=========================

qdk-pythonic supports bidirectional conversion between its Pythonic circuit
representation and OpenQASM 3.0 source strings. This enables interoperability
with other quantum frameworks that support OpenQASM.

Exporting to OpenQASM
----------------------

Generate an OpenQASM 3.0 program from a circuit:

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0]).cx(q[0], q[1]).measure_all()

   qasm = circ.to_openqasm()
   print(qasm)

This produces:

.. code-block:: text

   OPENQASM 3.0;
   include "stdgates.inc";

   qubit[2] q;

   h q[0];
   cx q[0], q[1];

   bit[2] c;
   c[0] = measure q[0];
   c[1] = measure q[1];

Importing from OpenQASM
------------------------

Parse an OpenQASM 3.0 string back into a circuit:

.. code-block:: python

   qasm_source = '''
   OPENQASM 3.0;
   include "stdgates.inc";

   qubit[3] q;

   h q[0];
   cx q[0], q[1];
   cx q[1], q[2];
   '''

   circ = Circuit.from_openqasm(qasm_source)
   print(circ.gate_count())   # {'CNOT': 2, 'H': 1}
   print(circ.qubit_count())  # 3

Round-Trip Conversion
----------------------

Convert between OpenQASM and Q#:

.. code-block:: python

   # Start with OpenQASM
   circ = Circuit.from_openqasm(qasm_source)

   # View as Q#
   print(circ.to_qsharp())

   # Export back to OpenQASM
   print(circ.to_openqasm())

The round-trip preserves the circuit structure (gates, qubits, measurements)
but may not preserve formatting or comments from the original source.

Supported Constructs
---------------------

The OpenQASM parser handles the following constructs:

- **Header**: ``OPENQASM 3.0;`` and ``include "stdgates.inc";``
- **Qubit declarations**: ``qubit[n] name;``
- **Standard gates**: h, x, y, z, s, t, cx, cz, swap, ccx
- **Rotation gates**: rx, ry, rz, p (mapped to R1)
- **Modifiers**: ``ctrl @`` (controlled), ``inv @`` (adjoint)
- **Measurements**: ``measure`` and ``bit`` declarations

Unsupported constructs (custom gate definitions, loops, conditionals) raise
:class:`~qdk_pythonic.exceptions.UnsupportedConstructError`.

Converting from Q#
-------------------

Similarly, Q# source strings can be imported:

.. code-block:: python

   qsharp_source = '''
   {
       use q = Qubit[2];
       H(q[0]);
       CNOT(q[0], q[1]);
       let r0 = MResetZ(q[0]);
       let r1 = MResetZ(q[1]);
       [r0, r1]
   }
   '''

   circ = Circuit.from_qsharp(qsharp_source)
   print(circ.draw())
