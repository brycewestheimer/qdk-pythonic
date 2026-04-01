"""Common circuit and state builder functions.

Provides factory functions for frequently used quantum circuits such as
Bell states, GHZ states, W states, QFT, and random circuits. Each
function returns a :class:`~qdk_pythonic.core.circuit.Circuit` instance.
"""

from __future__ import annotations

import math
import random as _random

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.exceptions import CircuitError

__all__ = [
    "bell_state",
    "ghz_state",
    "inverse_qft",
    "qft",
    "random_circuit",
    "w_state",
]


def bell_state(*, measure: bool = False) -> Circuit:
    """Build a 2-qubit Bell state circuit producing (|00> + |11>) / sqrt(2).

    Args:
        measure: If True, append measurements on both qubits.

    Returns:
        A 2-qubit circuit.
    """
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    if measure:
        circ.measure_all()
    return circ


def ghz_state(n: int, *, measure: bool = False) -> Circuit:
    """Build an N-qubit GHZ state circuit producing (|0...0> + |1...1>) / sqrt(2).

    Applies H to qubit 0, then a chain of CNOT(i, i+1).

    Args:
        n: Number of qubits. Must be >= 2.
        measure: If True, append measurements on all qubits.

    Returns:
        An N-qubit circuit.

    Raises:
        CircuitError: If *n* < 2.
    """
    if n < 2:
        raise CircuitError(f"GHZ state requires n >= 2, got {n}")
    circ = Circuit()
    q = circ.allocate(n)
    circ.h(q[0])
    for i in range(n - 1):
        circ.cx(q[i], q[i + 1])
    if measure:
        circ.measure_all()
    return circ


def w_state(n: int, *, measure: bool = False) -> Circuit:
    """Build an N-qubit W state circuit.

    The W state is the equal superposition of all single-excitation basis
    states: (|10...0> + |01...0> + ... + |00...1>) / sqrt(n).

    Uses X on the first qubit, then a sequence of Ry rotations and CNOTs
    to distribute the excitation evenly.

    Args:
        n: Number of qubits. Must be >= 2.
        measure: If True, append measurements on all qubits.

    Returns:
        An N-qubit circuit.

    Raises:
        CircuitError: If *n* < 2.
    """
    if n < 2:
        raise CircuitError(f"W state requires n >= 2, got {n}")
    circ = Circuit()
    q = circ.allocate(n)
    circ.x(q[0])
    for k in range(n - 1):
        theta = 2.0 * math.asin(math.sqrt(1.0 / (n - k)))
        circ.ry(theta, q[k + 1])
        circ.cx(q[k + 1], q[k])
    if measure:
        circ.measure_all()
    return circ


def qft(n: int) -> Circuit:
    """Build an N-qubit Quantum Fourier Transform circuit.

    Applies the standard QFT decomposition: for each qubit j, apply H
    followed by controlled-R1(pi / 2^(k-j)) from each qubit k > j.
    Finishes with SWAPs to reverse qubit order.

    Args:
        n: Number of qubits. Must be >= 1.

    Returns:
        An N-qubit circuit implementing QFT.

    Raises:
        CircuitError: If *n* < 1.
    """
    if n < 1:
        raise CircuitError(f"QFT requires n >= 1, got {n}")
    circ = Circuit()
    q = circ.allocate(n)
    for j in range(n):
        circ.h(q[j])
        for k in range(j + 1, n):
            angle = math.pi / (2 ** (k - j))
            circ.controlled(circ.r1, [q[k]], angle, q[j])
    for i in range(n // 2):
        circ.swap(q[i], q[n - 1 - i])
    return circ


def inverse_qft(n: int) -> Circuit:
    """Build an N-qubit inverse QFT circuit.

    Reverses the QFT by applying SWAPs first, then the adjoint of each
    H + controlled-R1 layer in reverse order.

    Args:
        n: Number of qubits. Must be >= 1.

    Returns:
        An N-qubit circuit implementing inverse QFT.

    Raises:
        CircuitError: If *n* < 1.
    """
    if n < 1:
        raise CircuitError(f"Inverse QFT requires n >= 1, got {n}")
    circ = Circuit()
    q = circ.allocate(n)
    for i in range(n // 2):
        circ.swap(q[i], q[n - 1 - i])
    for j in range(n - 1, -1, -1):
        for k in range(n - 1, j, -1):
            angle = -math.pi / (2 ** (k - j))
            circ.controlled(circ.r1, [q[k]], angle, q[j])
        circ.h(q[j])
    return circ


def random_circuit(
    n_qubits: int,
    depth: int,
    *,
    seed: int | None = None,
) -> Circuit:
    """Build a random circuit for benchmarking.

    Each layer applies random gates to random qubits drawn from a pool
    of single-qubit and two-qubit gates.

    Args:
        n_qubits: Number of qubits. Must be >= 1.
        depth: Number of gate layers. Must be >= 1.
        seed: Optional random seed for reproducibility.

    Returns:
        A random circuit.

    Raises:
        CircuitError: If *n_qubits* < 1 or *depth* < 1.
    """
    if n_qubits < 1:
        raise CircuitError(f"random_circuit requires n_qubits >= 1, got {n_qubits}")
    if depth < 1:
        raise CircuitError(f"random_circuit requires depth >= 1, got {depth}")

    rng = _random.Random(seed)
    circ = Circuit()
    q = circ.allocate(n_qubits)

    single_no_param = [circ.h, circ.x, circ.y, circ.z, circ.s, circ.t]
    single_param = [circ.rx, circ.ry, circ.rz]

    for _ in range(depth):
        indices = list(range(n_qubits))
        rng.shuffle(indices)
        pos = 0
        while pos < len(indices):
            remaining = len(indices) - pos
            # Try a two-qubit gate if we have room and enough qubits
            if remaining >= 2 and n_qubits >= 2 and rng.random() < 0.4:
                two_qubit_fn = rng.choice([circ.cx, circ.cz, circ.swap])
                two_qubit_fn(q[indices[pos]], q[indices[pos + 1]])
                pos += 2
            else:
                target = q[indices[pos]]
                if rng.random() < 0.4:
                    param_fn = rng.choice(single_param)
                    angle = rng.uniform(0.0, 2.0 * math.pi)
                    param_fn(angle, target)
                else:
                    no_param_fn = rng.choice(single_no_param)
                    no_param_fn(target)
                pos += 1

    return circ
