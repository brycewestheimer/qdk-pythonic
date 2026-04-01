"""Parameterized GHZ state for N qubits."""

import sys

from qdk_pythonic import Circuit


def build_ghz(n: int) -> Circuit:
    """Build an N-qubit GHZ state circuit.

    Applies H to the first qubit, then a chain of CNOTs.
    """
    circ = Circuit()
    q = circ.allocate(n)
    circ.h(q[0])
    for i in range(n - 1):
        circ.cx(q[i], q[i + 1])
    circ.measure_all()
    return circ


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    circ = build_ghz(n)

    print(f"GHZ state for {n} qubits:")
    print(circ.draw())
    print()
    print(f"Depth: {circ.depth()}")
    print(f"Gate count: {circ.gate_count()}")
    print()
    print("Q# output:")
    print(circ.to_qsharp())


if __name__ == "__main__":
    main()
