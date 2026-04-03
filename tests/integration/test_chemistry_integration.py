"""Integration tests for chemistry domain features.

Tests the full pipeline from PySCF molecular geometry through
quantum chemistry algorithms to Q# resource estimation.

Requires: pyscf, qsharp
"""

from __future__ import annotations

from typing import Any

import pytest

pyscf = pytest.importorskip("pyscf")
qsharp = pytest.importorskip("qsharp", reason="qsharp not installed")


# ── Helpers ──


def _h2_hamiltonian() -> Any:
    from qdk_pythonic.adapters.pyscf_adapter import molecular_hamiltonian

    return molecular_hamiltonian("H 0 0 0; H 0 0 0.74", basis="sto-3g")


# ── HartreeFockState ──


@pytest.mark.integration
def test_hf_state_circuit_generates_valid_qsharp() -> None:
    """HF state circuit should produce valid Q# that compiles."""
    from qdk_pythonic.domains.chemistry import HartreeFockState

    hf = HartreeFockState(n_qubits=4, n_electrons=2)
    circ = hf.to_circuit()
    qs = circ.to_qsharp()
    assert "X(" in qs


# ── UCCSD ──


@pytest.mark.integration
def test_uccsd_circuit_estimates() -> None:
    """UCCSD circuit should pass through resource estimation."""
    from qdk_pythonic.domains.chemistry import UCCSDAnsatz

    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    circ = ansatz.to_circuit([0.1] * ansatz.num_parameters)
    result = circ.estimate()
    assert result is not None
    assert result["physicalCounts"]["physicalQubits"] > 0


# ── ChemistryQPE ──


@pytest.mark.integration
def test_h2_qpe_resource_estimation() -> None:
    """Full H2 QPE -> resource estimation pipeline."""
    from qdk_pythonic.domains.chemistry import ChemistryQPE

    h = _h2_hamiltonian()
    qpe = ChemistryQPE(
        hamiltonian=h,
        n_electrons=2,
        n_estimation_qubits=4,
        trotter_steps=1,
    )
    result = qpe.estimate_resources()
    assert result is not None
    assert result["physicalCounts"]["physicalQubits"] > 0
    assert result["logicalCounts"]["numQubits"] > 0


@pytest.mark.integration
def test_h2_qpe_with_custom_params() -> None:
    """QPE estimation with custom qubit parameters."""
    from qdk_pythonic.domains.chemistry import ChemistryQPE

    h = _h2_hamiltonian()
    qpe = ChemistryQPE(
        hamiltonian=h, n_electrons=2, n_estimation_qubits=3,
    )
    params: dict[str, Any] = {
        "qubitParams": {"name": "qubit_gate_ns_e3"},
    }
    result = qpe.estimate_resources(params=params)
    assert result["jobParams"]["qubitParams"]["name"] == "qubit_gate_ns_e3"


# ── VQE ──


@pytest.mark.integration
def test_vqe_trial_circuit_estimates() -> None:
    """VQE trial-state circuit should pass resource estimation."""
    from qdk_pythonic.domains.chemistry import UCCSDAnsatz, VQE

    h = _h2_hamiltonian()
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    vqe = VQE(hamiltonian=h, ansatz=ansatz, n_electrons=2)
    circ = vqe.to_circuit([0.5] * ansatz.num_parameters)
    result = circ.estimate()
    assert result is not None


# ── Structured Resource Estimation ──


@pytest.mark.integration
def test_parse_real_estimation_result() -> None:
    """Parse an actual qsharp.estimate() result into structured form."""
    from qdk_pythonic.domains.chemistry import ChemistryQPE
    from qdk_pythonic.execution.chemistry_estimate import (
        parse_estimation_result,
    )

    h = _h2_hamiltonian()
    qpe = ChemistryQPE(
        hamiltonian=h, n_electrons=2, n_estimation_qubits=3,
    )
    raw = qpe.estimate_resources()
    result = parse_estimation_result(
        raw,
        algorithm_name="trotter_qpe",
        hamiltonian_info={"n_orbitals": 2, "n_electrons": 2},
    )

    assert result.algorithm_name == "trotter_qpe"
    assert result.logical.logical_qubits > 0
    assert result.logical.t_count >= 0
    assert result.physical.physical_qubits > 0
    assert result.physical.runtime_seconds >= 0
    assert result.physical.code_distance > 0
    assert result.qubit_model == "qubit_gate_ns_e3"
    assert result.qec_scheme == "surface_code"
    assert result.hamiltonian_info["n_orbitals"] == 2


