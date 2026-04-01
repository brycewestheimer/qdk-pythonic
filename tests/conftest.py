"""Shared test configuration and fixtures."""

from __future__ import annotations

import pytest

from qdk_pythonic.core.circuit import Circuit


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast tests, no qsharp needed")
    config.addinivalue_line("markers", "integration: requires qsharp package")


@pytest.fixture
def bell_circuit() -> Circuit:
    """Bell state circuit with measurements."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1]).measure_all()
    return circ


@pytest.fixture
def bell_circuit_no_measure() -> Circuit:
    """Bell state circuit without measurements."""
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).cx(q[0], q[1])
    return circ


@pytest.fixture
def estimable_circuit() -> Circuit:
    """Circuit with non-Clifford gates suitable for resource estimation.

    The Q# resource estimator requires at least one T gate or rotation
    (which decomposes into T gates) to have resources to estimate.
    Pure Clifford circuits (H, CNOT, S, etc.) will fail estimation.
    """
    circ = Circuit()
    q = circ.allocate(2)
    circ.h(q[0]).t(q[0]).cx(q[0], q[1]).measure_all()
    return circ
