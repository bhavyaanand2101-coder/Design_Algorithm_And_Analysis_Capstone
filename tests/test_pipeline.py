"""Integration tests for end-to-end Courier Planning Pipeline."""
import json
import pytest
from src.graph import RoadNetwork
from src.models import Parcel
from src.pipeline import CourierPlanningEngine


def test_pipeline_on_small_dataset():
    with open("data/small_dataset.json", "r") as f:
        data = json.load(f)

    network = RoadNetwork.from_dict(data)
    parcels = [Parcel.from_dict(p) for p in data["parcels"]]

    engine = CourierPlanningEngine(network)
    results = engine.run_full_pipeline(
        parcels=parcels,
        vehicle_weight_capacity=data["vehicle_capacity_weight"],
        vehicle_volume_capacity=data["vehicle_capacity_volume"],
        sort_algorithm="quicksort",
        apply_2opt=True
    )

    trip = results["delivery_trip"]
    plan = results["packing_plan"]

    assert len(plan.selected_parcels) > 0
    assert plan.total_weight <= data["vehicle_capacity_weight"]
    assert trip.total_distance_km > 0.0
    assert trip.visited_nodes[0] == 0
    assert trip.visited_nodes[-1] == 0
    assert len(trip.turn_by_turn_path) >= len(trip.visited_nodes)
    assert results["runtimes_ms"]["total_pipeline"] > 0
