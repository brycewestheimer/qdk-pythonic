"""Protocols for circuit-producing domain objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


class CircuitProducer(Protocol):
    """Protocol for objects that can produce a quantum circuit.

    Any class implementing a ``to_circuit`` method returning a
    ``Circuit`` satisfies this protocol.
    """

    def to_circuit(self) -> Circuit:
        """Convert this object to a Circuit."""
        ...
