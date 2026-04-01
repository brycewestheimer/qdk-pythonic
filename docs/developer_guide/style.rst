Code Style and Conventions
==========================

This page documents the coding conventions for qdk-pythonic.

Python Version
--------------

Python 3.10 or later. Use the ``X | Y`` union syntax instead of
``Optional[X]``:

.. code-block:: python

   # Yes
   def foo(x: int | None = None) -> str | bytes: ...

   # No
   from typing import Optional, Union
   def foo(x: Optional[int] = None) -> Union[str, bytes]: ...

Type Annotations
----------------

Every function and method must be fully annotated. The codebase must
pass:

.. code-block:: bash

   mypy src/qdk_pythonic/ --strict

Use ``from __future__ import annotations`` at the top of every module.
Use ``TYPE_CHECKING`` guards for imports that are only needed by type
checkers:

.. code-block:: python

   from __future__ import annotations

   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from qdk_pythonic.core.circuit import Circuit

Linting and Formatting
----------------------

**Linting:** ``ruff check`` with a line length of 99.

**Formatting:** ``ruff format``.

.. code-block:: bash

   ruff check src/ tests/
   ruff format src/ tests/

Docstrings
----------

Google style with ``Args:``, ``Returns:``, and ``Raises:`` sections. All
public classes, methods, and functions must have docstrings.

.. code-block:: python

   def allocate(self, n: int, label: str | None = None) -> QubitRegister:
       """Allocate n qubits and return them as a QubitRegister.

       Args:
           n: Number of qubits to allocate. Must be >= 1.
           label: Optional label prefix for the qubits.

       Returns:
           A QubitRegister containing the newly allocated qubits.

       Raises:
           CircuitError: If n < 1.
       """

Dataclass Conventions
---------------------

Use ``@dataclass(frozen=True)`` for IR types (``Qubit``, ``Instruction``,
``Measurement``, ``RawQSharp``, ``GateDefinition``, ``Parameter``,
``RunConfig``). ``Circuit`` is the exception: it is mutable by design.

.. code-block:: python

   from dataclasses import dataclass

   @dataclass(frozen=True)
   class MyIRType:
       value: int
       label: str | None = None

Lazy Imports
------------

Optional dependencies (``qsharp``) are never imported at module level.
Import inside functions or use the ``_compat.import_qsharp()`` helper:

.. code-block:: python

   def run_circuit(circuit, config):
       qsharp = import_qsharp()  # raises ImportError if missing
       # ...

For internal cross-package imports that would cause circular
dependencies, import inside the method body:

.. code-block:: python

   def to_qsharp(self) -> str:
       from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator
       return QSharpCodeGenerator().generate(self)

Naming
------

- Classes: ``PascalCase`` (``Circuit``, ``QSharpCodeGenerator``)
- Functions and methods: ``snake_case`` (``bell_state``, ``run_circuit``)
- Constants: ``UPPER_SNAKE_CASE`` (``GATE_CATALOG``, ``CNOT``)
- Private helpers: prefixed with ``_`` (``_apply_gate``, ``_build_body``)
- Modules: ``snake_case`` (``qsharp_parser.py``, ``_helpers.py``)

Commit Messages
---------------

Use conventional commit format::

    type(scope): short description

Common types: ``feat``, ``fix``, ``docs``, ``test``, ``refactor``,
``ci``, ``chore``.

Examples::

    feat(core): add SX gate
    fix(codegen): handle empty circuit in OpenQASM
    docs(user_guide): add parameters page
    test(parser): add round-trip tests for OpenQASM

PEP 561
-------

The ``py.typed`` marker file is present in the package root, enabling
downstream type checking for consumers of the library.
