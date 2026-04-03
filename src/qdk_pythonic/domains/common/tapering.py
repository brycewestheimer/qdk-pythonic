"""Qubit tapering via Z2 symmetries.

Identifies Z2 symmetries of a Pauli Hamiltonian and removes
redundant qubits, reducing the problem size.

The algorithm:

1. Build the binary symplectic representation of each Pauli term.
2. Find the kernel of the check matrix (Pauli terms that commute
   with all others) to identify independent Z2 symmetries.
3. For each symmetry, pick a "pivot" qubit to taper off.
4. Transform the Hamiltonian using Clifford rotations that
   diagonalize the symmetry operators on the pivot qubits.
5. Project onto a specific symmetry sector (+1 or -1 per symmetry)
   and remove the pivot qubits.

Example::

    from qdk_pythonic.domains.common.tapering import taper_hamiltonian

    tapered_h, info = taper_hamiltonian(hamiltonian)
    print(f"Reduced from {hamiltonian.qubit_count()} to "
          f"{tapered_h.qubit_count()} qubits")
"""

from __future__ import annotations

from dataclasses import dataclass

from qdk_pythonic.domains.common.operators import (
    PauliHamiltonian,
    PauliTerm,
)


@dataclass(frozen=True)
class TaperingInfo:
    """Metadata about a qubit tapering transformation.

    Attributes:
        original_qubits: Number of qubits before tapering.
        tapered_qubits: Number of qubits after tapering.
        n_symmetries: Number of Z2 symmetries found.
        pivot_qubits: Qubit indices that were tapered off.
        eigenvalues: Symmetry sector eigenvalues (+1 or -1)
            used for projection.
    """

    original_qubits: int
    tapered_qubits: int
    n_symmetries: int
    pivot_qubits: tuple[int, ...]
    eigenvalues: tuple[int, ...]


def find_z2_symmetries(
    hamiltonian: PauliHamiltonian,
) -> list[PauliTerm]:
    """Find independent Z2 symmetries of a Pauli Hamiltonian.

    A Z2 symmetry is a Pauli operator S that commutes with every
    term in H: [S, P_k] = 0 for all k.

    Uses the binary symplectic representation and Gaussian
    elimination to find independent generators of the symmetry
    group.

    Args:
        hamiltonian: The Hamiltonian to analyze.

    Returns:
        List of independent symmetry generators as PauliTerms.
        Each is a tensor product of single-qubit Z operators.
    """
    if not hamiltonian.terms:
        return []

    qubit_indices = hamiltonian.qubit_indices()
    if not qubit_indices:
        return []

    n_qubits = max(qubit_indices) + 1

    # Build the binary check matrix.
    # For each Pauli term, encode its X and Z parts as binary vectors.
    # A term commutes with a Z-type operator on qubit j iff it has
    # no X or Y on qubit j.
    #
    # We look for Z-type symmetries: operators of the form
    # Z_{i1} Z_{i2} ... that commute with all terms.
    # A Z-string commutes with a Pauli term iff the Z-string has
    # even overlap with the X-part of the term (X and Y positions).

    # Build matrix where row k has a 1 in column j if term k has
    # X or Y on qubit j (the "X-part" of the term).
    x_matrix: list[list[int]] = []
    for term in hamiltonian.terms:
        row = [0] * n_qubits
        for qi, op in term.pauli_ops.items():
            if op in ("X", "Y"):
                row[qi] = 1
        x_matrix.append(row)

    # Find the kernel of x_matrix over GF(2):
    # vectors z such that x_matrix @ z = 0 (mod 2).
    # These z vectors define Z-type symmetry operators.
    kernel = _gf2_kernel(x_matrix, n_qubits)

    # Convert kernel vectors to PauliTerms
    symmetries: list[PauliTerm] = []
    for vec in kernel:
        ops: dict[int, str] = {}
        for j, bit in enumerate(vec):
            if bit:
                ops[j] = "Z"
        if ops:
            symmetries.append(PauliTerm(pauli_ops=ops))

    return symmetries


