Domain Adapters
===============

qdk-pythonic includes domain adapter modules for condensed matter physics,
combinatorial optimization, quantum finance, and quantum machine learning.
These are integration examples showing how the core circuit API can be
specialized for real workflows -- not production-complete libraries.  Each
module provides high-level abstractions that produce standard
:class:`~qdk_pythonic.core.circuit.Circuit` objects.

Design Philosophy
-----------------

Every domain object either:

- Produces a circuit via ``to_circuit()`` (satisfying the
  :class:`~qdk_pythonic.core.protocols.CircuitProducer` protocol), or
- Produces a Hamiltonian via ``to_hamiltonian()`` for further processing.

Because the result is always a plain ``Circuit``, all standard operations
work on domain-produced circuits: code generation, simulation, resource
estimation, analysis, and serialization.

.. code-block:: python

   from qdk_pythonic.domains.condensed_matter import IsingModel, Chain

   model = IsingModel(lattice=Chain(6), j=1.0, h=0.5)
   hamiltonian = model.to_hamiltonian()

   from qdk_pythonic.domains.common import TrotterEvolution

   evol = TrotterEvolution(hamiltonian)
   circ = evol.to_circuit(dt=0.1, steps=5)

   # Standard Circuit operations work
   print(circ.depth())
   print(circ.to_qsharp())

Shared Primitives (``domains.common``)
--------------------------------------

The ``domains.common`` subpackage provides building blocks used across
all domain modules:

**Pauli operators and Hamiltonians**
    :class:`~qdk_pythonic.domains.common.operators.PauliTerm` and
    :class:`~qdk_pythonic.domains.common.operators.PauliHamiltonian`
    for constructing qubit Hamiltonians. Use the ``X(i)``, ``Y(i)``,
    ``Z(i)`` factory functions to create terms:

    .. code-block:: python

       from qdk_pythonic.domains.common import X, Z, PauliHamiltonian

       h = -1.0 * Z(0) * Z(1) + 0.5 * X(0) + 0.5 * X(1)

**Trotter evolution**
    :class:`~qdk_pythonic.domains.common.evolution.TrotterEvolution`
    implements first- and second-order Suzuki-Trotter decomposition of
    a Hamiltonian into a gate circuit.

**Variational ansatz**
    :class:`~qdk_pythonic.domains.common.ansatz.HardwareEfficientAnsatz`
    builds parameterized circuits with configurable rotation gates and
    entanglement patterns.

**State preparation**
    :class:`~qdk_pythonic.domains.common.states.BasisState`,
    :class:`~qdk_pythonic.domains.common.states.UniformSuperposition`,
    and :class:`~qdk_pythonic.domains.common.states.DiscreteProbabilityDistribution`
    for preparing initial quantum states.

**Fermionic operators**
    :class:`~qdk_pythonic.domains.common.fermion.FermionTerm` and
    :class:`~qdk_pythonic.domains.common.fermion.FermionOperator` for
    second-quantized Hamiltonians.  Builder functions ``creation()``,
    ``annihilation()``, ``number_operator()``, ``hopping()``, and
    ``from_integrals()`` simplify construction.

**Qubit mappings**
    :class:`~qdk_pythonic.domains.common.mapping.JordanWignerMapping` and
    :class:`~qdk_pythonic.domains.common.mapping.BravyiKitaevMapping`
    transform fermionic operators into Pauli Hamiltonians.  Both are
    available as standalone functions (``jordan_wigner()``,
    ``bravyi_kitaev()``) and as registered algorithms accessible via
    ``create("qubit_mapper", "jw")``.

Domain Overview
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 30

   * - Domain
     - Key classes
     - Produces
   * - Chemistry
     - ``HartreeFockState``, ``UCCSDAnsatz``, ``ChemistryQPE``,
       ``VQE``, ``ChemistryQubitization``, ``FCIDUMPData``,
       ``DoubleFactorizedHamiltonian``
     - QPE/VQE/qubitization circuits, resource estimates
   * - Condensed matter
     - ``IsingModel``, ``HeisenbergModel``, ``HubbardModel``,
       ``Chain``, ``SquareLattice``, ``HexagonalLattice``,
       ``simulate_dynamics``
     - Hamiltonians and time-evolution circuits
   * - Optimization
     - ``MaxCut``, ``QUBO``, ``TSP``, ``QAOA``
     - Cost/mixer Hamiltonians and QAOA circuits
   * - Finance
     - ``LogNormalDistribution``, ``EuropeanCallOption``,
       ``QuantumAmplitudeEstimation``
     - State-loading and amplitude estimation circuits
   * - Machine learning
     - ``AngleEncoding``, ``AmplitudeEncoding``,
       ``QuantumKernel``, ``VariationalClassifier``
     - Feature-encoding, kernel, and classifier circuits

Each domain has a dedicated tutorial with worked examples:

- :doc:`/tutorials/chemistry`
- :doc:`/tutorials/condensed_matter`
- :doc:`/tutorials/optimization`
- :doc:`/tutorials/quantum_finance`
- :doc:`/tutorials/quantum_ml`

External Package Adapters
-------------------------

The ``adapters`` package provides integration with external domain
libraries.  Each adapter translates domain-native objects into existing
qdk-pythonic primitives, so domain scientists never need to write Q# or
understand qubit mappings.

.. list-table::
   :header-rows: 1
   :widths: 15 25 40

   * - Package
     - Functions
     - Description
   * - `QuSpin <https://quspin.github.io/QuSpin/>`_
     - ``from_quspin_static_list``, ``from_quspin_hamiltonian``,
       ``simulate_quspin_model``
     - Convert spin Hamiltonian specifications to ``PauliHamiltonian``
       and Trotter circuits.  Handles ladder operators (S+/S-).
   * - `NetworkX <https://networkx.org/>`_
     - ``maxcut_from_networkx``, ``solve_maxcut``,
       ``compare_qaoa_depths``, ``build_qaoa_circuit``,
       ``graph_coloring_to_hamiltonian``
     - Convert graphs to ``MaxCut`` / ``QAOA`` circuits.
       Supports weighted edges and arbitrary node types.
   * - `PySCF <https://pyscf.org/>`_
     - ``run_scf``, ``get_integrals``,
       ``molecular_hamiltonian``, ``molecular_summary``
     - Build molecular qubit Hamiltonians from geometry strings.
       Supports active space selection and JW/BK qubit mappings.

Install the optional dependencies with:

.. code-block:: bash

   pip install "qdk-pythonic[quspin]"    # QuSpin adapter
   pip install "qdk-pythonic[networkx]"  # NetworkX adapter
   pip install "qdk-pythonic[pyscf]"     # PySCF chemistry adapter
   pip install "qdk-pythonic[adapters]"  # all adapters

Algorithm Registry
^^^^^^^^^^^^^^^^^^

All adapters register their algorithms with a lightweight registry
matching the QDK/Chemistry ``create()`` pattern:

.. code-block:: python

   from qdk_pythonic.registry import create, available

   # See what's registered
   print(available())

   # Build a Hamiltonian (any backend)
   h = create("hamiltonian_builder", "quspin").run(static_list, n_sites=8)
   h = create("hamiltonian_builder", "pyscf").run(atom="H 0 0 0; H 0 0 0.74")

   # Build a circuit
   circuit = create("time_evolution_builder", "trotter", time=1.0).run(h)

   # Map fermions to qubits
   pauli_h = create("qubit_mapper", "jw").run(fermion_op)

Adapter tutorials:

- :doc:`/tutorials/quspin_integration`
- :doc:`/tutorials/networkx_integration`
- :doc:`/tutorials/pyscf_integration`
