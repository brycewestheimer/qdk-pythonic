Code Generation
===============

qdk-pythonic can generate Q# and OpenQASM 3.0 source code from a circuit.
This page covers the details and differences between the two backends.

Q# Code Generation
-------------------

Call :meth:`~qdk_pythonic.core.circuit.Circuit.to_qsharp` to produce a Q#
block expression:

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0]).cx(q[0], q[1]).measure_all()

   print(circ.to_qsharp())

Output::

    {
        use q = Qubit[2];
        H(q[0]);
        CNOT(q[0], q[1]);
        let r0 = MResetZ(q[0]);
        let r1 = MResetZ(q[1]);
        [r0, r1]
    }

**Structure:**

- Each register produces a ``use label = Qubit[n];`` statement.
- Gates use Q# names: ``H``, ``CNOT``, ``Rx``, etc.
- Measurements use ``MResetZ()`` and bind results to ``r0``, ``r1``, etc.
- The return expression is inferred from measurements:
  no measurements returns nothing (``Unit``), one measurement returns the
  variable directly (``Result``), multiple measurements return an array
  (``Result[]``).

**Modifiers:**

- Controlled gates: ``Controlled H([q[0]], q[1]);``
- Adjoint gates: ``Adjoint S(q[0]);``
- Combined: ``Controlled Adjoint R1([q[0]], (0.5, q[1]));``

**Raw fragments** from ``raw_qsharp()`` are inserted verbatim.

**Named operations** are generated internally for ``run()`` and
``estimate()``, using ``QSharpCodeGenerator.generate_operation()``.

OpenQASM 3.0 Code Generation
-----------------------------

Call :meth:`~qdk_pythonic.core.circuit.Circuit.to_openqasm` to produce an
OpenQASM 3.0 program:

.. code-block:: python

   print(circ.to_openqasm())

Output::

    OPENQASM 3.0;
    include "stdgates.inc";

    qubit[2] q;

    h q[0];
    cx q[0], q[1];

    bit[2] c;
    c[0] = measure q[0];
    c[1] = measure q[1];

**Structure:**

- Starts with ``OPENQASM 3.0;`` header and ``include "stdgates.inc";``.
- Qubit declarations: ``qubit[n] label;``
- Gates use OpenQASM names: ``h``, ``cx``, ``rx``, etc.
- Measurements are collected into a classical bit register ``c``.

**Modifiers:**

- Controlled gates: ``ctrl @ h q[0], q[1];``
- Adjoint gates: ``inv @ s q[0];``
- Combined: ``ctrl @ inv @ p(0.5) q[0], q[1];``

**Limitations:**

- ``raw_qsharp()`` fragments cannot be exported to OpenQASM. Calling
  ``to_openqasm()`` on a circuit with raw fragments raises ``CodegenError``.
- Only version ``"3.0"`` is supported. Passing a different version string
  raises ``CodegenError``.

Differences Between Backends
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 20

   * - Feature
     - Q#
     - OpenQASM 3.0
   * - Gate names
     - ``H``, ``CNOT``, ``R1``
     - ``h``, ``cx``, ``p``
   * - Controlled
     - ``Controlled H([c], t)``
     - ``ctrl @ h c, t;``
   * - Adjoint
     - ``Adjoint S(q)``
     - ``inv @ s q;``
   * - Measurements
     - ``let r0 = MResetZ(q[0]);``
     - ``c[0] = measure q[0];``
   * - Return type
     - ``Unit``, ``Result``, ``Result[]``
     - N/A (classical register)
   * - Raw Q# fragments
     - Supported
     - Not supported
   * - Named operations
     - ``generate_operation()``
     - Same as ``generate()``

Unbound Parameters
------------------

Both backends raise ``CodegenError`` if the circuit contains unbound
:class:`~qdk_pythonic.core.parameter.Parameter` instances. Call
``bind_parameters()`` before code generation:

.. code-block:: python

   from qdk_pythonic.core.parameter import Parameter

   theta = Parameter("theta")
   circ = Circuit()
   q = circ.allocate(1)
   circ.ry(theta, q[0])

   # This raises CodegenError:
   # circ.to_qsharp()

   # Bind first:
   bound = circ.bind_parameters({"theta": 0.5})
   print(bound.to_qsharp())
