"""MaxCut on random graphs: QAOA circuit resource scaling.

Demonstrates the NetworkX adapter workflow: define a graph in
NetworkX, then use qdk-pythonic to build QAOA circuits and compare
resource requirements across graph sizes and QAOA depths.

No Q# or QDK knowledge required -- the adapter handles everything.

Requires: pip install qdk-pythonic[networkx]   (for NetworkX adapter)
          pip install networkx                  (graph library)
"""

import networkx as nx

from qdk_pythonic.adapters.networkx_adapter import (
    compare_qaoa_depths,
    solve_maxcut,
)

# ════════════════════════════════════════════
# Step 1: Single graph MaxCut
# ════════════════════════════════════════════

G = nx.random_regular_graph(d=3, n=10, seed=42)
print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

result = solve_maxcut(G, p=2)

print(f"\nQAOA MaxCut (p=2):")
print(f"  Qubits:            {result['n_qubits']}")
print(f"  Total gates:       {result['total_gates']}")
print(f"  Circuit depth:     {result['depth']}")
print(f"  Max possible cut:  {result['max_possible_cut']}")

# ════════════════════════════════════════════
# Step 2: QAOA depth comparison
# ════════════════════════════════════════════

print(f"\n--- QAOA depth comparison ---")
print(f"{'p':>4} {'Gates':>10} {'Depth':>8} {'Qubits':>8}")
print("-" * 34)

comparisons = compare_qaoa_depths(G, p_values=[1, 2, 3, 4, 5])
for r in comparisons:
    print(
        f"{r['p']:>4} {r['total_gates']:>10} "
        f"{r['depth']:>8} {r['n_qubits']:>8}"
    )

# ════════════════════════════════════════════
# Step 3: Scaling with graph size
# ════════════════════════════════════════════

print(
    f"\n{'Nodes':>6} {'Edges':>6} {'Gates (p=1)':>12} {'Gates (p=3)':>12} "
    f"{'Depth (p=1)':>12} {'Depth (p=3)':>12}"
)
print("-" * 66)

for n in [6, 10, 14, 20, 30]:
    G_scale = nx.random_regular_graph(d=3, n=n, seed=42)
    r1 = solve_maxcut(G_scale, p=1)
    r3 = solve_maxcut(G_scale, p=3)
    print(
        f"{n:>6} {G_scale.number_of_edges():>6} "
        f"{r1['total_gates']:>12} {r3['total_gates']:>12} "
        f"{r1['depth']:>12} {r3['depth']:>12}"
    )

# ════════════════════════════════════════════
# Step 4: Weighted graph
# ════════════════════════════════════════════

print("\n--- Weighted graph MaxCut ---")

G_w = nx.Graph()
G_w.add_weighted_edges_from([
    (0, 1, 2.0), (1, 2, 1.5), (2, 3, 3.0), (3, 0, 1.0), (0, 2, 0.5),
])

r_w = solve_maxcut(G_w, p=2)
print(
    f"Weighted graph: {G_w.number_of_nodes()} nodes, "
    f"{G_w.number_of_edges()} edges"
)
print(f"  Max possible cut:  {r_w['max_possible_cut']}")
print(f"  Qubits:            {r_w['n_qubits']}")
print(f"  Total gates:       {r_w['total_gates']}")
print(f"  Circuit depth:     {r_w['depth']}")

# ════════════════════════════════════════════
# Step 5: Benchmark graph families
# ════════════════════════════════════════════

print(
    f"\n{'Graph':<25} {'Nodes':>6} {'Edges':>6} "
    f"{'Qubits':>7} {'Gates(p=1)':>11} {'Gates(p=3)':>11}"
)
print("-" * 72)

graphs = {
    "Petersen": nx.petersen_graph(),
    "Cycle(12)": nx.cycle_graph(12),
    "Complete(6)": nx.complete_graph(6),
    "Grid(3x4)": nx.grid_2d_graph(3, 4),
    "Random regular(3,12)": nx.random_regular_graph(3, 12, seed=42),
}

for name, G_bench in graphs.items():
    r1 = solve_maxcut(G_bench, p=1)
    r3 = solve_maxcut(G_bench, p=3)
    print(
        f"{name:<25} {G_bench.number_of_nodes():>6} "
        f"{G_bench.number_of_edges():>6} "
        f"{r1['n_qubits']:>7} {r1['total_gates']:>11} "
        f"{r3['total_gates']:>11}"
    )

# ════════════════════════════════════════════
# Step 6: Inspect generated Q# (small example)
# ════════════════════════════════════════════

G_small = nx.cycle_graph(4)
r_small = solve_maxcut(G_small, p=1)
print("\n--- Generated Q# for 4-node cycle MaxCut (p=1) ---")
print(r_small["circuit"].to_qsharp())
