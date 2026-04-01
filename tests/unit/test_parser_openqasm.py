"""Tests for the OpenQASM parser."""

from __future__ import annotations

import math

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.gates import (
    CCNOT,
    CNOT,
    CZ,
    H,
    R1,
    RX,
    RY,
    RZ,
    S,
    SWAP,
    T,
    X,
    Y,
    Z,
)
from qdk_pythonic.core.instruction import Instruction, Measurement
from qdk_pythonic.exceptions import ParserError, UnsupportedConstructError
from qdk_pythonic.parser.openqasm_parser import OpenQASMParser


def _gate_instructions(circ: Circuit) -> list[Instruction]:
    """Extract only gate instructions from a circuit."""
    return [i for i in circ.instructions if isinstance(i, Instruction)]


def _measurements(circ: Circuit) -> list[Measurement]:
    """Extract only measurements from a circuit."""
    return [i for i in circ.instructions if isinstance(i, Measurement)]


# ------------------------------------------------------------------
# Bell state
# ------------------------------------------------------------------


@pytest.mark.unit
def test_bell_state() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;

h q[0];
cx q[0], q[1];

bit[2] c;
c[0] = measure q[0];
c[1] = measure q[1];
"""
    circ = OpenQASMParser().parse(source)
    assert circ.qubit_count() == 2
    gates = _gate_instructions(circ)
    assert len(gates) == 2
    assert gates[0].gate is H
    assert gates[1].gate is CNOT
    assert len(_measurements(circ)) == 2


# ------------------------------------------------------------------
# GHZ state
# ------------------------------------------------------------------


@pytest.mark.unit
def test_ghz_state() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;

h q[0];
cx q[0], q[1];
cx q[1], q[2];
"""
    circ = OpenQASMParser().parse(source)
    assert circ.qubit_count() == 3
    gates = _gate_instructions(circ)
    assert len(gates) == 3
    assert gates[0].gate is H
    assert gates[1].gate is CNOT
    assert gates[2].gate is CNOT


# ------------------------------------------------------------------
# Parameterized rotation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_rx_with_angle() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;

rx(1.5707) q[0];
"""
    circ = OpenQASMParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is RX
    assert math.isclose(gates[0].params[0], 1.5707, rel_tol=1e-9)


# ------------------------------------------------------------------
# Controlled gate (ctrl @)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_gate() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;

ctrl @ h q[0], q[1];
"""
    circ = OpenQASMParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is H
    assert len(gates[0].controls) == 1
    assert gates[0].is_adjoint is False


# ------------------------------------------------------------------
# Adjoint gate (inv @)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_adjoint_gate() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;

inv @ s q[0];
"""
    circ = OpenQASMParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is S
    assert gates[0].is_adjoint is True


# ------------------------------------------------------------------
# Controlled + Adjoint gate (ctrl @ inv @)
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_adjoint_gate() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;

ctrl @ inv @ s q[0], q[1];
"""
    circ = OpenQASMParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is S
    assert len(gates[0].controls) == 1
    assert gates[0].is_adjoint is True


# ------------------------------------------------------------------
# All 14 gate types
# ------------------------------------------------------------------


def _make_source(gate_line: str, n_qubits: int = 1) -> str:
    """Build a minimal OpenQASM source with one gate line."""
    return f"""OPENQASM 3.0;
include "stdgates.inc";
qubit[{n_qubits}] q;
{gate_line}
"""


@pytest.mark.unit
def test_h_gate() -> None:
    gates = _gate_instructions(OpenQASMParser().parse(_make_source("h q[0];")))
    assert gates[0].gate is H


@pytest.mark.unit
def test_x_gate() -> None:
    gates = _gate_instructions(OpenQASMParser().parse(_make_source("x q[0];")))
    assert gates[0].gate is X


@pytest.mark.unit
def test_y_gate() -> None:
    gates = _gate_instructions(OpenQASMParser().parse(_make_source("y q[0];")))
    assert gates[0].gate is Y


