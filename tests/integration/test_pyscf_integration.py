"""Integration tests for the PySCF chemistry adapter.

Requires PySCF: ``pip install pyscf>=2.0``
"""

from __future__ import annotations

import pytest

pyscf = pytest.importorskip("pyscf")


@pytest.mark.integration
def test_h2_scf_converges() -> None:
    from qdk_pythonic.adapters.pyscf_adapter import run_scf

    mf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    assert mf.converged


@pytest.mark.integration
def test_h2_integrals_shape() -> None:
    from qdk_pythonic.adapters.pyscf_adapter import get_integrals, run_scf

    mf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    h1e, h2e, nuc = get_integrals(mf)
    assert h1e.shape == (2, 2)
    assert h2e.shape == (2, 2, 2, 2)
    assert nuc > 0


@pytest.mark.integration
def test_h2_molecular_hamiltonian_jw() -> None:
    from qdk_pythonic.adapters.pyscf_adapter import molecular_hamiltonian

    h = molecular_hamiltonian(
        "H 0 0 0; H 0 0 0.74", basis="sto-3g", mapping="jordan_wigner",
    )
    # H2 in STO-3G: 2 spatial orbitals -> 4 spin-orbitals -> 4 qubits
    assert h.qubit_count() <= 4
    assert len(h.terms) > 0


@pytest.mark.integration
def test_h2_molecular_hamiltonian_bk() -> None:
    from qdk_pythonic.adapters.pyscf_adapter import molecular_hamiltonian

    h = molecular_hamiltonian(
        "H 0 0 0; H 0 0 0.74", basis="sto-3g", mapping="bravyi_kitaev",
    )
    assert h.qubit_count() <= 4
    assert len(h.terms) > 0


@pytest.mark.integration
def test_molecular_summary_structure() -> None:
    from qdk_pythonic.adapters.pyscf_adapter import molecular_summary

    result = molecular_summary("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    assert "scf_energy" in result
    assert "n_orbitals" in result
    assert "n_electrons" in result
    assert "hamiltonian" in result
    assert "hamiltonian_summary" in result
    assert "circuit" in result
    assert "n_qubits" in result
    assert result["n_orbitals"] == 2
    assert result["n_electrons"] == 2


@pytest.mark.integration
def test_create_pyscf_builder() -> None:
    from qdk_pythonic.adapters.pyscf_algorithms import load
    from qdk_pythonic.registry import _factories, create

    original = list(_factories)
    try:
        load()
        builder = create("hamiltonian_builder", "pyscf")
        h = builder.run(atom="H 0 0 0; H 0 0 0.74")
        assert h.qubit_count() <= 4
        assert len(h.terms) > 0
    finally:
        _factories.clear()
        _factories.extend(original)
