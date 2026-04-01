"""CodeGenerator protocol definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


class CodeGenerator(Protocol):
    """Protocol for circuit-to-source-code serialization."""

    def generate(self, circuit: Circuit) -> str:
        """Generate source code for the given circuit.

        Args:
            circuit: The circuit to serialize.

        Returns:
            The generated source code string.
        """
        ...

    def generate_operation(self, name: str, circuit: Circuit) -> str:
        """Generate a named operation from the given circuit.

        Args:
            name: The operation name.
            circuit: The circuit to serialize.

        Returns:
            The generated source code string with a named operation.
        """
        ...
