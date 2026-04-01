"""Mixer Hamiltonians for QAOA.

Example::

    from qdk_pythonic.domains.optimization.mixer import x_mixer

    mixer = x_mixer(4)  # X-mixer on 4 qubits
"""

from __future__ import annotations

from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm


def x_mixer(n_qubits: int) -> PauliHamiltonian:
    """Build the standard X-mixer Hamiltonian for QAOA.

    B = sum_i X_i

    Args:
        n_qubits: Number of qubits.

    Returns:
        The mixer Hamiltonian.
    """
    ham = PauliHamiltonian()
    for i in range(n_qubits):
        ham += PauliTerm(pauli_ops={i: "X"}, coeff=1.0)
    return ham
