Adding Domain Modules
=====================

Domain modules provide high-level abstractions for specific quantum
computing applications. This guide explains how to add a new domain
module that integrates with the rest of qdk-pythonic.

Package Structure
-----------------

Create a new subpackage under ``src/qdk_pythonic/domains/``:

::

    src/qdk_pythonic/domains/chemistry/
        __init__.py       # Re-export public classes
        molecule.py       # Problem encoding
        vqe.py            # VQE circuit construction

The ``__init__.py`` should re-export all public classes:

.. code-block:: python

   """Quantum chemistry domain module."""

   from qdk_pythonic.domains.chemistry.molecule import Molecule
   from qdk_pythonic.domains.chemistry.vqe import VQEAnsatz

   __all__ = ["Molecule", "VQEAnsatz"]

Design Contract
---------------

Domain objects should follow these conventions:

1. **Produce circuits via ``to_circuit()``** -- this is the standard
   interface. Any class with a ``to_circuit() -> Circuit`` method
   satisfies the :class:`~qdk_pythonic.core.protocols.CircuitProducer`
   protocol.

2. **Produce Hamiltonians via ``to_hamiltonian()``** when the domain
   involves a Hamiltonian that can be further processed (e.g., by
   ``TrotterEvolution``).

3. **Return plain Circuit objects** -- users should be able to call
   ``to_qsharp()``, ``run()``, ``estimate()``, ``draw()``, etc. on the
   result without any special handling.

Using Shared Primitives
-----------------------

Import building blocks from ``domains.common``:

.. code-block:: python

   from qdk_pythonic.core.circuit import Circuit
   from qdk_pythonic.domains.common.operators import (
       PauliHamiltonian,
       PauliTerm,
       X,
       Y,
       Z,
   )
   from qdk_pythonic.domains.common.evolution import TrotterEvolution
   from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz

Example: a molecule class that builds a Hamiltonian and an evolution
circuit:

.. code-block:: python

   class Molecule:
       def __init__(self, coefficients: list[tuple[float, str, list[int]]]):
           self._coefficients = coefficients

       def to_hamiltonian(self) -> PauliHamiltonian:
           terms = []
           pauli_map = {"X": X, "Y": Y, "Z": Z}
           for coeff, pauli, qubits in self._coefficients:
               term = coeff * pauli_map[pauli](qubits[0])
               for q in qubits[1:]:
                   term = term * pauli_map[pauli](q)
               terms.append(term)
           return PauliHamiltonian(terms)

       def to_circuit(self, dt: float = 0.1, steps: int = 1) -> Circuit:
           h = self.to_hamiltonian()
           evol = TrotterEvolution(h)
           return evol.to_circuit(dt=dt, steps=steps)

Follow Existing Patterns
------------------------

Look at existing domain modules for reference:

- **``domains/optimization/``**: ``problem.py`` encodes combinatorial
  problems, ``qaoa.py`` constructs QAOA circuits, ``mixer.py`` provides
  mixer Hamiltonians.
- **``domains/condensed_matter/``**: ``lattice.py`` defines geometries,
  ``models.py`` builds Hamiltonians, ``simulation.py`` produces
  time-evolution circuits.

Testing
-------

Add a test file ``tests/unit/test_domain_<name>.py`` with
``@pytest.mark.unit`` markers. Test the circuit output rather than exact
instruction sequences:

.. code-block:: python

   @pytest.mark.unit
   def test_molecule_circuit():
       mol = Molecule([(1.0, "Z", [0, 1]), (0.5, "X", [0])])
       circ = mol.to_circuit(dt=0.1, steps=2)
       assert circ.qubit_count() >= 2
       assert circ.total_gate_count() > 0
       assert circ.depth() > 0

Documentation
-------------

1. Add an API reference stub at ``docs/api/domains_<name>.rst``:

   .. code-block:: rst

      Chemistry
      =========

      .. automodule:: qdk_pythonic.domains.chemistry
         :members:
         :show-inheritance:

2. Add a tutorial at ``docs/tutorials/<name>.rst`` with worked examples.

3. Add both files to the appropriate ``toctree`` blocks in
   ``docs/index.rst``.