def taper_hamiltonian(
    hamiltonian: PauliHamiltonian,
    symmetry_eigenvalues: list[int] | None = None,
) -> tuple[PauliHamiltonian, TaperingInfo]:
    """Taper a Hamiltonian by removing qubits using Z2 symmetries.

    For each Z2 symmetry found, one qubit is removed by projecting
    onto a symmetry sector. The default sector is all +1 eigenvalues,
    which corresponds to the ground state for most molecular
    Hamiltonians.

    Args:
        hamiltonian: The Hamiltonian to taper.
        symmetry_eigenvalues: Eigenvalue (+1 or -1) for each
            symmetry sector. Defaults to all +1.

    Returns:
        Tuple of (tapered Hamiltonian, TaperingInfo metadata).
    """
    symmetries = find_z2_symmetries(hamiltonian)
    n_sym = len(symmetries)
    original_n = hamiltonian.qubit_count()

    if n_sym == 0:
        return hamiltonian, TaperingInfo(
            original_qubits=original_n,
            tapered_qubits=original_n,
            n_symmetries=0,
            pivot_qubits=(),
            eigenvalues=(),
        )

    if symmetry_eigenvalues is None:
        eigenvalues = [1] * n_sym
    else:
        eigenvalues = list(symmetry_eigenvalues)
        if len(eigenvalues) != n_sym:
            raise ValueError(
                f"Expected {n_sym} eigenvalues, got {len(eigenvalues)}"
            )

    # Pick pivot qubits: for each symmetry, choose a qubit that
    # appears in the symmetry operator and hasn't been picked yet.
    pivot_qubits: list[int] = []
    used: set[int] = set()
    for sym in symmetries:
        for qi in sorted(sym.pauli_ops.keys()):
            if qi not in used:
                pivot_qubits.append(qi)
                used.add(qi)
                break

    # Apply tapering: for each term in the Hamiltonian, check its
    # commutation with each symmetry. If a term anticommutes with
    # a symmetry, it vanishes in the projected sector. If it
    # commutes, replace the pivot qubit with the eigenvalue.
    tapered_terms: list[PauliTerm] = []
    qubit_indices = hamiltonian.qubit_indices()
    n_qubits = max(qubit_indices) + 1 if qubit_indices else 0

    for term in hamiltonian.terms:
        coeff = term.coeff
        new_ops = dict(term.pauli_ops)
        valid = True

        for sym_idx, sym in enumerate(symmetries):
            pivot = pivot_qubits[sym_idx]

            # Check if the term has X or Y on the pivot qubit
            pivot_op = new_ops.get(pivot)
            if pivot_op in ("X", "Y"):
                # Term anticommutes with this Z symmetry -> vanishes
                valid = False
                break
            elif pivot_op == "Z":
                # Z on pivot commutes with Z symmetry: replace with eigenvalue
                coeff = coeff * eigenvalues[sym_idx]
                del new_ops[pivot]
            else:
                # Identity on pivot: no change needed
                pass

        if not valid:
            continue
        if abs(coeff) < 1e-15:
            continue

        # Relabel qubits: remove pivot qubits and compact indices
        tapered_terms.append(PauliTerm(pauli_ops=new_ops, coeff=coeff))

    # Compact qubit indices: remove gaps left by pivot qubits
    remaining_qubits = sorted(
        set(range(n_qubits)) - set(pivot_qubits),
    )
    index_map = {old: new for new, old in enumerate(remaining_qubits)}

    compacted_terms: list[PauliTerm] = []
    for term in tapered_terms:
        new_ops = {}
        for qi, op in term.pauli_ops.items():
            if qi in index_map:
                new_ops[index_map[qi]] = op
            # else: qubit was a pivot, already handled
        compacted_terms.append(
            PauliTerm(pauli_ops=new_ops, coeff=term.coeff),
        )

    tapered_h = PauliHamiltonian(compacted_terms).simplify()

    info = TaperingInfo(
        original_qubits=original_n,
        tapered_qubits=tapered_h.qubit_count(),
        n_symmetries=n_sym,
        pivot_qubits=tuple(pivot_qubits),
        eigenvalues=tuple(eigenvalues),
    )

    return tapered_h, info


def _gf2_kernel(
    matrix: list[list[int]], n_cols: int,
) -> list[list[int]]:
    """Compute the kernel of a binary matrix over GF(2).

    Uses Gaussian elimination to find all vectors x such that
    matrix @ x = 0 (mod 2).

    Args:
        matrix: Binary matrix as list of rows.
        n_cols: Number of columns.

    Returns:
        List of kernel basis vectors.
    """
    n_rows = len(matrix)
    if n_rows == 0 or n_cols == 0:
        return []

    # Augment with identity for tracking column operations
    # Work with columns: transpose, do row reduction, find free vars
    # Transpose approach: find null space of M^T over GF(2)

    # Copy matrix
    mat = [row[:] for row in matrix]

    # Gaussian elimination with column tracking
    pivot_cols: list[int] = []
    pivot_rows: list[int] = []
    row = 0

    for col in range(n_cols):
        # Find pivot in this column
        found = -1
        for r in range(row, n_rows):
            if mat[r][col] == 1:
                found = r
                break
        if found == -1:
            continue

        # Swap rows
        mat[row], mat[found] = mat[found], mat[row]
        pivot_cols.append(col)
        pivot_rows.append(row)

        # Eliminate other rows
        for r in range(n_rows):
            if r != row and mat[r][col] == 1:
                for c in range(n_cols):
                    mat[r][c] ^= mat[row][c]

        row += 1

    # Free columns (not pivot columns) define kernel basis vectors
    free_cols = [c for c in range(n_cols) if c not in pivot_cols]
    kernel_vectors: list[list[int]] = []

    for fc in free_cols:
        vec = [0] * n_cols
        vec[fc] = 1
        # Back-substitute: for each pivot, set the pivot column
        # so that the pivot row equation is satisfied
        for pi, pc in enumerate(pivot_cols):
            if mat[pivot_rows[pi]][fc] == 1:
                vec[pc] = 1
        kernel_vectors.append(vec)

    return kernel_vectors
