PySCF Chemistry Integration
============================

This tutorial shows how to build qubit Hamiltonians for molecules
using `PySCF <https://pyscf.org/>`_ and the qdk-pythonic chemistry
adapter.  The adapter runs Hartree-Fock, extracts electron integrals,
applies a fermion-to-qubit mapping (Jordan-Wigner or Bravyi-Kitaev),
and produces a ``PauliHamiltonian`` ready for Trotter circuit
construction and resource estimation.

.. note::

   Install the optional dependency: ``pip install qdk-pythonic[pyscf]``

Hydrogen Molecule (H2)
-----------------------

The simplest molecular system -- two hydrogen atoms:

.. code-block:: python

   from qdk_pythonic.adapters.pyscf_adapter import molecular_hamiltonian

   h = molecular_hamiltonian("H 0 0 0; H 0 0 0.74", basis="sto-3g")
   h.print_summary()
   # PauliHamiltonian: N terms on 4 qubits
   #   Max Pauli weight: ...
   #   1-norm: ...
   #   Weight distribution: ...

H2 in the STO-3G basis has 2 spatial orbitals, giving 4 spin-orbitals
(4 qubits under Jordan-Wigner mapping).

Step-by-Step Workflow
----------------------

For more control, use the lower-level functions:

.. code-block:: python

   from qdk_pythonic.adapters.pyscf_adapter import run_scf, get_integrals
   from qdk_pythonic.domains.common.fermion import from_integrals
   from qdk_pythonic.domains.common.mapping import jordan_wigner
   from qdk_pythonic.domains.common.evolution import TrotterEvolution

   # Stage 1: Run Hartree-Fock
   mf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
   print(f"SCF energy: {mf.e_tot:.6f} Hartree")

   # Stage 2: Extract integrals
   h1e, h2e, nuc = get_integrals(mf)
   print(f"Orbitals: {h1e.shape[0]}, Nuclear repulsion: {nuc:.4f}")

   # Stage 3: Build fermionic Hamiltonian
   fermion_op = from_integrals(h1e, h2e, nuc)
   print(f"Fermionic terms: {len(fermion_op)}")

   # Stage 4: Map to qubits
   pauli_h = jordan_wigner(fermion_op)
   pauli_h.print_summary()

   # Stage 5: Build Trotter circuit
   evolution = TrotterEvolution(pauli_h, time=1.0, steps=5)
   circuit = evolution.to_circuit()
   print(f"Circuit: {circuit.qubit_count()} qubits, "
         f"{circuit.total_gate_count()} gates, depth {circuit.depth()}")

   # Stage 6: Export
   print(circuit.to_qsharp()[:200])

Using the Registry
-------------------

The same workflow is available through the QDK/Chemistry-style
``create()`` pattern:

.. code-block:: python

   from qdk_pythonic.registry import create

   # Build Hamiltonian
   builder = create("hamiltonian_builder", "pyscf", basis="sto-3g")
   h = builder.run(atom="H 0 0 0; H 0 0 0.74")

   # Build circuit
   circuit = create("time_evolution_builder", "trotter",
                     time=1.0, steps=5).run(h)

   print(f"Qubits: {circuit.qubit_count()}, Gates: {circuit.total_gate_count()}")

All three domain adapters (QuSpin, NetworkX, PySCF) produce
``PauliHamiltonian`` objects that flow through the same downstream
pipeline.

Bravyi-Kitaev Mapping
----------------------

The default mapping is Jordan-Wigner, which maps each fermionic mode
to one qubit with O(N) Pauli weight per operator.  Bravyi-Kitaev
reduces this to O(log N):

.. code-block:: python

   h_jw = molecular_hamiltonian("H 0 0 0; H 0 0 0.74", mapping="jordan_wigner")
   h_bk = molecular_hamiltonian("H 0 0 0; H 0 0 0.74", mapping="bravyi_kitaev")

   print(f"JW: {h_jw.summary()['max_pauli_weight']} max weight, "
         f"{len(h_jw)} terms")
   print(f"BK: {h_bk.summary()['max_pauli_weight']} max weight, "
         f"{len(h_bk)} terms")

Active Space Selection
-----------------------

For larger molecules, restrict to an active space to keep the qubit
count manageable:

.. code-block:: python

   h = molecular_hamiltonian(
       "Li 0 0 0; H 0 0 1.6",
       basis="sto-3g",
       n_active_electrons=2,
       n_active_orbitals=2,
   )
   print(f"Qubits: {h.qubit_count()}")  # 4 (2 orbitals * 2 spins)

Without the active space, LiH in STO-3G uses 6 spatial orbitals
(12 qubits).  With ``(2e, 2o)`` the problem reduces to 4 qubits.

End-to-End Summary
-------------------

The ``molecular_summary`` function returns all pipeline outputs in one
call:

.. code-block:: python

   from qdk_pythonic.adapters.pyscf_adapter import molecular_summary

   result = molecular_summary("H 0 0 0; H 0 0 0.74", basis="sto-3g")
   print(f"SCF energy:   {result['scf_energy']:.6f}")
   print(f"Orbitals:     {result['n_orbitals']}")
   print(f"Qubits:       {result['n_qubits']}")
   print(f"Total gates:  {result['total_gates']}")
   print(f"Depth:        {result['depth']}")

Convenience Functions
----------------------

For end-to-end workflows that handle the entire pipeline
automatically, use the one-call convenience functions:

.. code-block:: python

   from qdk_pythonic.adapters.pyscf_adapter import (
       molecular_qpe, molecular_vqe, molecular_resource_comparison,
   )

   # QPE with structured resource estimate (requires qsharp)
   result = molecular_qpe("H 0 0 0; H 0 0 0.74", n_estimation_qubits=8)
   result.print_report()

   # VQE with UCCSD ansatz (requires qsharp)
   vqe_result = molecular_vqe("H 0 0 0; H 0 0 0.74", max_iterations=50)
   print(f"Energy: {vqe_result.optimal_energy:.6f} Ha")

   # Side-by-side Trotter vs qubitization (requires qsharp)
   molecular_resource_comparison("H 0 0 0; H 0 0 0.74", n_estimation_qubits=8)

These functions support CASCI active space selection via the
``n_active_electrons`` and ``n_active_orbitals`` parameters.

Next Steps
-----------

- :doc:`/tutorials/chemistry` -- QPE, VQE, UCCSD, qubitization, tapering, and resource estimation
- :doc:`/tutorials/quspin_integration` -- condensed matter Hamiltonians
- :doc:`/tutorials/networkx_integration` -- graph optimization
- :doc:`/api/domains_chemistry` -- chemistry API reference
- :doc:`/api/adapters` -- full adapter API reference
