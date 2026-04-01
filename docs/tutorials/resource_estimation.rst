Resource Estimation
===================

Resource estimation is a first-class feature of qdk-pythonic. It uses the
Q# resource estimator under the hood to provide physical qubit counts, T-gate
depths, and other metrics for fault-tolerant quantum computing.

Basic Estimation
-----------------

Build a circuit and estimate its resources:

.. code-block:: python

   from qdk_pythonic import Circuit

   circ = Circuit()
   q = circ.allocate(3)
   circ.h(q[0]).cx(q[0], q[1]).cx(q[1], q[2])

   result = circ.estimate()
   print(result)

The result is a dict-like object containing physical resource estimates
such as logical qubit count, T-factory count, and runtime.

Configuring Estimator Parameters
---------------------------------

Pass estimator parameters to explore different hardware assumptions:

.. code-block:: python

   params = {
       "qubitParams": {"name": "qubit_gate_ns_e3"},
       "qecScheme": {"name": "surface_code"},
   }
   result = circ.estimate(params=params)

You can also use the ``qsharp`` parameter classes directly when the
``qsharp`` package is installed:

.. code-block:: python

   from qsharp import EstimatorParams, QubitParams, QECScheme

   params = EstimatorParams()
   params.qubit_params = QubitParams.GATE_NS_E3
   params.qec_scheme = QECScheme.SURFACE_CODE

   result = circ.estimate(params=params)

Comparing Hardware Configurations
-----------------------------------

Use :func:`~qdk_pythonic.execution.estimator.estimate_circuit_batch` to
sweep over multiple parameter sets in a single compilation:

.. code-block:: python

   from qdk_pythonic.execution import estimate_circuit_batch

   configs = [
       {"qubitParams": {"name": "qubit_gate_ns_e3"}},
       {"qubitParams": {"name": "qubit_gate_ns_e4"}},
       {"qubitParams": {"name": "qubit_gate_us_e3"}},
   ]

   results = estimate_circuit_batch(circ, configs)
   for cfg, res in zip(configs, results):
       name = cfg["qubitParams"]["name"]
       print(f"{name}: {res}")

Building Parameterized Circuits
--------------------------------

A common workflow is to sweep over circuit sizes and plot how resources
scale:

.. code-block:: python

   import math
   from qdk_pythonic import Circuit

   def build_trotter_step(n: int, angle: float) -> Circuit:
       """Build a single Trotter step for an n-qubit chain."""
       circ = Circuit()
       q = circ.allocate(n)
       for i in range(n - 1):
           circ.cx(q[i], q[i + 1])
           circ.rz(angle, q[i + 1])
           circ.cx(q[i], q[i + 1])
       return circ

   for n in [4, 8, 16]:
       circ = build_trotter_step(n, math.pi / 4)
       result = circ.estimate()
       print(f"n={n}: {result}")
