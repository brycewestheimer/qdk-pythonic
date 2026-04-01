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

    def test_zero_shots_raises(self) -> None:
        with pytest.raises(ValueError, match="shots must be >= 1"):
            RunConfig(shots=0)

    def test_negative_shots_raises(self) -> None:
        with pytest.raises(ValueError, match="shots must be >= 1"):
            RunConfig(shots=-1)

    def test_frozen(self) -> None:
        cfg = RunConfig()
        with pytest.raises(AttributeError):
            cfg.shots = 5  # type: ignore[misc]

    def test_seed_default_none(self) -> None:
        cfg = RunConfig()
        assert cfg.seed is None

    def test_seed_valid(self) -> None:
        cfg = RunConfig(seed=42)
        assert cfg.seed == 42

    def test_seed_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="seed must be non-negative"):
            RunConfig(seed=-1)

    def test_noise_default_none(self) -> None:
        cfg = RunConfig()
        assert cfg.noise is None

    def test_noise_valid(self) -> None:
        cfg = RunConfig(noise=(0.01, 0.02, 0.03))
        assert cfg.noise == (0.01, 0.02, 0.03)

    def test_noise_invalid_probability_raises(self) -> None:
        with pytest.raises(ValueError, match="noise probabilities"):
            RunConfig(noise=(0.5, 1.5, 0.0))

    def test_noise_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="noise probabilities"):
            RunConfig(noise=(-0.1, 0.0, 0.0))


@pytest.mark.unit
class TestImportQsharp:
    """Tests for the _import_qsharp helper."""

    def test_raises_import_error_with_message_when_missing(self) -> None:
        from qdk_pythonic.execution._compat import import_qsharp

        with patch.dict(sys.modules, {"qsharp": None}):
            with pytest.raises(ImportError, match="qsharp is required"):
                import_qsharp()

    def test_returns_module_when_available(self) -> None:
        from qdk_pythonic.execution._compat import import_qsharp

        fake_qsharp = ModuleType("qsharp")
        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            result = import_qsharp()
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

    def test_noise_forwarded_to_qsharp_run(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = [0, 1]

        noise = (0.01, 0.02, 0.03)
        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            run_circuit(circ, RunConfig(shots=2, noise=noise))

        call_kwargs = fake_qsharp.run.call_args[1]
        assert call_kwargs["noise"] == noise

    def test_noise_not_forwarded_when_none(self) -> None:
        from qdk_pythonic.execution.runner import run_circuit

        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = [0]

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            run_circuit(circ, RunConfig(shots=1))

        call_kwargs = fake_qsharp.run.call_args[1]
        assert "noise" not in call_kwargs

    def test_circuit_run_method_delegates(self) -> None:
        """Test that Circuit.run() properly delegates to run_circuit."""
        circ = self._make_circuit()
        fake_qsharp = MagicMock()
        fake_qsharp.run.return_value = [1, 0, 1]

        with patch.dict(sys.modules, {"qsharp": fake_qsharp}):
            results = circ.run(shots=3)

        assert results == [1, 0, 1]
