"""Tests for GateDefinition and the gate catalog."""

import pytest

from qdk_pythonic.core.gates import (
    CCNOT,
    CNOT,
    CZ,
    GATE_CATALOG,
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
    GateDefinition,
)


@pytest.mark.unit
def test_h_gate() -> None:
    assert H.name == "H"
    assert H.num_qubits == 1
    assert H.num_params == 0
    assert H.qsharp_name == "H"
    assert H.openqasm_name == "h"


@pytest.mark.unit
def test_x_gate() -> None:
    assert X.name == "X"
    assert X.num_qubits == 1
    assert X.num_params == 0


@pytest.mark.unit
def test_y_gate() -> None:
    assert Y.name == "Y"
    assert Y.num_qubits == 1
    assert Y.num_params == 0


@pytest.mark.unit
def test_z_gate() -> None:
    assert Z.name == "Z"
    assert Z.num_qubits == 1
    assert Z.num_params == 0


@pytest.mark.unit
def test_s_gate() -> None:
    assert S.name == "S"
    assert S.num_qubits == 1
    assert S.num_params == 0
    assert S.qsharp_name == "S"
    assert S.openqasm_name == "s"


@pytest.mark.unit
def test_t_gate() -> None:
    assert T.name == "T"
    assert T.num_qubits == 1
    assert T.num_params == 0


@pytest.mark.unit
def test_rx_gate() -> None:
    assert RX.name == "Rx"
    assert RX.num_qubits == 1
    assert RX.num_params == 1
    assert RX.qsharp_name == "Rx"
    assert RX.openqasm_name == "rx"


@pytest.mark.unit
def test_ry_gate() -> None:
    assert RY.name == "Ry"
    assert RY.num_qubits == 1
    assert RY.num_params == 1


@pytest.mark.unit
def test_rz_gate() -> None:
    assert RZ.name == "Rz"
    assert RZ.num_qubits == 1
    assert RZ.num_params == 1


@pytest.mark.unit
def test_r1_gate() -> None:
    assert R1.name == "R1"
    assert R1.num_qubits == 1
    assert R1.num_params == 1
    assert R1.qsharp_name == "R1"
    assert R1.openqasm_name == "p"


@pytest.mark.unit
def test_cnot_gate() -> None:
    assert CNOT.name == "CNOT"
    assert CNOT.num_qubits == 2
    assert CNOT.num_params == 0
    assert CNOT.qsharp_name == "CNOT"
    assert CNOT.openqasm_name == "cx"


@pytest.mark.unit
def test_cz_gate() -> None:
    assert CZ.name == "CZ"
    assert CZ.num_qubits == 2
    assert CZ.num_params == 0


@pytest.mark.unit
def test_swap_gate() -> None:
    assert SWAP.name == "SWAP"
    assert SWAP.num_qubits == 2
    assert SWAP.num_params == 0
    assert SWAP.openqasm_name == "swap"


@pytest.mark.unit
def test_ccnot_gate() -> None:
    assert CCNOT.name == "CCNOT"
    assert CCNOT.num_qubits == 3
    assert CCNOT.num_params == 0
    assert CCNOT.openqasm_name == "ccx"


@pytest.mark.unit
def test_gate_catalog_contains_all_14_gates() -> None:
    expected = {"H", "X", "Y", "Z", "S", "T", "Rx", "Ry", "Rz", "R1",
                "CNOT", "CZ", "SWAP", "CCNOT"}
    assert set(GATE_CATALOG.keys()) == expected
    assert len(GATE_CATALOG) == 14


@pytest.mark.unit
def test_gate_definition_is_frozen() -> None:
    with pytest.raises(AttributeError):
        H.name = "NotH"  # type: ignore[misc]
