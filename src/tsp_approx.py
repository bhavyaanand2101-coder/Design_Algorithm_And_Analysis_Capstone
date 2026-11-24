"""
tsp_approx.py
Phase 3: Route Maker & TSP Tour Optimization.
Implements:
1. Nearest Neighbor Heuristic (O(N^2) greedy tour)
2. 2-Opt Local Search (iterative edge-untangling improvement)
3. Exact Held-Karp / Brute-Force (O(N!) or O(N^2 2^N) for small N baseline & approximation ratio analysis)
"""

import itertools
import time
from typing import List, Tuple, Dict, Any


def tsp_nearest_neighbor(
    start_node: int,
    stops: List[int],
    dist_matrix: Dict[Tuple[int, int], float]
) -> Tuple[List[int], float, float]:
    """
    Constructs a delivery tour using the Nearest Neighbor TSP approximation algorithm.
    Tour starts at start_node (Depot), visits all stops exactly once, and returns to start_node.
    
    Time Complexity: O(N^2) where N is number of stops.
    Approximation Guarantee: O(log N) for general metric TSP.
    
    Returns:
        Tuple: (tour_node_sequence, total_distance, runtime_ms)
    """
    start_t = time.perf_counter()

    unvisited = set(stops)
    if start_node in unvisited:
        unvisited.remove(start_node)

    current = start_node
    tour = [current]
    total_dist = 0.0

    while unvisited:
        nearest_node = None
        min_dist = float('inf')

        for candidate in unvisited:
            d = dist_matrix.get((current, candidate), float('inf'))
            if d < min_dist:
                min_dist = d
                nearest_node = candidate

        if nearest_node is None:
            break

        tour.append(nearest_node)
        total_dist += min_dist
        unvisited.remove(nearest_node)
        current = nearest_node

    # Complete cycle back to depot
    return_dist = dist_matrix.get((current, start_node), float('inf'))
    tour.append(start_node)
    total_dist += return_dist

    runtime_ms = (time.perf_counter() - start_t) * 1000.0
    return tour, total_dist, runtime_ms


def calculate_tour_length(tour: List[int], dist_matrix: Dict[Tuple[int, int], float]) -> float:
    """Calculates total distance along a tour sequence."""
    total = 0.0
    for i in range(len(tour) - 1):
        total += dist_matrix.get((tour[i], tour[i + 1]), float('inf'))
    return total


def tsp_2opt(
    initial_tour: List[int],
    dist_matrix: Dict[Tuple[int, int], float],
    max_iterations: int = 500
) -> Tuple[List[int], float, int, float]:
    """
    Refines a TSP tour using 2-Opt local search edge-swapping heuristics.
    Eliminates crossing edges and trapped suboptimal paths.
    
    Returns:
        Tuple: (optimized_tour, optimized_distance, improvement_steps, runtime_ms)
    """
    start_t = time.perf_counter()
    best_tour = list(initial_tour)
    best_dist = calculate_tour_length(best_tour, dist_matrix)
    num_nodes = len(best_tour)

    improved = True
    iterations = 0
    swaps = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # We keep the depot fixed at index 0 and index num_nodes - 1
        for i in range(1, num_nodes - 2):
            for j in range(i + 1, num_nodes - 1):
                # Check delta distance if we reverse segment [i...j]
                node_a, node_b = best_tour[i - 1], best_tour[i]
                node_c, node_d = best_tour[j], best_tour[j + 1]

                current_edges = (
                    dist_matrix.get((node_a, node_b), float('inf')) +
                    dist_matrix.get((node_c, node_d), float('inf'))
                )
                new_edges = (
                    dist_matrix.get((node_a, node_c), float('inf')) +
                    dist_matrix.get((node_b, node_d), float('inf'))
                )

                if new_edges < current_edges - 1e-6:
                    # Perform 2-opt swap: reverse segment between i and j
                    best_tour[i:j + 1] = reversed(best_tour[i:j + 1])
                    best_dist = best_dist - (current_edges - new_edges)
                    improved = True
                    swaps += 1
                    break
            if improved:
                break

    # Recalculate exact total distance to avoid floating point drift
    final_dist = calculate_tour_length(best_tour, dist_matrix)
    runtime_ms = (time.perf_counter() - start_t) * 1000.0
    return best_tour, final_dist, swaps, runtime_ms


def tsp_exact_bruteforce(
    start_node: int,
    stops: List[int],
    dist_matrix: Dict[Tuple[int, int], float]
) -> Tuple[List[int], float, float]:
    """
    Computes exact optimal TSP tour via brute-force permutation.
    Used for verifying approximation ratio on small datasets (N <= 10).
    Time Complexity: O(N!)
    """
    start_t = time.perf_counter()
    customer_stops = [s for s in stops if s != start_node]

    if not customer_stops:
        return [start_node, start_node], 0.0, 0.0

    best_tour = None
    min_dist = float('inf')

    for perm in itertools.permutations(customer_stops):
        candidate_tour = [start_node] + list(perm) + [start_node]
        dist = calculate_tour_length(candidate_tour, dist_matrix)
        if dist < min_dist:
            min_dist = dist
            best_tour = candidate_tour

    runtime_ms = (time.perf_counter() - start_t) * 1000.0
    return best_tour or [start_node, start_node], min_dist, runtime_ms
