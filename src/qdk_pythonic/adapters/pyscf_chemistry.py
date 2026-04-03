"""PySCF chemistry algorithm implementations for the registry.

Provides registry-integrated QPE and VQE algorithms that combine
PySCF electronic structure with qdk-pythonic quantum algorithms.
"""

from __future__ import annotations

from typing import Any

from qdk_pythonic.registry import Algorithm, Settings, register

__all__ = [
    "PySCFQPEAlgorithm",
    "PySCFQubitizationAlgorithm",
    "PySCFVQEAlgorithm",
    "load",
]


class PySCFQPESettings(Settings):
    """Settings for PySCF-based QPE."""

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
        self._set_default(
            "n_estimation_qubits", 8, int,
            "Number of phase estimation qubits",
        )
        self._set_default(
            "evolution_time", 1.0, float,
            "Hamiltonian evolution time",
        )
        self._set_default(
            "trotter_steps", 1, int, "Trotter steps",
        )
        self._set_default(
            "trotter_order", 1, int, "Trotter-Suzuki order",
        )


class PySCFQPEAlgorithm(Algorithm):
    """QPE for molecular ground-state energy via PySCF.

    Registered type: ``"chemistry_algorithm"``
    Registered name: ``"pyscf_qpe"``

    Example::

        from qdk_pythonic.registry import create

        qpe = create("chemistry_algorithm", "pyscf_qpe",
                      basis="sto-3g",
                      n_estimation_qubits=10)
        result = qpe.run(atom="H 0 0 0; H 0 0 0.74")
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = PySCFQPESettings()

    def type_name(self) -> str:
        return "chemistry_algorithm"

    def name(self) -> str:
        return "pyscf_qpe"

    def aliases(self) -> list[str]:
        return ["pyscf_qpe"]

    def _run_impl(
        self,
        atom: str,
        estimate_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from qdk_pythonic.adapters.pyscf_adapter import (
            molecular_hamiltonian,
        )
        from qdk_pythonic.domains.chemistry.qpe import ChemistryQPE

        s = self._settings
        h = molecular_hamiltonian(
            atom=atom,
            basis=s.get("basis"),
            charge=s.get("charge"),
            spin=s.get("spin"),
            n_active_electrons=s.get("active_electrons"),
            n_active_orbitals=s.get("active_orbitals"),
            mapping=s.get("qubit_mapping"),
        )

        # Determine electron count for HF state
        n_active_e = s.get("active_electrons")
        if n_active_e is None:
            from qdk_pythonic.adapters.pyscf_adapter import run_scf
            scf_obj = run_scf(
                atom, s.get("basis"), s.get("charge"), s.get("spin"),
            )
            n_active_e = int(scf_obj.mol.nelectron)

        qpe = ChemistryQPE(
            hamiltonian=h,
            n_electrons=n_active_e,
            n_estimation_qubits=s.get("n_estimation_qubits"),
            evolution_time=s.get("evolution_time"),
            trotter_steps=s.get("trotter_steps"),
            trotter_order=s.get("trotter_order"),
        )

        circuit = qpe.to_circuit()
        result: dict[str, Any] = {
            "hamiltonian": h,
            "hamiltonian_summary": h.summary(),
            "circuit": circuit,
            "n_qubits": circuit.qubit_count(),
            "total_gates": circuit.total_gate_count(),
        }

        if estimate_params is not None:
            result["estimate_result"] = circuit.estimate(
                params=estimate_params,
            )

        return result


class PySCFVQESettings(Settings):
    """Settings for PySCF-based VQE."""

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
        self._set_default(
            "ansatz", "uccsd", str,
            "Ansatz type ('uccsd' or 'hardware_efficient')",
        )
        self._set_default(
            "optimizer", "COBYLA", str,
            "Classical optimizer for scipy.optimize.minimize",
        )
        self._set_default(
            "max_iterations", 100, int, "Maximum optimizer iterations",
        )
        self._set_default("shots", 10000, int, "Measurement shots")


class PySCFVQEAlgorithm(Algorithm):
    """VQE for molecular ground-state energy via PySCF.

    Registered type: ``"chemistry_algorithm"``
    Registered name: ``"pyscf_vqe"``

    Example::

        from qdk_pythonic.registry import create

        vqe = create("chemistry_algorithm", "pyscf_vqe",
                      optimizer="COBYLA", max_iterations=200)
        result = vqe.run(atom="H 0 0 0; H 0 0 0.74")
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = PySCFVQESettings()

    def type_name(self) -> str:
        return "chemistry_algorithm"

    def name(self) -> str:
        return "pyscf_vqe"

    def aliases(self) -> list[str]:
        return ["pyscf_vqe"]

    def _run_impl(
        self,
        atom: str,
        initial_params: list[float] | None = None,
        **kwargs: Any,
    ) -> Any:
        from qdk_pythonic.adapters.pyscf_adapter import (
            molecular_hamiltonian,
            run_scf,
        )
        from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz
        from qdk_pythonic.domains.chemistry.vqe import VQE
        from qdk_pythonic.domains.common.ansatz import (
            HardwareEfficientAnsatz,
        )

        s = self._settings
        h = molecular_hamiltonian(
            atom=atom,
            basis=s.get("basis"),
            charge=s.get("charge"),
            spin=s.get("spin"),
            n_active_electrons=s.get("active_electrons"),
            n_active_orbitals=s.get("active_orbitals"),
            mapping=s.get("qubit_mapping"),
        )

        scf_obj = run_scf(
            atom, s.get("basis"), s.get("charge"), s.get("spin"),
        )
        n_electrons: int = int(scf_obj.mol.nelectron)
        n_active_e = s.get("active_electrons")
        if n_active_e is not None:
            n_electrons = n_active_e

        n_orbitals = len(scf_obj.mo_energy)
        n_active_o = s.get("active_orbitals")
        if n_active_o is not None:
            n_orbitals = n_active_o

        ansatz_type: str = s.get("ansatz")
        ansatz: UCCSDAnsatz | HardwareEfficientAnsatz
        if ansatz_type == "uccsd":
            ansatz = UCCSDAnsatz(
                n_spatial_orbitals=n_orbitals,
                n_electrons=n_electrons,
                mapping=s.get("qubit_mapping"),
            )
        else:
            ansatz = HardwareEfficientAnsatz(
                n_qubits=2 * n_orbitals,
                depth=2,
            )

        vqe = VQE(
            hamiltonian=h,
            ansatz=ansatz,
            n_electrons=n_electrons,
            optimizer=s.get("optimizer"),
            max_iterations=s.get("max_iterations"),
            shots=s.get("shots"),
        )

        return vqe.run(initial_params=initial_params)


