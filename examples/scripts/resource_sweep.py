"""Sweep circuit sizes and estimate resources.

Requires qsharp: pip install "qdk-pythonic[qsharp]"
"""

import math

from qdk_pythonic import Circuit
from qdk_pythonic.execution import estimate_circuit_batch


def build_trotter_step(n: int, angle: float) -> Circuit:
    """Build one Trotter step for an n-qubit 1D Ising chain."""
    circ = Circuit()
    q = circ.allocate(n)
    for i in range(n - 1):
        circ.cx(q[i], q[i + 1])
        circ.rz(angle, q[i + 1])
        circ.cx(q[i], q[i + 1])
    for i in range(n):
        circ.rx(angle, q[i])
    return circ


def main() -> None:
    sizes = [4, 8, 12, 16]
    configs = [
        {"qubitParams": {"name": "qubit_gate_ns_e3"}},
        {"qubitParams": {"name": "qubit_gate_ns_e4"}},
    ]

    for n in sizes:
        circ = build_trotter_step(n, math.pi / 4)
        print(f"\n--- n={n} ({circ.qubit_count()} qubits, depth={circ.depth()}) ---")

        results = estimate_circuit_batch(circ, configs)
        for cfg, result in zip(configs, results):
            name = cfg["qubitParams"]["name"]
            print(f"  {name}: {result}")


if __name__ == "__main__":
    main()
