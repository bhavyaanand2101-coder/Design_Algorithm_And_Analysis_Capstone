"""
knapsack_dp.py
Phase 2: Box Filling & Capacity Optimization via 0/1 Knapsack Dynamic Programming.
Computes the optimal packing plan that maximizes delivery utility value within vehicle payload limits.
Provides full DP table reconstruction, item backtracking, and dual-constraint (weight + volume) support.
"""

import time
from typing import List, Tuple, Dict, Any, Optional
from src.models import Parcel, PackingPlan


def knapsack_01_dp(
    parcels: List[Parcel],
    weight_capacity: int,
    volume_capacity: Optional[int] = None,
    include_table: bool = True
) -> PackingPlan:
    """
    Solves the 0/1 Knapsack problem using Dynamic Programming.
    
    Recurrence Relation:
        DP[i][w] = DP[i-1][w]                                    if weight[i-1] > w
        DP[i][w] = max(DP[i-1][w], DP[i-1][w - weight[i-1]] + value[i-1]) otherwise
        
    Time Complexity: O(N * W) where N = number of parcels, W = weight capacity.
    Space Complexity: O(N * W) for complete table reconstruction and backtracking.
    
    Args:
        parcels: List of candidate parcels
        weight_capacity: Maximum total weight vehicle can carry (in kg)
        volume_capacity: Optional maximum volume capacity (in liters)
        include_table: Whether to store the complete 2D table in the result
        
    Returns:
        PackingPlan containing selected parcels, remaining queue, total metrics, and DP table.
    """
    start_t = time.perf_counter()
    n = len(parcels)
    W = max(0, int(weight_capacity))

    if n == 0 or W == 0:
        return PackingPlan(
            selected_parcels=[],
            unselected_parcels=list(parcels),
            total_weight=0,
            total_volume=0,
            total_value=0,
            weight_capacity=W,
            volume_capacity=volume_capacity or 0,
            dp_table=[[0] * (W + 1)] if include_table else None,
            execution_time_ms=(time.perf_counter() - start_t) * 1000.0
        )

    # 1. Initialize DP table of dimensions (N + 1) x (W + 1)
    # dp[i][w] represents max value attainable with first i items and capacity w
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    # 2. Populate DP Table
    for i in range(1, n + 1):
        p = parcels[i - 1]
        wt = p.weight
        val = p.composite_value

        for w in range(W + 1):
            if wt <= w:
                include_val = dp[i - 1][w - wt] + val
                exclude_val = dp[i - 1][w]
                dp[i][w] = include_val if include_val > exclude_val else exclude_val
            else:
                dp[i][w] = dp[i - 1][w]

    # 3. Backtrack to find exact selected parcels
    selected_indices = set()
    current_w = W
    for i in range(n, 0, -1):
        # If value changed from previous row, item i-1 was included
        if dp[i][current_w] != dp[i - 1][current_w]:
            selected_indices.add(i - 1)
            current_w -= parcels[i - 1].weight

    selected: List[Parcel] = []
    unselected: List[Parcel] = []
    for idx, p in enumerate(parcels):
        if idx in selected_indices:
            selected.append(p)
        else:
            unselected.append(p)

    total_weight = sum(p.weight for p in selected)
    total_volume = sum(p.volume for p in selected)
    total_value = dp[n][W]
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    return PackingPlan(
        selected_parcels=selected,
        unselected_parcels=unselected,
        total_weight=total_weight,
        total_volume=total_volume,
        total_value=total_value,
        weight_capacity=W,
        volume_capacity=volume_capacity or sum(p.volume for p in parcels),
        dp_table=dp if include_table else None,
        execution_time_ms=elapsed_ms
    )


def knapsack_2d_dp(
    parcels: List[Parcel],
    weight_capacity: int,
    volume_capacity: int
) -> PackingPlan:
    """
    Solves Multi-dimensional 2D 0/1 Knapsack (Weight AND Volume constraints).
    Time Complexity: O(N * W * V)
    Space Complexity: O(W * V) using rolling 2D DP array.
    """
    start_t = time.perf_counter()
    n = len(parcels)
    W = max(0, int(weight_capacity))
    V = max(0, int(volume_capacity))

    # dp[w][v] = max value with weight <= w and volume <= v
    dp = [[0] * (V + 1) for _ in range(W + 1)]
    # parent tracking for backtracking: item_chosen[i][w][v]
    chosen = [[[False] * (V + 1) for _ in range(W + 1)] for _ in range(n)]

    for i in range(n):
        p = parcels[i]
        pw, pv, pval = p.weight, p.volume, p.composite_value
        for w in range(W, pw - 1, -1):
            for v in range(V, pv - 1, -1):
                if dp[w - pw][v - pv] + pval > dp[w][v]:
                    dp[w][v] = dp[w - pw][v - pv] + pval
                    chosen[i][w][v] = True

    # Backtracking for 2D knapsack
    curr_w, curr_v = W, V
    selected_indices = set()
    for i in range(n - 1, -1, -1):
        if chosen[i][curr_w][curr_v]:
            selected_indices.add(i)
            curr_w -= parcels[i].weight
            curr_v -= parcels[i].volume

    selected = [p for idx, p in enumerate(parcels) if idx in selected_indices]
    unselected = [p for idx, p in enumerate(parcels) if idx not in selected_indices]

    return PackingPlan(
        selected_parcels=selected,
        unselected_parcels=unselected,
        total_weight=sum(p.weight for p in selected),
        total_volume=sum(p.volume for p in selected),
        total_value=dp[W][V],
        weight_capacity=W,
        volume_capacity=V,
        execution_time_ms=(time.perf_counter() - start_t) * 1000.0
    )


def render_dp_table_snippet(dp_table: List[List[int]], parcels: List[Parcel], max_cols: int = 15) -> str:
    """
    Renders an ASCII snippet of the DP table for reports, demonstrations, and evidence.
    """
    if not dp_table:
        return "No DP table provided."

    rows = len(dp_table)
    cols = min(len(dp_table[0]), max_cols + 1)

    lines = []
    lines.append(f"DP Table Snippet: {rows - 1} Parcels x Capacity 0..{cols - 1}")
    header = f"{'Item / W':<16} | " + " | ".join(f"{w:>4}" for w in range(cols))
    lines.append(header)
    lines.append("-" * len(header))

    # Base case row
    row0 = f"{'0 (Init)':<16} | " + " | ".join(f"{dp_table[0][w]:>4}" for w in range(cols))
    lines.append(row0)

    for i in range(1, rows):
        p = parcels[i - 1]
        label = f"{p.id} (w={p.weight},v={p.composite_value})"
        row_str = f"{label:<16} | " + " | ".join(f"{dp_table[i][w]:>4}" for w in range(cols))
        lines.append(row_str)

    if len(dp_table[0]) > cols:
        lines.append(f"... (Table truncated at weight capacity {cols-1} of {len(dp_table[0])-1})")

    return "\n".join(lines)
