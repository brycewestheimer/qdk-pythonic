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
    "get_orbital_info",
    "molecular_double_factorized",
    "molecular_hamiltonian",
    "molecular_qpe",
    "molecular_summary",
    "molecular_vqe",
    "run_scf",
]


def _import_pyscf() -> Any:
    """Lazily import PySCF with a clear error message."""
    try:
        import pyscf
        import pyscf.ao2mo  # noqa: F401
        import pyscf.mcscf  # noqa: F401
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


def get_orbital_info(
    scf_obj: Any,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
) -> Any:
    """Extract molecular orbital information from a PySCF SCF object.

    Args:
        scf_obj: Converged PySCF SCF object.
        n_active_electrons: Active electrons for CASCI.
        n_active_orbitals: Active orbitals for CASCI.

    Returns:
        MolecularOrbitalInfo with orbital energies, occupations,
        and active space metadata.
    """
    from qdk_pythonic.domains.chemistry.orbital_info import (
        MolecularOrbitalInfo,
    )

    return MolecularOrbitalInfo.from_pyscf(
        scf_obj, n_active_electrons, n_active_orbitals,
    )


def molecular_double_factorized(
    atom: str,
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
    threshold: float = 1e-6,
) -> Any:
    """Build a double-factorized Hamiltonian for a molecule.

    Runs the pipeline: geometry -> SCF -> integrals
    -> double factorization.

    Args:
        atom: Molecular geometry in PySCF format.
        basis: Basis set name.
        charge: Molecular charge.
        spin: 2S, number of unpaired electrons.
        n_active_electrons: Active electrons (None = all).
        n_active_orbitals: Active orbitals (None = all).
        threshold: Truncation threshold for factorization.

    Returns:
        DoubleFactorizedHamiltonian for the molecule.
    """
    from qdk_pythonic.domains.common.double_factorization import (
        double_factorize,
    )

    scf_obj = run_scf(atom, basis, charge, spin)
    h1e, h2e, nuc_repulsion = get_integrals(
        scf_obj, n_active_electrons, n_active_orbitals,
    )
    n_electrons = int(scf_obj.mol.nelectron)
    if n_active_electrons is not None:
        n_electrons = n_active_electrons
    return double_factorize(
        h1e, h2e, nuc_repulsion,
        n_electrons=n_electrons,
        threshold=threshold,
    )


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

    orbital_info = get_orbital_info(
        scf_obj, n_active_electrons, n_active_orbitals,
    )

    result: dict[str, Any] = {
        "scf_energy": float(scf_obj.e_tot),
        "n_orbitals": len(h1e),
        "n_electrons": int(scf_obj.mol.nelectron),
        "n_fermion_terms": len(fermion_op),
        "hamiltonian": pauli_h,
        "hamiltonian_summary": pauli_h.summary(),
        "orbital_info": orbital_info,
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


def molecular_qpe(
    atom: str,
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
    mapping: str = "jordan_wigner",
    n_estimation_qubits: int = 8,
    trotter_steps: int = 1,
    trotter_order: int = 1,
    estimate_params: dict[str, Any] | None = None,
) -> Any:
    """One-call QPE resource estimation for a molecule.

    Runs the full pipeline: PySCF SCF/CASCI -> fermionic Hamiltonian
    -> qubit mapping -> Trotter QPE circuit -> resource estimation.
    Returns a structured ``ChemistryResourceEstimate``.

    Args:
        atom: Molecular geometry in PySCF format.
        basis: Basis set name.
        charge: Molecular charge.
        spin: 2S, number of unpaired electrons.
        n_active_electrons: Active electrons (None = all).
        n_active_orbitals: Active orbitals (None = all).
        mapping: Qubit mapping.
        n_estimation_qubits: QPE precision bits.
        trotter_steps: Trotter steps for Hamiltonian simulation.
        trotter_order: Trotter-Suzuki order.
        estimate_params: Optional resource estimator parameters.

    Returns:
        ChemistryResourceEstimate with structured physical/logical
        resource counts, or a dict with circuit info if qsharp is
        not available.
    """
    from qdk_pythonic.domains.chemistry.qpe import ChemistryQPE

    scf_obj = run_scf(atom, basis, charge, spin)
    h1e, h2e, nuc = get_integrals(
        scf_obj, n_active_electrons, n_active_orbitals,
    )
    n_elec = int(scf_obj.mol.nelectron)
    if n_active_electrons is not None:
        n_elec = n_active_electrons

    fermion_op = from_integrals(h1e, h2e, nuc)
    if mapping == "bravyi_kitaev":
        pauli_h = BravyiKitaevMapping().map(fermion_op)
    else:
        pauli_h = JordanWignerMapping().map(fermion_op)

    qpe = ChemistryQPE(
        hamiltonian=pauli_h,
        n_electrons=n_elec,
        n_estimation_qubits=n_estimation_qubits,
        trotter_steps=trotter_steps,
        trotter_order=trotter_order,
    )
    circuit = qpe.to_circuit()

    ham_info = {
        "molecule": atom,
        "basis": basis,
        "n_orbitals": len(h1e),
        "n_electrons": n_elec,
        "mapping": mapping,
        "n_estimation_qubits": n_estimation_qubits,
        "trotter_steps": trotter_steps,
    }

    try:
        from qdk_pythonic.execution.chemistry_estimate import (
            parse_estimation_result,
        )

        raw = circuit.estimate(params=estimate_params)
        return parse_estimation_result(
            raw,
            algorithm_name="trotter_qpe",
            hamiltonian_info=ham_info,
        )
    except ImportError:
        # qsharp not available -- return circuit info
        return {
            "circuit": circuit,
            "n_qubits": circuit.qubit_count(),
            "total_gates": circuit.total_gate_count(),
            "depth": circuit.depth(),
            "hamiltonian_info": ham_info,
        }


def molecular_vqe(
    atom: str,
    basis: str = "sto-3g",
    charge: int = 0,
    spin: int = 0,
    n_active_electrons: int | None = None,
    n_active_orbitals: int | None = None,
    mapping: str = "jordan_wigner",
    optimizer: str = "COBYLA",
    max_iterations: int = 100,
    shots: int = 10000,
    initial_params: list[float] | None = None,
) -> Any:
    """One-call VQE for a molecule.

    Runs the full pipeline: PySCF SCF/CASCI -> UCCSD ansatz
    -> VQE optimization. Returns a ``VQEResult``.

    Args:
        atom: Molecular geometry in PySCF format.
        basis: Basis set name.
        charge: Molecular charge.
        spin: 2S, number of unpaired electrons.
        n_active_electrons: Active electrons (None = all).
        n_active_orbitals: Active orbitals (None = all).
        mapping: Qubit mapping.
        optimizer: Classical optimizer for scipy.
        max_iterations: Maximum optimizer iterations.
        shots: Measurement shots per expectation value.
        initial_params: Starting parameter values (None = zeros).

    Returns:
        VQEResult with optimal energy, parameters, and history.
    """
    from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz
    from qdk_pythonic.domains.chemistry.vqe import VQE

    scf_obj = run_scf(atom, basis, charge, spin)
    h1e, h2e, nuc = get_integrals(
        scf_obj, n_active_electrons, n_active_orbitals,
    )
    n_elec = int(scf_obj.mol.nelectron)
    if n_active_electrons is not None:
        n_elec = n_active_electrons
    n_orbs = len(h1e)
    if n_active_orbitals is not None:
        n_orbs = n_active_orbitals

    fermion_op = from_integrals(h1e, h2e, nuc)
    if mapping == "bravyi_kitaev":
        pauli_h = BravyiKitaevMapping().map(fermion_op)
    else:
        pauli_h = JordanWignerMapping().map(fermion_op)

    ansatz = UCCSDAnsatz(
        n_spatial_orbitals=n_orbs,
        n_electrons=n_elec,
        mapping=mapping,
    )
    vqe = VQE(
        hamiltonian=pauli_h,
        ansatz=ansatz,
        n_electrons=n_elec,
        optimizer=optimizer,
        max_iterations=max_iterations,
        shots=shots,
    )
    return vqe.run(initial_params=initial_params)
