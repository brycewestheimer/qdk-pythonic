Condensed Matter Simulation
===========================

qdk-pythonic provides lattice spin models that map directly to Pauli
Hamiltonians and Trotter circuits. The main use case is estimating the
physical resources needed for quantum simulation of condensed matter systems.

Ising Model on a Chain
-----------------------

Start by defining a transverse-field Ising model on a 1D chain:

.. code-block:: python

   from qdk_pythonic.domains.condensed_matter import Chain, IsingModel

   chain = Chain(10)
   model = IsingModel(chain, J=1.0, h=0.5)

   ham = model.to_hamiltonian()
   print(f"Terms: {len(ham)}, Qubits: {ham.qubit_count()}")

The Hamiltonian is ``H = -J sum Z_i Z_j - h sum X_i``, where the sums run
over nearest-neighbor pairs and all sites respectively.

Build the time-evolution circuit with ``simulate_dynamics``:

.. code-block:: python

   from qdk_pythonic.domains.condensed_matter import simulate_dynamics

   circuit = simulate_dynamics(model, time=1.0, steps=10)

   print(circuit.draw())
   print(f"Depth: {circuit.depth()}")
   print(f"Gate count: {circuit.gate_count()}")

This generates a first-order Trotter circuit approximating ``exp(-i H t)``.

Trotter Order and Accuracy
---------------------------

The ``order`` parameter controls the Trotter decomposition. First order
(``order=1``) is simpler but less accurate; second order (``order=2``) uses
the symmetric Suzuki-Trotter formula at roughly double the gate cost.

.. code-block:: python

   circ_order1 = simulate_dynamics(model, time=1.0, steps=10, order=1)
   circ_order2 = simulate_dynamics(model, time=1.0, steps=10, order=2)

   print(f"Order 1 gates: {circ_order1.total_gate_count()}")
   print(f"Order 2 gates: {circ_order2.total_gate_count()}")

You can also use ``TrotterEvolution`` directly for finer control:

.. code-block:: python

   from qdk_pythonic.domains.common import TrotterEvolution

   evo = TrotterEvolution(
       hamiltonian=ham, time=1.0, steps=20, order=2,
   )
   circuit = evo.to_circuit()

Resource Estimation
--------------------

Estimate the physical resources for fault-tolerant execution (requires
``qsharp``):

.. code-block:: python

   result = circuit.estimate()
   print(result)

Sweep over chain lengths to see how resources scale:

.. code-block:: python

   for n in [4, 8, 16, 32]:
       circ = simulate_dynamics(
           IsingModel(Chain(n), J=1.0, h=0.5),
           time=1.0, steps=10,
       )
       result = circ.estimate()
       print(f"n={n}: {result}")

Heisenberg Model on a Square Lattice
--------------------------------------

For 2D systems, use ``SquareLattice`` with the Heisenberg model:

.. code-block:: python

   from qdk_pythonic.domains.condensed_matter import (
       SquareLattice, HeisenbergModel, simulate_dynamics,
   )

   lattice = SquareLattice(3, 3)
   model = HeisenbergModel(lattice, Jx=1.0, Jy=1.0, Jz=0.5)

   circuit = simulate_dynamics(model, time=1.0, steps=10)
   print(f"Qubits: {circuit.qubit_count()}")
   print(f"Gate count: {circuit.gate_count()}")

The Heisenberg Hamiltonian is
``H = sum [Jx X_i X_j + Jy Y_i Y_j + Jz Z_i Z_j]``.

Hubbard Model
--------------

The Fermi-Hubbard model uses a Jordan-Wigner mapping and requires ``2N``
qubits for ``N`` lattice sites (one set for spin-up, one for spin-down):

.. code-block:: python

   from qdk_pythonic.domains.condensed_matter import Chain, HubbardModel

   model = HubbardModel(Chain(4), t=1.0, U=2.0)
   ham = model.to_hamiltonian()
   print(f"Qubits: {ham.qubit_count()}")  # 8 for 4 sites

   circuit = simulate_dynamics(model, time=0.5, steps=5)
   print(f"Gate count: {circuit.gate_count()}")

Lattice Geometries
-------------------

Three lattice types are available:

- ``Chain(n, periodic=False)`` -- 1D chain with optional periodic boundary
- ``SquareLattice(rows, cols, periodic=False)`` -- 2D square grid
- ``HexagonalLattice(rows, cols)`` -- 2D honeycomb lattice

All satisfy the ``Lattice`` protocol (``num_sites`` and ``edges`` properties).

Next Steps
-----------

See the :doc:`/api/domains_condensed_matter` API reference for full details
on all classes and functions. The ``07_condensed_matter.ipynb`` notebook in
``examples/notebooks/`` has more worked examples.
