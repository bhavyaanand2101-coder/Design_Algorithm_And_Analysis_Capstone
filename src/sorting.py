"""
sorting.py
Phase 2: Parcel Prioritization & Sorting Algorithms.
Implements QuickSort, MergeSort, and Multi-Criteria Prioritization for parcels.
Includes instrumentation for comparison count and execution runtime benchmarking.
"""

import time
import random
from typing import List, Tuple, Callable, Any, Optional
from src.models import Parcel


class SortingMetrics:
    """Tracks algorithmic metrics: comparisons, swaps/moves, and elapsed time."""
    def __init__(self, algorithm: str):
        self.algorithm = algorithm
        self.comparisons = 0
        self.swaps = 0
        self.time_seconds = 0.0

    def to_dict(self):
        return {
            "algorithm": self.algorithm,
            "comparisons": self.comparisons,
            "swaps": self.swaps,
            "time_ms": self.time_seconds * 1000.0
        }


def default_parcel_comparator(p1: Parcel, p2: Parcel) -> int:
    """
    Courier Business Priority Comparator:
    1. Primary Key: Deadline (Ascending - earlier deadline must be delivered first)
    2. Secondary Key: Priority Tier (Descending - Higher priority precedes lower)
    3. Tertiary Key: Value Density (Descending - higher utility per kg first)

    Returns:
        -1 if p1 should precede p2 (p1 < p2 in sort order)
         1 if p2 should precede p1 (p1 > p2 in sort order)
         0 if equivalent
    """
    # 1. Deadline comparison (tolerance of 15 mins / 0.25 hr)
    if abs(p1.deadline_hours - p2.deadline_hours) > 0.25:
        return -1 if p1.deadline_hours < p2.deadline_hours else 1

    # 2. Priority tier comparison (5 = highest)
    if p1.priority != p2.priority:
        return -1 if p1.priority > p2.priority else 1

    # 3. Value density comparison
    if abs(p1.value_density - p2.value_density) > 1e-4:
        return -1 if p1.value_density > p2.value_density else 1

    return 0


# =====================================================================
# MERGESORT IMPLEMENTATION (Stable, O(n log n))
# =====================================================================

def merge_sort(
    parcels: List[Parcel],
    comparator: Callable[[Parcel, Parcel], int] = default_parcel_comparator,
    metrics: Optional[SortingMetrics] = None
) -> List[Parcel]:
    """
    Stable Divide-and-Conquer MergeSort implementation for Parcel objects.
    Guaranteed Worst-Case Time Complexity: O(n log n)
    Auxiliary Space: O(n)
    """
    if len(parcels) <= 1:
        return list(parcels)

    mid = len(parcels) // 2
    left = merge_sort(parcels[:mid], comparator, metrics)
    right = merge_sort(parcels[mid:], comparator, metrics)

    return _merge(left, right, comparator, metrics)


def _merge(
    left: List[Parcel],
    right: List[Parcel],
    comparator: Callable[[Parcel, Parcel], int],
    metrics: Optional[SortingMetrics]
) -> List[Parcel]:
    merged = []
    i = j = 0

    while i < len(left) and j < len(right):
        if metrics:
            metrics.comparisons += 1
        # If left <= right, keep left (ensures stability)
        if comparator(left[i], right[j]) <= 0:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
        if metrics:
            metrics.swaps += 1

    while i < len(left):
        merged.append(left[i])
        i += 1
        if metrics:
            metrics.swaps += 1

    while j < len(right):
        merged.append(right[j])
        j += 1
        if metrics:
            metrics.swaps += 1

    return merged


# =====================================================================
# QUICKSORT IMPLEMENTATION (In-Place / Median-of-Three Partitioning)
# =====================================================================

