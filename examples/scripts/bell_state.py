"""Minimal Bell state example using the bell_state builder."""

from qdk_pythonic import bell_state


def main() -> None:
    circ = bell_state()

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
