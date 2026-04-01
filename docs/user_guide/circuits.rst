Circuit Building
================

The :class:`~qdk_pythonic.core.circuit.Circuit` class is the primary
interface for constructing quantum circuits.

Qubit Allocation
----------------

Allocate qubits with :meth:`~qdk_pythonic.core.circuit.Circuit.allocate`:

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(3)           # 3 qubits, auto-label "q"
   anc = circ.allocate(1, "anc")  # 1 qubit, label "anc"

Each call returns a :class:`~qdk_pythonic.core.qubit.QubitRegister` that
supports indexing (``q[0]``), slicing (``q[1:]``), iteration, and ``len()``.

Labels must start with a letter or underscore and contain only letters,
digits, and underscores. Duplicate labels raise ``CircuitError``. When no
label is given, the first register gets ``"q"``, subsequent ones get
``"q0"``, ``"q1"``, and so on.

Access all qubits and registers via ``circuit.qubits`` and
``circuit.registers``.

Fluent Chaining
---------------

Every gate method returns ``self``, so calls can be chained:

.. code-block:: python

   circ.h(q[0]).cx(q[0], q[1]).rz(0.5, q[1]).measure_all()

This is equivalent to calling each method on a separate line.

Gate Catalog
------------

.. list-table::
   :header-rows: 1
   :widths: 15 15 10 15 15

   * - Method
     - Gate
     - Qubits
     - Q# name
     - OpenQASM name
   * - ``h(target)``
     - Hadamard
     - 1
     - ``H``
     - ``h``
   * - ``x(target)``
     - Pauli-X
     - 1
     - ``X``
     - ``x``
   * - ``y(target)``
     - Pauli-Y
     - 1
     - ``Y``
     - ``y``
   * - ``z(target)``
     - Pauli-Z
     - 1
     - ``Z``
     - ``z``
   * - ``s(target)``
     - S (phase)
     - 1
     - ``S``
     - ``s``
   * - ``t(target)``
     - T (pi/8)
     - 1
     - ``T``
     - ``t``
   * - ``rx(theta, target)``
     - Rx rotation
     - 1
     - ``Rx``
     - ``rx``
   * - ``ry(theta, target)``
     - Ry rotation
     - 1
     - ``Ry``
     - ``ry``
   * - ``rz(theta, target)``
     - Rz rotation
     - 1
     - ``Rz``
     - ``rz``
   * - ``r1(theta, target)``
     - R1 (phase)
     - 1
     - ``R1``
     - ``p``
   * - ``cx(control, target)``
     - CNOT
     - 2
     - ``CNOT``
     - ``cx``
   * - ``cz(control, target)``
     - CZ
     - 2
     - ``CZ``
     - ``cz``
   * - ``swap(q0, q1)``
     - SWAP
     - 2
     - ``SWAP``
     - ``swap``
   * - ``ccx(c0, c1, target)``
     - Toffoli
     - 3
     - ``CCNOT``
     - ``ccx``

Rotation gates (``rx``, ``ry``, ``rz``, ``r1``) take a ``theta`` parameter
in radians. The parameter can be a ``float`` or a symbolic
:class:`~qdk_pythonic.core.parameter.Parameter` (see :doc:`parameters`).

Controlled and Adjoint Modifiers
--------------------------------

Add control qubits to any gate with
:meth:`~qdk_pythonic.core.circuit.Circuit.controlled`:

.. code-block:: python

   # Controlled-H: apply H to q[1] controlled on q[0]
   circ.controlled(circ.h, [q[0]], q[1])

   # Controlled rotation with parameter
   circ.controlled(circ.r1, [q[2]], 0.5, q[0])

Apply the adjoint (inverse) of a gate with
:meth:`~qdk_pythonic.core.circuit.Circuit.adjoint`:

.. code-block:: python

   # Adjoint S gate
   circ.adjoint(circ.s, q[0])

Both modifiers accept a bound gate method as the first argument, followed
by the method's normal arguments. The callable must add exactly one gate
instruction; otherwise ``CircuitError`` is raised.

These can be chained fluently:

.. code-block:: python

   circ.h(q[0]).controlled(circ.x, [q[0]], q[1]).adjoint(circ.t, q[0])

Measurement
-----------

Measure a single qubit or all qubits:

.. code-block:: python

   circ.measure(q[0])                # measure one qubit
   circ.measure(q[0], label="result") # with a label
   circ.measure_all()                # measure all allocated qubits
   circ.measure_all(label="out")     # labels become "out_0", "out_1", ...

Measurements appear in the generated code at the point where they are added
to the circuit. In Q#, each measurement generates a ``let rN = MResetZ(...)``
statement. In OpenQASM, measurements are collected into a ``bit[n] c;``
register.

Circuit Composition
-------------------

Concatenate two circuits with the ``+`` operator:

.. code-block:: python

   a = Circuit()
   qa = a.allocate(2)
   a.h(qa[0]).cx(qa[0], qa[1])

   b = Circuit()
   qb = b.allocate(2)
   b.x(qb[0]).cz(qb[0], qb[1])

   combined = a + b  # 4 qubits, a's gates then b's gates

Qubits from both operands are remapped to fresh allocations in the
result. Note that circuits containing ``raw_qsharp()`` fragments cannot
be composed (raises ``CircuitError``).

Builder Functions
-----------------

For common circuits, use the built-in builder functions:

.. code-block:: python

   from qdk_pythonic import bell_state, ghz_state, w_state, qft, inverse_qft

   bell = bell_state(measure=True)      # 2-qubit Bell state
   ghz = ghz_state(5)                   # 5-qubit GHZ state
   w = w_state(4, measure=True)         # 4-qubit W state
   ft = qft(3)                          # 3-qubit QFT
   ift = inverse_qft(3)                 # 3-qubit inverse QFT

For benchmarking, generate random circuits:

.. code-block:: python

   from qdk_pythonic import random_circuit

   circ = random_circuit(n_qubits=5, depth=10, seed=42)

All builders return plain ``Circuit`` objects that can be extended with
additional gates. See :doc:`/api/builders` for signatures and details.

Raw Q# Escape Hatch
--------------------

Embed arbitrary Q# fragments for constructs the gate-level API cannot
express (repeat-until-success loops, classical control flow, Q# library
calls):

.. code-block:: python

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0])
   circ.raw_qsharp("let r = M(q[0]);")
   circ.raw_qsharp("if r == One { X(q[1]); }")

Things to keep in mind:

- ``raw_qsharp()`` fragments are Q#-only. Calling ``to_openqasm()`` on
  a circuit with raw fragments raises ``CodegenError``.
- Analysis methods (``depth()``, ``gate_count()``, ``draw()``) skip raw
  fragments because their cost cannot be determined statically.
- The Q# code is not validated at build time; syntax errors will surface
  when the ``qsharp`` runtime compiles the generated code.

Best Practices
--------------

- **Allocate all qubits before applying gates** for cleaner generated code.
- **Use labels** for circuits with multiple registers to make the generated
  Q# and OpenQASM more readable.
- **Keep circuits small for visualization**: ``draw()`` truncates at 10
  qubits and 30 gates.
- **Use builder functions** for standard circuits rather than constructing
  them manually.
