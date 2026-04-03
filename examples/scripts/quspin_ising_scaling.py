"""Transverse-field Ising model: circuit resource scaling with system size.

Demonstrates the QuSpin adapter workflow: define a model in QuSpin's
operator specification format, then use qdk-pythonic to build Trotter
circuits and report gate counts and depths across system sizes.

No Q# or QDK knowledge required -- the adapter handles everything.

Requires: pip install qdk-pythonic[quspin]   (for QuSpin adapter)
"""

from qdk_pythonic.adapters.quspin_adapter import (
    from_quspin_static_list,
    simulate_quspin_model,
)
from qdk_pythonic.domains.common.evolution import TrotterEvolution

# ════════════════════════════════════════════
# Step 1: Define the model in QuSpin format
# ════════════════════════════════════════════

L = 8          # chain length
J = 1.0        # ZZ coupling
h_field = 0.5  # transverse field strength

# QuSpin coupling lists (periodic boundary conditions)
J_zz = [[J, i, (i + 1) % L] for i in range(L)]
h_x = [[h_field, i] for i in range(L)]

static_list = [
    ["zz", J_zz],  # ZZ nearest-neighbour interactions
    ["x", h_x],    # transverse field
]

# ════════════════════════════════════════════
# Step 2: One-call circuit analysis
# ════════════════════════════════════════════

result = simulate_quspin_model(
    static_list=static_list,
    n_sites=L,
    time=1.0,
    trotter_steps=10,
    trotter_order=1,
)

print(f"Transverse-field Ising model on {L}-site chain (periodic BC)")
print(f"  Qubits required:     {result['n_qubits']}")
print(f"  Hamiltonian terms:   {result['n_hamiltonian_terms']}")
print(f"  Total gates:         {result['total_gates']}")
print(f"  Circuit depth:       {result['depth']}")
print(f"  Gate breakdown:      {result['gate_count']}")

# ════════════════════════════════════════════
# Step 3: Scaling study
# ════════════════════════════════════════════

print(f"\n{'L':>4} {'Qubits':>8} {'Terms':>8} {'Gates':>10} {'Depth':>8}")
print("-" * 42)

for L_sweep in [4, 6, 8, 10, 12, 16, 20]:
    J_zz_sweep = [[J, i, (i + 1) % L_sweep] for i in range(L_sweep)]
    h_x_sweep = [[h_field, i] for i in range(L_sweep)]
    static_sweep = [["zz", J_zz_sweep], ["x", h_x_sweep]]

    r = simulate_quspin_model(
        static_list=static_sweep,
        n_sites=L_sweep,
        time=1.0,
        trotter_steps=10,
    )
    print(
        f"{L_sweep:>4} {r['n_qubits']:>8} {r['n_hamiltonian_terms']:>8} "
        f"{r['total_gates']:>10} {r['depth']:>8}"
    )

# ════════════════════════════════════════════
# Step 4: Trotter convergence study
# ════════════════════════════════════════════

print(f"\n--- Trotter convergence study (L={L}) ---")
print(f"{'Order':>6} {'Steps':>6} {'Gates':>10} {'Depth':>8}")
print("-" * 34)

for order in [1, 2]:
    for steps in [5, 10, 20, 40]:
        r = simulate_quspin_model(
            static_list=static_list,
            n_sites=L,
            time=1.0,
            trotter_steps=steps,
            trotter_order=order,
        )
        print(f"{order:>6} {steps:>6} {r['total_gates']:>10} {r['depth']:>8}")

# ════════════════════════════════════════════
# Step 5: Inspect generated Q# (small example)
# ════════════════════════════════════════════

hamiltonian = from_quspin_static_list(static_list, L)
evolution = TrotterEvolution(hamiltonian, time=1.0, steps=2, order=1)
circuit = evolution.to_circuit()

print("\n--- Generated Q# (first 20 lines) ---")
qsharp_code = circuit.to_qsharp()
for line in qsharp_code.splitlines()[:20]:
    print(line)
