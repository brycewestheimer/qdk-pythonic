"""Tests for quantum finance domain."""

from __future__ import annotations

import pytest

from qdk_pythonic.core.circuit import Circuit
from qdk_pythonic.core.instruction import Instruction
from qdk_pythonic.domains.finance.amplitude_estimation import (
    QuantumAmplitudeEstimation,
)
from qdk_pythonic.domains.finance.distributions import LogNormalDistribution
from qdk_pythonic.domains.finance.pricing import EuropeanCallOption

# ------------------------------------------------------------------
# LogNormalDistribution
# ------------------------------------------------------------------


@pytest.mark.unit
def test_lognormal_bin_values() -> None:
    dist = LogNormalDistribution(mu=0.0, sigma=0.5, n_qubits=2, bounds=(0.5, 2.0))
    bins = dist.bin_values()
    assert len(bins) == 4
    assert bins[0] > 0.5
    assert bins[-1] < 2.0


@pytest.mark.unit
def test_lognormal_to_state_prep() -> None:
    dist = LogNormalDistribution(mu=0.0, sigma=0.5, n_qubits=2, bounds=(0.5, 2.0))
    state_prep = dist.to_state_prep()
    circ = state_prep.to_circuit()
    assert circ.qubit_count() == 2


@pytest.mark.unit
def test_lognormal_probabilities_sum_to_one() -> None:
    dist = LogNormalDistribution(mu=0.0, sigma=0.5, n_qubits=3, bounds=(0.1, 5.0))
    state_prep = dist.to_state_prep()
    assert abs(sum(state_prep.probabilities) - 1.0) < 1e-8


@pytest.mark.unit
def test_lognormal_invalid_sigma() -> None:
    with pytest.raises(ValueError, match="sigma"):
        LogNormalDistribution(mu=0.0, sigma=0.0, n_qubits=2, bounds=(0.5, 2.0))


@pytest.mark.unit
def test_lognormal_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="bounds"):
        LogNormalDistribution(mu=0.0, sigma=0.5, n_qubits=2, bounds=(2.0, 0.5))


# ------------------------------------------------------------------
# EuropeanCallOption
# ------------------------------------------------------------------


@pytest.mark.unit
def test_european_call_to_circuit() -> None:
    dist = LogNormalDistribution(mu=0.0, sigma=0.5, n_qubits=2, bounds=(0.5, 2.0))
    option = EuropeanCallOption(strike=1.0, distribution=dist)
    circ = option.to_circuit(n_estimation_qubits=3)
    assert circ.qubit_count() > dist.n_qubits  # price + ancilla + estimation


@pytest.mark.unit
def test_european_call_payoff_oracle() -> None:
    dist = LogNormalDistribution(mu=0.0, sigma=0.5, n_qubits=2, bounds=(0.5, 2.0))
    option = EuropeanCallOption(strike=1.0, distribution=dist)
    oracle = option.payoff_oracle()
    assert oracle.qubit_count() > 0


@pytest.mark.unit
def test_european_call_invalid_strike() -> None:
    dist = LogNormalDistribution(mu=0.0, sigma=0.5, n_qubits=2, bounds=(0.5, 2.0))
    with pytest.raises(ValueError, match="strike"):
        EuropeanCallOption(strike=-1.0, distribution=dist)


# ------------------------------------------------------------------
# QuantumAmplitudeEstimation
# ------------------------------------------------------------------


@pytest.mark.unit
def test_qae_to_circuit() -> None:
    state = Circuit()
    q = state.allocate(2)
    state.h(q[0]).h(q[1])

    oracle = Circuit()
    q2 = oracle.allocate(2)
    oracle.z(q2[0])

    qae = QuantumAmplitudeEstimation(
        state_prep=state, oracle=oracle, n_estimation_qubits=4,
    )
    circ = qae.to_circuit()
    # 2 state qubits + 4 estimation qubits
    assert circ.qubit_count() == 6
    # Should have H gates on estimation register
    gates = circ.gate_count()
    assert gates.get("H", 0) >= 4


@pytest.mark.unit
def test_qae_invalid_n_estimation() -> None:
    state = Circuit()
    state.allocate(1)
    oracle = Circuit()
    oracle.allocate(1)
    with pytest.raises(ValueError, match="n_estimation_qubits"):
        QuantumAmplitudeEstimation(
            state_prep=state, oracle=oracle, n_estimation_qubits=0,
        )
