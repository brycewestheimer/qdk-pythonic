"""Structured chemistry resource estimation results.

Wraps the raw ``qsharp.estimate()`` output dict with typed
dataclasses and chemistry-specific labels.

Example::

    from qdk_pythonic.execution.chemistry_estimate import (
        parse_estimation_result,
    )

    raw = circuit.estimate(params={"qubitParams": {"name": "qubit_gate_ns_e3"}})
    result = parse_estimation_result(raw, algorithm_name="trotter_qpe")
    result.print_report()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LogicalResources:
    """Logical-level resource counts.

    Attributes:
        logical_qubits: Total logical qubits.
        t_count: Number of T gates.
        rotation_count: Number of rotation gates.
        rotation_depth: Depth of rotation sub-circuits.
        ccz_count: Number of CCZ gates.
        measurement_count: Number of measurements.
    """

    logical_qubits: int
    t_count: int
    rotation_count: int
    rotation_depth: int
    ccz_count: int
    measurement_count: int


@dataclass(frozen=True)
class PhysicalResources:
    """Physical-level resource counts.

    Attributes:
        physical_qubits: Total physical qubits.
        runtime_seconds: Estimated wall-clock time in seconds.
        runtime_human: Human-readable runtime string.
        code_distance: QEC code distance.
        t_factory_count: Number of T-state factories.
        t_factory_fraction: Fraction of qubits in T factories.
    """

    physical_qubits: int
    runtime_seconds: float
    runtime_human: str
    code_distance: int
    t_factory_count: int
    t_factory_fraction: float


@dataclass(frozen=True)
class ChemistryResourceEstimate:
    """Structured chemistry resource estimation result.

    Wraps the raw ``qsharp.estimate()`` output with typed fields
    and chemistry-specific metadata.

    Attributes:
        logical: Logical-level resources.
        physical: Physical-level resources.
        algorithm_name: Quantum algorithm used (e.g.
            ``"trotter_qpe"``, ``"df_qubitization"``).
        qubit_model: Name of the qubit parameter model.
        qec_scheme: QEC scheme name.
        error_budget: Total error budget.
        hamiltonian_info: Chemistry metadata (n_orbitals,
            n_electrons, one_norm, n_terms, etc.).
        raw_result: The original ``qsharp.estimate()`` dict.
    """

    logical: LogicalResources
    physical: PhysicalResources
    algorithm_name: str
    qubit_model: str
    qec_scheme: str
    error_budget: float
    hamiltonian_info: dict[str, Any]
    raw_result: dict[str, Any]

    def print_report(self) -> None:
        """Print a formatted resource estimation report."""
        print(f"Chemistry Resource Estimate ({self.algorithm_name})")
        print(f"  Qubit model: {self.qubit_model}")
        print(f"  QEC scheme:  {self.qec_scheme}")
        print(f"  Error budget: {self.error_budget}")
        print()
        print("Logical resources:")
        print(f"  Logical qubits:  {self.logical.logical_qubits}")
        print(f"  T-gate count:    {self.logical.t_count}")
        print(f"  Rotation count:  {self.logical.rotation_count}")
        print(f"  Rotation depth:  {self.logical.rotation_depth}")
        print(f"  CCZ count:       {self.logical.ccz_count}")
        print(f"  Measurements:    {self.logical.measurement_count}")
        print()
        print("Physical resources:")
        print(f"  Physical qubits: {self.physical.physical_qubits}")
        print(f"  Runtime:         {self.physical.runtime_human}")
        print(f"  Code distance:   {self.physical.code_distance}")
        print(f"  T factories:     {self.physical.t_factory_count}")
        print(
            f"  T factory frac:  "
            f"{self.physical.t_factory_fraction:.1%}"
        )
        if self.hamiltonian_info:
            print()
            print("Hamiltonian info:")
            for key, val in self.hamiltonian_info.items():
                print(f"  {key}: {val}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a flat dict for tabular analysis.

        Returns:
            Dict with all fields flattened to top-level keys.
        """
        return {
            "algorithm_name": self.algorithm_name,
            "qubit_model": self.qubit_model,
            "qec_scheme": self.qec_scheme,
            "error_budget": self.error_budget,
            "logical_qubits": self.logical.logical_qubits,
            "t_count": self.logical.t_count,
            "rotation_count": self.logical.rotation_count,
            "rotation_depth": self.logical.rotation_depth,
            "ccz_count": self.logical.ccz_count,
            "measurement_count": self.logical.measurement_count,
            "physical_qubits": self.physical.physical_qubits,
            "runtime_seconds": self.physical.runtime_seconds,
            "runtime_human": self.physical.runtime_human,
            "code_distance": self.physical.code_distance,
            "t_factory_count": self.physical.t_factory_count,
            "t_factory_fraction": self.physical.t_factory_fraction,
            **{
                f"ham_{k}": v
                for k, v in self.hamiltonian_info.items()
            },
        }


