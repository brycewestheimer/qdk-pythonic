"""Tests for HartreeFockState."""

from __future__ import annotations

import pytest

from qdk_pythonic.domains.chemistry.hartree_fock import HartreeFockState
from qdk_pythonic.exceptions import CircuitError


@pytest.mark.unit
def test_jw_bitstring_h2() -> None:
    """H2: 2 electrons in 4 spin-orbitals -> '1100'."""
    hf = HartreeFockState(n_qubits=4, n_electrons=2)
    assert hf.to_bitstring() == "1100"


@pytest.mark.unit
def test_jw_bitstring_lih() -> None:
    """LiH-like: 4 electrons in 12 spin-orbitals."""
    hf = HartreeFockState(n_qubits=12, n_electrons=4)
    assert hf.to_bitstring() == "1111" + "0" * 8


@pytest.mark.unit
def test_jw_bitstring_zero_electrons() -> None:
    hf = HartreeFockState(n_qubits=4, n_electrons=0)
    assert hf.to_bitstring() == "0000"


@pytest.mark.unit
def test_jw_bitstring_full_occupation() -> None:
    hf = HartreeFockState(n_qubits=4, n_electrons=4)
    assert hf.to_bitstring() == "1111"


@pytest.mark.unit
def test_jw_circuit_qubit_count() -> None:
    hf = HartreeFockState(n_qubits=4, n_electrons=2)
    circ = hf.to_circuit()
    assert circ.qubit_count() == 4


@pytest.mark.unit
def test_jw_circuit_gate_count() -> None:
    """JW HF state uses exactly n_electrons X gates."""
    hf = HartreeFockState(n_qubits=4, n_electrons=2)
    circ = hf.to_circuit()
    gates = circ.gate_count()
    assert gates.get("X", 0) == 2
    assert circ.total_gate_count() == 2


@pytest.mark.unit
def test_bk_bitstring_2_qubits() -> None:
    """2 qubits, 1 electron: occ=[1,0].

    BK qubit 0: responsible for [0,0] -> occ[0]=1 -> '1'
    BK qubit 1: responsible for [0,1] -> occ[0]^occ[1]=1 -> '1'
    """
    hf = HartreeFockState(n_qubits=2, n_electrons=1, mapping="bravyi_kitaev")
    assert hf.to_bitstring() == "11"


@pytest.mark.unit
def test_bk_bitstring_4_qubits_2_electrons() -> None:
    """4 qubits, 2 electrons: occ=[1,1,0,0].

    BK qubit 0: range [0,0] -> 1 -> '1'
    BK qubit 1: range [0,1] -> 1^1=0 -> '0'
    BK qubit 2: range [2,2] -> 0 -> '0'
    BK qubit 3: range [0,3] -> 1^1^0^0=0 -> '0'
    """
    hf = HartreeFockState(n_qubits=4, n_electrons=2, mapping="bravyi_kitaev")
    assert hf.to_bitstring() == "1000"


@pytest.mark.unit
def test_bk_bitstring_4_qubits_1_electron() -> None:
    """4 qubits, 1 electron: occ=[1,0,0,0].

    BK qubit 0: range [0,0] -> 1 -> '1'
    BK qubit 1: range [0,1] -> 1^0=1 -> '1'
    BK qubit 2: range [2,2] -> 0 -> '0'
    BK qubit 3: range [0,3] -> 1^0^0^0=1 -> '1'
    """
    hf = HartreeFockState(n_qubits=4, n_electrons=1, mapping="bravyi_kitaev")
    assert hf.to_bitstring() == "1101"


@pytest.mark.unit
def test_bk_circuit_produces_valid_circuit() -> None:
    hf = HartreeFockState(n_qubits=4, n_electrons=2, mapping="bravyi_kitaev")
    circ = hf.to_circuit()
    assert circ.qubit_count() == 4
    # BK bitstring "1000" -> 1 X gate
    assert circ.total_gate_count() == 1


@pytest.mark.unit
def test_frozen() -> None:
    hf = HartreeFockState(n_qubits=4, n_electrons=2)
    with pytest.raises(AttributeError):
        hf.n_qubits = 6  # type: ignore[misc]


@pytest.mark.unit
def test_invalid_n_qubits() -> None:
    with pytest.raises(CircuitError, match="n_qubits must be >= 1"):
        HartreeFockState(n_qubits=0, n_electrons=0)


@pytest.mark.unit
def test_invalid_n_electrons_negative() -> None:
    with pytest.raises(CircuitError, match="n_electrons must be >= 0"):
        HartreeFockState(n_qubits=4, n_electrons=-1)


@pytest.mark.unit
def test_invalid_n_electrons_exceeds_qubits() -> None:
    with pytest.raises(CircuitError, match="cannot exceed"):
        HartreeFockState(n_qubits=4, n_electrons=5)


@pytest.mark.unit
def test_invalid_mapping() -> None:
    with pytest.raises(CircuitError, match="Unknown mapping"):
        HartreeFockState(n_qubits=4, n_electrons=2, mapping="parity")
