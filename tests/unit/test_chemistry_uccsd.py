"""Tests for UCCSDAnsatz."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.chemistry.uccsd import UCCSDAnsatz
from qdk_pythonic.exceptions import CircuitError


@pytest.mark.unit
def test_n_qubits() -> None:
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    assert ansatz.n_qubits == 4


@pytest.mark.unit
def test_h2_singles() -> None:
    """H2 with 2 spatial orbitals, 2 electrons.

    Occupied spin-orbitals: 0 (alpha), 1 (beta)
    Virtual spin-orbitals: 2 (alpha), 3 (beta)
    Spin-preserving singles: (0,2), (1,3)
    """
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    singles = ansatz.singles()
    assert len(singles) == 2
    assert (0, 2) in singles
    assert (1, 3) in singles


@pytest.mark.unit
def test_h2_doubles() -> None:
    """H2: one double excitation (0,1) -> (2,3).

    spin_occ = 0%2 + 1%2 = 0 + 1 = 1
    spin_virt = 2%2 + 3%2 = 0 + 1 = 1 -> match
    """
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    doubles = ansatz.doubles()
    assert len(doubles) == 1
    assert (0, 1, 2, 3) in doubles


@pytest.mark.unit
def test_h2_num_parameters() -> None:
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    # 2 singles + 1 double = 3
    assert ansatz.num_parameters == 3


@pytest.mark.unit
def test_singles_only() -> None:
    ansatz = UCCSDAnsatz(
        n_spatial_orbitals=2, n_electrons=2,
        include_doubles=False,
    )
    assert ansatz.num_parameters == 2


@pytest.mark.unit
def test_doubles_only() -> None:
    ansatz = UCCSDAnsatz(
        n_spatial_orbitals=2, n_electrons=2,
        include_singles=False,
    )
    assert ansatz.num_parameters == 1


@pytest.mark.unit
def test_excitation_operators_count() -> None:
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    ops = ansatz.excitation_operators()
    assert len(ops) == ansatz.num_parameters


@pytest.mark.unit
def test_excitation_operators_are_anti_hermitian() -> None:
    """Each generator T - T† should satisfy G† = -G."""
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    for gen in ansatz.excitation_operators():
        assert len(gen.terms) == 2
        # First term has coeff +1, second has coeff -1
        coeffs = sorted([t.coeff.real for t in gen.terms])
        assert coeffs == [-1.0, 1.0]


@pytest.mark.unit
def test_to_circuit_qubit_count() -> None:
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    params = [0.1] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_to_circuit_contains_x_gates() -> None:
    """HF state preparation should produce X gates."""
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    params = [0.1] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    gates = circ.gate_count()
    assert gates.get("X", 0) >= 2  # At least from HF state


@pytest.mark.unit
def test_to_circuit_zero_params_only_hf() -> None:
    """All-zero parameters should produce only the HF state."""
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    params = [0.0] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    # Only HF X gates (JW: 2 electrons -> 2 X gates)
    assert circ.total_gate_count() == 2


@pytest.mark.unit
def test_to_circuit_has_rotations() -> None:
    """Non-zero parameters should add rotation gates."""
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    params = [0.5] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    gates = circ.gate_count()
    # Should have rotation gates from Trotter decomposition
    has_rotations = any(
        g in gates for g in ("Rx", "Ry", "Rz")
    )
    assert has_rotations


@pytest.mark.unit
def test_to_circuit_wrong_param_count() -> None:
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    with pytest.raises(CircuitError, match="Expected"):
        ansatz.to_circuit([0.1])


@pytest.mark.unit
def test_bk_mapping() -> None:
    ansatz = UCCSDAnsatz(
        n_spatial_orbitals=2, n_electrons=2,
        mapping="bravyi_kitaev",
    )
    params = [0.1] * ansatz.num_parameters
    circ = ansatz.to_circuit(params)
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_frozen() -> None:
    ansatz = UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=2)
    with pytest.raises(AttributeError):
        ansatz.n_electrons = 3  # type: ignore[misc]


@pytest.mark.unit
def test_invalid_spatial_orbitals() -> None:
    with pytest.raises(CircuitError, match="n_spatial_orbitals"):
        UCCSDAnsatz(n_spatial_orbitals=0, n_electrons=0)


@pytest.mark.unit
def test_invalid_electrons_exceed() -> None:
    with pytest.raises(CircuitError, match="cannot exceed"):
        UCCSDAnsatz(n_spatial_orbitals=2, n_electrons=5)


@pytest.mark.unit
def test_larger_system_parameter_count() -> None:
    """Verify parameter scaling for a larger system."""
    ansatz = UCCSDAnsatz(n_spatial_orbitals=3, n_electrons=2)
    # Occupied: 0(a), 1(b); Virtual: 2(a), 3(b), 4(a), 5(b)
    # Singles (spin-preserving): (0,2), (0,4), (1,3), (1,5) = 4
    assert len(ansatz.singles()) == 4
    # Doubles need spin conservation
    doubles = ansatz.doubles()
    assert len(doubles) > 0
    assert ansatz.num_parameters == len(ansatz.singles()) + len(doubles)