def parse_estimation_result(
    raw_result: dict[str, Any],
    algorithm_name: str = "unknown",
    hamiltonian_info: dict[str, Any] | None = None,
) -> ChemistryResourceEstimate:
    """Parse a raw ``qsharp.estimate()`` result dict.

    Extracts structured metrics from the nested result dictionary
    returned by the Azure Quantum resource estimator.

    Args:
        raw_result: The raw result from ``qsharp.estimate()``.
        algorithm_name: Label for the quantum algorithm.
        hamiltonian_info: Optional chemistry metadata dict.

    Returns:
        A structured ChemistryResourceEstimate.
    """
    logical_counts = raw_result.get("logicalCounts", {})
    physical_counts = raw_result.get("physicalCounts", {})
    formatted = raw_result.get("physicalCountsFormatted", {})
    logical_qubit = raw_result.get("logicalQubit", {})
    job_params = raw_result.get("jobParams", {})

    logical = LogicalResources(
        logical_qubits=int(logical_counts.get("numQubits", 0)),
        t_count=int(logical_counts.get("tCount", 0)),
        rotation_count=int(logical_counts.get("rotationCount", 0)),
        rotation_depth=int(logical_counts.get("rotationDepth", 0)),
        ccz_count=int(logical_counts.get("cczCount", 0)),
        measurement_count=int(
            logical_counts.get("measurementCount", 0),
        ),
    )

    runtime_us = physical_counts.get("runtime", 0)
    runtime_seconds = float(runtime_us) / 1e6

    t_factories = physical_counts.get(
        "breakdown", {},
    ).get("numTfactories", 0)
    total_phys = int(physical_counts.get("physicalQubits", 0))
    t_factory_qubits = physical_counts.get(
        "breakdown", {},
    ).get("physicalQubitsForTfactories", 0)
    t_frac = float(t_factory_qubits) / total_phys if total_phys > 0 else 0.0

    physical = PhysicalResources(
        physical_qubits=total_phys,
        runtime_seconds=runtime_seconds,
        runtime_human=str(formatted.get("runtime", "N/A")),
        code_distance=int(logical_qubit.get("codeDistance", 0)),
        t_factory_count=int(t_factories),
        t_factory_fraction=t_frac,
    )

    qubit_params = job_params.get("qubitParams", {})
    qec_scheme = job_params.get("qecScheme", {})

    return ChemistryResourceEstimate(
        logical=logical,
        physical=physical,
        algorithm_name=algorithm_name,
        qubit_model=str(qubit_params.get("name", "unknown")),
        qec_scheme=str(qec_scheme.get("name", "unknown")),
        error_budget=float(job_params.get("errorBudget", 0.0)),
        hamiltonian_info=hamiltonian_info or {},
        raw_result=raw_result,
    )


def compare_estimates(
    estimates: list[ChemistryResourceEstimate],
) -> list[dict[str, Any]]:
    """Build a comparison table across multiple estimates.

    Returns a list of flat dicts suitable for tabular display
    or pandas DataFrame construction.

    Args:
        estimates: List of estimation results to compare.

    Returns:
        List of flat dicts, one per estimate.
    """
    return [e.to_dict() for e in estimates]