@pytest.mark.unit
def test_z_gate() -> None:
    gates = _gate_instructions(OpenQASMParser().parse(_make_source("z q[0];")))
    assert gates[0].gate is Z


@pytest.mark.unit
def test_s_gate() -> None:
    gates = _gate_instructions(OpenQASMParser().parse(_make_source("s q[0];")))
    assert gates[0].gate is S


@pytest.mark.unit
def test_t_gate() -> None:
    gates = _gate_instructions(OpenQASMParser().parse(_make_source("t q[0];")))
    assert gates[0].gate is T


@pytest.mark.unit
def test_rx_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(_make_source("rx(0.5) q[0];"))
    )
    assert gates[0].gate is RX
    assert math.isclose(gates[0].params[0], 0.5)


@pytest.mark.unit
def test_ry_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(_make_source("ry(0.5) q[0];"))
    )
    assert gates[0].gate is RY


@pytest.mark.unit
def test_rz_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(_make_source("rz(0.5) q[0];"))
    )
    assert gates[0].gate is RZ


@pytest.mark.unit
def test_r1_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(_make_source("p(0.5) q[0];"))
    )
    assert gates[0].gate is R1


@pytest.mark.unit
def test_cx_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(_make_source("cx q[0], q[1];", n_qubits=2))
    )
    assert gates[0].gate is CNOT


@pytest.mark.unit
def test_cz_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(_make_source("cz q[0], q[1];", n_qubits=2))
    )
    assert gates[0].gate is CZ


@pytest.mark.unit
def test_swap_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(_make_source("swap q[0], q[1];", n_qubits=2))
    )
    assert gates[0].gate is SWAP


@pytest.mark.unit
def test_ccx_gate() -> None:
    gates = _gate_instructions(
        OpenQASMParser().parse(
            _make_source("ccx q[0], q[1], q[2];", n_qubits=3)
        )
    )
    assert gates[0].gate is CCNOT


# ------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------


@pytest.mark.unit
def test_missing_header() -> None:
    with pytest.raises(ParserError, match="Missing or invalid"):
        OpenQASMParser().parse("qubit[2] q;\nh q[0];")


@pytest.mark.unit
def test_wrong_version() -> None:
    with pytest.raises(ParserError, match="Unsupported OpenQASM version"):
        OpenQASMParser().parse("OPENQASM 2.0;\nqubit[1] q;\nh q[0];")


@pytest.mark.unit
def test_unsupported_gate_definition() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";
gate my_gate q { h q; }
"""
    with pytest.raises(UnsupportedConstructError, match="gate"):
        OpenQASMParser().parse(source)


@pytest.mark.unit
def test_unsupported_if() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
bit[1] c;
if (c[0]) x q[0];
"""
    with pytest.raises(UnsupportedConstructError, match="if"):
        OpenQASMParser().parse(source)


@pytest.mark.unit
def test_unknown_gate() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
foobar q[0];
"""
    with pytest.raises(ParserError, match="Unknown OpenQASM gate"):
        OpenQASMParser().parse(source)


@pytest.mark.unit
def test_empty_source_raises() -> None:
    with pytest.raises(ParserError, match="Empty OpenQASM source"):
        OpenQASMParser().parse("")


@pytest.mark.unit
def test_header_only_empty_circuit() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";
"""
    circ = OpenQASMParser().parse(source)
    assert circ.qubit_count() == 0
    assert len(circ.instructions) == 0


# ------------------------------------------------------------------
# Controlled rotation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_controlled_rx() -> None:
    source = """OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;

ctrl @ rx(1.5707) q[0], q[1];
"""
    circ = OpenQASMParser().parse(source)
    gates = _gate_instructions(circ)
    assert len(gates) == 1
    assert gates[0].gate is RX
    assert len(gates[0].controls) == 1
    assert math.isclose(gates[0].params[0], 1.5707, rel_tol=1e-9)
