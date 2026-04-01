"""Integration tests for resource estimation (requires qsharp)."""

from __future__ import annotations

from typing import Any

import pytest

from qdk_pythonic.core.circuit import Circuit

qsharp = pytest.importorskip("qsharp", reason="qsharp not installed")


@pytest.mark.integration
def test_bell_state_estimate_returns_result(bell_circuit: Circuit) -> None:
    """Bell state estimate() should return a result with physicalQubits."""
    result = bell_circuit.estimate()
    # The result should be dict-like with physical qubit information
    assert result is not None
    result_str = str(result)
    assert "physicalQubits" in result_str or hasattr(result, "physical_qubits")


@pytest.mark.integration
def test_estimate_with_custom_params() -> None:
    """Estimation with custom parameters should succeed."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])

    params: dict[str, Any] = {
        "qubitParams": {"name": "qubit_gate_ns_e3"},
    }

    result = circ.estimate(params=params)
    assert result is not None
