"""Compatibility helpers for optional qsharp dependency."""

from __future__ import annotations

from typing import Any


def import_qsharp() -> Any:
    """Lazily import qsharp, raising a clear error if not installed.

    Returns:
        The qsharp module.

    Raises:
        ImportError: If qsharp is not installed.
    """
    try:
        import qsharp  # type: ignore[import-not-found]

        return qsharp
    except ImportError:
        raise ImportError(
            "qsharp is required for this operation. "
            "Install it with: pip install 'qdk-pythonic[qsharp]'"
        ) from None
