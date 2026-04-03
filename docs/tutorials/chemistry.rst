Quantum Chemistry Algorithms
=============================

This tutorial walks through the full quantum chemistry workflow:
molecular geometry to quantum algorithms (QPE, VQE) and resource
estimation -- reproducing the Microsoft qdk-chemistry pipeline
using PySCF as the classical backend.

.. note::

   Install the chemistry dependencies: ``pip install qdk-pythonic[chemistry]``

Overview
--------

The qdk-chemistry workflow has six stages:

1. **Classical electronic structure** -- PySCF runs SCF and CASCI
2. **Fermionic Hamiltonian** -- one/two-electron integrals to second-quantized form
3. **Qubit mapping** -- Jordan-Wigner or Bravyi-Kitaev
4. **Initial state** -- Hartree-Fock reference preparation
5. **Quantum algorithm** -- QPE, VQE, or qubitization
6. **Resource estimation** -- physical qubit and runtime costs

Hartree-Fock State Preparation
-------------------------------

The Hartree-Fock state is the starting point for both QPE and VQE.
Under Jordan-Wigner mapping, it sets the first ``n_electrons`` qubits
to ``|1>``:

.. code-block:: python

   from qdk_pythonic.domains.chemistry import HartreeFockState

   hf = HartreeFockState(n_qubits=4, n_electrons=2)
   print(hf.to_bitstring())   # "1100"

   circuit = hf.to_circuit()
   print(circuit.draw())

Bravyi-Kitaev encoding is also supported:

.. code-block:: python

   hf_bk = HartreeFockState(n_qubits=4, n_electrons=2, mapping="bravyi_kitaev")
   print(hf_bk.to_bitstring())  # "1000" (BK parity encoding)

UCCSD Ansatz
-------------

The Unitary Coupled Cluster Singles and Doubles ansatz generates
parameterized excitation circuits for VQE:

.. code-block:: python

   from qdk_pythonic.domains.chemistry import UCCSDAnsatz

   ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
   print(f"Parameters: {ansatz.num_parameters}")
   print(f"Singles: {ansatz.singles()}")
   print(f"Doubles: {ansatz.doubles()}")

   # Build circuit with specific parameter values
   params = [0.1] * ansatz.num_parameters
   circuit = ansatz.to_circuit(params)
   print(f"{circuit.qubit_count()} qubits, {circuit.total_gate_count()} gates")

Quantum Phase Estimation
-------------------------

QPE uses controlled Hamiltonian simulation (Trotter) and inverse QFT
to extract molecular ground-state energy:

.. code-block:: python

   from qdk_pythonic.adapters.pyscf_adapter import molecular_hamiltonian
   from qdk_pythonic.domains.chemistry import ChemistryQPE

   h = molecular_hamiltonian("H 0 0 0; H 0 0 0.74", basis="sto-3g")

   qpe = ChemistryQPE(
       hamiltonian=h,
       n_electrons=2,
       n_estimation_qubits=8,
       trotter_steps=4,
   )
   circuit = qpe.to_circuit()
   print(f"QPE circuit: {circuit.qubit_count()} qubits, "
         f"{circuit.total_gate_count()} gates")

   # Resource estimation (requires qsharp)
   # result = qpe.estimate_resources()

The number of estimation qubits controls energy precision: ``m`` qubits
give ``2^m`` phase bins.

Variational Quantum Eigensolver
--------------------------------

VQE uses a parameterized ansatz and classical optimization to find the
ground-state energy:

.. code-block:: python

   from qdk_pythonic.domains.chemistry import VQE, UCCSDAnsatz

   ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
   vqe = VQE(
       hamiltonian=h,
       ansatz=ansatz,
       n_electrons=2,
       optimizer="COBYLA",
       max_iterations=100,
       shots=10000,
   )

   # Build trial-state circuit for specific parameters
   trial_circuit = vqe.to_circuit([0.0] * ansatz.num_parameters)

   # Run VQE optimization (requires qsharp for simulation)
   # result = vqe.run()
   # print(f"Energy: {result.optimal_energy:.6f} Ha")

VQE also works with the generic ``HardwareEfficientAnsatz``:

