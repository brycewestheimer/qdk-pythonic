"""Tests for MolecularOrbitalInfo."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.chemistry.orbital_info import MolecularOrbitalInfo


@pytest.mark.unit
def test_n_electrons() -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0, -0.5, 0.3, 0.8),
        occupation_numbers=(2.0, 2.0, 0.0, 0.0),
        n_alpha=2,
        n_beta=2,
        n_spatial_orbitals=4,
        active_space=None,
        hf_energy=-1.5,
        nuclear_repulsion=0.7,
    )
    assert info.n_electrons == 4


@pytest.mark.unit
def test_n_qubits_full_space() -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0, 0.5),
        occupation_numbers=(2.0, 0.0),
        n_alpha=1,
        n_beta=1,
        n_spatial_orbitals=2,
        active_space=None,
        hf_energy=-1.0,
        nuclear_repulsion=0.5,
    )
    assert info.n_qubits == 4  # 2 * 2 spatial


@pytest.mark.unit
def test_n_qubits_active_space() -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0, -0.5, 0.3, 0.8),
        occupation_numbers=(2.0, 2.0, 0.0, 0.0),
        n_alpha=2,
        n_beta=2,
        n_spatial_orbitals=4,
        active_space=(2, 2),
        hf_energy=-1.5,
        nuclear_repulsion=0.7,
    )
    assert info.n_qubits == 4  # 2 * 2 active orbitals


@pytest.mark.unit
def test_n_active_electrons_full() -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0, 0.5),
        occupation_numbers=(2.0, 0.0),
        n_alpha=1,
        n_beta=1,
        n_spatial_orbitals=2,
        active_space=None,
        hf_energy=-1.0,
        nuclear_repulsion=0.5,
    )
    assert info.n_active_electrons == 2


@pytest.mark.unit
def test_n_active_electrons_active_space() -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0, -0.5, 0.3, 0.8),
        occupation_numbers=(2.0, 2.0, 0.0, 0.0),
        n_alpha=2,
        n_beta=2,
        n_spatial_orbitals=4,
        active_space=(2, 3),
        hf_energy=-1.5,
        nuclear_repulsion=0.7,
    )
    assert info.n_active_electrons == 2


@pytest.mark.unit
def test_print_report(capsys: pytest.CaptureFixture[str]) -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0, 0.5),
        occupation_numbers=(2.0, 0.0),
        n_alpha=1,
        n_beta=1,
        n_spatial_orbitals=2,
        active_space=None,
        hf_energy=-1.12345678,
        nuclear_repulsion=0.71376600,
    )
    info.print_report()
    captured = capsys.readouterr()
    assert "Hartree-Fock energy" in captured.out
    assert "Nuclear repulsion" in captured.out
    assert "MO" in captured.out


@pytest.mark.unit
def test_print_report_with_active_space(
    capsys: pytest.CaptureFixture[str],
) -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0, -0.5, 0.3),
        occupation_numbers=(2.0, 2.0, 0.0),
        n_alpha=2,
        n_beta=2,
        n_spatial_orbitals=3,
        active_space=(2, 2),
        hf_energy=-2.0,
        nuclear_repulsion=1.0,
    )
    info.print_report()
    captured = capsys.readouterr()
    assert "Active space" in captured.out


@pytest.mark.unit
def test_frozen() -> None:
    info = MolecularOrbitalInfo(
        orbital_energies=(-1.0,),
        occupation_numbers=(2.0,),
        n_alpha=1,
        n_beta=1,
        n_spatial_orbitals=1,
        active_space=None,
        hf_energy=-0.5,
        nuclear_repulsion=0.0,
    )
    with pytest.raises(AttributeError):
        info.hf_energy = -1.0  # type: ignore[misc]
