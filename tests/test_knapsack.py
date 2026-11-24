"""Unit tests for 0/1 Knapsack Dynamic Programming."""
import pytest
from src.models import Parcel
from src.knapsack_dp import knapsack_01_dp, knapsack_2d_dp


@pytest.fixture
def classic_knapsack_items():
    # Weight capacity: 10
    # Items: (weight, value) -> (2, 6), (2, 10), (3, 12), (4, 16), (5, 22)
    # Optimal for W=10: items with weight 2(10) + 3(12) + 5(22) = wt 10, val 44
    return [
        Parcel(id="P1", destination_node=1, weight=2, base_value=6, priority=1, deadline_hours=24), # val=6
        Parcel(id="P2", destination_node=2, weight=2, base_value=10, priority=1, deadline_hours=24), # val=10
        Parcel(id="P3", destination_node=3, weight=3, base_value=12, priority=1, deadline_hours=24), # val=12
        Parcel(id="P4", destination_node=4, weight=4, base_value=16, priority=1, deadline_hours=24), # val=16
        Parcel(id="P5", destination_node=5, weight=5, base_value=22, priority=1, deadline_hours=24), # val=22
    ]


def test_knapsack_optimal_value(classic_knapsack_items):
    plan = knapsack_01_dp(classic_knapsack_items, weight_capacity=10, include_table=True)
    # Check optimal value
    assert plan.total_value == 44
    assert plan.total_weight <= 10
    assert len(plan.selected_parcels) == 3
    selected_ids = {p.id for p in plan.selected_parcels}
    assert selected_ids == {"P2", "P3", "P5"}
    assert plan.dp_table is not None
    assert len(plan.dp_table) == 6
    assert len(plan.dp_table[0]) == 11


def test_knapsack_zero_capacity(classic_knapsack_items):
    plan = knapsack_01_dp(classic_knapsack_items, weight_capacity=0)
    assert plan.total_value == 0
    assert len(plan.selected_parcels) == 0
    assert len(plan.unselected_parcels) == 5


def test_knapsack_oversized_item():
    items = [Parcel(id="Huge", destination_node=1, weight=100, base_value=500, priority=1, deadline_hours=24)]
    plan = knapsack_01_dp(items, weight_capacity=50)
    assert plan.total_value == 0
    assert len(plan.selected_parcels) == 0


def test_knapsack_2d_dp():
    # Items with weight and volume constraints
    items = [
        Parcel(id="P1", destination_node=1, weight=4, volume=5, base_value=30, priority=1, deadline_hours=24),
        Parcel(id="P2", destination_node=2, weight=5, volume=2, base_value=40, priority=1, deadline_hours=24),
        Parcel(id="P3", destination_node=3, weight=2, volume=6, base_value=20, priority=1, deadline_hours=24)
    ]
    # W=6, V=7 -> Can pick P1 (4, 5) or P2 (5, 2) or P3 (2, 6)
    # P2 has value 40, fits in 6 and 7.
    plan = knapsack_2d_dp(items, weight_capacity=6, volume_capacity=7)
    assert plan.total_weight <= 6
    assert plan.total_volume <= 7
    assert plan.total_value == 40
