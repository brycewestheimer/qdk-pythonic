"""FCIDUMP file format support.

Read and write molecular integrals in the FCIDUMP format, a standard
interchange format for quantum chemistry codes.

Example::

    from qdk_pythonic.domains.chemistry.fcidump import (
        read_fcidump, write_fcidump,
    )

    data = read_fcidump("molecule.fcidump")
    hamiltonian = data.to_hamiltonian()
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from qdk_pythonic.domains.common.fermion import FermionOperator, from_integrals
from qdk_pythonic.domains.common.mapping import (
    BravyiKitaevMapping,
    JordanWignerMapping,
)
from qdk_pythonic.domains.common.operators import PauliHamiltonian
from qdk_pythonic.exceptions import ParserError


def _import_numpy() -> Any:
    """Lazily import numpy."""
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "numpy is required for FCIDUMP support. "
            "Install it with: pip install numpy"
        ) from exc
    return np


@dataclass(frozen=True)
class FCIDUMPData:
    """Parsed FCIDUMP file contents.

    Stores the one- and two-electron integrals along with metadata
    needed to construct a molecular Hamiltonian.

    Attributes:
        n_orbitals: Number of spatial orbitals.
        n_electrons: Number of electrons.
        ms2: Twice the spin projection (2*Ms).
        h1e: One-electron integrals, shape ``(n, n)``.
        h2e: Two-electron integrals, shape ``(n, n, n, n)``,
            in physicist notation ``<pq|rs>``.
        nuclear_repulsion: Nuclear repulsion energy (core energy).
    """

    n_orbitals: int
    n_electrons: int
    ms2: int
    h1e: Any  # numpy ndarray
    h2e: Any  # numpy ndarray
    nuclear_repulsion: float

    def to_fermion_operator(self) -> FermionOperator:
        """Convert to a FermionOperator."""
        return from_integrals(
            self.h1e, self.h2e, self.nuclear_repulsion,
        )

    def to_double_factorized(
        self, threshold: float = 1e-6,
    ) -> Any:
        """Decompose into double-factorized form.

        Args:
            threshold: Truncation threshold for small eigenvalues.

        Returns:
            DoubleFactorizedHamiltonian.
        """
        from qdk_pythonic.domains.common.double_factorization import (
            from_fcidump,
        )

        return from_fcidump(self, threshold=threshold)

    def to_hamiltonian(
        self, mapping: str = "jordan_wigner",
    ) -> PauliHamiltonian:
        """Convert to a qubit Hamiltonian.

        Args:
            mapping: Qubit mapping to use.

        Returns:
            PauliHamiltonian for the molecule.
        """
        fermion_op = self.to_fermion_operator()
        if mapping == "bravyi_kitaev":
            return BravyiKitaevMapping().map(fermion_op)
        return JordanWignerMapping().map(fermion_op)


def read_fcidump(path: str) -> FCIDUMPData:
    """Parse an FCIDUMP file.

    The FCIDUMP format has a Fortran namelist header followed by
    integral values::

        &FCI NORB=n, NELEC=m, MS2=s,
          ORBSYM=1,1,...
        &END
        value  i  j  k  l

    Two-electron integrals have all four indices > 0 (1-indexed).
    One-electron integrals have k=l=0.
    Nuclear repulsion has i=j=k=l=0.

    Args:
        path: Path to the FCIDUMP file.

    Returns:
        Parsed FCIDUMPData.

    Raises:
        ParserError: If the file format is invalid.
    """
    with open(path) as f:
        content = f.read()
    return _parse_fcidump(content)


def write_fcidump(path: str, data: FCIDUMPData) -> None:
    """Write molecular integrals in FCIDUMP format.

    Args:
        path: Output file path.
        data: The molecular integral data to write.
    """
    np = _import_numpy()
    n = data.n_orbitals

    lines: list[str] = []
    # Header
    orbsym = ",".join(["1"] * n)
    lines.append(
        f" &FCI NORB={n},NELEC={data.n_electrons},"
        f"MS2={data.ms2},"
    )
    lines.append(f"  ORBSYM={orbsym},")
    lines.append("  ISYM=1,")
    lines.append(" &END")

    # Two-electron integrals (1-indexed, only non-zero)
    for p in range(n):
        for q in range(p, n):
            for r in range(n):
                for s in range(r, n):
                    val = float(np.real(data.h2e[p, q, r, s]))
                    if abs(val) > 1e-15:
                        lines.append(
                            f" {val: .16e}  {p + 1:4d}"
                            f"  {q + 1:4d}  {r + 1:4d}  {s + 1:4d}"
                        )

    # One-electron integrals (1-indexed, k=l=0)
    for p in range(n):
        for q in range(p, n):
            val = float(np.real(data.h1e[p, q]))
            if abs(val) > 1e-15:
                lines.append(
                    f" {val: .16e}  {p + 1:4d}"
                    f"  {q + 1:4d}     0     0"
                )

    # Nuclear repulsion (i=j=k=l=0)
    lines.append(
        f" {data.nuclear_repulsion: .16e}     0"
        f"     0     0     0"
    )

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _parse_fcidump(content: str) -> FCIDUMPData:
    """Parse FCIDUMP content string."""
    np = _import_numpy()

    # Split header and data
    header_match = re.search(
        r"&FCI(.*?)&END", content, re.DOTALL | re.IGNORECASE,
    )
    if not header_match:
        raise ParserError("No &FCI...&END header found in FCIDUMP")

    header_text = header_match.group(1)
    data_text = content[header_match.end():]

    # Parse header fields
    norb = _parse_header_int(header_text, "NORB")
    nelec = _parse_header_int(header_text, "NELEC")
    ms2_val = _parse_header_int(header_text, "MS2", default=0)
    ms2 = ms2_val if ms2_val is not None else 0

    if norb is None:
        raise ParserError("NORB not found in FCIDUMP header")
    if nelec is None:
        raise ParserError("NELEC not found in FCIDUMP header")

    n = norb
    h1e = np.zeros((n, n), dtype=np.float64)
    h2e = np.zeros((n, n, n, n), dtype=np.float64)
    nuclear_repulsion = 0.0

    # Parse integral lines
    for line in data_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        val = float(parts[0])
        ii, jj, kk, ll = (
            int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]),
        )

        if ii == 0 and jj == 0 and kk == 0 and ll == 0:
            nuclear_repulsion = val
        elif kk == 0 and ll == 0:
            # One-electron integral (1-indexed -> 0-indexed)
            p, q = ii - 1, jj - 1
            h1e[p, q] = val
            h1e[q, p] = val  # Hermitian symmetry
        else:
            # Two-electron integral (1-indexed -> 0-indexed)
            # FCIDUMP uses chemist notation (pq|rs)
            # Store in physicist notation <pq|rs> = (ps|qr)
            p, q, r, s = ii - 1, jj - 1, kk - 1, ll - 1
            # Chemist (pq|rs) -> physicist h2e[p,r,q,s]
            h2e[p, r, q, s] = val
            # Apply 8-fold symmetry
            h2e[q, s, p, r] = val
            h2e[r, p, s, q] = val
            h2e[s, q, r, p] = val
            h2e[q, r, p, s] = val
            h2e[p, s, q, r] = val
            h2e[s, p, r, q] = val
            h2e[r, q, s, p] = val

    return FCIDUMPData(
        n_orbitals=n,
        n_electrons=nelec,
        ms2=ms2,
        h1e=h1e,
        h2e=h2e,
        nuclear_repulsion=nuclear_repulsion,
    )


def _parse_header_int(
    header: str, key: str, default: int | None = None,
) -> int | None:
    """Extract an integer value from the FCIDUMP header."""
    pattern = rf"{key}\s*=\s*(\d+)"
    match = re.search(pattern, header, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return default
