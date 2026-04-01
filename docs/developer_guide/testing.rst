Testing
=======

This page covers the test organization, conventions, and patterns used
in qdk-pythonic.

Test Structure
--------------

::

    tests/
        conftest.py              # Shared fixtures and marker registration
        unit/                    # Fast tests, no qsharp needed
            test_builders.py
            test_codegen_qsharp.py
            test_codegen_openqasm.py
            test_codegen_edge_cases.py
            test_parser_qsharp.py
            test_parser_openqasm.py
            test_analysis.py
            test_roundtrip.py
            test_runner_unit.py
            test_domain_*.py     # One file per domain module
        integration/             # Requires qsharp >= 1.25
            test_end_to_end.py
            test_simulation.py
            test_estimation.py

Markers
-------

Every test must be decorated with one of:

- ``@pytest.mark.unit`` -- fast, no external dependencies.
- ``@pytest.mark.integration`` -- requires the ``qsharp`` package.

These markers are registered in ``tests/conftest.py``.

Shared Fixtures
---------------

``tests/conftest.py`` provides three fixtures:

**``bell_circuit``**
    A 2-qubit Bell state circuit with measurements. Use when you need a
    simple circuit that produces measurement results.

**``bell_circuit_no_measure``**
    Same Bell state without measurements. Use when you need a circuit
    for code generation or analysis without measurement instructions.

**``estimable_circuit``**
    A circuit with a T gate (non-Clifford) suitable for resource
    estimation. The Q# resource estimator requires at least one
    non-Clifford gate.

Running Tests
-------------

.. code-block:: bash

   # All unit tests
   pytest tests/unit/ -v

   # All integration tests
   pytest tests/integration/ -v

   # Single file
   pytest tests/unit/test_circuit.py -v

   # Single test by name
   pytest tests/unit/test_circuit.py -k "test_bell_state" -v

   # By marker
   pytest -m unit
   pytest -m integration

CI Matrix
---------

- **Unit tests** run on Python 3.10, 3.11, 3.12, and 3.13.
- **Integration tests** run on Python 3.12 only with
  ``continue-on-error: true`` (the ``qsharp`` package may not be
  available in all environments).

Unit Test Patterns
------------------

**Circuit tests:** verify that gate methods append the correct
instructions.

.. code-block:: python

   @pytest.mark.unit
   def test_h_gate():
       circ = Circuit()
       q = circ.allocate(1)
       circ.h(q[0])
       assert circ.total_gate_count() == 1
       assert circ.gate_count() == {"H": 1}

**Codegen tests:** generate code and check the output string.

.. code-block:: python

   @pytest.mark.unit
   def test_bell_qsharp(bell_circuit_no_measure):
       code = bell_circuit_no_measure.to_qsharp()
       assert "H(q[0]);" in code
       assert "CNOT(q[0], q[1]);" in code

**Parser tests:** parse a source string and verify the resulting circuit.

.. code-block:: python

   @pytest.mark.unit
   def test_parse_bell_qsharp():
       source = """
       {
           use q = Qubit[2];
           H(q[0]);
           CNOT(q[0], q[1]);
       }
       """
       circ = Circuit.from_qsharp(source)
       assert circ.qubit_count() == 2
       assert circ.gate_count() == {"CNOT": 1, "H": 1}

**Domain tests:** construct a domain object, produce a circuit, and
verify metrics.

.. code-block:: python

   @pytest.mark.unit
   def test_ising_model():
       from qdk_pythonic.domains.condensed_matter import IsingModel, Chain

       model = IsingModel(lattice=Chain(4), j=1.0, h=0.5)
       h = model.to_hamiltonian()
       assert len(h.terms) > 0

**Round-trip tests:** generate code, parse it back, and compare.

.. code-block:: python

   @pytest.mark.unit
   def test_qsharp_roundtrip(bell_circuit_no_measure):
       code = bell_circuit_no_measure.to_qsharp()
       restored = Circuit.from_qsharp(code)
       assert restored.gate_count() == bell_circuit_no_measure.gate_count()

Integration Test Patterns
-------------------------

Integration tests should use ``pytest.importorskip`` to skip gracefully
when ``qsharp`` is not available:

.. code-block:: python

   @pytest.mark.integration
   def test_bell_simulation():
       pytest.importorskip("qsharp")
       from qdk_pythonic import bell_state

       circ = bell_state(measure=True)
       results = circ.run(shots=100)
       assert len(results) == 100
