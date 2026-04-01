"""Quantum finance: amplitude estimation and option pricing.

Example::

    from qdk_pythonic.domains.finance import (
        LogNormalDistribution, EuropeanCallOption, QuantumAmplitudeEstimation,
    )

    dist = LogNormalDistribution(mu=0.05, sigma=0.2, n_qubits=4,
                                  bounds=(0.5, 2.0))
    option = EuropeanCallOption(strike=1.0, distribution=dist)
    circuit = option.to_circuit(n_estimation_qubits=6)
"""

from qdk_pythonic.domains.finance.amplitude_estimation import (
    QuantumAmplitudeEstimation,
)
from qdk_pythonic.domains.finance.distributions import LogNormalDistribution
from qdk_pythonic.domains.finance.pricing import EuropeanCallOption

__all__ = [
    "EuropeanCallOption",
    "LogNormalDistribution",
    "QuantumAmplitudeEstimation",
]
