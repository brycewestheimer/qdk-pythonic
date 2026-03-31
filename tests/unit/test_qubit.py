"""Tests for Qubit and QubitRegister."""

import pytest

from qdk_pythonic.core.qubit import Qubit, QubitRegister


@pytest.mark.unit
def test_qubit_creation_index_only() -> None:
    q = Qubit(index=0)
    assert q.index == 0
    assert q.label is None


@pytest.mark.unit
def test_qubit_creation_with_label() -> None:
    q = Qubit(index=3, label="ancilla")
    assert q.index == 3
    assert q.label == "ancilla"


@pytest.mark.unit
def test_qubit_is_frozen() -> None:
    q = Qubit(index=0)
    with pytest.raises(AttributeError):
        q.index = 5  # type: ignore[misc]


@pytest.mark.unit
def test_qubit_equality() -> None:
    q1 = Qubit(index=0, label="a")
    q2 = Qubit(index=0, label="a")
    q3 = Qubit(index=1, label="a")
    assert q1 == q2
    assert q1 != q3


@pytest.mark.unit
def test_qubit_hashing() -> None:
    q1 = Qubit(index=0, label="a")
    q2 = Qubit(index=0, label="a")
    assert hash(q1) == hash(q2)
    assert len({q1, q2}) == 1


@pytest.mark.unit
def test_register_creation_and_length() -> None:
    qubits = [Qubit(index=i) for i in range(4)]
    reg = QubitRegister(qubits, label="data")
    assert len(reg) == 4
    assert reg.label == "data"


@pytest.mark.unit
def test_register_integer_indexing_positive() -> None:
    qubits = [Qubit(index=i) for i in range(3)]
    reg = QubitRegister(qubits)
    assert reg[0] == qubits[0]
    assert reg[2] == qubits[2]


@pytest.mark.unit
def test_register_integer_indexing_negative() -> None:
    qubits = [Qubit(index=i) for i in range(3)]
    reg = QubitRegister(qubits)
    assert reg[-1] == qubits[2]
    assert reg[-3] == qubits[0]


@pytest.mark.unit
def test_register_slice_returns_register() -> None:
    qubits = [Qubit(index=i) for i in range(5)]
    reg = QubitRegister(qubits, label="test")
    sliced = reg[1:3]
    assert isinstance(sliced, QubitRegister)
    assert len(sliced) == 2
    assert sliced[0] == qubits[1]
    assert sliced[1] == qubits[2]


@pytest.mark.unit
def test_register_out_of_bounds_raises() -> None:
    reg = QubitRegister([Qubit(index=0)])
    with pytest.raises(IndexError):
        _ = reg[5]


@pytest.mark.unit
def test_register_iteration_yields_qubits() -> None:
    qubits = [Qubit(index=i) for i in range(3)]
    reg = QubitRegister(qubits)
    iterated = list(reg)
    assert iterated == qubits
    assert all(isinstance(q, Qubit) for q in reg)