.. code-block:: python

   from qdk_pythonic.domains.common import HardwareEfficientAnsatz

   ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=2)
   vqe = VQE(hamiltonian=h, ansatz=ansatz, n_electrons=2)

FCIDUMP Interoperability
-------------------------

Read and write molecular integrals in the standard FCIDUMP format:

.. code-block:: python

   from qdk_pythonic.domains.chemistry import read_fcidump, write_fcidump

   data = read_fcidump("h2.fcidump")
   print(f"{data.n_orbitals} orbitals, {data.n_electrons} electrons")

   # Convert to qubit Hamiltonian
   hamiltonian = data.to_hamiltonian()

   # Convert to double-factorized form
   df = data.to_double_factorized()
   df.print_summary()

Double Factorization
---------------------

Double factorization decomposes the two-electron integrals into a
compact form that reduces the cost of qubitization:

.. code-block:: python

   from qdk_pythonic.adapters.pyscf_adapter import run_scf, get_integrals
   from qdk_pythonic.domains.common.double_factorization import double_factorize

   scf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
   h1e, h2e, nuc = get_integrals(scf)

   df = double_factorize(h1e, h2e, nuc, n_electrons=2)
   df.print_summary()
   # Shows: leaves (rank), 1-norm (lambda), nuclear repulsion

The 1-norm (lambda) directly determines the number of QPE iterations
needed for qubitization. Lower rank means fewer leaves and lower cost.

Qubitization
-------------

Qubitization provides better asymptotic scaling than Trotterization
for chemistry simulation. Two modes are available:

**Gate-level** (small systems, circuit inspection):

.. code-block:: python

   from qdk_pythonic.domains.chemistry import ChemistryQubitization

   cq = ChemistryQubitization(
       hamiltonian=h,
       n_electrons=2,
       n_estimation_qubits=4,
       gate_level=True,
   )
   circuit = cq.to_circuit()
   print(f"Qubitization QPE: {circuit.qubit_count()} qubits")

**Bridge mode** (production resource estimation via qsharp.chemistry):

.. code-block:: python

   from qdk_pythonic.execution.chemistry_bridge import estimate_chemistry

   data = read_fcidump("molecule.fcidump")
   result = estimate_chemistry(data)
   result.print_report()

Structured Resource Estimation
-------------------------------

The ``ChemistryResourceEstimate`` wraps raw estimation results with
typed fields and chemistry-specific labels:

.. code-block:: python

   from qdk_pythonic.execution.chemistry_estimate import parse_estimation_result

   # raw_result from circuit.estimate() or qsharp.chemistry
   # result = parse_estimation_result(raw_result, algorithm_name="trotter_qpe")
   # result.print_report()
   # print(f"Logical qubits: {result.logical.logical_qubits}")
   # print(f"Physical qubits: {result.physical.physical_qubits}")
   # print(f"T-gates: {result.logical.t_count}")

Orbital Information
--------------------

Inspect molecular orbital energies and occupations:

.. code-block:: python

   from qdk_pythonic.domains.chemistry import MolecularOrbitalInfo
   from qdk_pythonic.adapters.pyscf_adapter import run_scf

   scf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
   info = MolecularOrbitalInfo.from_pyscf(scf)
   info.print_report()

Registry Integration
---------------------

All chemistry algorithms are available through the registry:

.. code-block:: python

   from qdk_pythonic.registry import create

   # QPE via PySCF
   qpe = create("chemistry_algorithm", "pyscf_qpe",
                 basis="sto-3g", n_estimation_qubits=10)
   # result = qpe.run(atom="H 0 0 0; H 0 0 0.74")

   # VQE via PySCF
   vqe = create("chemistry_algorithm", "pyscf_vqe",
                 optimizer="COBYLA", ansatz="uccsd")
   # result = vqe.run(atom="H 0 0 0; H 0 0 0.74")

   # DF-qubitization via PySCF + qsharp.chemistry
   est = create("chemistry_algorithm", "pyscf_qubitization",
                 basis="cc-pvdz")
   # result = est.run(atom="H 0 0 0; H 0 0 0.74")

Next Steps
-----------

- :doc:`/tutorials/pyscf_integration` -- basic PySCF adapter usage
- :doc:`/api/domains_chemistry` -- full API reference
- :doc:`/api/domains_common` -- shared primitives (operators, mappings, LCU)
