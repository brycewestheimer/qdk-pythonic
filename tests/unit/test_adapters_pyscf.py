"""Unit tests for PySCF adapter algorithm classes.

These tests verify registration and settings without requiring PySCF.
"""

from __future__ import annotations

import pytest

from qdk_pythonic.adapters.pyscf_algorithms import (
    PySCFHamiltonianBuilder,
    PySCFResourceEstimator,
)


@pytest.mark.unit
def test_pyscf_algorithm_type_and_name() -> None:
    builder = PySCFHamiltonianBuilder()
    assert builder.type_name() == "hamiltonian_builder"
    assert builder.name() == "pyscf"
    assert "pyscf" in builder.aliases()
    assert "pyscf_rhf" in builder.aliases()


@pytest.mark.unit
def test_pyscf_algorithm_settings() -> None:
    builder = PySCFHamiltonianBuilder()
    s = builder.settings()
    assert s.get("basis") == "sto-3g"
    assert s.get("charge") == 0
    assert s.get("spin") == 0
    assert s.get("active_electrons") is None
    assert s.get("active_orbitals") is None
    assert s.get("qubit_mapping") == "jordan_wigner"


@pytest.mark.unit
def test_pyscf_settings_describe() -> None:
    builder = PySCFHamiltonianBuilder()
    desc = builder.settings().describe()
    keys = [d[0] for d in desc]
    assert "basis" in keys
    assert "charge" in keys
    assert "qubit_mapping" in keys


@pytest.mark.unit
def test_pyscf_resource_estimator_type_and_name() -> None:
    est = PySCFResourceEstimator()
    assert est.type_name() == "resource_estimator"
    assert est.name() == "pyscf_trotter"


@pytest.mark.unit
def test_pyscf_resource_estimator_settings() -> None:
    est = PySCFResourceEstimator()
    s = est.settings()
    # Chemistry settings
    assert s.get("basis") == "sto-3g"
    # Trotter settings
    assert s.get("time") == 1.0
    assert s.get("trotter_steps") == 10
    assert s.get("trotter_order") == 1
