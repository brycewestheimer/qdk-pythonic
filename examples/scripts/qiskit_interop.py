"""Export a circuit to OpenQASM for use with other frameworks.

Demonstrates how to produce an OpenQASM 3.0 string that other tools
(e.g., Qiskit) can consume.
"""

from qdk_pythonic import Circuit


def main() -> None:
    # Build a circuit in qdk-pythonic
    circ = Circuit()
    q = circ.allocate(3)
    circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2]).measure_all()

    # Export to OpenQASM 3.0
    qasm = circ.to_openqasm()
    print("OpenQASM 3.0 output:")
    print(qasm)

    # Try importing into Qiskit if available
    try:
        from qiskit.qasm3 import loads  # type: ignore[import-not-found]

        qiskit_circ = loads(qasm)
        print("Loaded into Qiskit:")
        print(qiskit_circ)
    except ImportError:
        print("(Qiskit not installed -- skipping Qiskit import demo)")
        print("To try: pip install qiskit")


if __name__ == "__main__":
    main()
