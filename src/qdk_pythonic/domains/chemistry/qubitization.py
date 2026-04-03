"""Chemistry qubitization wrapper.

Unified interface for qubitization-based quantum chemistry,
supporting both gate-level circuit construction and production
resource estimation via the qsharp.chemistry bridge.

Example::

    from qdk_pythonic.domains.chemistry.qubitization import (
        ChemistryQubitization,
    )

    qubit = ChemistryQubitization(
        hamiltonian=pauli_h, n_electrons=2,
    )
    result = qubit.estimate_resources()
    result.print_report()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qdk_pythonic.domains.common.operators import PauliHamiltonian
from qdk_pythonic.exceptions import CircuitError

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit
    from qdk_pythonic.execution.chemistry_estimate import (
        ChemistryResourceEstimate,
    )


@dataclass(frozen=True)
class ChemistryQubitization:
    """Qubitization for molecular ground-state energy.

    Two modes of operation:

    - ``gate_level=True``: Builds explicit PREPARE/SELECT/QPE
      circuits from a PauliHamiltonian. Suitable for small systems,
      simulation, and circuit inspection.
    - ``gate_level=False`` (default): Delegates to the
      qsharp.chemistry bridge for production resource estimation
      using double-factorized qubitization.

    Attributes:
        hamiltonian: PauliHamiltonian or DoubleFactorizedHamiltonian.
        n_electrons: Number of electrons for HF initial state.
        n_estimation_qubits: Phase estimation precision bits.
        gate_level: If True, build explicit gate-level circuits.
    """

    hamiltonian: PauliHamiltonian | Any  # also accepts DF
    n_electrons: int
    n_estimation_qubits: int = 8
    gate_level: bool = False

    def __post_init__(self) -> None:
        if self.n_estimation_qubits < 1:
            raise CircuitError(
                f"n_estimation_qubits must be >= 1, "
                f"got {self.n_estimation_qubits}"
            )
        if self.n_electrons < 0:
            raise CircuitError(
                f"n_electrons must be >= 0, "
                f"got {self.n_electrons}"
            )

    def to_circuit(self) -> Circuit:
        """Build the gate-level qubitization QPE circuit.

        Only available when ``gate_level=True``. Requires the
        Hamiltonian to be a PauliHamiltonian.

        Returns:
            The full QPE circuit.

        Raises:
            CircuitError: If gate_level is False or Hamiltonian
                type is unsupported.
        """
        if not self.gate_level:
            raise CircuitError(
                "to_circuit() requires gate_level=True. "
                "For resource estimation, use estimate_resources()."
            )

        ham = self._get_pauli_hamiltonian()

        from qdk_pythonic.domains.common.lcu import QubitizationQPE

        qpe = QubitizationQPE(
            hamiltonian=ham,
            n_electrons=self.n_electrons,
            n_estimation_qubits=self.n_estimation_qubits,
        )
        return qpe.to_circuit()

    def estimate_resources(
        self,
        params: dict[str, Any] | None = None,
    ) -> ChemistryResourceEstimate:
        """Run resource estimation.

        In gate-level mode, builds the circuit and estimates via
        ``circuit.estimate()``. Otherwise, delegates to the
        qsharp.chemistry bridge (requires FCIDUMP-compatible data).

        Args:
            params: Optional estimator parameters.

        Returns:
            Structured ChemistryResourceEstimate.
        """
        from qdk_pythonic.execution.chemistry_estimate import (
            parse_estimation_result,
        )

        if self.gate_level:
            circ = self.to_circuit()
            raw = circ.estimate(params=params)
            ham = self._get_pauli_hamiltonian()
            return parse_estimation_result(
                raw,
                algorithm_name="qubitization_qpe",
                hamiltonian_info=ham.summary(),
            )

        # Bridge mode: need DF or FCIDUMP data
        from qdk_pythonic.domains.common.double_factorization import (
            DoubleFactorizedHamiltonian,
        )

        if isinstance(self.hamiltonian, DoubleFactorizedHamiltonian):
            fcidump = self.hamiltonian.to_fcidump_data()
        elif isinstance(self.hamiltonian, PauliHamiltonian):
            raise CircuitError(
                "Bridge-mode resource estimation requires a "
                "DoubleFactorizedHamiltonian or FCIDUMPData. "
                "Use gate_level=True for PauliHamiltonian, or "
                "convert via double_factorize() first."
            )
        else:
            # Assume FCIDUMPData-like
            fcidump = self.hamiltonian

        from qdk_pythonic.execution.chemistry_bridge import (
            ChemistryEstimationConfig,
            estimate_chemistry,
        )

        config = None
        if params is not None:
            config = ChemistryEstimationConfig(
                error_budget=params.get("errorBudget", 0.01),
                qubit_params=params.get(
                    "qubitParams", {},
                ).get("name", "qubit_gate_ns_e3")
                if isinstance(params.get("qubitParams"), dict)
                else "qubit_gate_ns_e3",
                qec_scheme=params.get(
                    "qecScheme", {},
                ).get("name", "surface_code")
                if isinstance(params.get("qecScheme"), dict)
                else "surface_code",
            )

        return estimate_chemistry(fcidump, config=config)

    def compare_with_trotter(
        self,
        trotter_steps: int = 1,
        trotter_order: int = 1,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Compare qubitization vs Trotter QPE resource estimates.

        Builds both a Trotter-based QPE circuit and a qubitization
        circuit, estimates resources for both, and returns a
        comparison table.

        Args:
            trotter_steps: Trotter steps for comparison.
            trotter_order: Trotter order for comparison.
            params: Optional estimator parameters.

        Returns:
            List of flat dicts, one per algorithm, suitable for
            tabular display.
        """
        from qdk_pythonic.domains.chemistry.qpe import ChemistryQPE
        from qdk_pythonic.execution.chemistry_estimate import (
            compare_estimates,
            parse_estimation_result,
        )

        ham = self._get_pauli_hamiltonian()

        # Trotter QPE estimate
        trotter_qpe = ChemistryQPE(
            hamiltonian=ham,
            n_electrons=self.n_electrons,
            n_estimation_qubits=self.n_estimation_qubits,
            trotter_steps=trotter_steps,
            trotter_order=trotter_order,
        )
        trotter_circ = trotter_qpe.to_circuit()
        trotter_raw = trotter_circ.estimate(params=params)
        trotter_est = parse_estimation_result(
            trotter_raw,
            algorithm_name="trotter_qpe",
            hamiltonian_info=ham.summary(),
        )

        # Qubitization QPE estimate
        from qdk_pythonic.domains.common.lcu import QubitizationQPE

        qubit_qpe = QubitizationQPE(
            hamiltonian=ham,
            n_electrons=self.n_electrons,
            n_estimation_qubits=self.n_estimation_qubits,
        )
        qubit_circ = qubit_qpe.to_circuit()
        qubit_raw = qubit_circ.estimate(params=params)
        qubit_est = parse_estimation_result(
            qubit_raw,
            algorithm_name="qubitization_qpe",
            hamiltonian_info=ham.summary(),
        )

        return compare_estimates([trotter_est, qubit_est])

    def _get_pauli_hamiltonian(self) -> PauliHamiltonian:
        """Extract or convert to PauliHamiltonian."""
        if isinstance(self.hamiltonian, PauliHamiltonian):
            return self.hamiltonian

        from qdk_pythonic.domains.common.double_factorization import (
            DoubleFactorizedHamiltonian,
        )

        if isinstance(self.hamiltonian, DoubleFactorizedHamiltonian):
            result: PauliHamiltonian = self.hamiltonian.to_pauli_hamiltonian()
            return result

        raise CircuitError(
            f"Unsupported Hamiltonian type: {type(self.hamiltonian)}"
        )
