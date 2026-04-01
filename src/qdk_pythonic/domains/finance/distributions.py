"""Probability distribution encoding for quantum finance.

Example::

    from qdk_pythonic.domains.finance.distributions import LogNormalDistribution

    dist = LogNormalDistribution(mu=0.05, sigma=0.2, n_qubits=4,
                                  bounds=(0.5, 2.0))
    state_prep = dist.to_state_prep()
    circuit = state_prep.to_circuit()
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from qdk_pythonic.domains.common.states import DiscreteProbabilityDistribution


@dataclass(frozen=True)
class LogNormalDistribution:
    """Log-normal price distribution for option pricing.

    Discretizes a log-normal distribution into 2^n_qubits bins.

    Attributes:
        mu: Mean of the underlying normal distribution.
        sigma: Standard deviation.
        n_qubits: Number of qubits for discretization (2^n bins).
        bounds: (low, high) price range for discretization.
    """

    mu: float
    sigma: float
    n_qubits: int
    bounds: tuple[float, float]

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise ValueError(
                f"n_qubits must be >= 1, got {self.n_qubits}"
            )
        if self.bounds[0] >= self.bounds[1]:
            raise ValueError(
                f"bounds[0] must be < bounds[1], got {self.bounds}"
            )
        if self.sigma <= 0:
            raise ValueError(
                f"sigma must be > 0, got {self.sigma}"
            )

    def bin_values(self) -> list[float]:
        """Return the midpoint price for each discretization bin."""
        n_bins = 2**self.n_qubits
        lo, hi = self.bounds
        step = (hi - lo) / n_bins
        return [lo + (i + 0.5) * step for i in range(n_bins)]

    def _pdf(self, x: float) -> float:
        """Log-normal probability density function."""
        if x <= 0:
            return 0.0
        z = (math.log(x) - self.mu) / self.sigma
        return math.exp(-0.5 * z * z) / (x * self.sigma * math.sqrt(2 * math.pi))

    def to_state_prep(self) -> DiscreteProbabilityDistribution:
        """Discretize the distribution and return a state preparation.

        Returns:
            A DiscreteProbabilityDistribution encoding the discretized
            log-normal distribution.
        """
        bins = self.bin_values()
        n_bins = len(bins)
        lo, hi = self.bounds
        step = (hi - lo) / n_bins

        # Compute un-normalized probabilities
        raw = [self._pdf(x) * step for x in bins]
        total = sum(raw)
        if total < 1e-15:
            # Uniform fallback
            probs = tuple(1.0 / n_bins for _ in range(n_bins))
        else:
            probs = tuple(p / total for p in raw)

        return DiscreteProbabilityDistribution(probabilities=probs)
