"""Unit tests for TSP route approximation and exact algorithms."""
import pytest
from src.tsp_approx import tsp_nearest_neighbor, tsp_2opt, tsp_exact_bruteforce, calculate_tour_length


@pytest.fixture
def distance_matrix():
    # 4 nodes: 0 (depot), 1, 2, 3
    # Distances symmetric
    coords = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 0)}
    dist = {}
    for i in coords:
        for j in coords:
            if i == j:
                dist[(i, j)] = 0.0
            else:
                dist[(i, j)] = ((coords[i][0] - coords[j][0])**2 + (coords[i][1] - coords[j][1])**2)**0.5
    return dist


def test_nearest_neighbor_tour_validity(distance_matrix):
    stops = [0, 1, 2, 3]
    tour, length, _ = tsp_nearest_neighbor(start_node=0, stops=stops, dist_matrix=distance_matrix)
    # Starts and ends at depot
    assert tour[0] == 0
    assert tour[-1] == 0
    # Visits all nodes
    assert set(tour) == {0, 1, 2, 3}
    assert len(tour) == 5  # [0, a, b, c, 0]
    assert length > 0


def test_2opt_refinement(distance_matrix):
    # Cross tour: 0 -> 2 -> 1 -> 3 -> 0 (crossed diagonals)
    suboptimal_tour = [0, 2, 1, 3, 0]
    initial_length = calculate_tour_length(suboptimal_tour, distance_matrix)

    opt_tour, opt_length, swaps, _ = tsp_2opt(suboptimal_tour, distance_matrix)
    # 2-opt should untangle the crossed edges
    assert opt_length <= initial_length
    assert set(opt_tour) == {0, 1, 2, 3}
    assert opt_tour[0] == 0 and opt_tour[-1] == 0


def test_exact_bruteforce_vs_approximation(distance_matrix):
    stops = [0, 1, 2, 3]
    exact_tour, exact_len, _ = tsp_exact_bruteforce(0, stops, distance_matrix)
    nn_tour, nn_len, _ = tsp_nearest_neighbor(0, stops, distance_matrix)
    opt_tour, opt_len, _, _ = tsp_2opt(nn_tour, distance_matrix)

    # Optimal perimeter of square is 4.0
    assert round(exact_len, 2) == 4.0
    assert opt_len >= exact_len - 1e-5
    # Verify approximation ratio <= 1.5
    ratio = opt_len / exact_len
    assert ratio <= 1.5
