Quantum Finance
================

qdk-pythonic provides building blocks for quantum computational finance:
probability distribution loading, payoff oracles, and quantum amplitude
estimation (QAE) for option pricing.

Loading a Price Distribution
-----------------------------

Start by discretizing a log-normal price distribution into ``2^n`` bins:

.. code-block:: python

   from qdk_pythonic.domains.finance import LogNormalDistribution

   dist = LogNormalDistribution(
       mu=0.05, sigma=0.2, n_qubits=4, bounds=(0.5, 2.0),
   )

   # Inspect bin midpoints
   print(dist.bin_values())

The distribution is encoded into a quantum state whose amplitudes match
the discretized probabilities. Convert it to a state-preparation circuit:

.. code-block:: python

   state_prep = dist.to_state_prep()
   circuit = state_prep.to_circuit()

   print(f"Qubits: {circuit.qubit_count()}")
   print(f"Gate count: {circuit.gate_count()}")

European Call Option
---------------------

``EuropeanCallOption`` combines the price distribution with a payoff oracle
that encodes ``max(S - K, 0)`` into an ancilla qubit's amplitude:

.. code-block:: python

   from qdk_pythonic.domains.finance import EuropeanCallOption

   option = EuropeanCallOption(strike=1.0, distribution=dist)

   # Inspect the payoff oracle alone
   oracle = option.payoff_oracle()
   print(f"Oracle gates: {oracle.gate_count()}")

Build the full pricing circuit, which wraps the oracle in quantum amplitude
estimation with ``n_estimation_qubits`` controlling the precision:

.. code-block:: python

   circuit = option.to_circuit(n_estimation_qubits=6)

   print(f"Qubits: {circuit.qubit_count()}")
   print(f"Depth: {circuit.depth()}")
   print(f"Gate count: {circuit.gate_count()}")

The circuit applies: state preparation on the price register, then
controlled Grover iterates on the estimation register, then inverse QFT.

Quantum Amplitude Estimation
------------------------------

For custom use cases beyond option pricing, ``QuantumAmplitudeEstimation``
can be used directly with any state-preparation and oracle circuit pair:

.. code-block:: python

   from qdk_pythonic.domains.finance import QuantumAmplitudeEstimation

   state_prep_circ = state_prep.to_circuit()
   oracle_circ = option.payoff_oracle()

   qae = QuantumAmplitudeEstimation(
       state_prep=state_prep_circ,
       oracle=oracle_circ,
       n_estimation_qubits=6,
   )
   circuit = qae.to_circuit()

This follows the canonical QAE algorithm (Brassard et al. 2002): Hadamard
on all estimation qubits, then controlled powers of the Grover iterate,
then inverse QFT on the estimation register.

Resource Estimation
--------------------

Estimate resources and see how precision affects cost (requires
``qsharp``):

.. code-block:: python

   for n_est in [4, 6, 8]:
       circuit = option.to_circuit(n_estimation_qubits=n_est)
       result = circuit.estimate()
       print(f"n_estimation={n_est}: {result}")

Higher ``n_estimation_qubits`` gives more precise amplitude estimates but
increases circuit depth due to larger controlled-power applications.

Next Steps
-----------

See the :doc:`/api/domains_finance` API reference for full details.
The ``09_quantum_finance.ipynb`` notebook in ``examples/notebooks/`` has
more worked examples.
