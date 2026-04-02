Combinatorial Optimization with QAOA
======================================

This tutorial demonstrates how the core circuit API extends to optimization
workflows.  The optimization module is an integration example, not a
production-ready solver.

qdk-pythonic maps combinatorial optimization problems to quantum circuits
using the Quantum Approximate Optimization Algorithm (QAOA). It provides
problem encodings for MaxCut, QUBO, and TSP, and a QAOA circuit builder
that produces standard ``Circuit`` objects for simulation or resource
estimation.

MaxCut Problem
---------------

Define a graph and encode it as a MaxCut problem:

.. code-block:: python

   from qdk_pythonic.domains.optimization import MaxCut

   problem = MaxCut(
       edges=[(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)],
       n_nodes=4,
   )

   ham = problem.to_hamiltonian()
   print(f"Terms: {len(ham)}, Qubits: {ham.qubit_count()}")

The cost Hamiltonian encodes ``C = sum (1 - Z_i Z_j) / 2`` over all edges.

Building a QAOA Circuit
------------------------

Create a QAOA instance and build the circuit with variational angles:

.. code-block:: python

   from qdk_pythonic.domains.optimization import QAOA

   qaoa = QAOA(problem.to_hamiltonian(), p=2)
   print(f"Parameters: {qaoa.num_parameters}")  # 4 (2*p)

   circuit = qaoa.to_circuit(
       gamma=[0.5, 0.3],
       beta=[0.7, 0.2],
   )

   print(circuit.draw())
   print(f"Depth: {circuit.depth()}")
   print(f"Gate count: {circuit.gate_count()}")

The circuit applies: (1) Hadamard on all qubits, then for each layer:
(2) cost unitary ``exp(-i gamma C)`` and (3) mixer ``exp(-i beta B)``.

Custom Mixers
--------------

By default, QAOA uses the standard X-mixer ``B = sum X_i``. You can provide
a different mixer Hamiltonian:

.. code-block:: python

   from qdk_pythonic.domains.optimization import x_mixer

   # Default X-mixer (same as QAOA's default)
   mixer = x_mixer(4)
   qaoa = QAOA(problem.to_hamiltonian(), p=2, mixer=mixer)

Any ``PauliHamiltonian`` can serve as a mixer if it has the right qubit
count.

QUBO Problems
--------------

Quadratic Unconstrained Binary Optimization problems can be expressed as a
weight matrix and converted to an Ising Hamiltonian:

.. code-block:: python

   from qdk_pythonic.domains.optimization import QUBO

   Q = {(0, 0): -1, (1, 1): -1, (0, 1): 2}
   qubo = QUBO(Q=Q, n_vars=2)

   ham = qubo.to_hamiltonian()
   qaoa = QAOA(ham, p=1)
   circuit = qaoa.to_circuit(gamma=[0.5], beta=[0.7])

The conversion uses the substitution ``x_i = (1 - Z_i) / 2`` to map binary
variables to Pauli-Z operators.

Traveling Salesman Problem
---------------------------

The TSP is encoded as a QUBO via one-hot binary variables ``x_{i,t}``
(city *i* visited at time *t*), requiring ``N^2`` qubits for *N* cities:

.. code-block:: python

   from qdk_pythonic.domains.optimization import TSP

   distances = [
       [0, 10, 15, 20],
       [10, 0, 25, 30],
       [15, 25, 0, 35],
       [20, 30, 35, 0],
   ]
   tsp = TSP(distances=distances)
   ham = tsp.to_hamiltonian()
   print(f"Qubits: {ham.qubit_count()}")  # 16 for 4 cities

   qaoa = QAOA(ham, p=1)
   circuit = qaoa.to_circuit(gamma=[0.5], beta=[0.3])

The qubit count grows quickly (``N^2``), so TSP is mainly useful for
resource estimation of modestly sized instances.

Resource Estimation
--------------------

Estimate the physical resources for QAOA at different depths (requires
``qsharp``):

.. code-block:: python

   for p in [1, 2, 4]:
       qaoa = QAOA(problem.to_hamiltonian(), p=p)
       gamma = [0.5] * p
       beta = [0.3] * p
       circuit = qaoa.to_circuit(gamma=gamma, beta=beta)
       result = circuit.estimate()
       print(f"p={p}: {result}")

Next Steps
-----------

See the :doc:`/api/domains_optimization` API reference for full details.
The ``08_optimization.ipynb`` notebook in ``examples/notebooks/`` has more
worked examples.
