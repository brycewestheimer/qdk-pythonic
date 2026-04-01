"""Circuit analysis: metrics and visualization."""

from qdk_pythonic.analysis.metrics import (
    circuit_from_dict,
    circuit_from_json,
    circuit_to_dict,
    circuit_to_json,
    compute_depth,
    compute_gate_count,
    compute_qubit_count,
)
from qdk_pythonic.analysis.visualization import draw_circuit

__all__ = [
    "circuit_from_dict",
    "circuit_from_json",
    "circuit_to_dict",
    "circuit_to_json",
    "compute_depth",
    "compute_gate_count",
    "compute_qubit_count",
    "draw_circuit",
]
