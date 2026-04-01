"""Round-trip tests: build -> serialize -> parse -> compare."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.instruction import Instruction, Measurement


def circuits_equivalent(c1: Circuit, c2: Circuit) -> bool:
    """Compare two circuits for structural equivalence.

    Checks qubit count, instruction count, gate names, parameter values
    (within tolerance), control counts, and adjoint flags. Ignores qubit
    labels and register names.

    Args:
        c1: First circuit.
        c2: Second circuit.

    Returns:
        True if the circuits are structurally equivalent.
    """
    if c1.qubit_count() != c2.qubit_count():
        return False

    insts1 = c1.instructions
    insts2 = c2.instructions

    if len(insts1) != len(insts2):
        return False

    for i1, i2 in zip(insts1, insts2):
        if type(i1) is not type(i2):
            return False

        if isinstance(i1, Instruction) and isinstance(i2, Instruction):
            if i1.gate.name != i2.gate.name:
                return False
            if len(i1.params) != len(i2.params):
                return False
            for p1, p2 in zip(i1.params, i2.params):
                if not math.isclose(p1, p2, rel_tol=1e-9, abs_tol=1e-12):
                    return False
            if len(i1.controls) != len(i2.controls):
                return False
            if i1.is_adjoint != i2.is_adjoint:
                return False

        elif isinstance(i1, Measurement) and isinstance(i2, Measurement):
            # Both are measurements; we don't compare labels
            pass

    return True


# ------------------------------------------------------------------
# Q# round-trips
# ------------------------------------------------------------------


@pytest.mark.unit
def test_qsharp_roundtrip_bell() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure(q[0]).measure(q[1])

    qsharp = circ.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    assert circuits_equivalent(circ, parsed)


@pytest.mark.unit
def test_qsharp_roundtrip_ghz() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2])

    qsharp = circ.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    assert circuits_equivalent(circ, parsed)


@pytest.mark.unit
def test_qsharp_roundtrip_rx_angle() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(1.5707, q[0])

    qsharp = circ.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    assert circuits_equivalent(circ, parsed)

    # Verify the angle is actually preserved
    gates = [i for i in parsed.instructions if isinstance(i, Instruction)]
    assert math.isclose(gates[0].params[0], 1.5707, rel_tol=1e-9)


@pytest.mark.unit
def test_qsharp_roundtrip_controlled() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.controlled(circ.h, [q[0]], q[1])

    qsharp = circ.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    assert circuits_equivalent(circ, parsed)

    gates = [i for i in parsed.instructions if isinstance(i, Instruction)]
    assert len(gates[0].controls) == 1


@pytest.mark.unit
def test_qsharp_roundtrip_adjoint() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.s, q[0])

    qsharp = circ.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    assert circuits_equivalent(circ, parsed)

    gates = [i for i in parsed.instructions if isinstance(i, Instruction)]
    assert gates[0].is_adjoint is True


# ------------------------------------------------------------------
# OpenQASM round-trips
# ------------------------------------------------------------------


@pytest.mark.unit
def test_openqasm_roundtrip_bell() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure(q[0]).measure(q[1])

    oq = circ.to_openqasm()
    parsed = Circuit.from_openqasm(oq)
    assert circuits_equivalent(circ, parsed)


@pytest.mark.unit
def test_openqasm_roundtrip_ghz() -> None:
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2])

    oq = circ.to_openqasm()
    parsed = Circuit.from_openqasm(oq)
    assert circuits_equivalent(circ, parsed)


@pytest.mark.unit
def test_openqasm_roundtrip_rx_angle() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.rx(1.5707, q[0])

    oq = circ.to_openqasm()
    parsed = Circuit.from_openqasm(oq)
    assert circuits_equivalent(circ, parsed)


@pytest.mark.unit
def test_openqasm_roundtrip_controlled() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.controlled(circ.h, [q[0]], q[1])

    oq = circ.to_openqasm()
    parsed = Circuit.from_openqasm(oq)
    assert circuits_equivalent(circ, parsed)


@pytest.mark.unit
def test_openqasm_roundtrip_adjoint() -> None:
    circ = Circuit()
    q = circ.allocate(1)
    circ.adjoint(circ.s, q[0])

    oq = circ.to_openqasm()
    parsed = Circuit.from_openqasm(oq)
    assert circuits_equivalent(circ, parsed)


# ------------------------------------------------------------------
# Cross-format
# ------------------------------------------------------------------


@pytest.mark.unit
def test_cross_qsharp_to_openqasm() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])

    qsharp = circ.to_qsharp()
    parsed = Circuit.from_qsharp(qsharp)
    oq_output = parsed.to_openqasm()
    assert "OPENQASM 3.0" in oq_output


@pytest.mark.unit
def test_cross_openqasm_to_qsharp() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])

    oq = circ.to_openqasm()
    parsed = Circuit.from_openqasm(oq)
    qsharp_output = parsed.to_qsharp()
    assert "Qubit" in qsharp_output
