Development Setup
=================

Prerequisites
-------------

- Python 3.10 or later
- git

Getting Started
---------------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/brycewestheimer/qdk-pythonic.git
   cd qdk-pythonic
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"

To run integration tests (simulation and resource estimation), also
install the ``qsharp`` extra:

.. code-block:: bash

   pip install -e ".[qsharp]"

Running Checks
--------------

**Linting:**

.. code-block:: bash

   ruff check src/ tests/

**Formatting:**

.. code-block:: bash

   ruff format src/ tests/

**Type checking:**

.. code-block:: bash

   mypy src/qdk_pythonic/ --strict

**Unit tests** (no ``qsharp`` dependency needed):

.. code-block:: bash

   pytest tests/unit/ -v

**Integration tests** (requires ``qsharp``):

.. code-block:: bash

   pytest tests/integration/ -v

**Run a single test file or test by name:**

.. code-block:: bash

   pytest tests/unit/test_circuit.py -v
   pytest tests/unit/test_circuit.py -k "test_bell_state" -v

**Run tests by marker:**

.. code-block:: bash

   pytest -m unit
   pytest -m integration

Building Documentation
----------------------

Install the documentation dependencies and build:

.. code-block:: bash

   pip install -r docs/requirements.txt
   cd docs && make html

The output is in ``docs/_build/html/``.

Branch Workflow
---------------

1. Create a branch from ``main``.
2. Make changes and run the checks above.
3. Commit using conventional commit format: ``type(scope): description``
   (e.g., ``feat(core): add SX gate``, ``fix(codegen): handle empty circuit``).
4. Open a pull request against ``main``.

CI Overview
-----------

The CI pipeline runs:

- Lint and type checking
- Unit tests across Python 3.10--3.13
- Integration tests (continue-on-error, since ``qsharp`` availability
  may vary)
- Documentation build
