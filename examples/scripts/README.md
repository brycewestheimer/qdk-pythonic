# Example Scripts

Standalone Python scripts demonstrating common qdk-pythonic workflows.

| Script | Description |
|--------|-------------|
| [bell_state.py](bell_state.py) | Minimal Bell state: build, draw, and generate Q# |
| [ghz_state.py](ghz_state.py) | Parameterized N-qubit GHZ state (accepts qubit count as CLI arg) |
| [resource_sweep.py](resource_sweep.py) | Sweep circuit sizes and compare resource estimates (requires qsharp) |
| [qiskit_interop.py](qiskit_interop.py) | Export to OpenQASM 3.0 and optionally import into Qiskit |
| [quspin_ising_scaling.py](quspin_ising_scaling.py) | Transverse-field Ising scaling study via QuSpin adapter |
| [networkx_maxcut_scaling.py](networkx_maxcut_scaling.py) | MaxCut on random graphs with QAOA depth comparison |
| [pyscf_h2_example.py](pyscf_h2_example.py) | Molecular Hamiltonian for H2 via PySCF with JW/BK comparison |

## Running

```bash
python examples/scripts/bell_state.py
python examples/scripts/ghz_state.py 8
```

Scripts that need `qsharp` or `qiskit` handle missing dependencies gracefully.
