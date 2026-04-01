"""Unit tests for the simulation runner (mock-based, no qsharp required)."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from qdk_pythonic.exceptions import ExecutionError
from qdk_pythonic.execution.config import RunConfig


@pytest.mark.unit
class TestRunConfig:
    """Tests for RunConfig dataclass."""

    def test_defaults(self) -> None:
        cfg = RunConfig()
        assert cfg.shots == 1000

    def test_custom_shots(self) -> None:
        cfg = RunConfig(shots=500)
        assert cfg.shots == 500


@pytest.mark.unit
class TestImportQsharp:
    """Tests for the _import_qsharp helper."""

    def test_raises_import_error_with_message_when_missing(self) -> None:
        from qdk_pythonic.execution.runner import _import_qsharp

        with patch.dict(sys.modules, {"qsharp": None}):
            with pytest.raises(ImportError, match="qsharp is required"):
                _import_qsharp()

    def test_returns_module_when_available(self) -> None:
        from qdk_pythonic.execution.runner import _import_qsharp

        fake_qsharp = ModuleType("qsharp")
        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            result = _import_qsharp()
            assert result is fake_qsharp


@pytest.mark.unit
class TestRunCircuit:
    """Tests for run_circuit function."""

    def _make_circuit(self) -> MagicMock:
        """Create a mock circuit with a bell-state-like setup."""
        from qdk_pythonic.core.circuit import Circuit

        circ = Circuit()
        q = circ.allocate(2)
        circ.h(q[0]).cx(q[0], q[1]).measure_all()
        return circ

    def test_generates_unique_operation_names(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = [0, 0]

        names_seen: list[str] = []

        def capture_eval(code: str) -> None:
            # Extract the operation name from the Q# code
            if code.startswith("operation "):
                name = code.split("(")[0].replace("operation ", "")
                names_seen.append(name)

        fake_qsharp.eval.side_effect = capture_eval

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            run_circuit(circ, RunConfig(shots=1))
            run_circuit(circ, RunConfig(shots=1))

        assert len(names_seen) == 2
        assert names_seen[0] != names_seen[1]
        assert all(name.startswith("_qdk_op_") for name in names_seen)

    def test_execution_error_on_eval_failure(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.eval.side_effect = RuntimeError("syntax error")

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError, match="Q# compilation failed"):
                run_circuit(circ)

    def test_execution_error_preserves_cause(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        cause = RuntimeError("original error")
        fake_qsharp.eval.side_effect = cause

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError) as exc_info:
                run_circuit(circ)
            assert exc_info.value.__cause__ is cause

    def test_execution_error_on_run_failure(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.side_effect = RuntimeError("simulation timeout")

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            with pytest.raises(ExecutionError, match="Simulation failed"):
                run_circuit(circ)

    def test_returns_list_of_results(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = [0, 1, 0, 1]

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            results = run_circuit(circ, RunConfig(shots=4))

        assert results == [0, 1, 0, 1]
        assert isinstance(results, list)

    def test_converts_non_list_results_to_list(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = (0, 1, 0)  # tuple instead of list

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            results = run_circuit(circ, RunConfig(shots=3))

        assert results == [0, 1, 0]
        assert isinstance(results, list)

    def test_default_config_when_none(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = [0] * 1000

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            run_circuit(circ)

        # Check that run was called with shots=1000 (the default)
        call_kwargs = fake_qsharp.run.call_args
        assert call_kwargs[1]["shots"] == 1000

    def test_circuit_run_method_delegates(self) -> None:
        """Test that Circuit.run() properly delegates to run_circuit."""
        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = [1, 0, 1]

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            results = circ.run(shots=3)

        assert results == [1, 0, 1]
