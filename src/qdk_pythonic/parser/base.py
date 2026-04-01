"""Parser protocol definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


class Parser(Protocol):
    """Protocol for source-code-to-circuit parsing."""

    def parse(self, source: str) -> Circuit:
        """Parse a source string into a Circuit.

        Args:
            source: The source code string.

        Returns:
            A Circuit built from the parsed source.
        """
        ...