@pytest.mark.integration
def test_estimate_and_parse_convenience() -> None:
    """estimate_and_parse() should return a ChemistryResourceEstimate."""
    from qdk_pythonic.domains.chemistry import UCCSDAnsatz
    from qdk_pythonic.execution.estimator import estimate_and_parse

    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    circ = ansatz.to_circuit([0.1] * ansatz.num_parameters)
    result = estimate_and_parse(
        circ,
        algorithm_name="uccsd",
        hamiltonian_info={"n_orbitals": 2},
    )
    assert result.algorithm_name == "uccsd"
    assert result.physical.physical_qubits > 0


@pytest.mark.integration
def test_compare_trotter_estimates_across_params() -> None:
    """Compare resource estimates across qubit parameter models."""
    from qdk_pythonic.domains.chemistry import ChemistryQPE
    from qdk_pythonic.execution.chemistry_estimate import (
        compare_estimates,
        parse_estimation_result,
    )

    h = _h2_hamiltonian()
    qpe = ChemistryQPE(
        hamiltonian=h, n_electrons=2, n_estimation_qubits=3,
    )

    estimates = []
    for model in ["qubit_gate_ns_e3", "qubit_gate_ns_e4"]:
        raw = qpe.estimate_resources(
            params={"qubitParams": {"name": model}},
        )
        est = parse_estimation_result(raw, algorithm_name=f"trotter_{model}")
        estimates.append(est)

    table = compare_estimates(estimates)
    assert len(table) == 2
    assert table[0]["algorithm_name"] != table[1]["algorithm_name"]
    # e4 should need fewer physical qubits than e3
    assert table[1]["physical_qubits"] < table[0]["physical_qubits"]


# ── Qubitization ──


@pytest.mark.integration
def test_qubitization_qpe_resource_estimation() -> None:
    """Gate-level qubitization QPE should pass resource estimation."""
    from qdk_pythonic.domains.common.lcu import QubitizationQPE
    from qdk_pythonic.domains.common.operators import PauliHamiltonian, X, Z

    # Use a small Hamiltonian to keep circuit size manageable
    h = PauliHamiltonian()
    h += -1.0 * Z(0)
    h += 0.5 * X(0)

    qpe = QubitizationQPE(
        hamiltonian=h, n_electrons=1, n_estimation_qubits=3,
    )
    result = qpe.estimate_resources()
    assert result is not None
    assert result["physicalCounts"]["physicalQubits"] > 0


@pytest.mark.integration
def test_chemistry_qubitization_gate_level_estimates() -> None:
    """ChemistryQubitization in gate_level mode should estimate."""
    from qdk_pythonic.domains.chemistry import ChemistryQubitization
    from qdk_pythonic.domains.common.operators import PauliHamiltonian, Z

    h = PauliHamiltonian([Z(0)])
    cq = ChemistryQubitization(
        hamiltonian=h, n_electrons=1,
        n_estimation_qubits=2, gate_level=True,
    )
    result = cq.estimate_resources()
    assert result.physical.physical_qubits > 0
    assert result.algorithm_name == "qubitization_qpe"


# ── Double Factorization ──


@pytest.mark.integration
def test_double_factorize_pyscf_h2() -> None:
    """Double-factorize H2 integrals from PySCF."""
    from qdk_pythonic.adapters.pyscf_adapter import get_integrals, run_scf
    from qdk_pythonic.domains.common.double_factorization import (
        double_factorize,
    )

    scf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    h1e, h2e, nuc = get_integrals(scf)
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)

    assert df.n_orbitals == 2
    assert df.n_leaves > 0
    assert df.one_norm() > 0


@pytest.mark.integration
def test_double_factorize_to_pauli_estimates() -> None:
    """DF -> PauliHamiltonian -> Trotter circuit -> estimate."""
    from qdk_pythonic.adapters.pyscf_adapter import get_integrals, run_scf
    from qdk_pythonic.domains.common.double_factorization import (
        double_factorize,
    )
    from qdk_pythonic.domains.common.evolution import TrotterEvolution

    scf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    h1e, h2e, nuc = get_integrals(scf)
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)

    pauli_h = df.to_pauli_hamiltonian()
    evo = TrotterEvolution(hamiltonian=pauli_h, time=1.0, steps=1)
    circ = evo.to_circuit()
    result = circ.estimate()
    assert result is not None
    assert result["physicalCounts"]["physicalQubits"] > 0


