"""
models.py
Data models for the Intelligent Courier Planning System.
Includes Parcel, DeliveryPoint, RoadEdge, RoadNetwork, PackingPlan, and DeliveryTrip.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import math


@dataclass
class Parcel:
    """
    Represents a parcel to be delivered by the courier service.
    
    Attributes:
        id: Unique identifier for the parcel (e.g., 'P001')
        destination_node: Graph node ID where the parcel must be delivered
        weight: Weight in kilograms (integer for exact DP, or scaled)
        volume: Volume in cubic decimeters / liters (optional 2nd constraint)
        priority: Priority tier (1=Standard, 2=Express, 3=Urgent, 4=Same-Day, 5=Critical)
        deadline_hours: Hours remaining until promised delivery SLA
        base_value: Base monetary or utility value of delivering this parcel
    """
    id: str
    destination_node: int
    weight: int
    volume: int = 1
    priority: int = 1
    deadline_hours: float = 24.0
    base_value: float = 10.0

    @property
    def composite_value(self) -> int:
        """
        Calculates the dynamic business value (DP reward) of the parcel.
        Parcels with high priority and tight deadlines yield higher delivery value.
        Formula: base_value * priority + max(0, (24 - deadline_hours) * 2)
        Rounded to integer for standard 0/1 knapsack dynamic programming.
        """
        urgency_bonus = max(0.0, (24.0 - self.deadline_hours) * 2.0)
        total_utility = (self.base_value * self.priority) + urgency_bonus
        return max(1, int(round(total_utility)))

    @property
    def value_density(self) -> float:
        """Value per unit weight (used in greedy sorting heuristics)."""
        return self.composite_value / max(1, self.weight)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "destination_node": self.destination_node,
            "weight": self.weight,
            "volume": self.volume,
            "priority": self.priority,
            "deadline_hours": self.deadline_hours,
            "base_value": self.base_value,
            "composite_value": self.composite_value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Parcel":
        return cls(
            id=data["id"],
            destination_node=data["destination_node"],
            weight=int(data["weight"]),
            volume=int(data.get("volume", 1)),
            priority=int(data.get("priority", 1)),
            deadline_hours=float(data.get("deadline_hours", 24.0)),
            base_value=float(data.get("base_value", 10.0))
        )


@dataclass
class DeliveryPoint:
    """
    Represents a spatial delivery location (customer location, hub, or street intersection).
    """
    id: int
    name: str
    x: float
    y: float
    is_depot: bool = False
    address: str = ""

    def distance_to(self, other: "DeliveryPoint") -> float:
        """Euclidean distance in kilometers between two spatial coordinates."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "is_depot": self.is_depot,
            "address": self.address
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeliveryPoint":
        return cls(
            id=int(data["id"]),
            name=data["name"],
            x=float(data["x"]),
            y=float(data["y"]),
            is_depot=bool(data.get("is_depot", False)),
            address=data.get("address", "")
        )


@dataclass
class RoadEdge:
    """Represents a navigable road segment between two graph vertices."""
    u: int
    v: int
    distance: float
    road_name: str = ""
    speed_kmh: float = 40.0


@dataclass
class PackingPlan:
    """
    Result of the Dynamic Programming Knapsack vehicle packing optimization.
    """
    selected_parcels: List[Parcel]
    unselected_parcels: List[Parcel]
    total_weight: int
    total_volume: int
    total_value: int
    weight_capacity: int
    volume_capacity: int
    dp_table: Optional[List[List[int]]] = None
    execution_time_ms: float = 0.0

    @property
    def capacity_utilization_pct(self) -> float:
        return (self.total_weight / max(1, self.weight_capacity)) * 100.0


@dataclass
class DeliveryTrip:
    """
    Complete delivery tour containing route sequence, turn-by-turn road traces, and metrics.
    """
    trip_id: str
    depot_node: int
    visited_nodes: List[int]                     # Sequence of customer stop IDs
    turn_by_turn_path: List[int]                 # Exact node IDs along shortest path edges
    total_distance_km: float
    estimated_travel_time_min: float
    packing_plan: PackingPlan
    node_names: Dict[int, str] = field(default_factory=dict)
    algorithm_used: str = "Dijkstra + Nearest-Neighbor + 2-Opt"
