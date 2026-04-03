QuSpin Integration
===================

This tutorial shows how to connect `QuSpin <https://quspin.github.io/QuSpin/>`_
condensed matter Hamiltonians to the qdk-pythonic circuit and resource estimation
pipeline.  The adapter converts QuSpin operator specifications into
``PauliHamiltonian`` objects, which then flow through the standard Trotter
circuit generation and estimation workflow.

The key idea: a condensed matter physicist defines their model in QuSpin
exactly as they normally would, and qdk-pythonic handles the Pauli
decomposition, Trotterisation, circuit construction, and Q# generation
behind the scenes.

.. note::

   Install the optional dependency: ``pip install qdk-pythonic[quspin]``

   The core conversion function ``from_quspin_static_list`` is pure Python
   and does **not** require QuSpin.  Only ``from_quspin_hamiltonian``
   (which accepts a live QuSpin object) needs QuSpin installed.

Transverse-Field Ising Model
-----------------------------

Define the model using QuSpin's operator specification format -- a list
of ``[operator_string, coupling_list]`` pairs:

.. code-block:: python

   from qdk_pythonic.adapters.quspin_adapter import simulate_quspin_model

   L = 8
   J = 1.0
   h_field = 0.5

   J_zz = [[J, i, (i + 1) % L] for i in range(L)]
   h_x = [[h_field, i] for i in range(L)]

   static_list = [["zz", J_zz], ["x", h_x]]

   result = simulate_quspin_model(
       static_list=static_list,
       n_sites=L,
       time=1.0,
       trotter_steps=10,
   )

   print(f"Qubits:           {result['n_qubits']}")
   print(f"Total gates:      {result['total_gates']}")
   print(f"Circuit depth:    {result['depth']}")
   print(f"Hamiltonian terms: {result['n_hamiltonian_terms']}")

The ``simulate_quspin_model`` function returns a dict containing the
Hamiltonian, circuit, and all circuit metrics.

Step-by-Step Workflow
----------------------

For more control, use the lower-level functions:

.. code-block:: python

   from qdk_pythonic.adapters.quspin_adapter import from_quspin_static_list
   from qdk_pythonic.domains.common.evolution import TrotterEvolution

   # Convert QuSpin format to PauliHamiltonian
   hamiltonian = from_quspin_static_list(static_list, n_sites=L)

   # Build Trotter circuit
   evolution = TrotterEvolution(
       hamiltonian=hamiltonian,
       time=1.0,
       steps=10,
       order=2,  # second-order Suzuki-Trotter
   )
   circuit = evolution.to_circuit()

   # Inspect generated Q# or OpenQASM
   print(circuit.to_qsharp())
   print(circuit.to_openqasm())

Scaling Study
--------------

The Pythonic API makes system-size sweeps natural:

.. code-block:: python

   for L in [4, 8, 12, 16, 20]:
       J_zz = [[1.0, i, (i + 1) % L] for i in range(L)]
       h_x = [[0.5, i] for i in range(L)]
       r = simulate_quspin_model(
           static_list=[["zz", J_zz], ["x", h_x]],
           n_sites=L,
           time=1.0,
           trotter_steps=10,
       )
       print(f"L={L:>3}: qubits={r['n_qubits']}, "
             f"gates={r['total_gates']}, depth={r['depth']}")

Heisenberg XXZ Model
----------------------

The adapter handles multi-component spin interactions (XX, YY, ZZ) on
arbitrary lattice geometries:

.. code-block:: python

   Lx, Ly = 3, 3
   N = Lx * Ly

   neighbors = []
   for x in range(Lx):
       for y in range(Ly):
           site = x * Ly + y
           if x + 1 < Lx:
               neighbors.append([site, (x + 1) * Ly + y])
           if y + 1 < Ly:
               neighbors.append([site, x * Ly + (y + 1)])

   Jxy = 1.0
   Jz = 0.8
   static_xxz = [
       ["xx", [[Jxy / 2, i, j] for i, j in neighbors]],
       ["yy", [[Jxy / 2, i, j] for i, j in neighbors]],
       ["zz", [[Jz, i, j] for i, j in neighbors]],
   ]

   result = simulate_quspin_model(
       static_list=static_xxz,
       n_sites=N,
       time=2.0,
       trotter_steps=20,
       trotter_order=2,
   )
   print(f"Qubits: {result['n_qubits']}, Gates: {result['total_gates']}")

Ladder Operators
-----------------

QuSpin uses ``"+"`` and ``"-"`` for raising and lowering operators.  The
adapter automatically decomposes these into Pauli X and Y components:

- ``S+ = (X + iY) / 2``
- ``S- = (X - iY) / 2``

For Hermitian Hamiltonians (the standard physics case), the imaginary
parts cancel when conjugate pairs are present (e.g. ``S+S- + S-S+``).

.. code-block:: python

   # Equivalent to XX + YY exchange interaction
   static_exchange = [
       ["+-", [[1.0, 0, 1]]],
       ["-+", [[1.0, 0, 1]]],
   ]
   h = from_quspin_static_list(static_exchange, n_sites=2)
   print(f"Terms: {len(h.terms)}")  # real-coefficient terms only

Using Live QuSpin Objects
--------------------------

If you have a constructed QuSpin ``hamiltonian`` object, pass it directly:

.. code-block:: python

   from quspin.basis import spin_basis_1d
   from quspin.operators import hamiltonian as quspin_hamiltonian
   from qdk_pythonic.adapters.quspin_adapter import from_quspin_hamiltonian

   basis = spin_basis_1d(8, pauli=True)
   H = quspin_hamiltonian(static_list, [], basis=basis, dtype=complex)

   pauli_h = from_quspin_hamiltonian(H, n_sites=8)

Dynamic (time-dependent) terms are evaluated at ``t=0`` and included as
static contributions with a warning.

Resource Estimation
--------------------

Pass ``estimate_params`` to run QDK resource estimation (requires
``qsharp``):

.. code-block:: python

   result = simulate_quspin_model(
       static_list=static_list,
       n_sites=8,
       time=1.0,
       trotter_steps=10,
       estimate_params={"qubitParams": {"name": "qubit_gate_ns_e3"}},
   )
   print(result["estimate_result"])

Next Steps
-----------

See the :doc:`/api/adapters` API reference for full function signatures.
The ``11_quspin_integration.ipynb`` notebook in ``examples/notebooks/``
has interactive versions of these examples.
