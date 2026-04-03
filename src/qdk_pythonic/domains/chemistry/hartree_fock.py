"""Hartree-Fock reference state preparation.

Prepares the computational-basis state corresponding to the
Hartree-Fock ground state under a given qubit mapping.

Example::

    from qdk_pythonic.domains.chemistry.hartree_fock import HartreeFockState

    hf = HartreeFockState(n_qubits=4, n_electrons=2)
    circuit = hf.to_circuit()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qdk_pythonic.exceptions import CircuitError

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit

_VALID_MAPPINGS = frozenset({"jordan_wigner", "bravyi_kitaev"})


@dataclass(frozen=True)
class HartreeFockState:
    """Prepare the Hartree-Fock reference state.

    Under Jordan-Wigner, qubit *j* stores the occupation of
    spin-orbital *j*, so the HF state is ``|1...10...0>`` with
    the first *n_electrons* qubits set to ``|1>``.

    Under Bravyi-Kitaev, the encoding stores parities rather
    than occupancies; the qubits to flip are determined by the
    BK update sets.

    Attributes:
        n_qubits: Total number of spin-orbitals (qubits).
        n_electrons: Number of occupied spin-orbitals.
        mapping: Qubit mapping (``"jordan_wigner"`` or
            ``"bravyi_kitaev"``).
    """

    n_qubits: int
    n_electrons: int
    mapping: str = "jordan_wigner"

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise CircuitError(
                f"n_qubits must be >= 1, got {self.n_qubits}"
            )
        if self.n_electrons < 0:
            raise CircuitError(
                f"n_electrons must be >= 0, got {self.n_electrons}"
            )
        if self.n_electrons > self.n_qubits:
            raise CircuitError(
                f"n_electrons ({self.n_electrons}) cannot exceed "
                f"n_qubits ({self.n_qubits})"
            )
        if self.mapping not in _VALID_MAPPINGS:
            raise CircuitError(
                f"Unknown mapping '{self.mapping}'; "
                f"valid options: {sorted(_VALID_MAPPINGS)}"
            )

    def to_bitstring(self) -> str:
        """Return the qubit bitstring for the HF state.

        Characters are ordered qubit-0 (left) to qubit-(n-1) (right).

        Returns:
            A string of ``'0'`` and ``'1'`` characters.
        """
        if self.mapping == "jordan_wigner":
            return self._jw_bitstring()
        return self._bk_bitstring()

    def to_circuit(self) -> Circuit:
        """Build a circuit that prepares the Hartree-Fock state.

        Returns:
            A circuit with X gates on the appropriate qubits.
        """
        from qdk_pythonic.core.circuit import Circuit

        bitstring = self.to_bitstring()
        circ = Circuit()
        q = circ.allocate(self.n_qubits)
        for i, bit in enumerate(bitstring):
            if bit == "1":
                circ.x(q[i])
        return circ

    # ── Private helpers ──

    def _jw_bitstring(self) -> str:
        """JW: qubits 0..n_electrons-1 are |1>, rest |0>."""
        return "1" * self.n_electrons + "0" * (self.n_qubits - self.n_electrons)

    def _bk_bitstring(self) -> str:
        """BK: compute the encoded bitstring from occupations.

        In the BK encoding, qubit *j* stores the parity of a
        specific subset of orbital occupations determined by the
        binary indexed tree structure. We compute the occupation
        vector, then derive each qubit value from its BK semantics.
        """
        # Occupation vector: first n_electrons orbitals occupied
        occ = [1] * self.n_electrons + [0] * (self.n_qubits - self.n_electrons)

        # BK qubit j stores the parity (XOR) of occupations in
        # its "responsibility range". For a Fenwick tree, qubit j
        # is responsible for orbitals in range
        # [j - (j & -j) + 1, j] (0-indexed: [j - lsb + 1, j]).
        bits = ["0"] * self.n_qubits
        for j in range(self.n_qubits):
            # Least significant bit of (j+1) gives the range width
            lsb = (j + 1) & -(j + 1)
            start = j - lsb + 1
            parity = 0
            for k in range(start, j + 1):
                parity ^= occ[k]
            bits[j] = "1" if parity else "0"

        return "".join(bits)
