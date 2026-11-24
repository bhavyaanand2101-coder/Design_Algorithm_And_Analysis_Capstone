"""Unit tests for sorting algorithms."""
import pytest
from src.models import Parcel
from src.sorting import quick_sort, merge_sort, sort_parcels, default_parcel_comparator


@pytest.fixture
def sample_parcels():
    return [
        Parcel(id="P1", destination_node=1, weight=5, priority=2, deadline_hours=12.0, base_value=20),
        Parcel(id="P2", destination_node=2, weight=8, priority=5, deadline_hours=2.0, base_value=50),
        Parcel(id="P3", destination_node=3, weight=4, priority=4, deadline_hours=2.0, base_value=35),
        Parcel(id="P4", destination_node=4, weight=7, priority=1, deadline_hours=20.0, base_value=10),
        Parcel(id="P5", destination_node=5, weight=3, priority=5, deadline_hours=1.0, base_value=60)
    ]


def test_quicksort_sorting_order(sample_parcels):
    sorted_p, metrics = sort_parcels(sample_parcels, algorithm="quicksort")
    assert len(sorted_p) == len(sample_parcels)
    # Earliest deadline first: P5 (1.0h) should be first
    assert sorted_p[0].id == "P5"
    # P2 and P3 both have 2.0h, but P2 has priority 5 while P3 has priority 4
    assert sorted_p[1].id == "P2"
    assert sorted_p[2].id == "P3"
    assert sorted_p[-1].id == "P4"  # 20.0h deadline
    assert metrics.comparisons > 0


def test_mergesort_stability(sample_parcels):
    sorted_p, metrics = sort_parcels(sample_parcels, algorithm="mergesort")
    assert [p.id for p in sorted_p] == ["P5", "P2", "P3", "P1", "P4"]
    assert metrics.comparisons > 0


def test_empty_and_single_element():
    res, _ = sort_parcels([], algorithm="quicksort")
    assert res == []

    p_single = [Parcel(id="P0", destination_node=1, weight=5)]
    res2, _ = sort_parcels(p_single, algorithm="mergesort")
    assert len(res2) == 1
