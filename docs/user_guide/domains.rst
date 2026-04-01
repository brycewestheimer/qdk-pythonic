Domain Modules
==============

qdk-pythonic includes domain modules for condensed matter physics,
combinatorial optimization, quantum finance, and quantum machine learning.
Each module provides high-level abstractions that produce standard
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

Domain Overview
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 30

   * - Domain
     - Key classes
     - Produces
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

- :doc:`/tutorials/condensed_matter`
- :doc:`/tutorials/optimization`
- :doc:`/tutorials/quantum_finance`
- :doc:`/tutorials/quantum_ml`
