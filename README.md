# qdk-pythonic

[![CI](https://github.com/brycewestheimer/qdk-pythonic/actions/workflows/ci.yml/badge.svg)](https://github.com/brycewestheimer/qdk-pythonic/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A typed, Pythonic workflow layer for the Microsoft Quantum Development Kit --
circuit construction, Q# and OpenQASM code generation, simulation, and resource
estimation. This is a proof of concept exploring what a more ergonomic
Python-facing API for QDK could look like; the core circuit IR is the focus,
and the included domain modules are integration examples rather than
production-complete libraries.

## Why qdk-pythonic?

**Before** -- raw Q# string manipulation:

```python
import qsharp

qsharp.eval("""
    operation BellState() : Result[] {
        use q = Qubit[2];
        H(q[0]);
        CNOT(q[0], q[1]);
        let r0 = MResetZ(q[0]);
        let r1 = MResetZ(q[1]);
        [r0, r1]
    }
""")
results = qsharp.run("BellState()", shots=1000)
```

**After** -- Pythonic API with type safety and IDE support:

```python
from qdk_pythonic import Circuit

circ = Circuit()
q = circ.allocate(2)
circ.h(q[0]).cx(q[0], q[1]).measure_all()

results = circ.run(shots=1000)
estimate = circ.estimate()
```

## Installation

```bash
pip install qdk-pythonic
```

To run circuits on the Q# simulator or use resource estimation:

```bash
pip install "qdk-pythonic[qsharp]"
```

For external package integrations:

```bash
pip install "qdk-pythonic[quspin]"    # QuSpin adapter
pip install "qdk-pythonic[networkx]"  # NetworkX adapter
pip install "qdk-pythonic[pyscf]"     # PySCF chemistry adapter
pip install "qdk-pythonic[adapters]"  # all adapters
```

## Quick Start

```python
from qdk_pythonic import Circuit

# Build a Bell state
circ = Circuit()
q = circ.allocate(2)
circ.h(q[0]).cx(q[0], q[1]).measure_all()

# Inspect
print(circ.draw())
print(f"Depth: {circ.depth()}, Gates: {circ.gate_count()}")

# Export to Q# or OpenQASM
print(circ.to_qsharp())
print(circ.to_openqasm())

# Simulate (requires qsharp)
results = circ.run(shots=1000)

# Resource estimation (requires qsharp)
estimate = circ.estimate()
```

## Features

- **Pythonic gate methods** -- `h()`, `cx()`, `rx()`, etc. with fluent chaining
- **Parameterized circuits** -- symbolic `Parameter` values with `bind_parameters()` for variational workflows
- **Common circuit builders** -- `bell_state()`, `ghz_state()`, `w_state()`, `qft()`, and more
- **Q# and OpenQASM 3.0 code generation** -- produce valid source strings from circuits
- **Bidirectional parsing** -- import circuits from Q# or OpenQASM source
- **Simulation** -- run circuits on the Q# simulator
- **Resource estimation** -- estimate physical resources for fault-tolerant execution
- **Circuit analysis** -- depth, gate count, ASCII visualization, JSON serialization
- **Raw Q# escape hatch** -- embed arbitrary Q# fragments for constructs the builder can't express
- **Type-safe** -- full type annotations, passes `mypy --strict`

### Domain Adapters

- **Condensed matter** -- Ising, Heisenberg, and Hubbard models on chain, square, and hexagonal lattices with Trotter time evolution
- **Optimization** -- MaxCut, QUBO, and TSP problem encodings with QAOA circuit generation
- **Finance** -- log-normal distributions, European call option pricing via quantum amplitude estimation
- **Machine learning** -- angle and amplitude encoding, quantum kernels, variational classifiers
- **Shared primitives** -- Pauli Hamiltonians, fermionic operators, Jordan-Wigner and Bravyi-Kitaev qubit mappings, Trotter decomposition, hardware-efficient ansatz, state preparation

### External Package Integrations

- **QuSpin** -- convert QuSpin spin Hamiltonian specifications to Trotter circuits and resource estimates
- **NetworkX** -- convert graph problems (MaxCut, coloring) to QAOA circuits with one function call
- **PySCF** -- build molecular qubit Hamiltonians from geometry strings with active space selection

## Domain Adapters

The repository includes domain adapters showing how the core API extends to
application-facing workflows. Every domain object produces a standard `Circuit`,
so you can inspect, export, simulate, or estimate resources on the result.

### Condensed Matter

```python
from qdk_pythonic.domains.condensed_matter import Chain, IsingModel, simulate_dynamics

model = IsingModel(Chain(10), J=1.0, h=0.5)
circuit = simulate_dynamics(model, time=1.0, steps=10)
print(f"Depth: {circuit.depth()}, Gates: {circuit.gate_count()}")
```

### Optimization

```python
from qdk_pythonic.domains.optimization import MaxCut, QAOA

problem = MaxCut(edges=[(0, 1), (1, 2), (2, 0)], n_nodes=3)
qaoa = QAOA(problem.to_hamiltonian(), p=2)
circuit = qaoa.to_circuit(gamma=[0.5, 0.3], beta=[0.7, 0.2])
```

### Finance

```python
from qdk_pythonic.domains.finance import LogNormalDistribution, EuropeanCallOption

dist = LogNormalDistribution(mu=0.05, sigma=0.2, n_qubits=4, bounds=(0.5, 2.0))
option = EuropeanCallOption(strike=1.0, distribution=dist)
circuit = option.to_circuit(n_estimation_qubits=6)
```

### Machine Learning

```python
from qdk_pythonic.domains.ml import AngleEncoding, QuantumKernel

encoding = AngleEncoding(n_features=4)
kernel = QuantumKernel(encoding)
circuit = kernel.to_circuit(x=[0.1, 0.2, 0.3, 0.4], y=[0.5, 0.6, 0.7, 0.8])
```

### QuSpin Integration

```python
from qdk_pythonic.adapters.quspin_adapter import simulate_quspin_model

static = [["zz", [[1.0, i, i+1] for i in range(7)]], ["x", [[0.5, i] for i in range(8)]]]
result = simulate_quspin_model(static, n_sites=8, time=1.0, trotter_steps=10)
# result has circuit, gate counts, depth -- zero Q# written
```

### NetworkX Integration

```python
import networkx as nx
from qdk_pythonic.adapters.networkx_adapter import solve_maxcut

result = solve_maxcut(nx.random_regular_graph(3, 20, seed=42), p=3)
# result has QAOA circuit, gate counts, depth -- zero Q# written
```

### PySCF Chemistry

```python
from qdk_pythonic.adapters.pyscf_adapter import molecular_hamiltonian

h = molecular_hamiltonian("H 0 0 0; H 0 0 0.74", basis="sto-3g")
h.print_summary()
# 4 qubits, full pipeline from geometry to Pauli Hamiltonian
```

### Algorithm Registry

All adapters register with a QDK/Chemistry-style registry:

```python
from qdk_pythonic.registry import create

h = create("hamiltonian_builder", "pyscf", basis="sto-3g").run(atom="H 0 0 0; H 0 0 0.74")
circuit = create("time_evolution_builder", "trotter", time=1.0, steps=5).run(h)
```

## Parameterized Circuits

```python
from qdk_pythonic import Circuit
from qdk_pythonic.core.parameter import Parameter

theta = Parameter("theta")
circ = Circuit()
q = circ.allocate(1)
circ.ry(theta, q[0])

bound = circ.bind_parameters({"theta": 0.5})
print(bound.to_qsharp())
```

## Where to Start

If you're reviewing this repo, the best entry points are:

1. [`src/qdk_pythonic/core/circuit.py`](src/qdk_pythonic/core/circuit.py) -- the typed circuit API
2. [`src/qdk_pythonic/codegen/qsharp.py`](src/qdk_pythonic/codegen/qsharp.py) -- Q# generation from the circuit IR
3. [`src/qdk_pythonic/execution/`](src/qdk_pythonic/execution/) -- QDK-backed simulation and resource estimation
4. [`tests/unit/test_circuit.py`](tests/unit/test_circuit.py) -- behavior, validation, and API expectations

## Examples

See [`examples/notebooks/`](examples/notebooks/) for Jupyter notebooks covering
circuit building, resource estimation, and domain workflows.
[`examples/scripts/`](examples/scripts/) has standalone scripts.

## Documentation

Sphinx API docs are in `docs/`. They can be built locally with `cd docs && make html`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
