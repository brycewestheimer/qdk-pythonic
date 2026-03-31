"""Gate definitions and the gate catalog."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GateDefinition:
    """Metadata for a quantum gate type.

    Attributes:
        name: The canonical name of the gate.
        num_qubits: Number of qubit operands.
        num_params: Number of floating-point parameters.
        qsharp_name: The gate name in Q# syntax.
        openqasm_name: The gate name in OpenQASM 3.0 syntax.
        is_controlled: Whether this is a controlled variant.
        is_adjoint: Whether this is an adjoint variant.
    """

    name: str
    num_qubits: int
    num_params: int
    qsharp_name: str
    openqasm_name: str
    is_controlled: bool = False
    is_adjoint: bool = False


# Single-qubit gates (no parameters)
H = GateDefinition(name="H", num_qubits=1, num_params=0, qsharp_name="H", openqasm_name="h")
X = GateDefinition(name="X", num_qubits=1, num_params=0, qsharp_name="X", openqasm_name="x")
Y = GateDefinition(name="Y", num_qubits=1, num_params=0, qsharp_name="Y", openqasm_name="y")
Z = GateDefinition(name="Z", num_qubits=1, num_params=0, qsharp_name="Z", openqasm_name="z")
S = GateDefinition(name="S", num_qubits=1, num_params=0, qsharp_name="S", openqasm_name="s")
T = GateDefinition(name="T", num_qubits=1, num_params=0, qsharp_name="T", openqasm_name="t")

# Single-qubit rotation gates (one parameter)
RX = GateDefinition(name="Rx", num_qubits=1, num_params=1, qsharp_name="Rx", openqasm_name="rx")
RY = GateDefinition(name="Ry", num_qubits=1, num_params=1, qsharp_name="Ry", openqasm_name="ry")
RZ = GateDefinition(name="Rz", num_qubits=1, num_params=1, qsharp_name="Rz", openqasm_name="rz")
R1 = GateDefinition(name="R1", num_qubits=1, num_params=1, qsharp_name="R1", openqasm_name="p")

# Two-qubit gates
CNOT = GateDefinition(
    name="CNOT", num_qubits=2, num_params=0, qsharp_name="CNOT", openqasm_name="cx"
)
CZ = GateDefinition(
    name="CZ", num_qubits=2, num_params=0, qsharp_name="CZ", openqasm_name="cz"
)
SWAP = GateDefinition(
    name="SWAP", num_qubits=2, num_params=0, qsharp_name="SWAP", openqasm_name="swap"
)

# Three-qubit gates
CCNOT = GateDefinition(
    name="CCNOT", num_qubits=3, num_params=0, qsharp_name="CCNOT", openqasm_name="ccx"
)

GATE_CATALOG: dict[str, GateDefinition] = {
    "H": H,
    "X": X,
    "Y": Y,
    "Z": Z,
    "S": S,
    "T": T,
    "Rx": RX,
    "Ry": RY,
    "Rz": RZ,
    "R1": R1,
    "CNOT": CNOT,
    "CZ": CZ,
    "SWAP": SWAP,
    "CCNOT": CCNOT,
}
