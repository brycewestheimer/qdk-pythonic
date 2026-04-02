Quantum Machine Learning
=========================

This tutorial demonstrates how the core circuit API extends to machine
learning workflows.  The ML module is an integration example, not a
production-ready QML library.

qdk-pythonic provides components for encoding classical data into quantum
states, computing quantum kernels, and building variational classifiers.
All components produce standard ``Circuit`` objects for inspection,
simulation, or resource estimation.

Angle Encoding
---------------

``AngleEncoding`` maps each classical feature to a rotation angle on a
dedicated qubit:

.. code-block:: python

   from qdk_pythonic.domains.ml import AngleEncoding

   encoding = AngleEncoding(n_features=4)
   circuit = encoding.to_circuit(data=[0.1, 0.2, 0.3, 0.4])

   print(circuit.draw())
   print(f"Qubits: {circuit.qubit_count()}")  # 4

Each feature ``x_i`` is encoded as ``Ry(x_i)`` on qubit ``i``. This scheme
requires one qubit per feature.

Amplitude Encoding
-------------------

``AmplitudeEncoding`` loads a normalized vector of ``2^n`` values into the
amplitudes of ``n`` qubits, giving exponential data compression:

.. code-block:: python

   import math
   from qdk_pythonic.domains.ml import AmplitudeEncoding

   # Normalized 8-element vector -> 3 qubits
   data = [1 / math.sqrt(8)] * 8
   encoding = AmplitudeEncoding(n_qubits=3)
   circuit = encoding.to_circuit(data=data)

   print(f"Qubits: {circuit.qubit_count()}")  # 3
   print(f"Gate count: {circuit.gate_count()}")

The data vector must be normalized (sum of squared magnitudes equals 1).
The circuit uses controlled rotations to prepare the exact state, so gate
count grows with vector length.

Quantum Kernel
---------------

``QuantumKernel`` estimates the overlap ``|<phi(x)|phi(y)>|^2`` between
two data encodings using a compute-uncompute approach:

.. code-block:: python

   from qdk_pythonic.domains.ml import QuantumKernel

   encoding = AngleEncoding(n_features=4)
   kernel = QuantumKernel(encoding)

   circuit = kernel.to_circuit(
       x=[0.1, 0.2, 0.3, 0.4],
       y=[0.5, 0.6, 0.7, 0.8],
   )

   print(circuit.draw())
   print(f"Depth: {circuit.depth()}")

The circuit applies ``U(x)`` followed by ``U(y)^dagger``, then measures
all qubits. The probability of measuring all zeros gives the kernel value.

Variational Classifier
-----------------------

``VariationalClassifier`` combines data encoding with a parameterized
ansatz to form a quantum classifier:

.. code-block:: python

   from qdk_pythonic.domains.ml import AngleEncoding, VariationalClassifier
   from qdk_pythonic.domains.common import HardwareEfficientAnsatz

   encoding = AngleEncoding(n_features=4)
   ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=2)

   classifier = VariationalClassifier(encoding, ansatz)
   print(f"Parameters: {ansatz.num_parameters}")

   circuit = classifier.to_circuit(
       data=[0.1, 0.2, 0.3, 0.4],
       params=[0.1] * ansatz.num_parameters,
   )

   print(circuit.draw())
   print(f"Depth: {circuit.depth()}")
   print(f"Gate count: {circuit.gate_count()}")

The circuit applies the encoding layer, then the ansatz (alternating
rotation and entangling layers), then measures the first qubit for binary
classification.

The ``HardwareEfficientAnsatz`` supports different entanglement patterns:

.. code-block:: python

   # Linear entanglement (adjacent qubits)
   ansatz_linear = HardwareEfficientAnsatz(
       n_qubits=4, depth=2, entanglement="linear",
   )

   # Full entanglement (all qubit pairs)
   ansatz_full = HardwareEfficientAnsatz(
       n_qubits=4, depth=2, entanglement="full",
   )

Resource Estimation
--------------------

Estimate the physical resources for a classifier circuit at different ansatz
depths (requires ``qsharp``):

.. code-block:: python

   for depth in [1, 2, 4]:
       ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=depth)
       classifier = VariationalClassifier(encoding, ansatz)
       circuit = classifier.to_circuit(
           data=[0.1, 0.2, 0.3, 0.4],
           params=[0.1] * ansatz.num_parameters,
       )
       result = circuit.estimate()
       print(f"depth={depth}: {result}")

Next Steps
-----------

See the :doc:`/api/domains_ml` API reference for full details.
The ``10_quantum_ml.ipynb`` notebook in ``examples/notebooks/`` has
more worked examples.
