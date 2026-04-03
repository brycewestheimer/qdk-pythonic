"""Execution backends for simulation and resource estimation."""

from qdk_pythonic.execution.chemistry_estimate import (
    ChemistryResourceEstimate,
    LogicalResources,
    PhysicalResources,
    compare_estimates,
    parse_estimation_result,
)
from qdk_pythonic.execution.config import RunConfig
from qdk_pythonic.execution.estimator import (
    estimate_and_parse,
    estimate_circuit,
    estimate_circuit_batch,
)
from qdk_pythonic.execution.runner import run_circuit

__all__ = [
    "ChemistryResourceEstimate",
    "LogicalResources",
    "PhysicalResources",
    "RunConfig",
    "compare_estimates",
    "estimate_and_parse",
    "estimate_circuit",
    "estimate_circuit_batch",
    "parse_estimation_result",
    "run_circuit",
]

try:
    from qsharp import EstimatorParams, QECScheme, QubitParams  # type: ignore[import-not-found]

    __all__ += ["EstimatorParams", "QECScheme", "QubitParams"]
except ImportError:
    pass
