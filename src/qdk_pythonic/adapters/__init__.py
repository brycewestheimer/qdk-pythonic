"""External package adapters for qdk-pythonic.

Adapters translate domain-native objects into qdk-pythonic primitives
(PauliHamiltonian, MaxCut, QAOA, etc.), which then flow through the
standard circuit/codegen/estimation pipeline.

Available adapters:

- ``quspin_adapter`` -- Convert QuSpin Hamiltonians to PauliHamiltonian.
  Requires ``pip install qdk-pythonic[quspin]``.
- ``networkx_adapter`` -- Convert NetworkX graphs to QAOA circuits.
  Requires ``pip install qdk-pythonic[networkx]``.
"""
