Getting Started
===============

Installation
------------

Install ``qdk-pythonic`` with pip:

.. code-block:: bash

   pip install qdk-pythonic

To run circuits on the Q# simulator or use resource estimation, install with
the ``qsharp`` extra:

.. code-block:: bash

   pip install "qdk-pythonic[qsharp]"

Building Your First Circuit
----------------------------

Create a Bell state circuit using the fluent API:

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0]).cx(q[0], q[1]).measure_all()

Inspecting the Circuit
-----------------------

View the generated Q# and OpenQASM code:

.. code-block:: python

   print(circ.to_qsharp())
   print(circ.to_openqasm())

Draw an ASCII diagram:

.. code-block:: python

   print(circ.draw())

Check circuit metrics:

.. code-block:: python

   print(f"Depth: {circ.depth()}")
   print(f"Gate count: {circ.gate_count()}")
   print(f"Qubit count: {circ.qubit_count()}")

Running the Circuit
--------------------

Execute the circuit on the Q# simulator (requires ``qsharp``):

.. code-block:: python

   results = circ.run(shots=1000)
   print(results[:10])  # first 10 shots

The results are correlated: you will see either ``[Zero, Zero]`` or
``[One, One]`` for each shot, reflecting the entanglement of the Bell pair.

Using Circuit Builders
-----------------------

For common circuits you can skip the manual gate calls and use the built-in
builder functions:

.. code-block:: python

   from qdk_pythonic import bell_state, ghz_state, qft

   # One-liner Bell state
   bell = bell_state(measure=True)
   print(bell.draw())

   # 5-qubit GHZ state
   ghz = ghz_state(5)
   print(ghz.to_qsharp())

   # 3-qubit QFT
   ft = qft(3)
   print(ft.draw())

Builders return regular ``Circuit`` objects, so you can keep adding gates:

.. code-block:: python

   circ = ghz_state(3)
   q = circ.qubits
   circ.cz(q[0], q[2]).measure_all()

See the :doc:`/api/builders` reference for the full list of builders.

Raw Q# Escape Hatch
---------------------

Some constructs -- repeat-until-success loops, classical control flow, Q#
standard library calls -- cannot be expressed with gate-level methods. For
these cases, embed a Q# fragment directly with ``raw_qsharp()``:

.. code-block:: python

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0])
   circ.raw_qsharp("let r = M(q[0]);")
   circ.raw_qsharp("if r == One { X(q[1]); }")

The fragment is inserted verbatim into the generated Q# output. It can be
freely interleaved with regular gate calls and chained fluently:

.. code-block:: python

   circ.h(q[0]).raw_qsharp("let r = M(q[0]);").x(q[1])

A few things to keep in mind:

- ``raw_qsharp()`` fragments are **Q#-only**. Calling ``to_openqasm()`` on a
  circuit that contains raw fragments raises ``CodegenError``.
- Analysis methods (``depth()``, ``gate_count()``, ``draw()``) skip raw
  fragments since their cost cannot be determined statically.
- The Q# code is not validated at build time -- syntax errors surface when the
  circuit is compiled by the ``qsharp`` runtime.

Serialization
--------------

Save and reload a circuit as JSON:

.. code-block:: python

   json_str = circ.to_json(name="bell")
   print(json_str)

   restored = Circuit.from_json(json_str)
   print(restored.gate_count())  # same as original
