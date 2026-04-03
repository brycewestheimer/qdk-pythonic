"""Expectation value measurement for Pauli Hamiltonians.

Computes ``<psi|H|psi>`` by decomposing the Hamiltonian into Pauli
terms and measuring each in the appropriate basis.

Example::

    from qdk_pythonic.domains.chemistry.expectation import (
        pauli_expectation_value,
    )

    energy = pauli_expectation_value(hamiltonian, circuit, shots=10000)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


def pauli_expectation_value(
    hamiltonian: PauliHamiltonian,
    circuit: Circuit,
    shots: int = 10000,
    seed: int | None = None,
) -> float:
    """Compute ``<psi|H|psi>`` via Pauli term measurements.

    For each Pauli term ``c_k * P_k``, measures the circuit in the
    eigenbasis of ``P_k`` and computes the expectation value. The
    total energy is ``sum(c_k * <P_k>)``.

    Identity terms contribute their coefficient directly.

    Args:
        hamiltonian: The Hamiltonian to measure.
        circuit: The state preparation circuit.
        shots: Number of measurement shots per term group.
        seed: Optional random seed.

    Returns:
        The expectation value as a float.
    """
    groups = group_commuting_terms(hamiltonian)
    total_energy = 0.0

    for group in groups:
        # Check if group is all-identity terms
        all_identity = all(not t.pauli_ops for t in group)
        if all_identity:
            for term in group:
                total_energy += term.coeff.real
            continue

        # Build measurement circuit for this group
        meas_circ = _build_measurement_circuit(circuit, group)
        results = meas_circ.run(shots=shots, seed=seed)

        # Compute expectation for each term from the shared results
        for term in group:
            if not term.pauli_ops:
                total_energy += term.coeff.real
                continue
            total_energy += term.coeff.real * _expectation_from_results(
                term, results,
            )

    return total_energy


def group_commuting_terms(
    hamiltonian: PauliHamiltonian,
) -> list[list[PauliTerm]]:
    """Group Pauli terms into qubit-wise commuting sets.

    Terms in the same group can be measured simultaneously because
    they share a common eigenbasis. Uses a greedy bin-packing
    strategy.

    Args:
        hamiltonian: The Hamiltonian whose terms to group.

    Returns:
        List of groups, each group a list of commuting PauliTerms.
    """
    groups: list[list[PauliTerm]] = []

    for term in hamiltonian.terms:
        placed = False
        for group in groups:
            if _qubitwise_commutes_with_group(term, group):
                group.append(term)
                placed = True
                break
        if not placed:
            groups.append([term])

    return groups


def _qubitwise_commutes_with_group(
    term: PauliTerm,
    group: list[PauliTerm],
) -> bool:
    """Check if a term qubit-wise commutes with all terms in a group.

    Two Pauli terms qubit-wise commute if, on every qubit where
    both act non-trivially, they use the same Pauli operator.
    """
    for existing in group:
        for qi, op in term.pauli_ops.items():
            other_op = existing.pauli_ops.get(qi)
            if other_op is not None and other_op != op:
                return False
    return True


def _build_measurement_circuit(
    state_circuit: Circuit,
    group: list[PauliTerm],
) -> Circuit:
    """Build a circuit that measures a commuting group of Pauli terms.

    Appends basis-change gates (H for X, Rx(-pi/2) for Y) and
    measurements to a copy of the state circuit.
    """
    from qdk_pythonic.core.circuit import Circuit

    n_qubits = state_circuit.qubit_count()
    circ = Circuit()
    q = circ.allocate(n_qubits)

    # Copy state preparation
    state_map = {
        src.index: q[i]
        for i, src in enumerate(state_circuit.qubits)
    }
    circ.compose_into(state_circuit, qubit_map=state_map)

    # Determine which qubits need basis changes and what basis
    qubit_basis: dict[int, str] = {}
    for term in group:
        for qi, op in term.pauli_ops.items():
            if qi in qubit_basis:
                # Should be the same (qubit-wise commuting)
                continue
            qubit_basis[qi] = op

    # Apply basis-change gates
    for qi, op in sorted(qubit_basis.items()):
        if op == "X":
            circ.h(q[qi])
        elif op == "Y":
            circ.rx(-math.pi / 2, q[qi])
        # Z needs no basis change

    # Measure all relevant qubits
    measured_qubits = sorted(qubit_basis.keys())
    for qi in measured_qubits:
        circ.measure(q[qi])

    return circ


def _expectation_from_results(
    term: PauliTerm,
    results: list[object],
) -> float:
    """Compute the expectation value of a Pauli term from measurement results.

    Each shot gives eigenvalue +1 or -1 depending on the parity
    of the measured qubits in the Pauli string.
    """
    if not results:
        return 0.0

    total = 0.0
    n_shots = len(results)
    term_qubits = sorted(term.pauli_ops.keys())

    for shot_result in results:
        # shot_result is a list of MeasurementResult objects
        parity = 0
        if isinstance(shot_result, list):
            for meas in shot_result:
                if hasattr(meas, "qubit") and hasattr(meas, "value"):
                    if meas.qubit.index in term_qubits and meas.value == 1:
                        parity ^= 1
        # Eigenvalue: (-1)^parity
        total += 1.0 - 2.0 * parity

    return total / n_shots
