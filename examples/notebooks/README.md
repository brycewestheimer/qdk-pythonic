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
| [07_condensed_matter.ipynb](07_condensed_matter.ipynb) | Lattice models, Trotter evolution, and dynamics simulation |
| [08_optimization.ipynb](08_optimization.ipynb) | MaxCut, QUBO, TSP, and QAOA circuit generation |
| [09_quantum_finance.ipynb](09_quantum_finance.ipynb) | Log-normal distributions and European call option pricing |
| [10_quantum_ml.ipynb](10_quantum_ml.ipynb) | Feature encoding, quantum kernels, and variational classifiers |
| [11_quspin_integration.ipynb](11_quspin_integration.ipynb) | QuSpin adapter: Ising and Heisenberg models with scaling studies |
| [12_networkx_integration.ipynb](12_networkx_integration.ipynb) | NetworkX adapter: MaxCut, weighted graphs, and benchmark families |

## Prerequisites

All notebooks work without `qsharp` for circuit construction and code generation.
Cells that run simulations or resource estimation require:

```bash
pip install "qdk-pythonic[qsharp]"
```

The adapter notebooks (11, 12) require their respective optional dependencies:

```bash
pip install "qdk-pythonic[quspin]"    # notebook 11
pip install "qdk-pythonic[networkx]"  # notebook 12
```
