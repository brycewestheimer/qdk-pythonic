"""Fermion-to-qubit mappings.

Provides Jordan-Wigner and Bravyi-Kitaev transformations from
:class:`FermionOperator` to :class:`PauliHamiltonian`.

Example::

    from qdk_pythonic.domains.common.fermion import number_operator
    from qdk_pythonic.domains.common.mapping import jordan_wigner

    pauli_h = jordan_wigner(number_operator(0))
    pauli_h.print_summary()
"""

from __future__ import annotations

from itertools import product as cartesian_product
from typing import Any, Protocol, runtime_checkable

from qdk_pythonic.domains.common.fermion import FermionOperator, FermionTerm
from qdk_pythonic.domains.common.operators import (
    PauliHamiltonian,
    PauliTerm,
    pauli_identity,
    pauli_multiply,
)
from qdk_pythonic.registry import Algorithm


@runtime_checkable
class QubitMapping(Protocol):
    """Protocol for fermion-to-qubit transformations."""

    def map(self, operator: FermionOperator) -> PauliHamiltonian: ...


# ── Jordan-Wigner ──


class JordanWignerMapping:
    """Jordan-Wigner fermion-to-qubit mapping.

    Maps each fermionic mode to one qubit. Qubit j stores the
    occupation of mode j.

    Transformation rules:
        a-dagger_j -> 0.5 (X_j - iY_j) Z_{j-1} ... Z_0
        a_j        -> 0.5 (X_j + iY_j) Z_{j-1} ... Z_0
    """

    def map(self, operator: FermionOperator) -> PauliHamiltonian:
        """Transform a fermionic operator to a qubit Hamiltonian."""
        result = PauliHamiltonian()
        for term in operator.terms:
            result += self._map_term(term)
        return result.simplify()

    def _map_term(self, term: FermionTerm) -> PauliHamiltonian:
        """Map a single FermionTerm to Pauli terms."""
        if not term.operators:
            # Identity term (e.g. nuclear repulsion)
            return PauliHamiltonian([pauli_identity() * term.coeff])

        # Each ladder operator maps to a sum of two Pauli strings.
        # Build the Cartesian product and multiply each combination.
        per_op_terms = [
            self._map_ladder(mode, is_creation)
            for mode, is_creation in term.operators
        ]

        result = PauliHamiltonian()
        for combo in cartesian_product(*per_op_terms):
            merged = combo[0]
            for p in combo[1:]:
                merged = pauli_multiply(merged, p)
            result += PauliTerm(
                pauli_ops=dict(merged.pauli_ops),
                coeff=merged.coeff * term.coeff,
            )
        return result

    def _map_ladder(
        self, mode: int, is_creation: bool,
    ) -> list[PauliTerm]:
        """Map a single creation or annihilation operator.

        a-dagger_j = 0.5 (X_j - iY_j) prod_{k<j} Z_k
        a_j        = 0.5 (X_j + iY_j) prod_{k<j} Z_k
        """
        z_string: dict[int, str] = {k: "Z" for k in range(mode)}

        x_ops = dict(z_string)
        x_ops[mode] = "X"

        y_ops = dict(z_string)
        y_ops[mode] = "Y"

        sign = -1j if is_creation else 1j
        return [
            PauliTerm(pauli_ops=x_ops, coeff=0.5),
            PauliTerm(pauli_ops=y_ops, coeff=0.5 * sign),
        ]


# ── Bravyi-Kitaev ──


