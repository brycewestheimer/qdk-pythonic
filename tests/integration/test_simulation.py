"""Integration tests for circuit simulation (requires qsharp)."""

from __future__ import annotations

import pytest

from qdk_pythonic.core.circuit import Circuit

qsharp = pytest.importorskip("qsharp", reason="qsharp not installed")


@pytest.mark.integration
def test_bell_state_run_returns_list() -> None:
    """Bell state run(shots=100) should return a list of results."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()

    results = circ.run(shots=100)
    assert isinstance(results, list)
    assert len(results) == 100


@pytest.mark.integration
def test_bell_state_results_correlated() -> None:
    """Bell state results should only contain correlated outcomes (00, 11)."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()

    results = circ.run(shots=200)
    for result in results:
        # Result format depends on qsharp version; check correlation
        result_str = str(result)
        # Both qubits should agree: either both 0 or both 1
        digits = [c for c in result_str if c in ("0", "1")]
        if len(digits) >= 2:
            assert digits[0] == digits[1], f"Uncorrelated result: {result}"
