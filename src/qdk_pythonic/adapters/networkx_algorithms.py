"""NetworkX adapter implementations registered as Algorithm subclasses.

Enables the create() -> run() pattern matching QDK/Chemistry.
"""

from __future__ import annotations

from typing import Any

from qdk_pythonic.registry import Algorithm, Settings, register

__all__ = [
    "NetworkXMaxCutHamiltonianBuilder",
    "NetworkXResourceEstimator",
    "QAOACircuitBuilder",
    "load",
]


class NetworkXMaxCutHamiltonianBuilder(Algorithm):
    """Build a MaxCut cost Hamiltonian from a NetworkX graph.

    Registered type: "hamiltonian_builder"
    Registered name: "networkx_maxcut"

    Example::

        from qdk_pythonic.registry import create

        builder = create("hamiltonian_builder", "networkx_maxcut")
        cost_h = builder.run(graph)
        cost_h.print_summary()
    """

    def type_name(self) -> str:
        return "hamiltonian_builder"

    def name(self) -> str:
        return "networkx_maxcut"

    def aliases(self) -> list[str]:
        return ["networkx_maxcut", "maxcut"]

    def _run_impl(self, graph: Any) -> Any:
        from qdk_pythonic.adapters.networkx_adapter import (
            maxcut_from_networkx,
        )

        problem = maxcut_from_networkx(graph)
        return problem.to_hamiltonian()


class QAOACircuitBuilderSettings(Settings):
    """Settings for the QAOA circuit builder."""

    def __init__(self) -> None:
        super().__init__()
        self._set_default("p", 1, int, "Number of QAOA layers")


class QAOACircuitBuilder(Algorithm):
    """Build a QAOA circuit from a cost Hamiltonian.

    Registered type: "circuit_builder"
    Registered name: "qaoa"

    Example::

        from qdk_pythonic.registry import create

        qaoa = create("circuit_builder", "qaoa", p=3)
        circuit = qaoa.run(cost_hamiltonian,
                           gamma=[0.5, 0.3, 0.1],
                           beta=[0.7, 0.5, 0.2])
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = QAOACircuitBuilderSettings()

    def type_name(self) -> str:
        return "circuit_builder"

    def name(self) -> str:
        return "qaoa"

    def _run_impl(
        self,
        cost_hamiltonian: Any,
        gamma: list[float] | None = None,
        beta: list[float] | None = None,
    ) -> Any:
        import math

        from qdk_pythonic.domains.optimization.qaoa import QAOA

        p = self._settings.get("p")
        if gamma is None:
            gamma = [math.pi / 4] * p
        if beta is None:
            beta = [math.pi / 8] * p

        qaoa = QAOA(cost_hamiltonian=cost_hamiltonian, p=p)
        return qaoa.to_circuit(gamma=gamma, beta=beta)


class NetworkXResourceEstimator(Algorithm):
    """End-to-end MaxCut QAOA resource estimation from a NetworkX graph.

    Registered type: "resource_estimator"
    Registered name: "networkx_maxcut_qaoa"
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = QAOACircuitBuilderSettings()

    def type_name(self) -> str:
        return "resource_estimator"

    def name(self) -> str:
        return "networkx_maxcut_qaoa"

    def _run_impl(
        self,
        graph: Any,
        estimate_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from qdk_pythonic.adapters.networkx_adapter import solve_maxcut

        return solve_maxcut(
            graph,
            p=self._settings.get("p"),
            estimate_params=estimate_params,
        )


def load() -> None:
    """Load NetworkX adapter algorithms into the registry."""
    register(lambda: NetworkXMaxCutHamiltonianBuilder())
    register(lambda: QAOACircuitBuilder())
    register(lambda: NetworkXResourceEstimator())
