"""Molecular orbital information from electronic structure calculations.

Example::

    from qdk_pythonic.adapters.pyscf_adapter import run_scf
    from qdk_pythonic.domains.chemistry.orbital_info import (
        MolecularOrbitalInfo,
    )

    scf_obj = run_scf("H 0 0 0; H 0 0 0.74")
    info = MolecularOrbitalInfo.from_pyscf(scf_obj)
    info.print_report()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MolecularOrbitalInfo:
    """Information about molecular orbitals from an SCF calculation.

    Attributes:
        orbital_energies: MO energies in Hartree, sorted ascending.
        occupation_numbers: Occupancy of each orbital (0.0, 1.0, or 2.0).
        n_alpha: Number of alpha electrons.
        n_beta: Number of beta electrons.
        n_spatial_orbitals: Total spatial orbitals.
        active_space: Optional ``(n_active_electrons, n_active_orbitals)``
            if active space selection was used.
        hf_energy: Hartree-Fock total energy in Hartree.
        nuclear_repulsion: Nuclear repulsion energy in Hartree.
    """

    orbital_energies: tuple[float, ...]
    occupation_numbers: tuple[float, ...]
    n_alpha: int
    n_beta: int
    n_spatial_orbitals: int
    active_space: tuple[int, int] | None
    hf_energy: float
    nuclear_repulsion: float

    @property
    def n_electrons(self) -> int:
        """Total number of electrons."""
        return self.n_alpha + self.n_beta

    @property
    def n_qubits(self) -> int:
        """Number of qubits needed (2 * active spatial orbitals)."""
        if self.active_space is not None:
            return 2 * self.active_space[1]
        return 2 * self.n_spatial_orbitals

    @property
    def n_active_electrons(self) -> int:
        """Number of active electrons."""
        if self.active_space is not None:
            return self.active_space[0]
        return self.n_electrons

    def print_report(self) -> None:
        """Print a human-readable orbital report."""
        print(f"Hartree-Fock energy: {self.hf_energy:.8f} Ha")
        print(f"Nuclear repulsion:   {self.nuclear_repulsion:.8f} Ha")
        print(
            f"Electrons: {self.n_electrons} "
            f"(alpha={self.n_alpha}, beta={self.n_beta})"
        )
        print(f"Spatial orbitals: {self.n_spatial_orbitals}")
        if self.active_space is not None:
            ne, no = self.active_space
            print(f"Active space: ({ne}e, {no}o)")
        print(f"Qubits required: {self.n_qubits}")
        print()
        print("Orbital energies (Ha):")
        for i, (e, occ) in enumerate(
            zip(self.orbital_energies, self.occupation_numbers),
        ):
            label = "occ" if occ > 0.5 else "vir"
            print(f"  MO {i:3d}: {e:12.6f}  [{label}]  occ={occ:.1f}")

    @classmethod
    def from_pyscf(
        cls,
        scf_obj: Any,
        n_active_electrons: int | None = None,
        n_active_orbitals: int | None = None,
    ) -> MolecularOrbitalInfo:
        """Extract orbital info from a PySCF SCF object.

        Args:
            scf_obj: Converged PySCF SCF object.
            n_active_electrons: Active electrons (if active space used).
            n_active_orbitals: Active orbitals (if active space used).

        Returns:
            MolecularOrbitalInfo with orbital energies and occupations.
        """
        mol = scf_obj.mol
        energies = tuple(float(e) for e in scf_obj.mo_energy)
        occ = tuple(float(o) for o in scf_obj.mo_occ)
        n_total = mol.nelectron
        n_alpha = (n_total + mol.spin) // 2
        n_beta = n_total - n_alpha

        active: tuple[int, int] | None = None
        if n_active_electrons is not None and n_active_orbitals is not None:
            active = (n_active_electrons, n_active_orbitals)

        return cls(
            orbital_energies=energies,
            occupation_numbers=occ,
            n_alpha=n_alpha,
            n_beta=n_beta,
            n_spatial_orbitals=len(energies),
            active_space=active,
            hf_energy=float(scf_obj.e_tot),
            nuclear_repulsion=float(mol.energy_nuc()),
        )
