# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Circuit builder with fluent gate methods, type annotations, and `mypy --strict` compliance
- Q# code generation from circuits (`Circuit.to_qsharp()`)
- OpenQASM 3.0 code generation (`Circuit.to_openqasm()`)
- Bidirectional parsing: `Circuit.from_qsharp()` and `Circuit.from_openqasm()`
- Simulation via Q# runtime (`Circuit.run()`)
- Resource estimation via Q# runtime (`Circuit.estimate()`)
- Parameterized circuits with symbolic `Parameter` and `bind_parameters()`
- Circuit analysis: depth, gate count, ASCII visualization, JSON serialization
- Common builders: `bell_state()`, `ghz_state()`, `w_state()`, `qft()`, `inverse_qft()`
- Raw Q# escape hatch (`Circuit.raw_qsharp()`)
- Controlled and adjoint gate modifiers
- Circuit composition via `+` operator with qubit remapping
- `Circuit.compose_into()` for merging sub-circuit instructions with qubit remapping
- Domain adapter modules (integration examples):
  - Condensed matter: Ising, Heisenberg, Hubbard models with Trotter evolution
  - Optimization: MaxCut, QUBO, TSP problem encodings with QAOA
  - Finance: log-normal distributions, European call option pricing, quantum amplitude estimation
  - Machine learning: angle/amplitude encoding, quantum kernels, variational classifiers
- Shared primitives: Pauli Hamiltonians, Trotter decomposition, hardware-efficient ansatz, state preparation
- Fermionic operators with Jordan-Wigner and Bravyi-Kitaev qubit mappings
- PySCF chemistry adapter: molecular Hamiltonians from geometry strings with active space (CASCI) selection
- Quantum chemistry domain (``domains.chemistry``):
  - Hartree-Fock state preparation (JW and BK encodings)
  - UCCSD variational ansatz with spin-preserving single and double excitations
  - Quantum Phase Estimation for molecular ground-state energy (Trotterized)
  - Variational Quantum Eigensolver with scipy classical optimizer
  - Pauli expectation value measurement with commuting-term grouping
  - FCIDUMP file I/O for molecular integral interchange
  - Molecular orbital information reporting
- Double-factorized Hamiltonian representation (``domains.common.double_factorization``)
- Gate-level LCU framework: PREPARE, SELECT, walk operator, qubitization QPE (``domains.common.lcu``)
- Chemistry qubitization wrapper with gate-level and qsharp.chemistry bridge modes
- Structured resource estimation results: ``ChemistryResourceEstimate`` with logical/physical resource breakdowns
- Bridge to ``qsharp.chemistry`` for production DF-qubitization resource estimation
- Registry algorithms for QPE, VQE, and qubitization via PySCF

### Fixed
- Domain module circuit composition now remaps qubit references correctly instead of copying foreign-qubit instructions
