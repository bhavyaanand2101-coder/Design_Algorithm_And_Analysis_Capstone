"""
dijkstra.py
Phase 3: Shortest Path Computation using Dijkstra's Algorithm with a Min-Heap.
Finds single-source shortest path distances and predecessor chains for full road route expansion.
Time Complexity: O((V + E) log V) using Python's heapq (binary min-heap).
"""

import heapq
import time
from typing import Dict, List, Tuple, Optional
from src.graph import RoadNetwork


def dijkstra_shortest_path(
    network: RoadNetwork,
    start_node: int
) -> Tuple[Dict[int, float], Dict[int, Optional[int]], float]:
    """
    Computes shortest path from start_node to all reachable nodes in the road network.
    
    Args:
        network: RoadNetwork graph
        start_node: Starting vertex ID
        
    Returns:
        Tuple:
            - distances: Dict mapping node_id -> shortest distance from start_node
            - predecessors: Dict mapping node_id -> previous node along optimal path
            - execution_time_ms: Computation runtime in milliseconds
    """
    start_t = time.perf_counter()

    distances: Dict[int, float] = {node_id: float('inf') for node_id in network.nodes}
    predecessors: Dict[int, Optional[int]] = {node_id: None for node_id in network.nodes}

    if start_node not in network.nodes:
        raise ValueError(f"Start node {start_node} not found in road network.")

    distances[start_node] = 0.0
    # Min-heap priority queue stores tuples: (current_distance, node_id)
    pq: List[Tuple[float, int]] = [(0.0, start_node)]

    while pq:
        curr_dist, u = heapq.heappop(pq)

        # Skip stale entries in heap
        if curr_dist > distances[u]:
            continue

        for v, weight, _ in network.get_neighbors(u):
            new_dist = curr_dist + weight
            if new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
    return distances, predecessors, elapsed_ms


def reconstruct_path(predecessors: Dict[int, Optional[int]], target_node: int) -> List[int]:
    """
    Reconstructs the full node sequence from the source up to target_node using predecessor pointers.
    """
    path = []
    curr: Optional[int] = target_node
    while curr is not None:
        path.append(curr)
        curr = predecessors.get(curr)
    path.reverse()
    return path


def compute_metric_distance_matrix(
    network: RoadNetwork,
    active_nodes: List[int]
) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], List[int]], float]:
    """
    Computes all-pairs shortest paths among the subset of active stops (Depot + delivery destinations).
    
    Returns:
        - dist_matrix: (u, v) -> shortest distance
        - path_matrix: (u, v) -> full list of nodes in shortest road path
        - total_time_ms: Total Dijkstra execution time
    """
    start_t = time.perf_counter()
    dist_matrix: Dict[Tuple[int, int], float] = {}
    path_matrix: Dict[Tuple[int, int], List[int]] = {}

    for u in active_nodes:
        distances, predecessors, _ = dijkstra_shortest_path(network, u)
        for v in active_nodes:
            dist_matrix[(u, v)] = distances[v]
            path_matrix[(u, v)] = reconstruct_path(predecessors, v)

    total_time_ms = (time.perf_counter() - start_t) * 1000.0
    return dist_matrix, path_matrix, total_time_ms
