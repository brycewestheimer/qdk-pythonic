Error Handling
==============

qdk-pythonic defines a custom exception hierarchy rooted at
:class:`~qdk_pythonic.exceptions.QdkPythonicError`. Catching specific
exception types lets you handle different failure modes appropriately.

Exception Hierarchy
-------------------

::

    QdkPythonicError (base)
    +-- CircuitError
    +-- CodegenError
    +-- ExecutionError
    +-- ParserError
    +-- UnsupportedConstructError

All exceptions are defined in :mod:`qdk_pythonic.exceptions`.

CircuitError
^^^^^^^^^^^^

Raised during circuit construction or validation:

- Allocating fewer than 1 qubit
- Duplicate register labels
- Invalid register label format
- Using a qubit not owned by the circuit
- Gate arity mismatch (wrong number of qubits or parameters)
- Duplicate target qubits in a multi-qubit gate
- ``controlled()`` or ``adjoint()`` called with a callable that does not
  add exactly one gate instruction
- Control qubits overlapping with target qubits
- Composing circuits that contain ``RawQSharp`` instructions

.. code-block:: python

   from qdk_pythonic import Circuit
   from qdk_pythonic.exceptions import CircuitError

   try:
       circ = Circuit()
       circ.allocate(0)  # n must be >= 1
   except CircuitError as e:
       print(e)  # "Cannot allocate 0 qubits; n must be >= 1"

CodegenError
^^^^^^^^^^^^

Raised during code generation (``to_qsharp()`` or ``to_openqasm()``):

- Unbound symbolic parameters
- Qubit not allocated in the circuit
- ``raw_qsharp()`` fragments in OpenQASM export
- Unsupported OpenQASM version

.. code-block:: python

   from qdk_pythonic.exceptions import CodegenError

   try:
       circ.to_openqasm(version="2.0")
   except CodegenError as e:
       print(e)  # "Unsupported OpenQASM version: 2.0"

ExecutionError
^^^^^^^^^^^^^^

Raised when Q# compilation, simulation, or resource estimation fails.
Wraps the underlying ``qsharp`` exception and includes the generated Q#
source in the error message for debugging.

.. code-block:: python

   from qdk_pythonic.exceptions import ExecutionError

   try:
       result = circ.run()
   except ExecutionError as e:
       print(e)  # includes the generated Q# code

ParserError
^^^^^^^^^^^

Raised when parsing Q# or OpenQASM source code encounters syntax errors.

.. code-block:: python

   from qdk_pythonic.exceptions import ParserError

   try:
       Circuit.from_qsharp("not valid Q#")
   except ParserError as e:
       print(e)

UnsupportedConstructError
^^^^^^^^^^^^^^^^^^^^^^^^^

Raised when the parser encounters a construct it recognizes but cannot
convert to the circuit IR (custom gate definitions, loops, conditionals).

.. code-block:: python

   from qdk_pythonic.exceptions import UnsupportedConstructError

   try:
       Circuit.from_openqasm("OPENQASM 3.0;\ngate foo q { h q; }\n")
   except UnsupportedConstructError as e:
       print(e)

ImportError
-----------

Note that ``ImportError`` is raised (not a ``QdkPythonicError`` subclass)
when calling ``run()`` or ``estimate()`` without the ``qsharp`` package
installed.

Best Practices
--------------

- Catch specific exception types rather than the base
  ``QdkPythonicError``.
- When debugging ``ExecutionError``, check the generated Q# in the error
  message. You can also call ``to_qsharp()`` directly to inspect the code
  before execution.
- Use ``circuit.parameters`` to check for unbound parameters before
  calling code generation methods.
