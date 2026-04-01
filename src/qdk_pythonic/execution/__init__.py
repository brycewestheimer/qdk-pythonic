"""Execution backends for simulation and resource estimation."""

from qdk_pythonic.execution.config import RunConfig
from qdk_pythonic.execution.estimator import estimate_circuit, estimate_circuit_batch
from qdk_pythonic.execution.runner import run_circuit

__all__ = [
    "RunConfig",
    "estimate_circuit",
    "estimate_circuit_batch",
    "run_circuit",
]

try:
    from qsharp import EstimatorParams, QECScheme, QubitParams  # type: ignore[import-not-found]

    __all__ += ["EstimatorParams", "QECScheme", "QubitParams"]
except ImportError:
    pass
