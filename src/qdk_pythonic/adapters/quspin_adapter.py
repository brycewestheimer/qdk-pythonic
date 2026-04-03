"""Adapter for QuSpin quantum many-body Hamiltonians.

Converts QuSpin operator specifications into
:class:`~qdk_pythonic.domains.common.operators.PauliHamiltonian` objects
that flow through the standard qdk-pythonic circuit/estimation pipeline.

The core conversion function :func:`from_quspin_static_list` is pure
Python and does not require QuSpin to be installed.  Only
:func:`from_quspin_hamiltonian` needs a live QuSpin import.

Example::

    from qdk_pythonic.adapters.quspin_adapter import simulate_quspin_model

    static = [["zz", [[1.0, 0, 1]]], ["x", [[0.5, 0], [0.5, 1]]]]
    result = simulate_quspin_model(static, n_sites=2, time=1.0, trotter_steps=5)
"""

from __future__ import annotations

import warnings
from typing import Any

from qdk_pythonic.domains.common.evolution import TrotterEvolution
from qdk_pythonic.domains.common.operators import PauliHamiltonian, PauliTerm

# ── Mapping from QuSpin operator strings to Pauli operators ──

# QuSpin uses spin-1/2 operators: "x", "y", "z", "+", "-", "I"
# Single-character labels map directly to Pauli labels.
# Multi-character strings like "zz" are tensor products.

QUSPIN_TO_PAULI: dict[str, str] = {
    "x": "X",
    "y": "Y",
    "z": "Z",
    "I": "I",
}


def _parse_quspin_operator_string(op_str: str) -> list[str]:
    """Parse a QuSpin operator string into per-site Pauli labels.

    Args:
        op_str: Concatenated operator characters, e.g. ``"zz"``,
            ``"x"``, ``"+-"``.

    Returns:
        List of Pauli labels (``"X"``, ``"Y"``, ``"Z"``, ``"I"``,
        ``"+"``, or ``"-"``).

    Raises:
        ValueError: If an unrecognised character is encountered.
    """
    paulis: list[str] = []
    for char in op_str:
        if char in QUSPIN_TO_PAULI:
            paulis.append(QUSPIN_TO_PAULI[char])
        elif char in ("+", "-"):
            paulis.append(char)
        else:
            raise ValueError(f"Unknown QuSpin operator character: '{char}'")
    return paulis


def _expand_ladder_operators(
    paulis: list[str],
    sites: list[int],
    coefficient: complex,
) -> list[tuple[complex, dict[int, str]]]:
    """Expand ladder operators (+/-) into X/Y Pauli components.

    S+_j = (X_j + iY_j) / 2,  S-_j = (X_j - iY_j) / 2.

    A term like J * S+_i S-_j expands via the Cartesian product of
    per-site decompositions.

    Args:
        paulis: Per-site labels, possibly containing ``"+"`` / ``"-"``.
        sites: Qubit indices corresponding to each label.
        coefficient: Overall numerical coefficient.

    Returns:
        List of ``(coeff, {site: pauli})`` tuples.  The coefficients
        may be complex.
    """
    if "+" not in paulis and "-" not in paulis:
        pauli_dict = {site: p for site, p in zip(sites, paulis) if p != "I"}
        return [(coefficient, pauli_dict)]

    # Build per-site expansion lists: each site contributes a list of
    # (factor, pauli_label) pairs.
    site_expansions: list[list[tuple[complex, str]]] = []
    for p in paulis:
        if p == "+":
            site_expansions.append([(0.5, "X"), (0.5j, "Y")])
        elif p == "-":
            site_expansions.append([(0.5, "X"), (-0.5j, "Y")])
        else:
            site_expansions.append([(1.0, p)])

    results: list[tuple[complex, dict[int, str]]] = []
    _expand_recursive(site_expansions, sites, 0, coefficient, {}, results)
    return results


def _expand_recursive(
    expansions: list[list[tuple[complex, str]]],
    sites: list[int],
    depth: int,
    running_coeff: complex,
    running_paulis: dict[int, str],
    results: list[tuple[complex, dict[int, str]]],
) -> None:
    """Recursively build the Cartesian product of per-site expansions."""
    if depth == len(expansions):
        if abs(running_coeff) > 1e-15:
            results.append((running_coeff, dict(running_paulis)))
        return

    for factor, pauli in expansions[depth]:
        new_paulis = dict(running_paulis)
        if pauli != "I":
            new_paulis[sites[depth]] = pauli
        _expand_recursive(
            expansions, sites, depth + 1,
            running_coeff * factor, new_paulis, results,
        )


# ═══════════════════════════════════════════════════════════
# Core Conversion Functions
# ═══════════════════════════════════════════════════════════


