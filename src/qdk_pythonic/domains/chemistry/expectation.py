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
import uuid
from typing import TYPE_CHECKING, Any

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

    Measurement circuits for commuting Pauli groups are compiled
    in a single batch to reduce Q# compilation overhead.

    Args:
        hamiltonian: The Hamiltonian to measure.
        circuit: The state preparation circuit.
        shots: Number of measurement shots per term group.
        seed: Optional random seed.

    Returns:
        The expectation value as a float.
    """
    groups = group_commuting_terms(hamiltonian)

    # Separate identity groups from measurement groups
    identity_energy = 0.0
    measurement_groups: list[list[PauliTerm]] = []
    for group in groups:
        if all(not t.pauli_ops for t in group):
            for term in group:
                identity_energy += term.coeff.real
        else:
            measurement_groups.append(group)

    if not measurement_groups:
        return identity_energy

    # Build all measurement circuits
    circuits: list[Circuit] = []
    for group in measurement_groups:
        circuits.append(_build_measurement_circuit(circuit, group))

    # Batch-run all circuits
    all_results = _batch_run_circuits(circuits, shots=shots, seed=seed)

    # Compute expectation values from results
    total_energy = identity_energy
    for group, results in zip(measurement_groups, all_results):
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

    # Measure ALL qubits so the Q# runtime can release them.
    # MResetZ resets each qubit to |0> after measurement, which
    # is required by the Q# qubit release semantics.
    for qi in range(n_qubits):
        circ.measure(q[qi])

    return circ


def _batch_run_circuits(
    circuits: list[Circuit],
    shots: int,
    seed: int | None = None,
) -> list[list[Any]]:
    """Compile and run multiple circuits with a single Q# eval call.

    Generates all Q# operations in one code block, compiles them
    in a single ``qsharp.eval()`` call, then runs each separately.
    This reduces per-circuit compilation overhead compared to
    calling ``circuit.run()`` on each independently.

    Args:
        circuits: List of circuits to run.
        shots: Number of shots per circuit.
        seed: Optional random seed.

    Returns:
        List of result lists, one per circuit.
    """
    from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator
    from qdk_pythonic.exceptions import ExecutionError
    from qdk_pythonic.execution._compat import import_qsharp

    qsharp = import_qsharp()
    generator = QSharpCodeGenerator()

    batch_id = uuid.uuid4().hex[:6]
    op_names: list[str] = []
    code_blocks: list[str] = []

    for i, circ in enumerate(circuits):
        name = f"_qdk_batch_{batch_id}_{i}"
        op_names.append(name)
        code_blocks.append(generator.generate_operation(name, circ))

    # Single eval for all operations
    combined_code = "\n".join(code_blocks)
    try:
        qsharp.eval(combined_code)
    except Exception as e:
        raise ExecutionError(
            f"Batch Q# compilation failed: {e}"
        ) from e

    # Run each operation
    all_results: list[list[Any]] = []
    run_kwargs: dict[str, Any] = {"shots": shots}
    if seed is not None:
        run_kwargs["seed"] = seed

    for name in op_names:
        try:
            results = qsharp.run(f"{name}()", **run_kwargs)
            result_list = (
                list(results) if not isinstance(results, list)
                else results
            )
            all_results.append(result_list)
        except Exception as e:
            raise ExecutionError(
                f"Batch simulation failed for '{name}': {e}"
            ) from e

    return all_results


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
