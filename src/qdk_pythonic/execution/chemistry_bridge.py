"""Bridge to qsharp.chemistry for DF-qubitization resource estimation.

Passes FCIDUMP data to the qsharp runtime's native chemistry
pipeline for production-scale resource estimation.

Example::

    from qdk_pythonic.execution.chemistry_bridge import estimate_chemistry
    from qdk_pythonic.domains.chemistry.fcidump import read_fcidump

    data = read_fcidump("molecule.fcidump")
    result = estimate_chemistry(data)
    result.print_report()
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qdk_pythonic.exceptions import ExecutionError
from qdk_pythonic.execution.chemistry_estimate import (
    parse_estimation_result,
)

if TYPE_CHECKING:
    from qdk_pythonic.execution.chemistry_estimate import (
        ChemistryResourceEstimate,
    )


def _import_qsharp_chemistry() -> tuple[Any, Any]:
    """Import qsharp and its chemistry module.

    Returns:
        Tuple of (qsharp module, qsharp.chemistry module).

    Raises:
        ImportError: If qsharp or qsharp.chemistry is unavailable.
    """
    try:
        import qsharp  # type: ignore[import-not-found]
    except ImportError:
        raise ImportError(
            "qsharp is required for chemistry resource estimation. "
            "Install it with: pip install 'qdk-pythonic[qsharp]'"
        ) from None

    try:
        import qsharp.chemistry as chem  # type: ignore[import-not-found]
    except (ImportError, AttributeError):
        raise ImportError(
            "qsharp.chemistry module not available. "
            "Requires qsharp >= 1.25 with chemistry support."
        ) from None

    return qsharp, chem


@dataclass(frozen=True)
class ChemistryEstimationConfig:
    """Configuration for chemistry resource estimation.

    Attributes:
        error_budget: Target error budget for the computation.
        qubit_params: Qubit parameter model name (e.g.
            ``"qubit_gate_ns_e3"``, ``"qubit_gate_ns_e4"``).
        qec_scheme: QEC scheme name (e.g. ``"surface_code"``,
            ``"floquet_code"``).
    """

    error_budget: float = 0.01
    qubit_params: str = "qubit_gate_ns_e3"
    qec_scheme: str = "surface_code"

    def to_estimator_params(self) -> dict[str, Any]:
        """Convert to the dict expected by qsharp.estimate().

        Returns:
            Estimator parameters dict.
        """
        return {
            "errorBudget": self.error_budget,
            "qubitParams": {"name": self.qubit_params},
            "qecScheme": {"name": self.qec_scheme},
        }


def estimate_chemistry(
    fcidump_data: Any,
    config: ChemistryEstimationConfig | None = None,
) -> ChemistryResourceEstimate:
    """Run chemistry resource estimation via qsharp.chemistry.

    Passes FCIDUMP data to the qsharp runtime's native
    double-factorized qubitization pipeline.

    Args:
        fcidump_data: A FCIDUMPData instance with molecular integrals.
        config: Optional estimation configuration.

    Returns:
        Structured ChemistryResourceEstimate.

    Raises:
        ImportError: If qsharp.chemistry is not available.
        ExecutionError: If estimation fails.
    """
    from qdk_pythonic.domains.chemistry.fcidump import write_fcidump

    if config is None:
        config = ChemistryEstimationConfig()

    _, chem = _import_qsharp_chemistry()

    # Write FCIDUMP to a temporary file for the qsharp API
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fcidump", delete=False,
    ) as f:
        write_fcidump(f.name, fcidump_data)
        fcidump_path = f.name

    try:
        raw_result = _call_qsharp_chemistry(
            chem, fcidump_path, config,
        )
    except Exception as e:
        raise ExecutionError(
            f"Chemistry resource estimation failed: {e}"
        ) from e

    ham_info: dict[str, Any] = {
        "n_orbitals": fcidump_data.n_orbitals,
        "n_electrons": fcidump_data.n_electrons,
        "nuclear_repulsion": fcidump_data.nuclear_repulsion,
    }

    return parse_estimation_result(
        raw_result,
        algorithm_name="df_qubitization",
        hamiltonian_info=ham_info,
    )


def estimate_chemistry_from_pyscf(
    atom: str,
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
    config: ChemistryEstimationConfig | None = None,
) -> ChemistryResourceEstimate:
    """Run chemistry resource estimation from a PySCF specification.

    Convenience function that runs the PySCF pipeline and passes
    the resulting integrals to qsharp.chemistry.

    Args:
        atom: Molecular geometry in PySCF format.
        basis: Basis set name.
        charge: Molecular charge.
        spin: 2S, number of unpaired electrons.
        n_active_electrons: Active electrons (None = all).
        n_active_orbitals: Active orbitals (None = all).
        config: Optional estimation configuration.

    Returns:
        Structured ChemistryResourceEstimate.
    """
    from qdk_pythonic.adapters.pyscf_adapter import get_integrals, run_scf
    from qdk_pythonic.domains.chemistry.fcidump import FCIDUMPData

    scf_obj = run_scf(atom, basis, charge, spin)
    h1e, h2e, nuc = get_integrals(
        scf_obj, n_active_electrons, n_active_orbitals,
    )
    n_orbs = len(h1e)
    n_elec = int(scf_obj.mol.nelectron)
    if n_active_electrons is not None:
        n_elec = n_active_electrons

    data = FCIDUMPData(
        n_orbitals=n_orbs,
        n_electrons=n_elec,
        ms2=0,
        h1e=h1e,
        h2e=h2e,
        nuclear_repulsion=nuc,
    )
    return estimate_chemistry(data, config=config)


def _call_qsharp_chemistry(
    chem: Any,
    fcidump_path: str,
    config: ChemistryEstimationConfig,
) -> dict[str, Any]:
    """Call the qsharp.chemistry API.

    Isolated to simplify adaptation to different qsharp versions.

    Args:
        chem: The qsharp.chemistry module.
        fcidump_path: Path to FCIDUMP file.
        config: Estimation configuration.

    Returns:
        Raw estimation result dict.
    """
    # The qsharp.chemistry API may vary by version.
    # Try the most common invocations.
    params = config.to_estimator_params()

    if hasattr(chem, "estimate_from_fcidump"):
        return dict(chem.estimate_from_fcidump(fcidump_path, params=params))

    if hasattr(chem, "estimate"):
        return dict(chem.estimate(fcidump_path, params=params))

    # Fallback: load the FCIDUMP and use qsharp.estimate
    import qsharp  # type: ignore[import-not-found,unused-ignore]  # noqa: F811

    if hasattr(chem, "load_fcidump"):
        chem.load_fcidump(fcidump_path)
        return dict(qsharp.estimate(
            "Microsoft.Quantum.Chemistry.RunChemistry()",
            params=params,
        ))

    raise ExecutionError(
        "Could not find a compatible qsharp.chemistry API. "
        "Ensure qsharp >= 1.25 is installed."
    )
