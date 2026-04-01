qdk-pythonic
============

A Pythonic circuit-builder API for the Microsoft Quantum Development Kit.

Build quantum circuits, model condensed matter systems, price financial
derivatives, encode data for quantum ML, and solve combinatorial optimization
problems -- with Q# and OpenQASM code generation, simulation, and resource
estimation.

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
   tutorials/condensed_matter
   tutorials/optimization
   tutorials/quantum_finance
   tutorials/quantum_ml

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

.. toctree::
   :maxdepth: 2
   :caption: Domain Modules

   api/domains_common
   api/domains_condensed_matter
   api/domains_optimization
   api/domains_finance
   api/domains_ml

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
