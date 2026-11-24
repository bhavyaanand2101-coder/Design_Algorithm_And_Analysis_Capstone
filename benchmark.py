"""
benchmark.py
Phase 4: Algorithmic Performance Testing, Scalability Profiling, and Runtime Benchmarking.
Compares:
1. Sorting: QuickSort vs MergeSort vs TimSort
2. Knapsack DP: Runtime scaling vs O(N * W)
3. Dijkstra Shortest Paths: Latency vs Graph size
4. TSP Optimization: Exact Brute-Force vs Nearest-Neighbor vs 2-Opt Refinement
5. End-to-End Pipeline Latency Breakdown
Outputs statistical markdown tables and exports visualization plots to output/charts/.
"""

import time
import random
import json
import os
from typing import Dict, List, Any

from src.models import Parcel, DeliveryPoint
from src.graph import RoadNetwork
from src.sorting import sort_parcels
from src.knapsack_dp import knapsack_01_dp
from src.dijkstra import dijkstra_shortest_path, compute_metric_distance_matrix
from src.tsp_approx import tsp_nearest_neighbor, tsp_2opt, tsp_exact_bruteforce
from src.pipeline import CourierPlanningEngine
from src.visualizer import plot_benchmark_charts


def generate_benchmark_parcels(n: int, seed: int = 42) -> List[Parcel]:
    random.seed(seed)
    parcels = []
    for i in range(1, n + 1):
        p = random.randint(1, 5)
        d = round(random.uniform(1.0, 24.0), 1)
        w = random.randint(2, 15)
        v = random.randint(2, 15)
        base = random.randint(10, 70)
        dest = random.randint(1, max(2, n // 3))
        parcels.append(Parcel(
            id=f"P{i:04d}",
            destination_node=dest,
            weight=w,
            volume=v,
            priority=p,
            deadline_hours=d,
            base_value=base
        ))
    return parcels


def generate_benchmark_network(num_nodes: int, seed: int = 42) -> RoadNetwork:
    random.seed(seed)
    net = RoadNetwork(f"Benchmark-Graph-{num_nodes}")
    net.add_node(DeliveryPoint(id=0, name="Central Depot", x=10.0, y=10.0, is_depot=True))

    for i in range(1, num_nodes):
        net.add_node(DeliveryPoint(
            id=i,
            name=f"Stop {i}",
            x=round(random.uniform(0.0, 20.0), 2),
            y=round(random.uniform(0.0, 20.0), 2)
        ))

    # Add edges to 3 nearest
    nodes = list(net.nodes.values())
    for i in range(num_nodes):
        dists = []
        for j in range(num_nodes):
            if i != j:
                d = nodes[i].distance_to(nodes[j])
                dists.append((d, j))
        dists.sort()
        for d, j in dists[:min(3, len(dists))]:
            net.add_edge(i, j, round(max(1.0, d * 1.2), 2))

    return net


def benchmark_sorting() -> Dict[str, Any]:
    print("\n[Phase 4.1] Benchmarking Sorting Algorithms (QuickSort vs MergeSort vs TimSort)...")
    sizes = [10, 25, 50, 100, 250, 500, 1000]
    results = {
        "sizes": sizes,
        "quicksort": [],
        "mergesort": [],
        "timsort": [],
        "qs_comparisons": [],
        "ms_comparisons": []
    }

    for n in sizes:
        parcels = generate_benchmark_parcels(n, seed=n)

        # QuickSort
        _, m_qs = sort_parcels(parcels, algorithm="quicksort")
        results["quicksort"].append(round(m_qs.time_seconds * 1000.0, 4))
        results["qs_comparisons"].append(m_qs.comparisons)

        # MergeSort
        _, m_ms = sort_parcels(parcels, algorithm="mergesort")
        results["mergesort"].append(round(m_ms.time_seconds * 1000.0, 4))
        results["ms_comparisons"].append(m_ms.comparisons)

        # TimSort
        _, m_ts = sort_parcels(parcels, algorithm="timsort")
        results["timsort"].append(round(m_ts.time_seconds * 1000.0, 4))

    return results


def benchmark_knapsack() -> Dict[str, Any]:
    print("[Phase 4.2] Benchmarking 0/1 Knapsack DP Complexity O(N * W)...")
    configs = [
        (10, 20),
        (25, 40),
        (50, 75),
        (100, 120),
        (150, 200),
        (200, 300)
    ]
    results = {
        "configs": [f"N={n},W={w}" for n, w in configs],
        "n_times_w": [n * w for n, w in configs],
        "runtimes_ms": [],
        "optimal_values": [],
        "selected_counts": []
    }

    for n, w in configs:
        parcels = generate_benchmark_parcels(n, seed=n + w)
        plan = knapsack_01_dp(parcels, weight_capacity=w, include_table=False)
        results["runtimes_ms"].append(round(plan.execution_time_ms, 4))
        results["optimal_values"].append(plan.total_value)
        results["selected_counts"].append(len(plan.selected_parcels))

    return results


def benchmark_tsp() -> Dict[str, Any]:
    print("[Phase 4.3] Benchmarking TSP Optimization: Exact Brute-Force vs Nearest-Neighbor vs 2-Opt...")
    # Exact becomes intractable beyond N=9-10 (9! = 362,880, 10! = 3,628,800)
    stop_counts = [4, 6, 8, 9, 12, 16, 20, 25]
    results = {
        "stops": stop_counts,
        "exact": [],
        "nn": [],
        "two_opt": [],
        "approx_ratios": [],
        "two_opt_improvements": []
    }

    net = generate_benchmark_network(30, seed=999)

    for k in stop_counts:
        active_stops = list(range(k))
        dist_mat, _, _ = compute_metric_distance_matrix(net, active_stops)

        # Exact Brute-Force (only for small k <= 9)
        if k <= 9:
            _, exact_d, exact_ms = tsp_exact_bruteforce(0, active_stops, dist_mat)
            results["exact"].append(round(exact_ms, 3))
        else:
            exact_d = None
            results["exact"].append(None)

        # Nearest-Neighbor
        nn_tour, nn_d, nn_ms = tsp_nearest_neighbor(0, active_stops, dist_mat)
        results["nn"].append(round(nn_ms, 3))

        # 2-Opt
        _, opt_d, swaps, opt_ms = tsp_2opt(nn_tour, dist_mat)
        results["two_opt"].append(round(opt_ms, 3))

        # Improvements & Approximation Ratios
        improvement = ((nn_d - opt_d) / max(1e-6, nn_d)) * 100.0
        results["two_opt_improvements"].append(round(improvement, 2))

        if exact_d is not None and exact_d > 0:
            ratio = opt_d / exact_d
            results["approx_ratios"].append(round(ratio, 3))
        else:
            results["approx_ratios"].append(None)

    return results


def benchmark_pipeline_breakdown() -> Dict[str, float]:
    print("[Phase 4.4] Profiling End-to-End Pipeline Stage Latency Breakdown...")
    with open("data/city_courier_scenario.json", "r") as f:
        data = json.load(f)

    net = RoadNetwork.from_dict(data)
    parcels = [Parcel.from_dict(p) for p in data["parcels"]]

    engine = CourierPlanningEngine(net)
    res = engine.run_full_pipeline(
        parcels=parcels,
        vehicle_weight_capacity=data["vehicle_capacity_weight"],
        vehicle_volume_capacity=data["vehicle_capacity_volume"],
        sort_algorithm="quicksort",
        apply_2opt=True
    )
    r = res["runtimes_ms"]
    return {
        "Sorting (QuickSort)": round(r["sorting"], 3),
        "Packing (Knapsack DP)": round(r["knapsack_dp"], 3),
        "Shortest Paths (Dijkstra)": round(r["dijkstra"], 3),
        "Route Maker (NN TSP)": round(r["tsp_nearest_neighbor"], 3),
        "Route Refinement (2-Opt)": round(r["tsp_2opt"], 3)
    }


def run_full_benchmark():
    os.makedirs("output/charts", exist_ok=True)
    bench_data = {
        "sorting": benchmark_sorting(),
        "knapsack": benchmark_knapsack(),
        "tsp": benchmark_tsp(),
        "breakdown": benchmark_pipeline_breakdown()
    }

    # Generate publication charts
    plot_benchmark_charts(bench_data, output_dir="output/charts")
    print("\nAll benchmark plots successfully rendered to output/charts/")

    # Print Markdown Summary Tables
    print("\n" + "=" * 70)
    print("PHASE 4 BENCHMARK SUMMARY REPORT")
    print("=" * 70)

    print("\n### 1. Sorting Algorithms Benchmark (Runtime in ms)")
    print("| Parcels (N) | QuickSort (ms) | MergeSort (ms) | TimSort (ms) | QS Comparisons | MS Comparisons |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    s = bench_data["sorting"]
    for i, n in enumerate(s["sizes"]):
        print(f"| {n:<11} | {s['quicksort'][i]:<14} | {s['mergesort'][i]:<14} | {s['timsort'][i]:<12} | {s['qs_comparisons'][i]:<14} | {s['ms_comparisons'][i]:<14} |")

    print("\n### 2. 0/1 Knapsack DP Complexity O(N · W)")
    print("| Configuration | State Space (N × W) | DP Runtime (ms) | Max Value | Items Selected |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    k = bench_data["knapsack"]
    for i, cfg in enumerate(k["configs"]):
        print(f"| {cfg:<13} | {k['n_times_w'][i]:<19} | {k['runtimes_ms'][i]:<15} | {k['optimal_values'][i]:<9} | {k['selected_counts'][i]:<14} |")

    print("\n### 3. TSP Scalability: Exact O(N!) vs Heuristics")
    print("| Stops (N) | Exact Brute-Force (ms) | Nearest-Neighbor (ms) | 2-Opt (ms) | 2-Opt Improvement (%) | Approx Ratio (Opt / Exact) |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    t = bench_data["tsp"]
    for i, st in enumerate(t["stops"]):
        ex = f"{t['exact'][i]} ms" if t['exact'][i] is not None else "Intractable"
        ar = f"{t['approx_ratios'][i]:.3f}" if t['approx_ratios'][i] is not None else "N/A"
        print(f"| {st:<9} | {ex:<22} | {t['nn'][i]:<21} | {t['two_opt'][i]:<10} | {t['two_opt_improvements'][i]:<21} | {ar:<26} |")

    print("\n### 4. Full Pipeline Latency Breakdown (City Scenario, 50 Parcels)")
    for stage, ms in bench_data["breakdown"].items():
        print(f"  - {stage:<28}: {ms:>6.3f} ms")
    total_ms = sum(bench_data["breakdown"].values())
    print(f"  - Total Integrated Latency   : {total_ms:>6.3f} ms")
    print("=" * 70)

    # Save benchmark JSON
    with open("output/benchmark_results.json", "w") as f:
        json.dump(bench_data, f, indent=2)


if __name__ == "__main__":
    run_full_benchmark()