def quick_sort(
    parcels: List[Parcel],
    comparator: Callable[[Parcel, Parcel], int] = default_parcel_comparator,
    metrics: Optional[SortingMetrics] = None,
    pivot_strategy: str = "median3"
) -> List[Parcel]:
    """
    In-place Partition QuickSort with Median-of-Three pivot selection to prevent O(n^2) worst case.
    Average Time Complexity: O(n log n)
    Space Complexity: O(log n) call stack
    """
    arr = list(parcels)
    _quicksort_helper(arr, 0, len(arr) - 1, comparator, metrics, pivot_strategy)
    return arr


def _quicksort_helper(
    arr: List[Parcel],
    low: int,
    high: int,
    comparator: Callable[[Parcel, Parcel], int],
    metrics: Optional[SortingMetrics],
    pivot_strategy: str
):
    if low < high:
        p_index = _partition(arr, low, high, comparator, metrics, pivot_strategy)
        _quicksort_helper(arr, low, p_index - 1, comparator, metrics, pivot_strategy)
        _quicksort_helper(arr, p_index + 1, high, comparator, metrics, pivot_strategy)


def _select_pivot_index(arr: List[Parcel], low: int, high: int, comparator: Callable, metrics: Optional[SortingMetrics], strategy: str) -> int:
    if strategy == "first":
        return low
    elif strategy == "random":
        return random.randint(low, high)
    else:  # "median3"
        mid = (low + high) // 2
        # Sort low, mid, high to find median
        triplet = [(low, arr[low]), (mid, arr[mid]), (high, arr[high])]
        # Bubble sort 3 items
        for i in range(2):
            for j in range(2 - i):
                if metrics:
                    metrics.comparisons += 1
                if comparator(triplet[j][1], triplet[j+1][1]) > 0:
                    triplet[j], triplet[j+1] = triplet[j+1], triplet[j]
        return triplet[1][0]


def _partition(
    arr: List[Parcel],
    low: int,
    high: int,
    comparator: Callable[[Parcel, Parcel], int],
    metrics: Optional[SortingMetrics],
    pivot_strategy: str
) -> int:
    pivot_idx = _select_pivot_index(arr, low, high, comparator, metrics, pivot_strategy)
    # Move pivot to high
    arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
    if metrics:
        metrics.swaps += 1

    pivot = arr[high]
    i = low - 1

    for j in range(low, high):
        if metrics:
            metrics.comparisons += 1
        if comparator(arr[j], pivot) <= 0:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
            if metrics:
                metrics.swaps += 1

    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    if metrics:
        metrics.swaps += 1
    return i + 1


# =====================================================================
# PUBLIC SORTING API & BENCHMARK RUNNER
# =====================================================================

def sort_parcels(
    parcels: List[Parcel],
    algorithm: str = "quicksort",
    comparator: Callable[[Parcel, Parcel], int] = default_parcel_comparator
) -> Tuple[List[Parcel], SortingMetrics]:
    """
    Sorts a list of parcels using the requested algorithm.
    Supported algorithms: 'quicksort', 'mergesort', 'timsort'
    
    Returns:
        Tuple of (sorted_parcels, SortingMetrics)
    """
    algo_clean = algorithm.lower().strip()
    metrics = SortingMetrics(algo_clean)

    start_t = time.perf_counter()
    if algo_clean == "quicksort":
        result = quick_sort(parcels, comparator=comparator, metrics=metrics)
    elif algo_clean == "mergesort":
        result = merge_sort(parcels, comparator=comparator, metrics=metrics)
    elif algo_clean == "timsort":
        # Python built-in sort (TimSort)
        from functools import cmp_to_key
        def counting_cmp(a, b):
            metrics.comparisons += 1
            return comparator(a, b)
        result = sorted(parcels, key=cmp_to_key(counting_cmp))
    else:
        raise ValueError(f"Unknown sorting algorithm: {algorithm}. Choose 'quicksort', 'mergesort', or 'timsort'.")

    metrics.time_seconds = time.perf_counter() - start_t
    return result, metrics
