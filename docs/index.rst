qdk-pythonic
============

A Pythonic circuit-builder API for the Microsoft Quantum Development Kit.

Build quantum circuits using native Python methods, generate Q# or OpenQASM
source code, run simulations, and estimate resources for fault-tolerant
quantum computing.

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0]).cx(q[0], q[1]).measure_all()

   print(circ.to_qsharp())
   print(circ.draw())

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   tutorials/getting_started
   tutorials/resource_estimation
   tutorials/openqasm_interop

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/circuit
   api/builders
   api/qubit
   api/gates
   api/instruction
   api/codegen
   api/parser
   api/execution
   api/analysis
   api/exceptions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
