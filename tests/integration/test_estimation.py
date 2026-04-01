"""Integration tests for resource estimation (requires qsharp)."""

from __future__ import annotations

from typing import Any

import pytest

from qdk_pythonic.core.circuit import Circuit

qsharp = pytest.importorskip("qsharp", reason="qsharp not installed")


@pytest.mark.integration
def test_estimate_returns_result(estimable_circuit: Circuit) -> None:
    """Estimation of a circuit with T gates should return a result."""
    result = estimable_circuit.estimate()
    assert result is not None
    result_str = str(result)
    assert "physicalQubits" in result_str or hasattr(result, "physical_qubits")


@pytest.mark.integration
def test_estimate_with_custom_params(estimable_circuit: Circuit) -> None:
    """Estimation with custom parameters should succeed."""
    params: dict[str, Any] = {
        "qubitParams": {"name": "qubit_gate_ns_e3"},
    }

    result = estimable_circuit.estimate(params=params)
    assert result is not None
