"""External package adapters for qdk-pythonic.

Adapters translate domain-native objects into qdk-pythonic primitives
(PauliHamiltonian, MaxCut, QAOA, etc.), which then flow through the
standard circuit/codegen/estimation pipeline.

Each adapter follows the QDK/Chemistry plugin pattern: a ``load()``
function that registers Algorithm implementations with the global
registry.

Available adapters:

- ``quspin_adapter`` -- Convert QuSpin Hamiltonians to PauliHamiltonian.
  Requires ``pip install qdk-pythonic[quspin]``.
- ``networkx_adapter`` -- Convert NetworkX graphs to QAOA circuits.
  Requires ``pip install qdk-pythonic[networkx]``.
"""

import contextlib

# Auto-load adapters for available packages.
# Mirrors qdk_chemistry.__init__._import_plugins().

with contextlib.suppress(ImportError):
    from qdk_pythonic.adapters.quspin_algorithms import load as _load_quspin

    _load_quspin()

with contextlib.suppress(ImportError):
    from qdk_pythonic.adapters.networkx_algorithms import (
        load as _load_networkx,
    )

    _load_networkx()

