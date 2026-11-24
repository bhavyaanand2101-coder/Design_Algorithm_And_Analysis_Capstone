"""
pipeline.py
Core Integrated Courier Planning Pipeline.
Orchestrates:
  Phase 1: Problem Design & Data Loading
  Phase 2: Parcel Prioritization (QuickSort/MergeSort) & Box Packing (0/1 Knapsack DP)
  Phase 3: Route Generation (Dijkstra Shortest Paths + TSP Nearest-Neighbor with 2-Opt)
Produces an actionable dispatch manifest and performance audit.
"""

import time
from typing import List, Dict, Tuple, Any, Optional
from src.models import Parcel, DeliveryPoint, PackingPlan, DeliveryTrip
from src.graph import RoadNetwork
from src.sorting import sort_parcels, SortingMetrics
from src.knapsack_dp import knapsack_01_dp
from src.dijkstra import compute_metric_distance_matrix
from src.tsp_approx import tsp_nearest_neighbor, tsp_2opt, tsp_exact_bruteforce, calculate_tour_length


class CourierPlanningEngine:
    """
    Main system coordinator executing the 4 algorithmic phases.
    """
    def __init__(self, network: RoadNetwork):
        self.network = network

    def run_full_pipeline(
        self,
        parcels: List[Parcel],
        vehicle_weight_capacity: int,
        vehicle_volume_capacity: Optional[int] = None,
        sort_algorithm: str = "quicksort",
        apply_2opt: bool = True,
        compare_exact_tsp_limit: int = 9
    ) -> Dict[str, Any]:
        """
        Executes the full courier planning workflow.
        
        Returns:
            Dict containing:
                - 'sorted_parcels': List[Parcel]
                - 'sorting_metrics': SortingMetrics
                - 'packing_plan': PackingPlan
                - 'metric_dist_matrix': Dict[(u, v), float]
                - 'raw_nn_tour': List[int]
                - 'optimized_tour': List[int]
                - 'exact_tour': Optional[List[int]]
                - 'delivery_trip': DeliveryTrip
                - 'runtimes_ms': Dict[str, float]
        """
        pipeline_start = time.perf_counter()
        runtimes = {}

        # -------------------------------------------------------------
        # PHASE 2: PACKAGE PRIORITIZATION (SORTING)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        sorted_parcels, sort_metrics = sort_parcels(parcels, algorithm=sort_algorithm)
        runtimes["sorting"] = (time.perf_counter() - t0) * 1000.0

        # -------------------------------------------------------------
        # PHASE 2: BOX FILLING (0/1 KNAPSACK DYNAMIC PROGRAMMING)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        packing_plan = knapsack_01_dp(
            sorted_parcels,
            weight_capacity=vehicle_weight_capacity,
            volume_capacity=vehicle_volume_capacity,
            include_table=True
        )
        runtimes["knapsack_dp"] = (time.perf_counter() - t0) * 1000.0

        # -------------------------------------------------------------
        # PHASE 3: GRAPH PROCESSING & SHORTEST PATHS (DIJKSTRA)
        # -------------------------------------------------------------
        # Extract unique destination nodes from chosen parcels + Depot
        depot_id = self.network.depot_id
        active_customer_nodes = sorted(list({p.destination_node for p in packing_plan.selected_parcels}))
        all_stops = [depot_id] + [n for n in active_customer_nodes if n != depot_id]

        t0 = time.perf_counter()
        dist_matrix, path_matrix, dijkstra_time = compute_metric_distance_matrix(
            self.network,
            active_nodes=all_stops
        )
        runtimes["dijkstra"] = dijkstra_time

        # -------------------------------------------------------------
        # PHASE 3: ROUTE MAKER (NEAREST-NEIGHBOR TSP + 2-OPT)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        nn_tour, nn_dist, nn_time = tsp_nearest_neighbor(
            start_node=depot_id,
            stops=all_stops,
            dist_matrix=dist_matrix
        )
        runtimes["tsp_nearest_neighbor"] = nn_time

        final_tour = nn_tour
        final_dist = nn_dist
        two_opt_swaps = 0

        if apply_2opt and len(all_stops) > 2:
            opt_tour, opt_dist, swaps, two_opt_time = tsp_2opt(nn_tour, dist_matrix)
            runtimes["tsp_2opt"] = two_opt_time
            final_tour = opt_tour
            final_dist = opt_dist
            two_opt_swaps = swaps
        else:
            runtimes["tsp_2opt"] = 0.0

        # Optional Exact TSP for benchmarking approximation ratio on small instances
        exact_tour = None
        exact_dist = None
        exact_time = 0.0
        if len(all_stops) <= compare_exact_tsp_limit:
            exact_tour, exact_dist, exact_time = tsp_exact_bruteforce(
                start_node=depot_id,
                stops=all_stops,
                dist_matrix=dist_matrix
            )
            runtimes["tsp_exact"] = exact_time

        # -------------------------------------------------------------
        # EXPAND FULL TURN-BY-TURN ROAD SEGMENTS
        # -------------------------------------------------------------
        full_turn_by_turn: List[int] = []
        for idx in range(len(final_tour) - 1):
            u, v = final_tour[idx], final_tour[idx + 1]
            segment_path = path_matrix.get((u, v), [u, v])
            if not full_turn_by_turn:
                full_turn_by_turn.extend(segment_path)
            else:
                # Omit duplicate junction
                full_turn_by_turn.extend(segment_path[1:])

        # Average vehicle speed 35 km/h + 5 min delivery drop-off service time per stop
        travel_time_min = (final_dist / 35.0) * 60.0 + (len(active_customer_nodes) * 5.0)

        node_names = {nid: self.network.nodes[nid].name for nid in self.network.nodes}

        delivery_trip = DeliveryTrip(
            trip_id=f"TRIP-{int(time.time())}",
            depot_node=depot_id,
            visited_nodes=final_tour,
            turn_by_turn_path=full_turn_by_turn,
            total_distance_km=round(final_dist, 2),
            estimated_travel_time_min=round(travel_time_min, 1),
            packing_plan=packing_plan,
            node_names=node_names,
            algorithm_used="Dijkstra + NN + 2-Opt" if apply_2opt else "Dijkstra + NN"
        )

        runtimes["total_pipeline"] = (time.perf_counter() - pipeline_start) * 1000.0

        return {
            "sorted_parcels": sorted_parcels,
            "sorting_metrics": sort_metrics,
            "packing_plan": packing_plan,
            "active_stops": all_stops,
            "metric_dist_matrix": dist_matrix,
            "path_matrix": path_matrix,
            "raw_nn_tour": nn_tour,
            "raw_nn_dist": round(nn_dist, 2),
            "final_tour": final_tour,
            "final_dist": round(final_dist, 2),
            "two_opt_swaps": two_opt_swaps,
            "exact_tour": exact_tour,
            "exact_dist": round(exact_dist, 2) if exact_dist is not None else None,
            "delivery_trip": delivery_trip,
            "runtimes_ms": runtimes
        }
