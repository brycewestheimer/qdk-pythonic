"""Complete H2 quantum chemistry workflow.

Demonstrates the full pipeline from molecular geometry through
QPE, VQE setup, and qubitization -- reproducing the qdk-chemistry
workflow using PySCF with qdk-pythonic.

Requirements: pip install qdk-pythonic[chemistry]
"""

from qdk_pythonic.adapters.pyscf_adapter import (
    molecular_hamiltonian,
    run_scf,
    get_integrals,
)
from qdk_pythonic.domains.chemistry import (
    ChemistryQPE,
    HartreeFockState,
    MolecularOrbitalInfo,
    UCCSDAnsatz,
    VQE,
    group_commuting_terms,
)
from qdk_pythonic.domains.common.double_factorization import double_factorize
from qdk_pythonic.domains.common.lcu import QubitizationQPE


def main() -> None:
    atom = "H 0 0 0; H 0 0 0.74"
    basis = "sto-3g"

    # ── Stage 1: Classical electronic structure ──
    print("=" * 60)
    print("Stage 1: PySCF Hartree-Fock")
    print("=" * 60)
    scf = run_scf(atom, basis=basis)
    info = MolecularOrbitalInfo.from_pyscf(scf)
    info.print_report()

    # ── Stage 2: Build qubit Hamiltonian ──
    print("\n" + "=" * 60)
    print("Stage 2: Qubit Hamiltonian (Jordan-Wigner)")
    print("=" * 60)
    h = molecular_hamiltonian(atom, basis=basis)
    h.print_summary()

    groups = group_commuting_terms(h)
    print(f"Measurement groups: {len(groups)} "
          f"(from {len(h)} Pauli terms)")

    # ── Stage 3: Hartree-Fock state ──
    print("\n" + "=" * 60)
    print("Stage 3: Hartree-Fock State")
    print("=" * 60)
    hf = HartreeFockState(n_qubits=h.qubit_count(), n_electrons=2)
    print(f"JW bitstring: {hf.to_bitstring()}")
    hf_circ = hf.to_circuit()
    print(f"HF circuit: {hf_circ.qubit_count()} qubits, "
          f"{hf_circ.total_gate_count()} gates")

    # ── Stage 4: UCCSD ansatz ──
    print("\n" + "=" * 60)
    print("Stage 4: UCCSD Ansatz")
    print("=" * 60)
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    print(f"Parameters: {ansatz.num_parameters}")
    print(f"Singles: {ansatz.singles()}")
    print(f"Doubles: {ansatz.doubles()}")
    uccsd_circ = ansatz.to_circuit([0.1] * ansatz.num_parameters)
    print(f"Circuit: {uccsd_circ.qubit_count()} qubits, "
          f"{uccsd_circ.total_gate_count()} gates, "
          f"depth {uccsd_circ.depth()}")

    # ── Stage 5: QPE circuit ──
    print("\n" + "=" * 60)
    print("Stage 5: Quantum Phase Estimation (Trotter)")
    print("=" * 60)
    qpe = ChemistryQPE(
        hamiltonian=h, n_electrons=2,
        n_estimation_qubits=4, trotter_steps=2,
    )
    qpe_circ = qpe.to_circuit()
    print(f"QPE circuit: {qpe_circ.qubit_count()} qubits, "
          f"{qpe_circ.total_gate_count()} gates, "
          f"depth {qpe_circ.depth()}")

    # ── Stage 6: VQE setup ──
    print("\n" + "=" * 60)
    print("Stage 6: VQE Setup")
    print("=" * 60)
    vqe = VQE(
        hamiltonian=h, ansatz=ansatz, n_electrons=2,
        optimizer="COBYLA", max_iterations=100,
    )
    trial = vqe.to_circuit([0.0] * ansatz.num_parameters)
    print(f"Trial circuit: {trial.qubit_count()} qubits, "
          f"{trial.total_gate_count()} gates")
    print("(Run vqe.run() with qsharp installed for optimization)")

    # ── Stage 7: Double factorization ──
    print("\n" + "=" * 60)
    print("Stage 7: Double Factorization")
    print("=" * 60)
    h1e, h2e, nuc = get_integrals(scf)
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)
    df.print_summary()

    # ── Stage 8: Qubitization QPE ──
    print("\n" + "=" * 60)
    print("Stage 8: Qubitization QPE")
    print("=" * 60)
    qubit_qpe = QubitizationQPE(
        hamiltonian=h, n_electrons=2, n_estimation_qubits=4,
    )
    qubit_circ = qubit_qpe.to_circuit()
    print(f"Qubitization QPE: {qubit_circ.qubit_count()} qubits, "
          f"{qubit_circ.total_gate_count()} gates, "
          f"depth {qubit_circ.depth()}")

    # ── Comparison ──
    print("\n" + "=" * 60)
    print("Comparison: Trotter vs Qubitization QPE")
    print("=" * 60)
    print(f"{'Method':<20} {'Qubits':>8} {'Gates':>10} {'Depth':>8}")
    print("-" * 50)
    print(f"{'Trotter QPE':<20} {qpe_circ.qubit_count():>8} "
          f"{qpe_circ.total_gate_count():>10} {qpe_circ.depth():>8}")
    print(f"{'Qubitization QPE':<20} {qubit_circ.qubit_count():>8} "
          f"{qubit_circ.total_gate_count():>10} {qubit_circ.depth():>8}")

    # ── Stage 9: Qubit tapering ──
    print("\n" + "=" * 60)
    print("Stage 9: Qubit Tapering")
    print("=" * 60)
    from qdk_pythonic.domains.common.tapering import (
        find_z2_symmetries,
        taper_hamiltonian,
    )

    h_631g = molecular_hamiltonian(atom, basis="6-31g")
    print(f"H2 (6-31G) before tapering: {h_631g.qubit_count()} qubits, "
          f"{len(h_631g)} terms")
    symmetries = find_z2_symmetries(h_631g)
    print(f"Z2 symmetries found: {len(symmetries)}")
    tapered_h, info = taper_hamiltonian(h_631g)
    print(f"After tapering: {info.tapered_qubits} qubits, "
          f"{len(tapered_h)} terms")

    # ── Stage 10: Convenience functions ──
    print("\n" + "=" * 60)
    print("Stage 10: One-Call Convenience Functions")
    print("=" * 60)
    print("These require qsharp to be installed:")
    print("  molecular_qpe(atom) -> ChemistryResourceEstimate")
    print("  molecular_vqe(atom) -> VQEResult")
    print("  molecular_resource_comparison(atom) -> printed table")


if __name__ == "__main__":
    main()
