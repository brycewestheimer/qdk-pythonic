"""Common quantum primitives shared across domains.

Re-exports the key types from sub-modules for convenient access::

    from qdk_pythonic.domains.common import PauliHamiltonian, TrotterEvolution
"""

from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz
from qdk_pythonic.domains.common.evolution import TrotterEvolution
from qdk_pythonic.domains.common.operators import (
    PauliHamiltonian,
    PauliTerm,
    X,
    Y,
    Z,
)
from qdk_pythonic.domains.common.states import (
    BasisState,
    DiscreteProbabilityDistribution,
    UniformSuperposition,
)

__all__ = [
    "BasisState",
    "DiscreteProbabilityDistribution",
    "HardwareEfficientAnsatz",
    "PauliHamiltonian",
    "PauliTerm",
    "TrotterEvolution",
    "UniformSuperposition",
    "X",
    "Y",
    "Z",
]
