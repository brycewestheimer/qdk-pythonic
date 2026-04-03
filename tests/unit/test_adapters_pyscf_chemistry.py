"""Unit tests for PySCF chemistry algorithm registry classes."""

from __future__ import annotations

import pytest

from qdk_pythonic.adapters.pyscf_chemistry import (
    PySCFQPEAlgorithm,
    PySCFQubitizationAlgorithm,
    PySCFVQEAlgorithm,
)


@pytest.mark.unit
def test_qpe_type_and_name() -> None:
    alg = PySCFQPEAlgorithm()
    assert alg.type_name() == "chemistry_algorithm"
    assert alg.name() == "pyscf_qpe"
    assert "pyscf_qpe" in alg.aliases()


@pytest.mark.unit
def test_qpe_settings_defaults() -> None:
    alg = PySCFQPEAlgorithm()
    s = alg.settings()
    assert s.get("basis") == "sto-3g"
    assert s.get("charge") == 0
    assert s.get("spin") == 0
    assert s.get("active_electrons") is None
    assert s.get("active_orbitals") is None
    assert s.get("qubit_mapping") == "jordan_wigner"
    assert s.get("n_estimation_qubits") == 8
    assert s.get("evolution_time") == 1.0
    assert s.get("trotter_steps") == 1
    assert s.get("trotter_order") == 1


@pytest.mark.unit
def test_qpe_settings_describe() -> None:
    alg = PySCFQPEAlgorithm()
    desc = alg.settings().describe()
    keys = [d[0] for d in desc]
    assert "basis" in keys
    assert "n_estimation_qubits" in keys
    assert "evolution_time" in keys


@pytest.mark.unit
def test_vqe_type_and_name() -> None:
    alg = PySCFVQEAlgorithm()
    assert alg.type_name() == "chemistry_algorithm"
    assert alg.name() == "pyscf_vqe"
    assert "pyscf_vqe" in alg.aliases()


@pytest.mark.unit
def test_vqe_settings_defaults() -> None:
    alg = PySCFVQEAlgorithm()
    s = alg.settings()
    assert s.get("basis") == "sto-3g"
    assert s.get("charge") == 0
    assert s.get("ansatz") == "uccsd"
    assert s.get("optimizer") == "COBYLA"
    assert s.get("max_iterations") == 100
    assert s.get("shots") == 10000


@pytest.mark.unit
def test_vqe_settings_describe() -> None:
    alg = PySCFVQEAlgorithm()
    desc = alg.settings().describe()
    keys = [d[0] for d in desc]
    assert "basis" in keys
    assert "ansatz" in keys
    assert "optimizer" in keys


@pytest.mark.unit
def test_qubitization_type_and_name() -> None:
    alg = PySCFQubitizationAlgorithm()
    assert alg.type_name() == "chemistry_algorithm"
    assert alg.name() == "pyscf_qubitization"
    assert "pyscf_qubitization" in alg.aliases()
    assert "pyscf_df" in alg.aliases()


@pytest.mark.unit
def test_qubitization_settings_defaults() -> None:
    alg = PySCFQubitizationAlgorithm()
    s = alg.settings()
    assert s.get("basis") == "sto-3g"
    assert s.get("charge") == 0
    assert s.get("error_budget") == 0.01
    assert s.get("qubit_params") == "qubit_gate_ns_e3"
    assert s.get("qec_scheme") == "surface_code"


@pytest.mark.unit
def test_qubitization_settings_describe() -> None:
    alg = PySCFQubitizationAlgorithm()
    desc = alg.settings().describe()
    keys = [d[0] for d in desc]
    assert "basis" in keys
    assert "error_budget" in keys
    assert "qubit_params" in keys