class PySCFQubitizationSettings(Settings):
    """Settings for PySCF-based qubitization resource estimation."""

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
            "error_budget", 0.01, float, "Error budget",
        )
        self._set_default(
            "qubit_params", "qubit_gate_ns_e3", str,
            "Qubit parameter model",
        )
        self._set_default(
            "qec_scheme", "surface_code", str, "QEC scheme",
        )


class PySCFQubitizationAlgorithm(Algorithm):
    """DF-qubitization resource estimation via PySCF + qsharp.chemistry.

    Registered type: ``"chemistry_algorithm"``
    Registered name: ``"pyscf_qubitization"``

    Example::

        from qdk_pythonic.registry import create

        est = create("chemistry_algorithm", "pyscf_qubitization",
                      basis="cc-pvdz")
        result = est.run(atom="H 0 0 0; H 0 0 0.74")
    """

    def __init__(self) -> None:
        super().__init__()
        self._settings = PySCFQubitizationSettings()

    def type_name(self) -> str:
        return "chemistry_algorithm"

    def name(self) -> str:
        return "pyscf_qubitization"

    def aliases(self) -> list[str]:
        return ["pyscf_qubitization", "pyscf_df"]

    def _run_impl(
        self,
        atom: str,
        **kwargs: Any,
    ) -> Any:
        from qdk_pythonic.execution.chemistry_bridge import (
            ChemistryEstimationConfig,
            estimate_chemistry_from_pyscf,
        )

        s = self._settings
        config = ChemistryEstimationConfig(
            error_budget=s.get("error_budget"),
            qubit_params=s.get("qubit_params"),
            qec_scheme=s.get("qec_scheme"),
        )
        return estimate_chemistry_from_pyscf(
            atom=atom,
            basis=s.get("basis"),
            charge=s.get("charge"),
            spin=s.get("spin"),
            n_active_electrons=s.get("active_electrons"),
            n_active_orbitals=s.get("active_orbitals"),
            config=config,
        )


def load() -> None:
    """Load PySCF chemistry algorithms into the registry."""
    register(lambda: PySCFQPEAlgorithm())
    register(lambda: PySCFVQEAlgorithm())
    register(lambda: PySCFQubitizationAlgorithm())
