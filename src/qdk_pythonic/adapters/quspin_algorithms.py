"""QuSpin adapter implementations registered as Algorithm subclasses.

Enables the create() -> run() pattern matching QDK/Chemistry.
"""

from __future__ import annotations

from typing import Any

from qdk_pythonic.registry import Algorithm, Settings, register

__all__ = [
    "QuSpinHamiltonianBuilder",
    "QuSpinResourceEstimator",
    "TrotterEvolutionBuilder",
    "load",
]


class QuSpinHamiltonianBuilderSettings(Settings):
    """Settings for the QuSpin Hamiltonian builder."""

    def __init__(self) -> None:
        super().__init__()
        # No additional settings — the QuSpin static_list fully
        # specifies the Hamiltonian.


class QuSpinHamiltonianBuilder(Algorithm):
    """Build a PauliHamiltonian from a QuSpin operator specification.

    Registered type: "hamiltonian_builder"
    Registered name: "quspin"

    Example::

        from qdk_pythonic.registry import create

        builder = create("hamiltonian_builder", "quspin")
        hamiltonian = builder.run(static_list, n_sites=8)
        hamiltonian.print_summary()
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = QuSpinHamiltonianBuilderSettings()

    def type_name(self) -> str:
        return "hamiltonian_builder"

    def name(self) -> str:
        return "quspin"

    def aliases(self) -> list[str]:
        return ["quspin", "quspin_static"]

    def _run_impl(
        self,
        static_list: list[list[Any]],
        n_sites: int,
    ) -> Any:
        from qdk_pythonic.adapters.quspin_adapter import (
            from_quspin_static_list,
        )

        return from_quspin_static_list(static_list, n_sites)


class TrotterEvolutionBuilderSettings(Settings):
    """Settings for the Trotter time evolution builder."""

    def __init__(self) -> None:
        super().__init__()
        self._set_default("time", 1.0, float, "Total evolution time")
        self._set_default(
            "steps", 10, int, "Number of Trotter steps",
        )
        self._set_default(
            "order", 1, int, "Trotter-Suzuki order (1 or 2)",
        )


class TrotterEvolutionBuilder(Algorithm):
    """Build a Trotter time evolution circuit from a PauliHamiltonian.

    Registered type: "time_evolution_builder"
    Registered name: "trotter"

    Example::

        from qdk_pythonic.registry import create

        builder = create("time_evolution_builder", "trotter",
                         time=1.0, steps=10, order=2)
        circuit = builder.run(hamiltonian)
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = TrotterEvolutionBuilderSettings()

    def type_name(self) -> str:
        return "time_evolution_builder"

    def name(self) -> str:
        return "trotter"

    def _run_impl(self, hamiltonian: Any) -> Any:
        from qdk_pythonic.domains.common.evolution import TrotterEvolution

        evolution = TrotterEvolution(
            hamiltonian=hamiltonian,
            time=self._settings.get("time"),
            steps=self._settings.get("steps"),
            order=self._settings.get("order"),
        )
        return evolution.to_circuit()


class QuSpinResourceEstimatorSettings(Settings):
    """Settings for the end-to-end QuSpin resource estimator."""

    def __init__(self) -> None:
        super().__init__()
        self._set_default("time", 1.0, float, "Total evolution time")
        self._set_default(
            "trotter_steps", 10, int, "Number of Trotter steps",
        )
        self._set_default(
            "trotter_order", 1, int, "Trotter-Suzuki order",
        )


class QuSpinResourceEstimator(Algorithm):
    """End-to-end resource estimation for a QuSpin model.

    Registered type: "resource_estimator"
    Registered name: "quspin_trotter"

    Chains: QuSpin static_list -> PauliHamiltonian -> Trotter ->
    Circuit -> estimate.

    Example::

        from qdk_pythonic.registry import create

        estimator = create("resource_estimator", "quspin_trotter",
                           time=2.0, trotter_steps=20, trotter_order=2)
        result = estimator.run(static_list, n_sites=8)
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = QuSpinResourceEstimatorSettings()

    def type_name(self) -> str:
        return "resource_estimator"

    def name(self) -> str:
        return "quspin_trotter"

    def _run_impl(
        self,
        static_list: list[list[Any]],
        n_sites: int,
        estimate_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from qdk_pythonic.adapters.quspin_adapter import (
            simulate_quspin_model,
        )

        return simulate_quspin_model(
            static_list=static_list,
            n_sites=n_sites,
            time=self._settings.get("time"),
            trotter_steps=self._settings.get("trotter_steps"),
            trotter_order=self._settings.get("trotter_order"),
            estimate_params=estimate_params,
        )


# ── Plugin Registration ──


def load() -> None:
    """Load QuSpin adapter algorithms into the registry.

    Mirrors the qdk_chemistry.plugins.pyscf.load() pattern.
    """
    register(lambda: QuSpinHamiltonianBuilder())
    register(lambda: TrotterEvolutionBuilder())
    register(lambda: QuSpinResourceEstimator())
