NetworkX Integration
=====================

This tutorial shows how to connect `NetworkX <https://networkx.org/>`_
graphs to QAOA circuits for MaxCut and graph coloring, with automatic
resource estimation.

The adapter converts NetworkX graph objects into the existing ``MaxCut``
and ``QAOA`` domain classes, which then produce standard ``Circuit``
objects.  An optimization researcher defines their graph in NetworkX as
they normally would, and qdk-pythonic handles the Ising encoding, QAOA
circuit construction, and Q# generation.

.. note::

   Install the optional dependency: ``pip install qdk-pythonic[networkx]``

MaxCut on a Graph
------------------

The simplest workflow is a single function call:

.. code-block:: python

   import networkx as nx
   from qdk_pythonic.adapters.networkx_adapter import solve_maxcut

   G = nx.random_regular_graph(d=3, n=10, seed=42)
   result = solve_maxcut(G, p=2)

   print(f"Qubits:           {result['n_qubits']}")
   print(f"Total gates:      {result['total_gates']}")
   print(f"Circuit depth:    {result['depth']}")
   print(f"Max possible cut: {result['max_possible_cut']}")

``solve_maxcut`` returns a dict with the problem, cost Hamiltonian,
circuit, and all metrics.

Step-by-Step Workflow
----------------------

For more control, use the lower-level functions:

.. code-block:: python

   from qdk_pythonic.adapters.networkx_adapter import maxcut_from_networkx
   from qdk_pythonic.domains.optimization import QAOA

   G = nx.cycle_graph(6)
   problem = maxcut_from_networkx(G)

   # problem is a standard MaxCut instance
   cost_h = problem.to_hamiltonian()
   qaoa = QAOA(cost_hamiltonian=cost_h, p=3)
   circuit = qaoa.to_circuit(
       gamma=[0.5, 0.3, 0.7],
       beta=[0.4, 0.6, 0.2],
   )

   print(circuit.draw())
   print(circuit.to_qsharp())

QAOA Depth Comparison
----------------------

Compare resource requirements across QAOA layer counts:

.. code-block:: python

   from qdk_pythonic.adapters.networkx_adapter import compare_qaoa_depths

   G = nx.random_regular_graph(d=3, n=10, seed=42)
   results = compare_qaoa_depths(G, p_values=[1, 2, 3, 4, 5])

   for r in results:
       print(f"p={r['p']}: gates={r['total_gates']}, depth={r['depth']}")

Weighted Graphs
----------------

Edge weights are read from the NetworkX ``"weight"`` attribute:

.. code-block:: python

   G = nx.Graph()
   G.add_weighted_edges_from([
       (0, 1, 2.0), (1, 2, 1.5), (2, 3, 3.0), (3, 0, 1.0),
   ])

   result = solve_maxcut(G, p=2)
   print(f"Max possible cut: {result['max_possible_cut']}")

The adapter produces a ``MaxCut`` instance with per-edge weights, and
the cost Hamiltonian reflects the weighted ZZ terms.

Scaling with Graph Size
------------------------

.. code-block:: python

   for n in [6, 10, 20, 30, 50]:
       G = nx.random_regular_graph(d=3, n=n, seed=42)
       r = solve_maxcut(G, p=1)
       print(f"n={n:>3}: qubits={r['n_qubits']}, "
             f"gates={r['total_gates']}, depth={r['depth']}")

Benchmark Graph Families
-------------------------

NetworkX ships with many standard graph generators:

.. code-block:: python

   graphs = {
       "Petersen": nx.petersen_graph(),
       "Cycle(12)": nx.cycle_graph(12),
       "Complete(6)": nx.complete_graph(6),
       "Grid(3x4)": nx.grid_2d_graph(3, 4),
   }

   for name, G in graphs.items():
       r = solve_maxcut(G, p=2)
       print(f"{name:<15} qubits={r['n_qubits']}, gates={r['total_gates']}")

Node types are handled automatically -- non-integer nodes (strings,
tuples from grid graphs, etc.) are remapped to contiguous integers.

Graph Coloring
---------------

For graph coloring, the adapter builds a cost Hamiltonian using one-hot
encoding with ``n_nodes * n_colors`` qubits:

.. code-block:: python

   from qdk_pythonic.adapters.networkx_adapter import (
       graph_coloring_to_hamiltonian,
   )
   from qdk_pythonic.domains.optimization import QAOA

   G = nx.petersen_graph()
   ham = graph_coloring_to_hamiltonian(G, n_colors=3, penalty=2.0)

   qaoa = QAOA(cost_hamiltonian=ham, p=1)
   circuit = qaoa.to_circuit(gamma=[0.5], beta=[0.3])
   print(f"Qubits: {circuit.qubit_count()}")

Direct Circuit Access
----------------------

Use ``build_qaoa_circuit`` if you only need the circuit:

.. code-block:: python

   from qdk_pythonic.adapters.networkx_adapter import build_qaoa_circuit

   circuit = build_qaoa_circuit(nx.cycle_graph(6), p=2)
   print(circuit.to_qsharp())
   print(circuit.to_openqasm())

Resource Estimation
--------------------

Pass ``estimate_params`` to run QDK resource estimation (requires
``qsharp``):

.. code-block:: python

   result = solve_maxcut(
       nx.random_regular_graph(3, 20, seed=42),
       p=3,
       estimate_params={"qubitParams": {"name": "qubit_gate_ns_e3"}},
   )
   print(result["estimate_result"])

Next Steps
-----------

See the :doc:`/api/adapters` API reference for full function signatures.
The ``12_networkx_integration.ipynb`` notebook in ``examples/notebooks/``
has interactive versions of these examples.
