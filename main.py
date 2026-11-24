"""
main.py
Main Interactive CLI for Intelligent Courier Planning System.
Usage:
    python main.py --dataset data/small_dataset.json
    python main.py --dataset data/city_courier_scenario.json --sort mergesort --plot
    python main.py --help
"""

import argparse
import json
import sys
import os
from tabulate import tabulate

from src.models import Parcel
from src.graph import RoadNetwork
from src.pipeline import CourierPlanningEngine
from src.knapsack_dp import render_dp_table_snippet
from src.visualizer import plot_delivery_route, plot_dp_table_heatmap


def print_banner():
    banner = r"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   INTELLIGENT COURIER PLANNING SYSTEM                         ║
║         Design & Analysis of Algorithms Capstone Project (100 Marks)          ║
║      Sorting • Dynamic Programming • Dijkstra • TSP Approximation (2-Opt)     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_courier_planner(
    dataset_path: str,
    sort_algo: str = "quicksort",
    apply_2opt: bool = True,
    show_dp_table: bool = True,
    save_plot: bool = True,
    plot_prefix: str = "demo"
):
    print(f"\n📂 Loading Problem Dataset: {dataset_path}")
    if not os.path.exists(dataset_path):
        print(f"❌ Error: File {dataset_path} not found.")
        sys.exit(1)

    with open(dataset_path, "r") as f:
        data = json.load(f)

    network = RoadNetwork.from_dict(data)
    parcels = [Parcel.from_dict(p) for p in data["parcels"]]
    weight_cap = data["vehicle_capacity_weight"]
    vol_cap = data.get("vehicle_capacity_volume", 100)

    print(f"   • Scenario Name: {data.get('name', 'Delivery Problem')}")
    print(f"   • Network Topology: {network.num_nodes()} Locations / Hubs, {network.num_edges()} Road Segments")
    print(f"   • Courier Fleet Capacity: {weight_cap} kg Weight, {vol_cap} L Volume")
    print(f"   • Incoming Parcels Queue: {len(parcels)} items")

    engine = CourierPlanningEngine(network)
    results = engine.run_full_pipeline(
        parcels=parcels,
        vehicle_weight_capacity=weight_cap,
        vehicle_volume_capacity=vol_cap,
        sort_algorithm=sort_algo,
        apply_2opt=apply_2opt
    )

    plan = results["packing_plan"]
    trip = results["delivery_trip"]
    metrics = results["sorting_metrics"]
    runtimes = results["runtimes_ms"]

    # ---------------------------------------------------------
    # PHASE 2 EVIDENCE: SORTING & BOX FILLING
    # ---------------------------------------------------------
    print("\n" + "=" * 75)
    print("PHASE 2: PACKAGE PRIORITIZATION & BOX FILLING (0/1 KNAPSACK DP)")
    print("=" * 75)
    print(f"✅ Sorting Algorithm: {sort_algo.upper()} | Comparisons: {metrics.comparisons} | Time: {metrics.time_seconds*1000.0:.3f} ms")

    sorted_sample = results["sorted_parcels"][:8]
    table_sort = []
    for p in sorted_sample:
        table_sort.append([p.id, p.destination_node, f"{p.weight} kg", p.priority, f"{p.deadline_hours} hrs", p.composite_value, f"{p.value_density:.2f}"])
    print("\nTop Prioritized Parcels (Sorted by Deadline ASC, Priority DESC, Density DESC):")
    print(tabulate(table_sort, headers=["Parcel ID", "Dest Node", "Weight", "Priority", "Deadline", "Utility Value", "Value/Kg"], tablefmt="github"))
    if len(results["sorted_parcels"]) > 8:
        print(f"... and {len(results['sorted_parcels']) - 8} more parcels in prioritized queue.")

    print(f"\n📦 Dynamic Programming Knapsack Results:")
    print(f"   • Vehicle Payload Capacity: {weight_cap} kg")
    print(f"   • Selected Parcels Loaded : {len(plan.selected_parcels)} of {len(parcels)}")
    print(f"   • Total Cargo Weight      : {plan.total_weight} kg ({plan.capacity_utilization_pct:.1f}% capacity utilization)")
    print(f"   • Total Accumulated Value : {plan.total_value} pts")
    print(f"   • DP Execution Latency    : {plan.execution_time_ms:.3f} ms")

    selected_rows = []
    for p in plan.selected_parcels:
        dest_name = network.nodes[p.destination_node].name if p.destination_node in network.nodes else f"Node {p.destination_node}"
        selected_rows.append([p.id, dest_name, f"{p.weight} kg", p.priority, f"{p.deadline_hours}h", p.composite_value])
    print("\nLoaded Cargo Manifest:")
    print(tabulate(selected_rows, headers=["Parcel", "Destination Stop", "Weight", "Priority", "Deadline", "Value"], tablefmt="github"))

    if show_dp_table and plan.dp_table and len(parcels) <= 15:
        print("\n" + "-" * 75)
        print("EVIDENCE: 0/1 KNAPSACK DYNAMIC PROGRAMMING TABLE:")
        print("-" * 75)
        print(render_dp_table_snippet(plan.dp_table, results["sorted_parcels"], max_cols=min(weight_cap, 25)))

    # ---------------------------------------------------------
    # PHASE 3 EVIDENCE: ROUTE MAKER & GRAPH PROCESSING
    # ---------------------------------------------------------
    print("\n" + "=" * 75)
    print("PHASE 3: ROUTE MAKER & GRAPH PROCESSING (DIJKSTRA + TSP 2-OPT)")
    print("=" * 75)
    print(f"✅ Metric Distance Matrix computed via Dijkstra's Algorithm for {len(results['active_stops'])} active points.")
    print(f"   • Nearest Neighbor Initial Tour: {' -> '.join(str(n) for n in results['raw_nn_tour'])}")
    print(f"   • NN Tour Distance             : {results['raw_nn_dist']} km")

    if apply_2opt:
        improvement = ((results['raw_nn_dist'] - results['final_dist']) / max(1e-6, results['raw_nn_dist'])) * 100.0
        print(f"   • 2-Opt Optimized Tour         : {' -> '.join(str(n) for n in results['final_tour'])}")
        print(f"   • Optimized Tour Distance      : {results['final_dist']} km")
        print(f"   • 2-Opt Swaps Executed         : {results['two_opt_swaps']} passes (Improvement: {improvement:.2f}%)")

    if results.get("exact_dist") is not None:
        approx_ratio = results['final_dist'] / results['exact_dist']
        print(f"   • Exact Brute-Force Tour       : {' -> '.join(str(n) for n in results['exact_tour'])}")
        print(f"   • Exact Optimal Tour Distance  : {results['exact_dist']} km")
        print(f"   • Measured Approximation Ratio : {approx_ratio:.3f}x (1.000 = Provably Optimal)")

    print(f"\n🚗 Turn-by-Turn Road Transit Sequence:")
    turn_str = " -> ".join(network.nodes[nid].name for nid in trip.turn_by_turn_path)
    print(f"   {turn_str}")
    print(f"   • Total Transit Distance       : {trip.total_distance_km} km")
    print(f"   • Estimated Total Tour Time    : {trip.estimated_travel_time_min} minutes (Driving + Drop-off SLA)")

    # ---------------------------------------------------------
    # PHASE 4 LATENCY SUMMARY
    # ---------------------------------------------------------
    print("\n" + "=" * 75)
    print("PHASE 4: ALGORITHMIC COMPONENT RUNTIME AUDIT")
    print("=" * 75)
    rt_table = [
        ["1. Priority Sorting", sort_algo.capitalize(), f"{runtimes['sorting']:.4f} ms"],
        ["2. Knapsack Box Packing", "0/1 Dynamic Programming", f"{runtimes['knapsack_dp']:.4f} ms"],
        ["3. Shortest Path Graph", "Dijkstra Min-Heap", f"{runtimes['dijkstra']:.4f} ms"],
        ["4. TSP Route Generation", "Nearest Neighbor", f"{runtimes['tsp_nearest_neighbor']:.4f} ms"],
        ["5. TSP Route Refinement", "2-Opt Local Search", f"{runtimes['tsp_2opt']:.4f} ms"],
        ["TOTAL Integrated Latency", "End-to-End Pipeline", f"{runtimes['total_pipeline']:.4f} ms"]
    ]
    print(tabulate(rt_table, headers=["Pipeline Stage", "Algorithm", "Elapsed Runtime"], tablefmt="github"))

    # ---------------------------------------------------------
    # VISUALIZATION
    # ---------------------------------------------------------
    if save_plot:
        route_plot_path = f"output/charts/{plot_prefix}_route_map.png"
        plot_delivery_route(network, trip, output_path=route_plot_path, title=f"Delivery Route: {data.get('name')}")
        print(f"\n🗺️  Delivery Route Map saved to: {route_plot_path}")

        if plan.dp_table:
            dp_plot_path = f"output/charts/{plot_prefix}_dp_heatmap.png"
            plot_dp_table_heatmap(plan, results["sorted_parcels"], output_path=dp_plot_path)
            print(f"📊 DP Table Heatmap saved to: {dp_plot_path}")

    print("\n" + "=" * 75)
    print("✅ EXECUTION SUCCESSFULLY COMPLETED")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Intelligent Courier Planning System (DAA Capstone)")
    parser.add_argument("--dataset", type=str, default="data/small_dataset.json", help="Path to JSON dataset")
    parser.add_argument("--sort", type=str, default="quicksort", choices=["quicksort", "mergesort", "timsort"], help="Sorting algorithm")
    parser.add_argument("--no-2opt", action="store_true", help="Disable 2-opt route refinement")
    parser.add_argument("--no-dp-table", action="store_true", help="Suppress ASCII DP table display")
    parser.add_argument("--no-plot", action="store_true", help="Suppress generating matplotlib charts")
    parser.add_argument("--prefix", type=str, default="run", help="Prefix for chart outputs")

    args = parser.parse_args()
    print_banner()
    run_courier_planner(
        dataset_path=args.dataset,
        sort_algo=args.sort,
        apply_2opt=not args.no_2opt,
        show_dp_table=not args.no_dp_table,
        save_plot=not args.no_plot,
        plot_prefix=args.prefix
    )


if __name__ == "__main__":
    main()
