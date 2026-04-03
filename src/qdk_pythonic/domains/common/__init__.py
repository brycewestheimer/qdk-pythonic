"""Common quantum primitives shared across domains.

Re-exports the key types from sub-modules for convenient access::

    from qdk_pythonic.domains.common import PauliHamiltonian, TrotterEvolution
"""

from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz
from qdk_pythonic.domains.common.double_factorization import (
    DoubleFactorizedHamiltonian,
    double_factorize,
)
from qdk_pythonic.domains.common.evolution import TrotterEvolution
from qdk_pythonic.domains.common.fermion import (
    FermionOperator,
    FermionTerm,
    annihilation,
    creation,
    from_integrals,
    hopping,
    number_operator,
)
from qdk_pythonic.domains.common.lcu import (
    PrepareOracle,
    QubitizationQPE,
    QubitizationWalkOperator,
    SelectOracle,
)
from qdk_pythonic.domains.common.mapping import (
    BravyiKitaevMapping,
    JordanWignerMapping,
    bravyi_kitaev,
    jordan_wigner,
    load_mappings,
)
from qdk_pythonic.domains.common.operators import (
    PauliHamiltonian,
    PauliTerm,
    X,
    Y,
    Z,
    pauli_identity,
    pauli_multiply,
)
from qdk_pythonic.domains.common.states import (
    BasisState,
    DiscreteProbabilityDistribution,
    UniformSuperposition,
)

# Register qubit mapping algorithms with the global registry.
load_mappings()

__all__ = [
    "BasisState",
    "BravyiKitaevMapping",
    "DoubleFactorizedHamiltonian",
    "DiscreteProbabilityDistribution",
    "FermionOperator",
    "FermionTerm",
    "HardwareEfficientAnsatz",
    "JordanWignerMapping",
    "PauliHamiltonian",
    "PauliTerm",
    "PrepareOracle",
    "QubitizationQPE",
    "QubitizationWalkOperator",
    "SelectOracle",
    "TrotterEvolution",
    "UniformSuperposition",
    "X",
    "Y",
    "Z",
    "annihilation",
    "bravyi_kitaev",
    "double_factorize",
    "creation",
    "from_integrals",
    "hopping",
    "jordan_wigner",
    "load_mappings",
    "number_operator",
    "pauli_identity",
    "pauli_multiply",
]
