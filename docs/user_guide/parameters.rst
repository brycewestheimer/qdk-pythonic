Symbolic Parameters
===================

Parameterized circuits are circuit templates where rotation angles are
left as symbolic placeholders. This is the standard pattern for
variational algorithms (VQE, QAOA, etc.) where a classical optimizer
tunes the angles.

Creating Parameters
-------------------

Create a :class:`~qdk_pythonic.core.parameter.Parameter` with a name
and use it as a rotation angle:

.. code-block:: python

   from qdk_pythonic import Circuit
   from qdk_pythonic.core.parameter import Parameter

   theta = Parameter("theta")
   phi = Parameter("phi")

   circ = Circuit()
   q = circ.allocate(2)
   circ.ry(theta, q[0]).rz(phi, q[1]).cx(q[0], q[1])

Parameters work with any rotation gate: ``rx``, ``ry``, ``rz``, ``r1``,
and with ``controlled`` rotation gates.

Inspecting Parameters
---------------------

Retrieve the unique parameters in a circuit, in order of first appearance:

.. code-block:: python

   print(circ.parameters)  # [Parameter(name='theta'), Parameter(name='phi')]

Binding Parameters
------------------

Replace symbolic parameters with concrete values using
:meth:`~qdk_pythonic.core.circuit.Circuit.bind_parameters`:

.. code-block:: python

   bound = circ.bind_parameters({"theta": 0.5, "phi": 1.2})
   print(bound.to_qsharp())

``bind_parameters`` returns a **new** circuit; the original is unchanged.
It raises ``ValueError`` if any parameter has no binding.

Code Generation Constraint
--------------------------

Both ``to_qsharp()`` and ``to_openqasm()`` require all parameters to be
bound. Calling code generation on a circuit with unbound parameters
raises ``CodegenError``:

.. code-block:: python

   circ.to_qsharp()  # raises CodegenError

Always call ``bind_parameters()`` before code generation or execution.

Variational Workflow
--------------------

A typical variational workflow:

.. code-block:: python

   import math
   from qdk_pythonic import Circuit
   from qdk_pythonic.core.parameter import Parameter

   # 1. Define a parameterized circuit template
   theta = Parameter("theta")
   template = Circuit()
   q = template.allocate(2)
   template.ry(theta, q[0]).cx(q[0], q[1]).measure_all()

   # 2. Define a cost function
   def cost(angle: float) -> float:
       bound = template.bind_parameters({"theta": angle})
       results = bound.run(shots=100)
       # ... compute cost from results ...
       return 0.0  # placeholder

   # 3. Optimize with a classical optimizer
   # (e.g. scipy.optimize.minimize)
   best_angle = 0.0  # result of optimization

   # 4. Run the final circuit
   final = template.bind_parameters({"theta": best_angle})
   final_results = final.run(shots=1000)

Domain Module Integration
-------------------------

Some domain modules produce parameterized circuits. For example, the
:class:`~qdk_pythonic.domains.common.ansatz.HardwareEfficientAnsatz`
takes concrete parameter values directly in its ``to_circuit()`` method:

.. code-block:: python

   from qdk_pythonic.domains.common import HardwareEfficientAnsatz

   ansatz = HardwareEfficientAnsatz(n_qubits=4, depth=2)
   print(f"Parameters needed: {ansatz.num_parameters}")

   # Pass concrete values directly
   params = [0.1] * ansatz.num_parameters
   circ = ansatz.to_circuit(params)
