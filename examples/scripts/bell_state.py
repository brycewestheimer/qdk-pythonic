"""Minimal Bell state example."""

from qdk_pythonic import Circuit


def main() -> None:
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()

    print("Q# output:")
    print(circ.to_qsharp())
    print()
    print("Circuit diagram:")
    print(circ.draw())
    print()
    print(f"Depth: {circ.depth()}")
    print(f"Gate count: {circ.gate_count()}")


if __name__ == "__main__":
    main()
