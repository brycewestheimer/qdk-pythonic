Analysis and Serialization
==========================

qdk-pythonic provides methods for inspecting circuit metrics, visualizing
circuits as ASCII diagrams, and serializing circuits to JSON.

Circuit Metrics
---------------

**Depth**

:meth:`~qdk_pythonic.core.circuit.Circuit.depth` computes the circuit
depth using greedy time-step scheduling. Each instruction is placed at the
earliest step where all its qubits are available. ``RawQSharp``
instructions are skipped.

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(3)
   circ.h(q[0]).h(q[1]).cx(q[0], q[2])

   print(circ.depth())  # 2: the two H gates run in parallel

**Gate count**

:meth:`~qdk_pythonic.core.circuit.Circuit.gate_count` returns a dict
mapping gate name to count, sorted alphabetically. Measurements and raw
fragments are excluded.

.. code-block:: python

   counts = circ.gate_count()
   print(counts)  # {'CNOT': 1, 'H': 2}

:meth:`~qdk_pythonic.core.circuit.Circuit.total_gate_count` returns the
sum of all per-gate counts.

.. code-block:: python

   print(circ.total_gate_count())  # 3

**Qubit count**

:meth:`~qdk_pythonic.core.circuit.Circuit.qubit_count` returns the total
number of allocated qubits.

.. code-block:: python

   print(circ.qubit_count())  # 3

ASCII Visualization
-------------------

:meth:`~qdk_pythonic.core.circuit.Circuit.draw` renders the circuit as
an ASCII diagram:

.. code-block:: python

   print(circ.draw())

Each qubit is drawn as a horizontal wire. Gates are placed in
time-step-aligned columns. Controlled gates show ``*`` on control qubits
with ``|`` vertical connectors to the target.

The diagram truncates at 10 qubits and 30 gates, appending a note about
how many more were omitted.

``RawQSharp`` instructions are skipped in the visualization since their
qubit usage cannot be determined.

JSON Serialization
------------------

Save and reload circuits as JSON:

.. code-block:: python

   # Serialize
   json_str = circ.to_json(name="my_circuit")
   print(json_str)

   # Deserialize
   restored = Circuit.from_json(json_str)
   assert restored.gate_count() == circ.gate_count()

The ``to_json()`` and ``from_json()`` methods support:

- Gate instructions (including controlled and adjoint flags)
- Measurements (with optional labels)
- Raw Q# fragments
- Symbolic parameters (serialized as ``{"kind": "symbolic", "name": "theta"}``)
- Optional circuit name and metadata

For working with plain dicts instead of JSON strings, use ``to_dict()``
and ``from_dict()``.

.. code-block:: python

   data = circ.to_dict(name="my_circuit", metadata={"version": 1})
   restored = Circuit.from_dict(data)
