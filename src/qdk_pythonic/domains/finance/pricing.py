"""Option pricing via quantum circuits.

Example::

    from qdk_pythonic.domains.finance import LogNormalDistribution, EuropeanCallOption

    dist = LogNormalDistribution(mu=0.05, sigma=0.2, n_qubits=4,
                                  bounds=(0.5, 2.0))
    option = EuropeanCallOption(strike=1.0, distribution=dist)
    circuit = option.to_circuit(n_estimation_qubits=6)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qdk_pythonic.domains.finance.distributions import LogNormalDistribution

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


@dataclass(frozen=True)
class EuropeanCallOption:
    """European call option pricing via quantum amplitude estimation.

    Constructs a circuit combining state preparation (price distribution)
    with a payoff oracle (comparator + controlled rotations).

    Attributes:
        strike: The strike price.
        distribution: The price distribution to use.
    """

    strike: float
    distribution: LogNormalDistribution

    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError(
                f"strike must be > 0, got {self.strike}"
            )

    def payoff_oracle(self) -> Circuit:
        """Build the payoff computation sub-circuit.

        Encodes max(S - K, 0) into the amplitude of an ancilla qubit
        using controlled Ry rotations conditioned on the price register.

        Returns:
            A circuit implementing the payoff oracle.
        """
        from qdk_pythonic.core.circuit import Circuit

        bins = self.distribution.bin_values()
        n_price = self.distribution.n_qubits
        _, hi = self.distribution.bounds

        circ = Circuit()
        price_q = circ.allocate(n_price, label="price")
        ancilla_q = circ.allocate(1, label="payoff")

        # For each bin whose midpoint > strike, apply controlled Ry
        max_payoff = hi - self.strike
        if max_payoff <= 0:
            return circ

        for i, s in enumerate(bins):
            payoff = max(s - self.strike, 0.0)
            if payoff <= 0:
                continue
            # Normalized payoff amplitude
            amplitude = math.sqrt(payoff / max_payoff)
            amplitude = min(amplitude, 1.0)
            theta = 2.0 * math.asin(amplitude)

            # Encode bin index i as X gates on the price register
            bits = format(i, f"0{n_price}b")
            for bit_idx, bit in enumerate(bits):
                if bit == "0":
                    circ.x(price_q[bit_idx])

            # Controlled Ry on ancilla
            circ.controlled(circ.ry, list(price_q), theta, ancilla_q[0])

            # Undo X gates
            for bit_idx, bit in enumerate(bits):
                if bit == "0":
                    circ.x(price_q[bit_idx])

        return circ

    def to_circuit(self, n_estimation_qubits: int = 4) -> Circuit:
        """Build the full pricing circuit.

        Combines state preparation with the payoff oracle. The number
        of estimation qubits controls the precision of the amplitude
        estimation.

        Args:
            n_estimation_qubits: Qubits for amplitude estimation
                precision.

        Returns:
            The pricing circuit.
        """
        state_prep = self.distribution.to_state_prep().to_circuit()
        oracle = self.payoff_oracle()

        from qdk_pythonic.core.circuit import Circuit

        n_price = self.distribution.n_qubits
        circ = Circuit()
        circ.allocate(n_price, label="price")
        circ.allocate(1, label="payoff")
        est_q = circ.allocate(n_estimation_qubits, label="est")

        # State preparation on price register
        prep_circ = state_prep
        for inst in prep_circ.instructions:
            circ.add_instruction(inst)

        # Payoff oracle
        for inst in oracle.instructions:
            circ.add_instruction(inst)

        # Estimation register: Hadamard for QPE initialization
        for i in range(n_estimation_qubits):
            circ.h(est_q[i])

        return circ
