"""Qubit and QubitRegister dataclasses."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import overload


@dataclass(frozen=True)
class Qubit:
    """A handle to a single qubit within a circuit.

    Attributes:
        index: The integer index of this qubit in the circuit.
        label: An optional human-readable label.
    """

    index: int
    label: str | None = None
    _circuit_id: int = field(default=0, repr=False)


class QubitRegister:
    """An ordered collection of qubit handles.

    Supports integer indexing, slicing, iteration, and length queries.

    Attributes:
        label: An optional human-readable label for the register.
    """

    def __init__(self, qubits: list[Qubit], label: str | None = None) -> None:
        """Create a QubitRegister from a list of Qubit objects.

        Args:
            qubits: The qubits in this register.
            label: An optional label for the register.
        """
        self._qubits = list(qubits)
        self.label = label

    @overload
    def __getitem__(self, key: int) -> Qubit: ...
    @overload
    def __getitem__(self, key: slice) -> QubitRegister: ...

    def __getitem__(self, key: int | slice) -> Qubit | QubitRegister:
        """Index or slice into the register.

        Args:
            key: An integer index or slice.

        Returns:
            A single Qubit for integer keys, or a new QubitRegister for slices.

        Raises:
            IndexError: If the integer index is out of bounds.
        """
        if isinstance(key, slice):
            return QubitRegister(self._qubits[key], label=self.label)
        return self._qubits[key]

    def __len__(self) -> int:
        """Return the number of qubits in this register."""
        return len(self._qubits)

    def __iter__(self) -> Iterator[Qubit]:
        """Iterate over the qubits in this register."""
        return iter(self._qubits)

    def __repr__(self) -> str:
        """Return a string representation of this register."""
        label_str = f", label={self.label!r}" if self.label else ""
        return f"QubitRegister({self._qubits!r}{label_str})"
