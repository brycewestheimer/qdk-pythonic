"""Quantum chemistry algorithms and utilities.

Provides chemistry-specific quantum algorithm implementations that
mirror the Microsoft qdk-chemistry workflow: molecular Hamiltonian
construction, Hartree-Fock state preparation, UCCSD ansatz, QPE,
VQE, qubitization, and FCIDUMP interoperability.

Example::

    from qdk_pythonic.domains.chemistry import (
        HartreeFockState, UCCSDAnsatz, ChemistryQPE,
        ChemistryQubitization,
    )
"""

from qdk_pythonic.domains.chemistry.expectation import (
    group_commuting_terms,
    pauli_expectation_value,
)
from qdk_pythonic.domains.chemistry.fcidump import (
    FCIDUMPData,
    read_fcidump,
    write_fcidump,
)
from qdk_pythonic.domains.chemistry.hartree_fock import HartreeFockState
from qdk_pythonic.domains.chemistry.orbital_info import MolecularOrbitalInfo
from qdk_pythonic.domains.chemistry.qpe import ChemistryQPE
from qdk_pythonic.domains.chemistry.qubitization import ChemistryQubitization
from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz
from qdk_pythonic.domains.chemistry.vqe import VQE, VQEResult
from qdk_pythonic.domains.common.double_factorization import (
    DoubleFactorizedHamiltonian,
)
from qdk_pythonic.execution.chemistry_estimate import (
    ChemistryResourceEstimate,
)

__all__ = [
    "ChemistryQPE",
    "ChemistryQubitization",
    "ChemistryResourceEstimate",
    "DoubleFactorizedHamiltonian",
    "FCIDUMPData",
    "HartreeFockState",
    "MolecularOrbitalInfo",
    "UCCSDAnsatz",
    "VQE",
    "VQEResult",
    "group_commuting_terms",
    "pauli_expectation_value",
    "read_fcidump",
    "write_fcidump",
]