def from_quspin_static_list(
    static_list: list[list[Any]],
    n_sites: int,
) -> PauliHamiltonian:
    """Convert a QuSpin static operator list to a PauliHamiltonian.

    QuSpin ``static_list`` format::

        [
            ["zz", [[J, i, j], [J, i, j], ...]],   # ZZ interactions
            ["x",  [[h, i], [h, i], ...]],           # X field terms
            ...
        ]

    Each entry is ``[operator_string, coupling_list]`` where each element
    of *coupling_list* is ``[coefficient, site_0, site_1, ...]``.

    This function is pure Python and does **not** require QuSpin.

    Args:
        static_list: QuSpin-format static operator specification.
        n_sites: Number of lattice sites (= number of qubits).

    Returns:
        A PauliHamiltonian ready for Trotterisation or direct use.

    Raises:
        ValueError: If operator string or site counts are inconsistent.
    """
    hamiltonian = PauliHamiltonian()

    for op_str, coupling_list in static_list:
        pauli_labels = _parse_quspin_operator_string(op_str)
        n_sites_per_term = len(pauli_labels)

        for coupling_entry in coupling_list:
            coeff = complex(coupling_entry[0])
            sites = [int(s) for s in coupling_entry[1:]]

            if len(sites) != n_sites_per_term:
                raise ValueError(
                    f"Operator '{op_str}' expects {n_sites_per_term} "
                    f"sites, got {len(sites)} in coupling entry "
                    f"{coupling_entry}"
                )

            expanded = _expand_ladder_operators(pauli_labels, sites, coeff)

            for term_coeff, pauli_dict in expanded:
                if pauli_dict:  # skip pure-identity terms
                    hamiltonian += PauliTerm(
                        pauli_ops=pauli_dict,
                        coeff=term_coeff,
                    )

    return hamiltonian


def from_quspin_hamiltonian(
    quspin_ham: Any,
    n_sites: int,
) -> PauliHamiltonian:
    """Convert a QuSpin ``hamiltonian`` object to a PauliHamiltonian.

    Extracts the static operator list from the QuSpin hamiltonian and
    converts it.  Dynamic (time-dependent) terms are evaluated at t=0
    and included as static contributions with a warning.

    Args:
        quspin_ham: A constructed ``quspin.operators.hamiltonian`` object.
        n_sites: Number of lattice sites.

    Returns:
        A PauliHamiltonian.

    Raises:
        ImportError: If QuSpin is not installed.
    """
    try:
        import quspin.operators  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        raise ImportError(
            "QuSpin is required for from_quspin_hamiltonian(). "
            "Install it with: pip install qdk-pythonic[quspin]"
        ) from None

    pauli_h = from_quspin_static_list(quspin_ham.static_list, n_sites)

    if hasattr(quspin_ham, "dynamic_list") and quspin_ham.dynamic_list:
        warnings.warn(
            "QuSpin Hamiltonian has dynamic (time-dependent) terms. "
            "These are evaluated at t=0 and included as static terms. "
            "For time-dependent simulation, build separate "
            "PauliHamiltonians for each time step.",
            UserWarning,
            stacklevel=2,
        )
        for op_str, coupling_list, *_rest in quspin_ham.dynamic_list:
            dynamic_h = from_quspin_static_list(
                [[op_str, coupling_list]], n_sites,
            )
            for term in dynamic_h.terms:
                pauli_h += term

    return pauli_h


# ═══════════════════════════════════════════════════════════
# High-Level Convenience Functions
# ═══════════════════════════════════════════════════════════


def simulate_quspin_model(
    static_list: list[list[Any]],
    n_sites: int,
    time: float = 1.0,
    trotter_steps: int = 10,
    trotter_order: int = 1,
    estimate_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One-call QuSpin model to quantum resource estimation.

    Takes a QuSpin operator specification and returns a complete
    analysis including the circuit, gate counts, depth, and
    (optionally) resource estimation results.

    Args:
        static_list: QuSpin-format static operator specification.
        n_sites: Number of lattice sites.
        time: Total evolution time.
        trotter_steps: Number of Trotter steps.
        trotter_order: Trotter-Suzuki order (1 or 2).
        estimate_params: Hardware configuration for resource estimation.
            If ``None``, estimation is skipped.

    Returns:
        A dict with keys ``hamiltonian``, ``circuit``, ``n_qubits``,
        ``gate_count``, ``total_gates``, ``depth``,
        ``n_hamiltonian_terms``, and optionally ``estimate_result``.
    """
    hamiltonian = from_quspin_static_list(static_list, n_sites)

    evolution = TrotterEvolution(
        hamiltonian=hamiltonian,
        time=time,
        steps=trotter_steps,
        order=trotter_order,
    )
    circuit = evolution.to_circuit()

    result: dict[str, Any] = {
        "hamiltonian": hamiltonian,
        "circuit": circuit,
        "n_qubits": circuit.qubit_count(),
        "gate_count": circuit.gate_count(),
        "total_gates": circuit.total_gate_count(),
        "depth": circuit.depth(),
        "n_hamiltonian_terms": len(hamiltonian.terms),
    }

    if estimate_params is not None:
        result["estimate_result"] = circuit.estimate(params=estimate_params)

    return result
