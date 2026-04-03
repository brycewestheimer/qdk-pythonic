"""PySCF adapter implementations registered as Algorithm subclasses.

Enables the create() -> run() pattern matching QDK/Chemistry.
"""

from __future__ import annotations

from typing import Any

from qdk_pythonic.registry import Algorithm, Settings, register

__all__ = [
    "PySCFHamiltonianBuilder",
    "PySCFResourceEstimator",
    "load",
]


class PySCFHamiltonianBuilderSettings(Settings):
    """Settings for the PySCF Hamiltonian builder."""

    def __init__(self) -> None:
        super().__init__()
        self._set_default("basis", "sto-3g", str, "Basis set")
        self._set_default("charge", 0, int, "Molecular charge")
        self._set_default(
            "spin", 0, int, "2S (number of unpaired electrons)",
        )
        self._set_default(
            "active_electrons", None, object,
            "Active electrons (None = all)",
        )
        self._set_default(
            "active_orbitals", None, object,
            "Active orbitals (None = all)",
        )
        self._set_default(
            "qubit_mapping", "jordan_wigner", str,
            "Fermion-to-qubit mapping",
        )


class PySCFHamiltonianBuilder(Algorithm):
    """Build a qubit Hamiltonian from a PySCF molecular specification.

    Registered type: "hamiltonian_builder"
    Registered name: "pyscf"

    Runs: geometry -> PySCF RHF/ROHF -> active space -> integrals
    -> Jordan-Wigner or Bravyi-Kitaev mapping -> PauliHamiltonian.

    Example::

        from qdk_pythonic.registry import create

        builder = create("hamiltonian_builder", "pyscf",
                         basis="cc-pvdz",
                         active_electrons=6,
                         active_orbitals=6)
        hamiltonian = builder.run(atom="N 0 0 0; N 0 0 1.1")
        hamiltonian.print_summary()
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = PySCFHamiltonianBuilderSettings()

    def type_name(self) -> str:
        return "hamiltonian_builder"

    def name(self) -> str:
        return "pyscf"

    def aliases(self) -> list[str]:
        return ["pyscf", "pyscf_rhf"]

    def _run_impl(self, atom: str, **kwargs: Any) -> Any:
        from qdk_pythonic.adapters.pyscf_adapter import (
            molecular_hamiltonian,
        )

        s = self._settings
        return molecular_hamiltonian(
            atom=atom,
            basis=s.get("basis"),
            charge=s.get("charge"),
            spin=s.get("spin"),
            n_active_electrons=s.get("active_electrons"),
            n_active_orbitals=s.get("active_orbitals"),
            mapping=s.get("qubit_mapping"),
        )


class PySCFResourceEstimatorSettings(Settings):
    """Settings for end-to-end PySCF resource estimation."""

    def __init__(self) -> None:
        super().__init__()
        self._set_default("basis", "sto-3g", str, "Basis set")
        self._set_default("charge", 0, int, "Molecular charge")
        self._set_default(
            "spin", 0, int, "2S (number of unpaired electrons)",
        )
        self._set_default(
            "active_electrons", None, object,
            "Active electrons (None = all)",
        )
        self._set_default(
            "active_orbitals", None, object,
            "Active orbitals (None = all)",
        )
        self._set_default(
            "qubit_mapping", "jordan_wigner", str,
            "Fermion-to-qubit mapping",
        )
        self._set_default("time", 1.0, float, "Evolution time")
        self._set_default(
            "trotter_steps", 10, int, "Number of Trotter steps",
        )
        self._set_default(
            "trotter_order", 1, int, "Trotter-Suzuki order",
        )


class PySCFResourceEstimator(Algorithm):
    """End-to-end resource estimation for a molecule via PySCF.

    Registered type: "resource_estimator"
    Registered name: "pyscf_trotter"
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = PySCFResourceEstimatorSettings()

    def type_name(self) -> str:
        return "resource_estimator"

    def name(self) -> str:
        return "pyscf_trotter"

    def _run_impl(
        self,
        atom: str,
        estimate_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from qdk_pythonic.adapters.pyscf_adapter import (
            molecular_summary,
        )

        return molecular_summary(
            atom=atom,
            basis=self._settings.get("basis"),
            charge=self._settings.get("charge"),
            spin=self._settings.get("spin"),
            n_active_electrons=self._settings.get("active_electrons"),
            n_active_orbitals=self._settings.get("active_orbitals"),
            mapping=self._settings.get("qubit_mapping"),
            estimate_params=estimate_params,
        )


def load() -> None:
    """Load PySCF adapter algorithms into the registry."""
    register(lambda: PySCFHamiltonianBuilder())
    register(lambda: PySCFResourceEstimator())
