# Example Notebooks

Jupyter notebooks demonstrating qdk-pythonic features.

| Notebook | Description |
|----------|-------------|
| [01_getting_started.ipynb](01_getting_started.ipynb) | Circuit construction, gate methods, inspection, and Q# generation |
| [02_bell_state.ipynb](02_bell_state.ipynb) | Bell state creation, visualization, code generation, and simulation |
| [03_resource_estimation.ipynb](03_resource_estimation.ipynb) | Resource estimation workflow with custom parameters and batch sweeps |
| [04_openqasm_interop.ipynb](04_openqasm_interop.ipynb) | OpenQASM 3.0 export, import, round-trip conversion, and JSON serialization |
| [05_ising_model.ipynb](05_ising_model.ipynb) | Trotterized Ising model with scaling analysis and resource estimation |
| [06_circuit_builders.ipynb](06_circuit_builders.ipynb) | Builder functions, controlled/adjoint modifiers, and composition |

## Prerequisites

All notebooks work without `qsharp` for circuit construction and code generation.
Cells that run simulations or resource estimation require:

```bash
pip install "qdk-pythonic[qsharp]"
```