class BravyiKitaevMapping:
    """Bravyi-Kitaev fermion-to-qubit mapping.

    Uses a binary tree encoding to reduce Pauli weight from
    O(N) (Jordan-Wigner) to O(log N).

    Reference: Seeley, Richard, Love (2012).
    """

    def map(self, operator: FermionOperator) -> PauliHamiltonian:
        """Transform a fermionic operator to a qubit Hamiltonian."""
        result = PauliHamiltonian()
        n_modes = operator.num_modes
        for term in operator.terms:
            result += self._map_term(term, n_modes)
        return result.simplify()

    def _map_term(
        self, term: FermionTerm, n_modes: int,
    ) -> PauliHamiltonian:
        """Map a single FermionTerm to Pauli terms."""
        if not term.operators:
            return PauliHamiltonian([pauli_identity() * term.coeff])

        per_op_terms = [
            self._map_ladder(mode, is_creation, n_modes)
            for mode, is_creation in term.operators
        ]

        result = PauliHamiltonian()
        for combo in cartesian_product(*per_op_terms):
            merged = combo[0]
            for p in combo[1:]:
                merged = pauli_multiply(merged, p)
            result += PauliTerm(
                pauli_ops=dict(merged.pauli_ops),
                coeff=merged.coeff * term.coeff,
            )
        return result

    def _map_ladder(
        self, mode: int, is_creation: bool, n_modes: int,
    ) -> list[PauliTerm]:
        """Map a single ladder operator under BK encoding."""
        update = self._update_set(mode, n_modes)
        parity = self._parity_set(mode)
        remainder = update - {mode}

        # Build the X-part and Y-part Pauli strings.
        # Convention from Seeley et al. (2012):
        #   a†_j + a_j  -> X_j * prod(X on update\\{j}) * prod(Z on parity)
        #   i(a†_j - a_j) depends on parity structure

        # X component: X on mode, X on remainder, Z on parity set
        x_ops: dict[int, str] = {mode: "X"}
        for k in remainder:
            x_ops[k] = "X"
        for k in parity:
            if k in x_ops:
                # X * Z = -iY
                x_ops[k] = "Y"
            else:
                x_ops[k] = "Z"

        # Y component: Y on mode, X on remainder, Z on parity set
        y_ops: dict[int, str] = {mode: "Y"}
        for k in remainder:
            y_ops[k] = "X"
        for k in parity:
            if k == mode:
                # Y * Z = iX  (but we already set Y, need to compose)
                y_ops[k] = "X"
            elif k in y_ops:
                # X * Z = -iY
                y_ops[k] = "Y"
            else:
                y_ops[k] = "Z"

        # Fix phases: we need to track how many X*Z and Y*Z products
        # we did to get the accumulated phase right.
        # Recompute cleanly using pauli_multiply.
        x_term = self._build_from_sets(
            mode, "X", remainder, parity,
        )
        y_term = self._build_from_sets(
            mode, "Y", remainder, parity,
        )

        sign = -1j if is_creation else 1j
        return [
            PauliTerm(
                pauli_ops=dict(x_term.pauli_ops),
                coeff=0.5 * x_term.coeff,
            ),
            PauliTerm(
                pauli_ops=dict(y_term.pauli_ops),
                coeff=0.5 * sign * y_term.coeff,
            ),
        ]

    def _build_from_sets(
        self,
        mode: int,
        base_pauli: str,
        remainder: set[int],
        parity: set[int],
    ) -> PauliTerm:
        """Build a PauliTerm from BK update/parity sets.

        Multiplies: base_pauli on mode * X on each remainder
        qubit * Z on each parity qubit.
        """
        result = PauliTerm(pauli_ops={mode: base_pauli})
        for k in sorted(remainder):
            result = pauli_multiply(
                result, PauliTerm(pauli_ops={k: "X"}),
            )
        for k in sorted(parity):
            result = pauli_multiply(
                result, PauliTerm(pauli_ops={k: "Z"}),
            )
        return result

    @staticmethod
    def _update_set(j: int, n: int) -> set[int]:
        """Qubits whose value must flip when mode j changes.

        In the BK encoding these are the ancestors of j in the
        Fenwick (binary indexed) tree.
        """
        result: set[int] = set()
        idx = j
        while idx < n:
            result.add(idx)
            # Move to parent in Fenwick tree
            idx |= idx + 1
        return result

    @staticmethod
    def _parity_set(j: int) -> set[int]:
        """Qubits encoding parity of modes 0..j-1.

        In the BK tree, these are the children in the left subtree
        of j, i.e. the bits we need to XOR to recover occupation
        parity up to mode j.
        """
        result: set[int] = set()
        if j == 0:
            return result
        idx = j - 1
        while idx >= 0 and idx not in result:
            result.add(idx)
            # Move to the "parent" of idx in terms of parity
            if idx == 0:
                break
            # Clear the lowest set bit to traverse the tree
            idx = (idx & (idx + 1)) - 1
            if idx < 0:
                break
        return result


# ── Convenience functions ──


def jordan_wigner(operator: FermionOperator) -> PauliHamiltonian:
    """Map a fermionic operator to qubits via Jordan-Wigner."""
    return JordanWignerMapping().map(operator)


def bravyi_kitaev(operator: FermionOperator) -> PauliHamiltonian:
    """Map a fermionic operator to qubits via Bravyi-Kitaev."""
    return BravyiKitaevMapping().map(operator)


# ── Registry integration (Phase 4) ──


class JordanWignerMapper(Algorithm):
    """Algorithm wrapper for JW mapping.

    Registered type: ``"qubit_mapper"``
    Registered name: ``"jordan_wigner"``
    """

    def type_name(self) -> str:
        return "qubit_mapper"

    def name(self) -> str:
        return "jordan_wigner"

    def aliases(self) -> list[str]:
        return ["jordan_wigner", "jw"]

    def _run_impl(self, operator: Any, **kwargs: Any) -> Any:
        return JordanWignerMapping().map(operator)


class BravyiKitaevMapper(Algorithm):
    """Algorithm wrapper for BK mapping.

    Registered type: ``"qubit_mapper"``
    Registered name: ``"bravyi_kitaev"``
    """

    def type_name(self) -> str:
        return "qubit_mapper"

    def name(self) -> str:
        return "bravyi_kitaev"

    def aliases(self) -> list[str]:
        return ["bravyi_kitaev", "bk"]

    def _run_impl(self, operator: Any, **kwargs: Any) -> Any:
        return BravyiKitaevMapping().map(operator)


def load_mappings() -> None:
    """Register qubit mapping algorithms with the global registry."""
    from qdk_pythonic.registry import register

    register(lambda: JordanWignerMapper())
    register(lambda: BravyiKitaevMapper())
