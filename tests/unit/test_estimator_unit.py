"""Unit tests for the resource estimator (mock-based, no qsharp required)."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, call, patch

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.exceptions import ExecutionError


def _make_bell_circuit() -> Circuit:
    """Create a bell state circuit with measurements."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    return circ


def _make_bell_circuit_no_measure() -> Circuit:
    """Create a bell state circuit without measurements."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    return circ


@pytest.mark.unit
class TestEstimateCircuit:
    """Tests for estimate_circuit function."""

    def test_generates_code_without_measurements(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.return_value = {"physicalQubits": 100}

        captured_code: list[str] = []

        def capture_eval(code: str) -> None:
            captured_code.append(code)

        fake_qsharp.eval.side_effect = capture_eval

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            estimate_circuit(circ)

        assert len(captured_code) == 1
        code = captured_code[0]
        # Should NOT contain MResetZ (measurement)
        assert "MResetZ" not in code
        # Should be Unit return type
        assert ": Unit" in code
        # Should still contain gate operations
        assert "H(" in code
        assert "CNOT(" in code

    def test_circuit_instructions_restored_after_estimation(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        original_count = len(circ._instructions)

        fake_qsharp = MagicMock()
        fake_qsharp.estimate.return_value = {}

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            estimate_circuit(circ)

        assert len(circ._instructions) == original_count

    def test_params_passed_through(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.return_value = {"physicalQubits": 50}
        params = {"qubitParams": {"name": "qubit_gate_ns_e3"}}

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            estimate_circuit(circ, params=params)

        # Verify params were passed to qsharp.estimate
        est_call = fake_qsharp.estimate.call_args
        assert est_call[1]["params"] == params

    def test_no_params_passed_when_none(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.return_value = {}

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            estimate_circuit(circ, params=None)

        est_call = fake_qsharp.estimate.call_args
        assert "params" not in est_call[1]

    def test_execution_error_on_eval_failure(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.eval.side_effect = RuntimeError("compile error")

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError, match="Q# compilation failed"):
                estimate_circuit(circ)

    def test_execution_error_on_estimate_failure(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.side_effect = RuntimeError("estimation failed")

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError, match="Resource estimation failed"):
                estimate_circuit(circ)

    def test_execution_error_preserves_cause(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        cause = RuntimeError("root cause")
        fake_qsharp.estimate.side_effect = cause

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError) as exc_info:
                estimate_circuit(circ)
            assert exc_info.value.__cause__ is cause

    def test_import_error_when_qsharp_missing(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit()
        with patch.dict(sys.modules, {"qsharp": None}):
            with pytest.raises(ImportError, match="qsharp is required"):
                estimate_circuit(circ)

    def test_circuit_estimate_method_delegates(self) -> None:
        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.return_value = {"physicalQubits": 200}

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            result = circ.estimate()

        assert result == {"physicalQubits": 200}

    def test_circuit_without_measurements_works(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit

        circ = _make_bell_circuit_no_measure()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.return_value = {"physicalQubits": 10}

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            result = estimate_circuit(circ)

        assert result == {"physicalQubits": 10}


@pytest.mark.unit
class TestEstimateCircuitBatch:
    """Tests for estimate_circuit_batch function."""

    def test_registers_operation_once_calls_estimate_n_times(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit_batch

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.side_effect = [
            {"physicalQubits": 100},
            {"physicalQubits": 200},
            {"physicalQubits": 300},
        ]

        params_list = [
            {"qubitParams": {"name": "a"}},
            {"qubitParams": {"name": "b"}},
            {"qubitParams": {"name": "c"}},
        ]

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            results = estimate_circuit_batch(circ, params_list)

        # eval called exactly once (compile once)
        assert fake_qsharp.eval.call_count == 1
        # estimate called 3 times (once per param set)
        assert fake_qsharp.estimate.call_count == 3
        assert len(results) == 3
        assert results[0] == {"physicalQubits": 100}
        assert results[2] == {"physicalQubits": 300}

    def test_execution_error_on_eval_failure(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit_batch

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.eval.side_effect = RuntimeError("compile error")

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError, match="Q# compilation failed"):
                estimate_circuit_batch(circ, [{}])

    def test_execution_error_on_estimate_failure(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit_batch

        circ = _make_bell_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.estimate.side_effect = RuntimeError("bad params")

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError, match="Resource estimation failed"):
                estimate_circuit_batch(circ, [{"bad": True}])

    def test_import_error_when_qsharp_missing(self) -> None:
        from qdk_pythonic.execution.estimator import estimate_circuit_batch

        circ = _make_bell_circuit()
        with patch.dict(sys.modules, {"qsharp": None}):
            with pytest.raises(ImportError, match="qsharp is required"):
                estimate_circuit_batch(circ, [{}])
