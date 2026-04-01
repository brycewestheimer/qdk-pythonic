"""Lattice geometries for condensed matter models.

Provides lattice objects that generate site lists and nearest-neighbor
edge lists for use with Hamiltonian constructors.

Example::

    from qdk_pythonic.domains.condensed_matter.lattice import Chain, SquareLattice

    chain = Chain(10, periodic=True)
    grid = SquareLattice(4, 4)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chain:
    """1D chain lattice.

    Attributes:
        n: Number of sites.
        periodic: Whether to include the wrap-around edge.
    """

    n: int
    periodic: bool = False

    def __post_init__(self) -> None:
        if self.n < 2:
            raise ValueError(f"Chain requires n >= 2, got {self.n}")

    @property
    def num_sites(self) -> int:
        """Total number of lattice sites."""
        return self.n

    @property
    def edges(self) -> list[tuple[int, int]]:
        """Nearest-neighbor edges."""
        e = [(i, i + 1) for i in range(self.n - 1)]
        if self.periodic:
            e.append((self.n - 1, 0))
        return e


@dataclass(frozen=True)
class SquareLattice:
    """2D square lattice.

    Sites are numbered row-major: site = row * cols + col.

    Attributes:
        rows: Number of rows.
        cols: Number of columns.
        periodic: Whether to include periodic boundary edges.
    """

    rows: int
    cols: int
    periodic: bool = False

    def __post_init__(self) -> None:
        if self.rows < 1 or self.cols < 1:
            raise ValueError(
                f"SquareLattice requires rows >= 1 and cols >= 1, "
                f"got rows={self.rows}, cols={self.cols}"
            )

    @property
    def num_sites(self) -> int:
        """Total number of lattice sites."""
        return self.rows * self.cols

    def _site(self, r: int, c: int) -> int:
        return r * self.cols + c

    @property
    def edges(self) -> list[tuple[int, int]]:
        """Nearest-neighbor edges."""
        e: list[tuple[int, int]] = []
        for r in range(self.rows):
            for c in range(self.cols):
                # Horizontal
                if c + 1 < self.cols:
                    e.append((self._site(r, c), self._site(r, c + 1)))
                elif self.periodic and self.cols > 1:
                    e.append((self._site(r, c), self._site(r, 0)))
                # Vertical
                if r + 1 < self.rows:
                    e.append((self._site(r, c), self._site(r + 1, c)))
                elif self.periodic and self.rows > 1:
                    e.append((self._site(r, c), self._site(0, c)))
        return e


@dataclass(frozen=True)
class HexagonalLattice:
    """2D hexagonal (honeycomb) lattice.

    Uses a two-site unit cell. Sites are numbered sequentially
    across unit cells.

    Attributes:
        rows: Number of unit-cell rows.
        cols: Number of unit-cell columns.
    """

    rows: int
    cols: int

    def __post_init__(self) -> None:
        if self.rows < 1 or self.cols < 1:
            raise ValueError(
                f"HexagonalLattice requires rows >= 1 and cols >= 1, "
                f"got rows={self.rows}, cols={self.cols}"
            )

    @property
    def num_sites(self) -> int:
        """Total number of lattice sites (2 per unit cell)."""
        return 2 * self.rows * self.cols

    def _site(self, r: int, c: int, sub: int) -> int:
        """Map (row, col, sublattice) to site index."""
        return 2 * (r * self.cols + c) + sub

    @property
    def edges(self) -> list[tuple[int, int]]:
        """Nearest-neighbor edges for the honeycomb lattice."""
        e: list[tuple[int, int]] = []
        for r in range(self.rows):
            for c in range(self.cols):
                a = self._site(r, c, 0)
                b = self._site(r, c, 1)
                # Intra-cell bond
                e.append((a, b))
                # Inter-cell horizontal bond (A to B of left neighbor)
                if c + 1 < self.cols:
                    e.append((b, self._site(r, c + 1, 0)))
                # Inter-cell vertical bond
                if r + 1 < self.rows:
                    e.append((b, self._site(r + 1, c, 0)))
        return e
