"""Tests for Instruction, Measurement, and RawQSharp."""

import math

import pytest

from qdk_pythonic.core.gates import CNOT, H, RX, S
from qdk_pythonic.core.instruction import Instruction, Measurement, RawQSharp
from qdk_pythonic.core.qubit import Qubit


@pytest.mark.unit
def test_instruction_creation() -> None:
    q = Qubit(index=0)
    inst = Instruction(gate=H, targets=(q,))
    assert inst.gate is H
    assert inst.targets == (q,)
    assert inst.params == ()
    assert inst.controls == ()
    assert inst.is_adjoint is False


@pytest.mark.unit
def test_instruction_with_params() -> None:
    q = Qubit(index=0)
    inst = Instruction(gate=RX, targets=(q,), params=(math.pi / 2,))
    assert inst.params == (math.pi / 2,)


@pytest.mark.unit
def test_instruction_with_controls() -> None:
    q0 = Qubit(index=0)
    q1 = Qubit(index=1)
    inst = Instruction(gate=H, targets=(q1,), controls=(q0,))
    assert inst.controls == (q0,)


@pytest.mark.unit
def test_instruction_with_adjoint() -> None:
    q = Qubit(index=0)
    inst = Instruction(gate=S, targets=(q,), is_adjoint=True)
    assert inst.is_adjoint is True


@pytest.mark.unit
def test_instruction_is_frozen() -> None:
    q = Qubit(index=0)
    inst = Instruction(gate=H, targets=(q,))
    with pytest.raises(AttributeError):
        inst.gate = CNOT  # type: ignore[misc]


@pytest.mark.unit
def test_measurement_creation() -> None:
    q = Qubit(index=0)
    m = Measurement(target=q)
    assert m.target == q
    assert m.label is None


@pytest.mark.unit
def test_measurement_with_label() -> None:
    q = Qubit(index=0)
    m = Measurement(target=q, label="result_0")
    assert m.label == "result_0"


@pytest.mark.unit
def test_raw_qsharp_creation() -> None:
    raw = RawQSharp(code="let x = 1;")
    assert raw.code == "let x = 1;"
