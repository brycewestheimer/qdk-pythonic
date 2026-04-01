# qdk-pythonic

[![CI](https://github.com/westh/qdk-pythonic/actions/workflows/ci.yml/badge.svg)](https://github.com/westh/qdk-pythonic/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Pythonic circuit-builder API for the Microsoft Quantum Development Kit.

Build quantum circuits with native Python methods, generate Q# or OpenQASM code,
run simulations, and estimate resources for fault-tolerant quantum computing.

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
- **Q# and OpenQASM 3.0 code generation** -- produce valid source strings from circuits
- **Bidirectional parsing** -- import circuits from Q# or OpenQASM source
- **Simulation** -- run circuits on the Q# simulator
- **Resource estimation** -- estimate physical resources for fault-tolerant execution
- **Circuit analysis** -- depth, gate count, ASCII visualization
- **Serialization** -- save/load circuits as JSON or dicts
- **Type-safe** -- full type annotations, passes `mypy --strict`

## Examples

See [`examples/notebooks/`](examples/notebooks/) for Jupyter notebooks and
[`examples/scripts/`](examples/scripts/) for standalone scripts.

## Documentation

Full API documentation is available at the project's GitHub Pages site.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
