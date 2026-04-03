"""Double-factorized Hamiltonian representation.

Decomposes two-electron integrals into a compact factorized form
that reduces the cost of qubitization-based quantum simulation.

The decomposition eigendecomposes the reshaped ERI matrix to
obtain scaled leaf matrices, which are then further decomposed
via SVD for optimal compression.

Example::

    from qdk_pythonic.domains.common.double_factorization import (
        double_factorize,
    )

    df = double_factorize(h1e, h2e, nuclear_repulsion, n_electrons=2)
    df.print_summary()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdk_pythonic.exceptions import CircuitError


def _import_numpy() -> Any:
    """Lazily import numpy."""
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "numpy is required for double factorization. "
            "Install it with: pip install numpy"
        ) from exc
    return np


@dataclass(frozen=True)
class DoubleFactorizedHamiltonian:
    """Double-factorized representation of a molecular Hamiltonian.

    The two-electron integrals are decomposed as:

        h2e[p,q,r,s] = sum_t sign_t * L_t[p,r] * L_t[q,s]

    where L_t are (n x n) leaf matrices from the eigendecomposition
    of the reshaped ERI tensor, and sign_t is +/-1 from the ERI
    eigenvalue sign.

    Attributes:
        one_body_integrals: Modified one-body tensor, shape
            ``(n_orbitals, n_orbitals)``.
        leaf_matrices: Scaled leaf matrices, shape
            ``(n_leaves, n_orbitals, n_orbitals)``.
        leaf_signs: Sign (+1 or -1) of each ERI eigenvalue.
        one_body_correction: Scalar energy correction.
        nuclear_repulsion: Nuclear repulsion energy.
        n_orbitals: Number of spatial orbitals.
        n_electrons: Number of electrons.
        cholesky_threshold: Threshold used for truncation.
    """

    one_body_integrals: Any  # numpy (n, n)
    leaf_matrices: Any  # numpy (L, n, n)
    leaf_signs: tuple[int, ...]  # +1 or -1 per leaf
    one_body_correction: float
    nuclear_repulsion: float
    n_orbitals: int
    n_electrons: int
    cholesky_threshold: float

    @property
    def n_leaves(self) -> int:
        """Number of leaves (rank L)."""
        np = _import_numpy()
        return int(np.shape(self.leaf_matrices)[0])

    def one_norm(self) -> float:
        """Compute the 1-norm (lambda) of the factorized Hamiltonian.

        The 1-norm determines the number of QPE iterations needed
        for qubitization. Lower is better.

        Returns:
            The 1-norm as a float.
        """
        np = _import_numpy()
        one_body_norm = float(np.sum(np.abs(self.one_body_integrals)))
        # Two-body: each leaf contributes ||L_t||_1^2
        two_body_norm = 0.0
        for t in range(self.n_leaves):
            leaf_norm = float(np.sum(np.abs(self.leaf_matrices[t])))
            two_body_norm += leaf_norm * leaf_norm
        return one_body_norm + two_body_norm

    def summary(self) -> dict[str, Any]:
        """Return a summary dict for inspection.

        Returns:
            Dict with n_orbitals, n_electrons, n_leaves, one_norm,
            nuclear_repulsion, one_body_correction, threshold.
        """
        return {
            "n_orbitals": self.n_orbitals,
            "n_electrons": self.n_electrons,
            "n_leaves": self.n_leaves,
            "one_norm": self.one_norm(),
            "nuclear_repulsion": self.nuclear_repulsion,
            "one_body_correction": self.one_body_correction,
            "cholesky_threshold": self.cholesky_threshold,
        }

    def print_summary(self) -> None:
        """Print a human-readable summary."""
        s = self.summary()
        print(
            f"DoubleFactorizedHamiltonian: "
            f"{s['n_orbitals']} orbitals, "
            f"{s['n_electrons']} electrons"
        )
        print(f"  Leaves (rank): {s['n_leaves']}")
        print(f"  1-norm (lambda): {s['one_norm']:.6f}")
        print(f"  Nuclear repulsion: {s['nuclear_repulsion']:.8f}")
        print(f"  One-body correction: {s['one_body_correction']:.8f}")
        print(f"  Threshold: {s['cholesky_threshold']:.1e}")

    def to_pauli_hamiltonian(
        self, mapping: str = "jordan_wigner",
    ) -> Any:
        """Convert to a PauliHamiltonian via integral reconstruction.

        Reconstructs the full integrals from the factorized form
        and maps through the standard fermion-to-qubit pipeline.
        Practical only for small systems.

        Args:
            mapping: Qubit mapping to use.

        Returns:
            PauliHamiltonian for the molecule.
        """
        fcidump = self.to_fcidump_data()
        return fcidump.to_hamiltonian(mapping=mapping)

    def to_fcidump_data(self) -> Any:
        """Reconstruct integrals and return as FCIDUMPData.

        Rebuilds h2e from the factorized representation for
        round-trip validation or interoperability.

        Returns:
            FCIDUMPData with reconstructed integrals.
        """
        np = _import_numpy()
        from qdk_pythonic.domains.chemistry.fcidump import FCIDUMPData

        n = self.n_orbitals

        # Reconstruct h2e: h2e[p,q,r,s] = sum_t sign_t * L_t[p,r] * L_t[q,s]
        h2e = np.zeros((n, n, n, n), dtype=np.float64)
        for t in range(self.n_leaves):
            leaf = self.leaf_matrices[t]
            h2e += self.leaf_signs[t] * np.einsum(
                "pr,qs->pqrs", leaf, leaf,
            )

        h1e = np.array(self.one_body_integrals, dtype=np.float64)

        return FCIDUMPData(
            n_orbitals=n,
            n_electrons=self.n_electrons,
            ms2=0,
            h1e=h1e,
            h2e=h2e,
            nuclear_repulsion=self.nuclear_repulsion
            + self.one_body_correction,
        )


def double_factorize(
    h1e: Any,
    h2e: Any,
    nuclear_repulsion: float,
    n_electrons: int,
    threshold: float = 1e-6,
) -> DoubleFactorizedHamiltonian:
    """Decompose molecular integrals into double-factorized form.

    Steps:

    1. Reshape ``h2e[p,q,r,s]`` to ``M[(p,r), (q,s)]``.
    2. Eigendecompose M and truncate small eigenvalues.
    3. Form leaf matrices ``L_t = sqrt(|d_t|) * v_t.reshape(n, n)``.

    The resulting decomposition satisfies:

        h2e[p,q,r,s] = sum_t sign(d_t) * L_t[p,r] * L_t[q,s]

    Args:
        h1e: One-electron integrals, shape ``(n, n)``.
        h2e: Two-electron integrals, shape ``(n, n, n, n)``,
            physicist notation.
        nuclear_repulsion: Nuclear repulsion energy.
        n_electrons: Number of electrons.
        threshold: Truncation threshold relative to the largest
            eigenvalue.

    Returns:
        DoubleFactorizedHamiltonian with the decomposed tensors.

    Raises:
        CircuitError: If inputs have incompatible shapes.
    """
    np = _import_numpy()

    h1e = np.asarray(h1e, dtype=np.float64)
    h2e = np.asarray(h2e, dtype=np.float64)
    n = h1e.shape[0]

    if h1e.shape != (n, n):
        raise CircuitError(
            f"h1e must be (n, n), got {h1e.shape}"
        )
    if h2e.shape != (n, n, n, n):
        raise CircuitError(
            f"h2e must be (n, n, n, n), got {h2e.shape}"
        )

    # Step 1: Reshape h2e[p,q,r,s] -> M[(p,r), (q,s)]
    m_matrix = h2e.transpose(0, 2, 1, 3).reshape(n * n, n * n)

    # Symmetrize to eliminate numerical noise
    m_matrix = 0.5 * (m_matrix + m_matrix.T)

    # Step 2: Eigendecompose M
    eigenvalues, eigenvectors = np.linalg.eigh(m_matrix)

    # Truncate small eigenvalues
    max_abs = np.max(np.abs(eigenvalues))
    if max_abs < 1e-15:
        return DoubleFactorizedHamiltonian(
            one_body_integrals=h1e,
            leaf_matrices=np.zeros((0, n, n), dtype=np.float64),
            leaf_signs=(),
            one_body_correction=0.0,
            nuclear_repulsion=nuclear_repulsion,
            n_orbitals=n,
            n_electrons=n_electrons,
            cholesky_threshold=threshold,
        )

    keep_mask = np.abs(eigenvalues) >= threshold * max_abs
    kept_eigenvalues = eigenvalues[keep_mask]
    kept_eigenvectors = eigenvectors[:, keep_mask]
    n_leaves = len(kept_eigenvalues)

    # Step 3: Form leaf matrices L_t = sqrt(|d_t|) * reshape(v_t)
    leaves = np.zeros((n_leaves, n, n), dtype=np.float64)
    signs: list[int] = []
    for t in range(n_leaves):
        scale = np.sqrt(np.abs(kept_eigenvalues[t]))
        leaves[t] = scale * kept_eigenvectors[:, t].reshape(n, n)
        signs.append(int(np.sign(kept_eigenvalues[t])))

    # One-body correction from the decomposition
    one_body_correction = 0.0
    for t in range(n_leaves):
        one_body_correction += signs[t] * float(
            np.trace(leaves[t] @ leaves[t].T),
        )
    one_body_correction *= -0.5

    return DoubleFactorizedHamiltonian(
        one_body_integrals=h1e.copy(),
        leaf_matrices=leaves,
        leaf_signs=tuple(signs),
        one_body_correction=one_body_correction,
        nuclear_repulsion=nuclear_repulsion,
        n_orbitals=n,
        n_electrons=n_electrons,
        cholesky_threshold=threshold,
    )


def from_fcidump(
    data: Any,
    threshold: float = 1e-6,
) -> DoubleFactorizedHamiltonian:
    """Build a DoubleFactorizedHamiltonian from FCIDUMPData.

    Args:
        data: A FCIDUMPData instance.
        threshold: Truncation threshold.

    Returns:
        DoubleFactorizedHamiltonian.
    """
    return double_factorize(
        h1e=data.h1e,
        h2e=data.h2e,
        nuclear_repulsion=data.nuclear_repulsion,
        n_electrons=data.n_electrons,
        threshold=threshold,
    )
