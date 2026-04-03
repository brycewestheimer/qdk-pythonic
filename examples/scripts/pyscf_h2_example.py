"""Molecular Hamiltonian construction for H2 via PySCF.

Demonstrates the full pipeline: geometry -> SCF -> integrals
-> FermionOperator -> qubit mapping -> PauliHamiltonian -> circuit.

Requires: pip install qdk-pythonic[pyscf]
"""

from __future__ import annotations

import sys


def main() -> None:
    try:
        import pyscf  # noqa: F401
    except ImportError:
        print("PySCF is required: pip install qdk-pythonic[pyscf]")
        sys.exit(1)

    from qdk_pythonic.adapters.pyscf_adapter import (
        molecular_hamiltonian,
        molecular_summary,
        run_scf,
    )

    # ── Simple one-call interface ──
    print("=== H2 Molecular Hamiltonian (Jordan-Wigner) ===\n")
    h_jw = molecular_hamiltonian("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    h_jw.print_summary()

    print("\n=== H2 Molecular Hamiltonian (Bravyi-Kitaev) ===\n")
    h_bk = molecular_hamiltonian(
        "H 0 0 0; H 0 0 0.74", basis="sto-3g", mapping="bravyi_kitaev",
    )
    h_bk.print_summary()

    # ── Step-by-step interface ──
    print("\n=== Step-by-Step Pipeline ===\n")
    mf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    print(f"SCF energy: {mf.e_tot:.8f} Hartree")
    print(f"Converged:  {mf.converged}")

    # ── End-to-end summary ──
    print("\n=== Full Summary ===\n")
    result = molecular_summary("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    print(f"SCF energy:     {result['scf_energy']:.8f}")
    print(f"Orbitals:       {result['n_orbitals']}")
    print(f"Electrons:      {result['n_electrons']}")
    print(f"Fermion terms:  {result['n_fermion_terms']}")
    print(f"Qubits:         {result['n_qubits']}")
    print(f"Total gates:    {result['total_gates']}")
    print(f"Circuit depth:  {result['depth']}")

    # ── Registry pattern ──
    print("\n=== Registry Pattern ===\n")
    from qdk_pythonic.registry import create

    builder = create("hamiltonian_builder", "pyscf", basis="sto-3g")
    h = builder.run(atom="H 0 0 0; H 0 0 0.74")
    print(f"Registry builder produced {len(h)} terms on {h.qubit_count()} qubits")


if __name__ == "__main__":
    main()
