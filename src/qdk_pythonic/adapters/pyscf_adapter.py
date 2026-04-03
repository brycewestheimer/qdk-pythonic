"""PySCF adapter for molecular quantum chemistry.

Converts PySCF molecular computations into qdk-pythonic primitives
(FermionOperator, PauliHamiltonian) for downstream circuit building
and resource estimation.

Requires ``pip install qdk-pythonic[pyscf]`` (pyscf>=2.0).

Example::

    from qdk_pythonic.adapters.pyscf_adapter import molecular_hamiltonian

    h = molecular_hamiltonian("H 0 0 0; H 0 0 0.74")
    h.print_summary()
"""

from __future__ import annotations

from typing import Any

from qdk_pythonic.domains.common.fermion import from_integrals
from qdk_pythonic.domains.common.mapping import (
    BravyiKitaevMapping,
    JordanWignerMapping,
)
from qdk_pythonic.domains.common.operators import PauliHamiltonian
from qdk_pythonic.exceptions import ExecutionError

__all__ = [
    "get_integrals",
    "molecular_hamiltonian",
    "molecular_summary",
    "run_scf",
]


def _import_pyscf() -> Any:
    """Lazily import PySCF with a clear error message."""
    try:
        import pyscf  # type: ignore[import-untyped]  # noqa: F811
    except ImportError as exc:
        raise ImportError(
            "PySCF is required for the chemistry adapter. "
            "Install it with: pip install qdk-pythonic[pyscf]"
        ) from exc
    return pyscf


def run_scf(
    atom: str,
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0,
) -> Any:
    """Run a Hartree-Fock calculation with PySCF.

    Args:
        atom: Molecular geometry in PySCF format,
            e.g. ``"H 0 0 0; H 0 0 0.74"``.
        basis: Basis set name (e.g. ``"sto-3g"``, ``"cc-pvdz"``).
        charge: Total molecular charge.
        spin: 2S, number of unpaired electrons.

    Returns:
        PySCF SCF object with converged wavefunction.

    Raises:
        ExecutionError: If SCF does not converge.
    """
    pyscf = _import_pyscf()
    mol = pyscf.gto.M(
        atom=atom, basis=basis, charge=charge, spin=spin,
    )
    if spin > 0:
        mf = pyscf.scf.ROHF(mol)
    else:
        mf = pyscf.scf.RHF(mol)
    mf.kernel()
    if not mf.converged:
        raise ExecutionError(
            f"SCF did not converge for molecule with basis={basis}"
        )
    return mf


def get_integrals(
    scf_obj: Any,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
) -> tuple[Any, Any, float]:
    """Extract molecular integrals from a PySCF SCF object.

    Args:
        scf_obj: Converged PySCF SCF object.
        n_active_electrons: Active electrons for CASCI.
            None means all electrons.
        n_active_orbitals: Active orbitals for CASCI.
            None means all orbitals.

    Returns:
        Tuple of (h1e, h2e, nuclear_repulsion) where h1e has shape
        (n, n), h2e has shape (n, n, n, n) in physicist notation,
        and nuclear_repulsion is a scalar.
    """
    pyscf = _import_pyscf()
    mol = scf_obj.mol
    nuclear_repulsion = float(mol.energy_nuc())

    if n_active_electrons is not None and n_active_orbitals is not None:
        # Active space via CASCI
        cas = pyscf.mcscf.CASCI(
            scf_obj, n_active_orbitals, n_active_electrons,
        )
        h1e_cas, e_core = cas.get_h1cas()
        h2e_cas = cas.get_h2cas()
        n = n_active_orbitals
        # Restore full 4-index tensor
        h2e_full = pyscf.ao2mo.restore(1, h2e_cas, n)
        # Convert chemist (pq|rs) to physicist <pq||rs>:
        # h2e_phys[p,q,r,s] = h2e_chem[p,s,q,r]
        import numpy as np
        h2e_phys = np.transpose(h2e_full, (0, 2, 3, 1))
        return h1e_cas, h2e_phys, e_core + nuclear_repulsion
    else:
        # Full space
        mo_coeff = scf_obj.mo_coeff
        n = mo_coeff.shape[1]
        h1e = mo_coeff.T @ scf_obj.get_hcore() @ mo_coeff
        eri = pyscf.ao2mo.full(mol, mo_coeff)
        h2e_full = pyscf.ao2mo.restore(1, eri, n)
        import numpy as np
        h2e_phys = np.transpose(h2e_full, (0, 2, 3, 1))
        return h1e, h2e_phys, nuclear_repulsion


def molecular_hamiltonian(
    atom: str,
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
    mapping: str = "jordan_wigner",
) -> PauliHamiltonian:
    """Build a qubit Hamiltonian for a molecule.

    Runs the full pipeline: geometry -> SCF -> integrals
    -> FermionOperator -> qubit mapping -> PauliHamiltonian.

    Args:
        atom: Molecular geometry in PySCF format.
        basis: Basis set name.
        charge: Molecular charge.
        spin: 2S, number of unpaired electrons.
        n_active_electrons: Active electrons (None = all).
        n_active_orbitals: Active orbitals (None = all).
        mapping: Qubit mapping (``"jordan_wigner"`` or
            ``"bravyi_kitaev"``).

    Returns:
        PauliHamiltonian for the molecule.
    """
    scf_obj = run_scf(atom, basis, charge, spin)
    h1e, h2e, nuc_repulsion = get_integrals(
        scf_obj, n_active_electrons, n_active_orbitals,
    )
    fermion_op = from_integrals(h1e, h2e, nuc_repulsion)

    if mapping == "bravyi_kitaev":
        return BravyiKitaevMapping().map(fermion_op)
    return JordanWignerMapping().map(fermion_op)


def molecular_summary(
    atom: str,
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
    mapping: str = "jordan_wigner",
    estimate_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """End-to-end molecular analysis with optional resource estimation.

    Returns a dict with SCF energy, orbital counts, Hamiltonian
    summary, circuit metrics, and optional resource estimate.
    """
    from qdk_pythonic.domains.common.evolution import TrotterEvolution

    scf_obj = run_scf(atom, basis, charge, spin)
    h1e, h2e, nuc_repulsion = get_integrals(
        scf_obj, n_active_electrons, n_active_orbitals,
    )
    fermion_op = from_integrals(h1e, h2e, nuc_repulsion)

    if mapping == "bravyi_kitaev":
        pauli_h = BravyiKitaevMapping().map(fermion_op)
    else:
        pauli_h = JordanWignerMapping().map(fermion_op)

    evolution = TrotterEvolution(hamiltonian=pauli_h, time=1.0, steps=1)
    circuit = evolution.to_circuit()

    result: dict[str, Any] = {
        "scf_energy": float(scf_obj.e_tot),
        "n_orbitals": len(h1e),
        "n_electrons": int(scf_obj.mol.nelectron),
        "n_fermion_terms": len(fermion_op),
        "hamiltonian": pauli_h,
        "hamiltonian_summary": pauli_h.summary(),
        "circuit": circuit,
        "n_qubits": circuit.qubit_count(),
        "gate_count": circuit.gate_count(),
        "total_gates": circuit.total_gate_count(),
        "depth": circuit.depth(),
    }

    if estimate_params is not None:
        result["estimate_result"] = circuit.estimate(
            params=estimate_params,
        )

    return result
