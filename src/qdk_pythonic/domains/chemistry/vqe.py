"""Variational Quantum Eigensolver (VQE).

Hybrid quantum-classical algorithm for finding molecular ground-state
energies using a parametrized ansatz circuit and classical optimization.

Example::

    from qdk_pythonic.domains.chemistry.vqe import VQE
    from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz

    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    vqe = VQE(hamiltonian=h, ansatz=ansatz, n_electrons=2)
    result = vqe.run()
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qdk_pythonic.domains.common.operators import PauliHamiltonian
from qdk_pythonic.exceptions import CircuitError

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit
    from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz
    from qdk_pythonic.domains.common.ansatz import HardwareEfficientAnsatz


def _import_scipy_minimize() -> Any:
    """Lazily import scipy.optimize.minimize."""
    try:
        from scipy.optimize import minimize
    except ImportError as exc:
        raise ImportError(
            "scipy is required for VQE optimization. "
            "Install it with: pip install qdk-pythonic[chemistry]"
        ) from exc
    return minimize


@dataclass(frozen=True)
class VQEResult:
    """Result of a VQE optimization.

    Attributes:
        optimal_energy: Best energy found (Hartree).
        optimal_params: Parameters at the minimum.
        history: Energy values at each iteration.
        n_iterations: Number of optimizer iterations.
        converged: Whether the optimizer converged.
    """

    optimal_energy: float
    optimal_params: tuple[float, ...]
    history: tuple[float, ...]
    n_iterations: int
    converged: bool


@dataclass
class VQE:
    """Variational Quantum Eigensolver.

    Uses a parametrized ansatz circuit and a classical optimizer
    to minimize ``<psi(theta)|H|psi(theta)>``.

    Attributes:
        hamiltonian: Molecular Hamiltonian.
        ansatz: Parametrized ansatz (UCCSDAnsatz or
            HardwareEfficientAnsatz).
        n_electrons: Number of electrons for HF initial state.
            Required when ansatz is UCCSDAnsatz.
        optimizer: Classical optimizer name compatible with
            ``scipy.optimize.minimize`` (e.g. ``"COBYLA"``,
            ``"L-BFGS-B"``, ``"Nelder-Mead"``).
        max_iterations: Maximum optimizer iterations.
        shots: Number of measurement shots per expectation value.
        tol: Convergence tolerance.
    """

    hamiltonian: PauliHamiltonian
    ansatz: UCCSDAnsatz | HardwareEfficientAnsatz
    n_electrons: int | None = None
    optimizer: str = "COBYLA"
    max_iterations: int = 100
    shots: int = 10000
    tol: float = 1e-6

    def _get_num_parameters(self) -> int:
        return self.ansatz.num_parameters

    def to_circuit(self, params: Sequence[float]) -> Circuit:
        """Build the VQE trial-state circuit for given parameters.

        For UCCSDAnsatz, the HF state is built into the ansatz.
        For HardwareEfficientAnsatz, the HF state is prepended
        if ``n_electrons`` is set.

        Args:
            params: Variational parameter values.

        Returns:
            The trial-state circuit.
        """
        from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz

        if isinstance(self.ansatz, UCCSDAnsatz):
            return self.ansatz.to_circuit(params)

        # HardwareEfficientAnsatz path
        circ = self.ansatz.to_circuit(params)

        if self.n_electrons is not None and self.n_electrons > 0:
            from qdk_pythonic.core.circuit import Circuit as Circ
            from qdk_pythonic.domains.chemistry.hartree_fock import (
                HartreeFockState,
            )

            hf = HartreeFockState(
                n_qubits=self.ansatz.n_qubits,
                n_electrons=self.n_electrons,
            )
            hf_circ = hf.to_circuit()
            combined = Circ()
            q = combined.allocate(self.ansatz.n_qubits)
            hf_map = {
                src.index: q[i]
                for i, src in enumerate(hf_circ.qubits)
            }
            combined.compose_into(hf_circ, qubit_map=hf_map)
            ansatz_map = {
                src.index: q[i]
                for i, src in enumerate(circ.qubits)
            }
            combined.compose_into(circ, qubit_map=ansatz_map)
            return combined

        return circ

    def expectation_value(
        self,
        params: Sequence[float],
        seed: int | None = None,
    ) -> float:
        """Compute ``<psi(params)|H|psi(params)>`` via simulation.

        Args:
            params: Variational parameter values.
            seed: Optional random seed.

        Returns:
            The expectation value.
        """
        from qdk_pythonic.domains.chemistry.expectation import (
            pauli_expectation_value,
        )

        circ = self.to_circuit(params)
        return pauli_expectation_value(
            self.hamiltonian, circ,
            shots=self.shots, seed=seed,
        )

    def run(
        self,
        initial_params: Sequence[float] | None = None,
    ) -> VQEResult:
        """Run the full VQE optimization loop.

        Args:
            initial_params: Starting parameter values. Defaults to
                all zeros.

        Returns:
            A VQEResult with optimal energy, parameters, and history.

        Raises:
            ExecutionError: If optimization fails.
        """
        minimize = _import_scipy_minimize()

        n_params = self._get_num_parameters()
        if initial_params is None:
            x0 = [0.0] * n_params
        else:
            x0 = list(initial_params)
            if len(x0) != n_params:
                raise CircuitError(
                    f"Expected {n_params} initial params, "
                    f"got {len(x0)}"
                )

        history: list[float] = []

        def objective(params: Any) -> float:
            energy = self.expectation_value(list(params))
            history.append(energy)
            return energy

        result = minimize(
            objective,
            x0=x0,
            method=self.optimizer,
            options={"maxiter": self.max_iterations},
            tol=self.tol,
        )

        return VQEResult(
            optimal_energy=float(result.fun),
            optimal_params=tuple(float(p) for p in result.x),
            history=tuple(history),
            n_iterations=len(history),
            converged=bool(result.success),
        )

    def estimate_resources(
        self,
        params: Sequence[float] | None = None,
        estimate_params: dict[str, Any] | None = None,
    ) -> Any:
        """Resource estimation for the trial-state circuit.

        Args:
            params: Parameter values for the circuit. Defaults to
                all zeros.
            estimate_params: Optional resource estimator parameters.

        Returns:
            The resource estimation result.
        """
        n_params = self._get_num_parameters()
        if params is None:
            params = [0.0] * n_params
        circ = self.to_circuit(params)
        return circ.estimate(params=estimate_params)
