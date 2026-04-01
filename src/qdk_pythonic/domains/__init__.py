"""Domain-specific quantum computing abstractions.

Subpackages provide domain objects that map to quantum circuits via
``to_circuit()`` or ``to_hamiltonian()`` methods.

Available domains:

- ``common`` -- Pauli operators, Hamiltonians, Trotter evolution, ansatze
- ``condensed_matter`` -- Lattice models (Ising, Heisenberg)
- ``optimization`` -- Combinatorial problems and QAOA
- ``finance`` -- Quantum amplitude estimation and option pricing
- ``ml`` -- Quantum feature encoding and kernels
"""
