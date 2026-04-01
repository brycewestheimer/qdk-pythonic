Simulation and Resource Estimation
==================================

qdk-pythonic provides two execution modes: simulation (running the circuit
and collecting measurement results) and resource estimation (computing
physical resource requirements for fault-tolerant execution).

Both require the ``qsharp`` package (version 1.25 or later):

.. code-block:: bash

   pip install "qdk-pythonic[qsharp]"

Simulation
----------

Execute a circuit on the Q# simulator with
:meth:`~qdk_pythonic.core.circuit.Circuit.run`:

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0]).cx(q[0], q[1]).measure_all()

   results = circ.run(shots=1000)
   print(results[:5])

Under the hood, ``run()`` generates a uniquely named Q# operation,
compiles it with ``qsharp.eval()``, then executes it with
``qsharp.run()``.

**Configuration options:**

- ``shots`` (default 1000): number of simulation repetitions.
- ``seed``: optional RNG seed for reproducible results.
- ``noise``: optional 3-tuple of (depolarizing, dephasing, bitflip)
  probabilities, each in [0, 1].

.. code-block:: python

   # Reproducible simulation
   results = circ.run(shots=500, seed=42)

   # Noisy simulation
   results = circ.run(shots=1000, noise=(0.01, 0.01, 0.001))

If Q# compilation or simulation fails, an ``ExecutionError`` is raised
with the generated Q# source included in the error message for debugging.

Resource Estimation
-------------------

Estimate the physical resources needed for fault-tolerant execution with
:meth:`~qdk_pythonic.core.circuit.Circuit.estimate`:

.. code-block:: python

   circ = Circuit()
   q = circ.allocate(2)
   circ.h(q[0]).t(q[0]).cx(q[0], q[1])

   result = circ.estimate()
   print(result)

The estimator automatically strips measurements and ``raw_qsharp()``
fragments from the circuit, since the resource estimator requires
Unit-returning operations. A warning is emitted when raw fragments are
removed.

**Configuring estimator parameters:**

Pass a dict with qubit model and QEC scheme settings:

.. code-block:: python

   params = {
       "qubitParams": {"name": "qubit_gate_ns_e3"},
       "qecScheme": {"name": "surface_code"},
   }
   result = circ.estimate(params=params)

Or use the typed ``qsharp`` parameter classes:

.. code-block:: python

   from qsharp import EstimatorParams, QubitParams, QECScheme

   params = EstimatorParams()
   params.qubit_params = QubitParams.GATE_NS_E3
   params.qec_scheme = QECScheme.SURFACE_CODE

   result = circ.estimate(params=params)

**Batch estimation:**

Sweep over multiple parameter configurations with
:func:`~qdk_pythonic.execution.estimator.estimate_circuit_batch`:

.. code-block:: python

   from qdk_pythonic.execution.estimator import estimate_circuit_batch

   configs = [
       {"qubitParams": {"name": "qubit_gate_ns_e3"}},
       {"qubitParams": {"name": "qubit_gate_ns_e4"}},
   ]

   results = estimate_circuit_batch(circ, configs)
   for cfg, res in zip(configs, results):
       print(f"{cfg['qubitParams']['name']}: {res}")

You can also pass a list of circuits to estimate each one against all
parameter configurations.

Common Pitfalls
---------------

**Pure Clifford circuits fail estimation.** The resource estimator needs
at least one non-Clifford gate (T gate or rotation) to decompose into
T gates. Circuits with only H, CNOT, S, and other Clifford gates will
fail. Add a T gate or rotation to make the circuit estimable.

**raw_qsharp() is stripped silently.** Raw Q# fragments are removed
before estimation. If your circuit's cost is dominated by raw fragments,
the resource estimate will be incomplete. A warning is emitted, but the
estimation proceeds with the remaining gates.

**qsharp not installed.** Calling ``run()`` or ``estimate()`` without
the ``qsharp`` package raises ``ImportError`` with a message suggesting
``pip install "qdk-pythonic[qsharp]"``.
