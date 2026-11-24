"""
graph.py
Phase 3: Graph representation and road network modeling.
Implements RoadNetwork with adjacency list, node management, and road coordinates.
"""

from typing import Dict, List, Tuple, Set, Optional, Any
import json
import math
from src.models import DeliveryPoint, RoadEdge


class RoadNetwork:
    """
    Weighted graph representation of the courier service delivery territory.
    Vertices = Customer addresses, hubs, intersections, and depot.
    Edges = Navigable road segments with real travel distances in km.
    """
    def __init__(self, name: str = "Courier Delivery Network"):
        self.name = name
        self.nodes: Dict[int, DeliveryPoint] = {}
        # Adjacency list: node_id -> list of (neighbor_id, distance_km, road_name)
        self.adjacency: Dict[int, List[Tuple[int, float, str]]] = {}
        self.depot_id: int = 0

    def add_node(self, node: DeliveryPoint):
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []
        if node.is_depot:
            self.depot_id = node.id

    def add_edge(self, u: int, v: int, distance: float, road_name: str = "", bidirectional: bool = True):
        if u not in self.adjacency:
            self.adjacency[u] = []
        if v not in self.adjacency:
            self.adjacency[v] = []

        self.adjacency[u].append((v, distance, road_name))
        if bidirectional:
            self.adjacency[v].append((u, distance, road_name))

    def get_neighbors(self, u: int) -> List[Tuple[int, float, str]]:
        return self.adjacency.get(u, [])

    def num_nodes(self) -> int:
        return len(self.nodes)

    def num_edges(self) -> int:
        total = sum(len(edges) for edges in self.adjacency.values())
        return total // 2  # Assuming undirected

    def to_dict(self) -> Dict[str, Any]:
        edges_data = []
        seen = set()
        for u, neighbors in self.adjacency.items():
            for v, dist, name in neighbors:
                edge_key = tuple(sorted((u, v)))
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges_data.append({"u": u, "v": v, "distance": dist, "road_name": name})

        return {
            "name": self.name,
            "depot_id": self.depot_id,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": edges_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoadNetwork":
        net = cls(name=data.get("name", "Courier Delivery Network"))
        net.depot_id = data.get("depot_id", 0)

        for nd in data.get("nodes", []):
            net.add_node(DeliveryPoint.from_dict(nd))

        for ed in data.get("edges", []):
            net.add_edge(
                u=ed["u"],
                v=ed["v"],
                distance=float(ed["distance"]),
                road_name=ed.get("road_name", ""),
                bidirectional=True
            )
        return net

    def save_to_file(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "RoadNetwork":
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