@pytest.mark.integration
def test_molecular_double_factorized_convenience() -> None:
    """molecular_double_factorized() end-to-end convenience function."""
    from qdk_pythonic.adapters.pyscf_adapter import (
        molecular_double_factorized,
    )

    df = molecular_double_factorized("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    assert df.n_orbitals == 2
    assert df.n_electrons == 2
    assert df.n_leaves > 0


# ── FCIDUMP round-trip with PySCF ──


@pytest.mark.integration
def test_fcidump_round_trip_with_estimation() -> None:
    """PySCF -> FCIDUMP -> Hamiltonian -> Trotter -> estimate."""
    import numpy as np

    from qdk_pythonic.adapters.pyscf_adapter import get_integrals, run_scf
    from qdk_pythonic.domains.chemistry import FCIDUMPData
    from qdk_pythonic.domains.common.evolution import TrotterEvolution

    scf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    h1e, h2e, nuc = get_integrals(scf)

    data = FCIDUMPData(
        n_orbitals=h1e.shape[0],
        n_electrons=int(scf.mol.nelectron),
        ms2=0,
        h1e=np.asarray(h1e),
        h2e=np.asarray(h2e),
        nuclear_repulsion=float(nuc),
    )

    h = data.to_hamiltonian()
    evo = TrotterEvolution(hamiltonian=h, time=1.0, steps=1)
    circ = evo.to_circuit()
    result = circ.estimate()
    assert result is not None


# ── Orbital Info ──


@pytest.mark.integration
def test_orbital_info_from_pyscf() -> None:
    """MolecularOrbitalInfo extracted from PySCF SCF object."""
    from qdk_pythonic.adapters.pyscf_adapter import run_scf
    from qdk_pythonic.domains.chemistry import MolecularOrbitalInfo

    scf = run_scf("H 0 0 0; H 0 0 0.74", basis="sto-3g")
    info = MolecularOrbitalInfo.from_pyscf(scf)

    assert info.n_electrons == 2
    assert info.n_spatial_orbitals == 2
    assert info.n_qubits == 4
    assert len(info.orbital_energies) == 2
    assert info.hf_energy < 0  # Should be negative for bound system


@pytest.mark.integration
def test_orbital_info_with_active_space() -> None:
    """Orbital info with active space from LiH."""
    from qdk_pythonic.adapters.pyscf_adapter import run_scf
    from qdk_pythonic.domains.chemistry import MolecularOrbitalInfo

    scf = run_scf("Li 0 0 0; H 0 0 1.6", basis="sto-3g")
    info = MolecularOrbitalInfo.from_pyscf(
        scf, n_active_electrons=2, n_active_orbitals=2,
    )

    assert info.active_space == (2, 2)
    assert info.n_qubits == 4  # 2 active orbitals * 2 spins
    assert info.n_active_electrons == 2


# ── Registry ──


@pytest.mark.integration
def test_registry_pyscf_qpe() -> None:
    """Registry-based QPE should produce a result with circuit info."""
    from qdk_pythonic.adapters.pyscf_chemistry import load
    from qdk_pythonic.registry import _factories, create

    original = list(_factories)
    try:
        load()
        alg = create(
            "chemistry_algorithm", "pyscf_qpe",
            n_estimation_qubits=3,
        )
        result = alg.run(atom="H 0 0 0; H 0 0 0.74")
        assert "circuit" in result
        assert "hamiltonian" in result
        assert result["n_qubits"] > 0
        assert result["total_gates"] > 0
    finally:
        _factories.clear()
        _factories.extend(original)


# ── qsharp.chemistry bridge ──


@pytest.mark.integration
def test_chemistry_bridge_skips_without_module() -> None:
    """Bridge should raise ImportError when qsharp.chemistry is absent."""
    try:
        import qsharp.chemistry  # type: ignore[import-not-found]  # noqa: F401
        pytest.skip("qsharp.chemistry is available, skip this test")
    except (ImportError, AttributeError):
        pass

    from qdk_pythonic.execution.chemistry_bridge import (
        _import_qsharp_chemistry,
    )

    with pytest.raises(ImportError, match="qsharp.chemistry"):
        _import_qsharp_chemistry()
