"""Parameterized GHZ state for N qubits using the ghz_state builder."""

import sys

from qdk_pythonic import ghz_state


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    circ = ghz_state(n)

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
