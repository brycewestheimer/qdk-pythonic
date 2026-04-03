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
   tutorials/quspin_integration
   tutorials/networkx_integration
   tutorials/pyscf_integration

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/overview
   user_guide/circuits
   user_guide/parameters
   user_guide/codegen
   user_guide/execution
   user_guide/domains
   user_guide/analysis
   user_guide/interop
   user_guide/errors

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   developer_guide/setup
   developer_guide/architecture
   developer_guide/adding_gates
   developer_guide/adding_domains
   developer_guide/codegen_backend
   developer_guide/parser_backend
   developer_guide/testing
   developer_guide/style

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
   api/adapters

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
