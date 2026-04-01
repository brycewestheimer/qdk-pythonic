Adding New Gates
================

This guide walks through adding a new gate to qdk-pythonic. The process
involves five files and is designed so that the code generators
automatically handle new gates without modification.

Step 1: Define the Gate
-----------------------

Add a ``GateDefinition`` to ``src/qdk_pythonic/core/gates.py``:

.. code-block:: python

   SX = GateDefinition(
       name="SX",
       num_qubits=1,
       num_params=0,
       qsharp_name="SX",
       openqasm_name="sx",
   )

Fields:

- ``name``: canonical name used in gate counts, serialization, and display.
- ``num_qubits``: number of qubit operands.
- ``num_params``: number of floating-point parameters (0 for fixed gates).
- ``qsharp_name``: the gate name emitted in Q# code.
- ``openqasm_name``: the gate name emitted in OpenQASM code.

Add it to the ``GATE_CATALOG`` dict in the same file:

.. code-block:: python

   GATE_CATALOG: dict[str, GateDefinition] = {
       # ... existing entries ...
       "SX": SX,
   }

Step 2: Export from core
------------------------

Add the new constant to ``src/qdk_pythonic/core/__init__.py`` if it needs
to be importable from ``qdk_pythonic.core``.

Step 3: Add a Circuit Method
-----------------------------

Add a convenience method to ``src/qdk_pythonic/core/circuit.py``.
Follow the pattern of existing gates:

.. code-block:: python

   def sx(self, target: Qubit) -> Circuit:
       """Apply SX (sqrt-X) gate.

       Args:
           target: The qubit to apply the gate to.

       Returns:
           self, for fluent chaining.
       """
       return self._apply_gate(SX, (target,))

Import the new constant at the top of the file alongside the other gate
imports.

For rotation gates with parameters, the method signature includes the
parameter:

.. code-block:: python

   def rxx(self, theta: float | Parameter, q0: Qubit, q1: Qubit) -> Circuit:
       """Apply RXX rotation gate.

       Args:
           theta: Rotation angle in radians, or a symbolic Parameter.
           q0: First qubit.
           q1: Second qubit.

       Returns:
           self, for fluent chaining.
       """
       return self._apply_gate(RXX, (q0, q1), (theta,))

Step 4: Verify Code Generation
-------------------------------

The Q# and OpenQASM code generators use ``inst.gate.qsharp_name`` and
``inst.gate.openqasm_name`` respectively, so no changes to the code
generators are needed for standard gates. The ``_serialize_instruction``
methods handle parameters, controls, and adjoint flags generically.

If the gate requires special serialization (unusual syntax in Q# or
OpenQASM), you would need to add a case in the generator's
``_serialize_instruction`` method.

Step 5: Add Tests
-----------------

Add tests in the following files:

**``tests/unit/test_circuit.py``** -- verify the method appends the
correct instruction:

.. code-block:: python

   @pytest.mark.unit
   def test_sx_gate():
       circ = Circuit()
       q = circ.allocate(1)
       circ.sx(q[0])
       assert circ.total_gate_count() == 1
       assert circ.gate_count() == {"SX": 1}

**``tests/unit/test_codegen_qsharp.py``** -- verify Q# output:

.. code-block:: python

   @pytest.mark.unit
   def test_sx_qsharp():
       circ = Circuit()
       q = circ.allocate(1)
       circ.sx(q[0])
       code = circ.to_qsharp()
       assert "SX(q[0]);" in code

**``tests/unit/test_codegen_openqasm.py``** -- verify OpenQASM output:

.. code-block:: python

   @pytest.mark.unit
   def test_sx_openqasm():
       circ = Circuit()
       q = circ.allocate(1)
       circ.sx(q[0])
       code = circ.to_openqasm()
       assert "sx q[0];" in code

Step 6: Update Documentation
-----------------------------

Add the gate to the gate catalog table in ``docs/user_guide/circuits.rst``.
