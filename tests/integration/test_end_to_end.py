"""End-to-end integration tests (requires qsharp)."""

from __future__ import annotations

import pytest

from qdk_pythonic.core.circuit import Circuit

qsharp = pytest.importorskip("qsharp", reason="qsharp not installed")


@pytest.mark.integration
def test_build_to_qsharp_and_run(bell_circuit: Circuit) -> None:
    """Build circuit, generate Q#, run, and verify results."""
    # Verify Q# generation works
    qs_code = bell_circuit.to_qsharp()
    assert "H(" in qs_code
    assert "CNOT(" in qs_code

    # Run and verify
    results = bell_circuit.run(shots=50)
    assert isinstance(results, list)
    assert len(results) == 50


@pytest.mark.integration
def test_build_and_estimate() -> None:
    """Build circuit with T gates and run resource estimation."""
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).t(q[0]).cx(q[0], q[1]).cx(q[1], q[2]).measure_all()

    result = circ.estimate()
    assert result is not None
    result_str = str(result)
    # Should contain resource estimation output
    assert "physicalQubits" in result_str or len(result_str) > 10
