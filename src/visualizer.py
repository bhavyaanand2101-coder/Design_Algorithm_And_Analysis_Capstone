"""
visualizer.py
Visualization suite for Capstone Courier Planning System.
Generates publication-quality charts for:
1. Spatial Road Network with Highlighted Delivery Route (Matplotlib)
2. 0/1 Knapsack DP Table Heatmap
3. Algorithmic Runtime Performance Benchmarks (Phase 4)
"""

import os
from typing import List, Dict, Tuple, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless rendering
import matplotlib.pyplot as plt
import numpy as np

from src.graph import RoadNetwork
from src.models import DeliveryTrip, PackingPlan, Parcel


def plot_delivery_route(
    network: RoadNetwork,
    trip: DeliveryTrip,
    output_path: str = "output/charts/delivery_route.png",
    title: str = "Optimized Courier Delivery Route"
):
    """
    Plots the spatial delivery network and overlays the calculated delivery route tour.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(11, 8))
    ax = plt.subplot(111)

    # 1. Draw all road segments in background
    drawn_edges = set()
    for u, neighbors in network.adjacency.items():
        p1 = network.nodes[u]
        for v, dist, _ in neighbors:
            edge_key = tuple(sorted((u, v)))
            if edge_key not in drawn_edges:
                drawn_edges.add(edge_key)
                p2 = network.nodes[v]
                ax.plot([p1.x, p2.x], [p1.y, p2.y], color="#D1D5DB", linewidth=1.5, zorder=1, linestyle="--")

    # 2. Draw nodes
    for node_id, node in network.nodes.items():
        if node.is_depot:
            ax.scatter(node.x, node.y, color="#DC2626", s=250, marker="s", zorder=5, label="Central Depot (Start/End)")
            ax.text(node.x + 0.3, node.y + 0.3, f"{node.name} (Depot)", fontsize=10, weight="bold", color="#991B1B")
        elif node_id in trip.visited_nodes:
            # Visited customer stop
            ax.scatter(node.x, node.y, color="#2563EB", s=180, marker="o", zorder=5)
            # Find sequence number in tour
            seq = [i for i, stop in enumerate(trip.visited_nodes[:-1]) if stop == node_id]
            seq_label = f"Stop #{seq[0]}: {node.name}" if seq else node.name
            ax.text(node.x + 0.2, node.y + 0.2, seq_label, fontsize=9, weight="semibold", color="#1E3A8A")
        else:
            # Unvisited node / road junction
            ax.scatter(node.x, node.y, color="#9CA3AF", s=50, marker=".", zorder=3)

    # 3. Highlight route path with directional arrows
    tour_nodes = trip.turn_by_turn_path
    for i in range(len(tour_nodes) - 1):
        u_id = tour_nodes[i]
        v_id = tour_nodes[i + 1]
        p1 = network.nodes[u_id]
        p2 = network.nodes[v_id]

        dx = p2.x - p1.x
        dy = p2.y - p1.y

        ax.annotate(
            "",
            xy=(p2.x, p2.y),
            xytext=(p1.x, p1.y),
            arrowprops=dict(
                arrowstyle="-|>",
                color="#059669",
                lw=2.5,
                mutation_scale=15,
                shrinkA=5,
                shrinkB=5
            ),
            zorder=4
        )

    ax.set_title(f"{title}\nTotal Distance: {trip.total_distance_km} km | Est. Time: {trip.estimated_travel_time_min} mins", fontsize=13, weight="bold", pad=12)
    ax.set_xlabel("X Coordinate (km)", fontsize=10)
    ax.set_ylabel("Y Coordinate (km)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_dp_table_heatmap(
    packing_plan: PackingPlan,
    parcels: List[Parcel],
    output_path: str = "output/charts/dp_table_heatmap.png",
    max_cols: int = 40
):
    """
    Renders a 2D Heatmap of the 0/1 Knapsack Dynamic Programming Table.
    """
    if not packing_plan.dp_table:
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    table_matrix = np.array(packing_plan.dp_table)

    # Cap columns for clean rendering
    num_cols = min(table_matrix.shape[1], max_cols)
    sub_matrix = table_matrix[:, :num_cols]

    plt.figure(figsize=(12, 6))
    im = plt.imshow(sub_matrix, cmap="YlGnBu", aspect="auto")
    plt.colorbar(im, label="Accumulated Maximum Utility Value")

    y_labels = ["0 (Empty)"] + [f"{p.id} (w={p.weight})" for p in parcels]
    plt.yticks(range(len(y_labels)), y_labels, fontsize=9)
    plt.xticks(range(0, num_cols, max(1, num_cols // 15)), range(0, num_cols, max(1, num_cols // 15)))

    plt.title(f"0/1 Knapsack Dynamic Programming Table Heatmap (Capacity 0..{num_cols-1} kg)\nOptimal Value: {packing_plan.total_value} | Selected Weight: {packing_plan.total_weight}/{packing_plan.weight_capacity} kg", fontsize=11, weight="bold")
    plt.xlabel("Knapsack Capacity State w (kg)", fontsize=10)
    plt.ylabel("Parcel Stage i Considered", fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_benchmark_charts(
    benchmark_data: Dict[str, Any],
    output_dir: str = "output/charts"
):
    """
    Plots comprehensive runtime charts comparing:
    1. Sorting Algorithms (QuickSort vs MergeSort vs TimSort) vs N
    2. 0/1 Knapsack DP Runtime vs (N * W)
    3. Route Optimization: Nearest Neighbor vs 2-Opt vs Exact TSP
    4. End-to-End Pipeline Execution Time Breakdown
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Sorting Algorithm Comparison
    sizes = benchmark_data["sorting"]["sizes"]
    qs_times = benchmark_data["sorting"]["quicksort"]
    ms_times = benchmark_data["sorting"]["mergesort"]
    ts_times = benchmark_data["sorting"]["timsort"]

    plt.figure(figsize=(9, 5))
    plt.plot(sizes, qs_times, marker="o", label="QuickSort (Median-of-3)", color="#E11D48", linewidth=2)
    plt.plot(sizes, ms_times, marker="s", label="MergeSort (Stable O(N log N))", color="#2563EB", linewidth=2)
    plt.plot(sizes, ts_times, marker="^", label="TimSort (Python Builtin)", color="#059669", linewidth=2)
    plt.title("Sorting Algorithm Benchmark: Runtime vs Parcel Count N", fontsize=12, weight="bold")
    plt.xlabel("Number of Parcels (N)", fontsize=10)
    plt.ylabel("Runtime (milliseconds)", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "sorting_runtime_comparison.png"), dpi=300)
    plt.close()

    # 2. Knapsack DP Runtime vs (N * W)
    knapsack_inputs = benchmark_data["knapsack"]["n_times_w"]
    knapsack_times = benchmark_data["knapsack"]["runtimes_ms"]

    plt.figure(figsize=(9, 5))
    plt.plot(knapsack_inputs, knapsack_times, marker="o", color="#7C3AED", linewidth=2)
    plt.title("0/1 Knapsack DP Complexity Verification: O(N · W)", fontsize=12, weight="bold")
    plt.xlabel("Problem State Size (N × W)", fontsize=10)
    plt.ylabel("Runtime (milliseconds)", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "knapsack_runtime_comparison.png"), dpi=300)
    plt.close()

    # 3. TSP Scalability: Exact vs Nearest-Neighbor vs 2-Opt
    tsp_stops = benchmark_data["tsp"]["stops"]
    tsp_exact = benchmark_data["tsp"]["exact"]
    tsp_nn = benchmark_data["tsp"]["nn"]
    tsp_2opt = benchmark_data["tsp"]["two_opt"]

    plt.figure(figsize=(9, 5))
    valid_exact_stops = [s for s, t in zip(tsp_stops, tsp_exact) if t is not None]
    valid_exact_times = [t for t in tsp_exact if t is not None]

    if valid_exact_times:
        plt.plot(valid_exact_stops, valid_exact_times, marker="x", label="Exact Brute-Force O(N!)", color="#DC2626", linewidth=2, linestyle="--")
    plt.plot(tsp_stops, tsp_nn, marker="o", label="Nearest-Neighbor Approx O(N²)", color="#2563EB", linewidth=2)
    plt.plot(tsp_stops, tsp_2opt, marker="s", label="2-Opt Refined Tour", color="#059669", linewidth=2)

    plt.yscale("log")
    plt.title("TSP Route Optimization: Runtime vs Stop Count (Log Scale)", fontsize=12, weight="bold")
    plt.xlabel("Number of Stops (N)", fontsize=10)
    plt.ylabel("Runtime (ms) - Log Scale", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "tsp_runtime_comparison.png"), dpi=300)
    plt.close()

    # 4. Pipeline Execution Breakdown
    stages = list(benchmark_data["breakdown"].keys())
    stage_times = list(benchmark_data["breakdown"].values())

    plt.figure(figsize=(8, 5))
    bars = plt.bar(stages, stage_times, color=["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EC4899"])
    plt.title("Courier Planning Pipeline: Phase-by-Phase Latency Breakdown", fontsize=12, weight="bold")
    plt.ylabel("Runtime (milliseconds)", fontsize=10)
    plt.xticks(rotation=15, ha="right", fontsize=9)
    plt.grid(axis="y", linestyle=":", alpha=0.6)

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., h + 0.05, f"{h:.2f}ms", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pipeline_latency_breakdown.png"), dpi=300)
    plt.close()
