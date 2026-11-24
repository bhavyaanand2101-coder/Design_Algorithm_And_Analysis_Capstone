"""Unit tests for Dijkstra's shortest path algorithm."""
import pytest
from src.graph import RoadNetwork
from src.models import DeliveryPoint
from src.dijkstra import dijkstra_shortest_path, reconstruct_path, compute_metric_distance_matrix


@pytest.fixture
def sample_graph():
    net = RoadNetwork("Test Network")
    net.add_node(DeliveryPoint(id=0, name="Depot", x=0, y=0, is_depot=True))
    net.add_node(DeliveryPoint(id=1, name="Point A", x=1, y=0))
    net.add_node(DeliveryPoint(id=2, name="Point B", x=1, y=1))
    net.add_node(DeliveryPoint(id=3, name="Point C", x=0, y=1))

    # Add weighted edges forming a square with diagonal shortcut
    net.add_edge(0, 1, 4.0)
    net.add_edge(1, 2, 2.0)
    net.add_edge(2, 3, 3.0)
    net.add_edge(3, 0, 8.0)
    net.add_edge(0, 2, 5.0)  # Shortcut directly to 2
    return net


def test_dijkstra_shortest_distances(sample_graph):
    dist, pred, _ = dijkstra_shortest_path(sample_graph, 0)
    assert dist[0] == 0.0
    assert dist[1] == 4.0
    # 0 -> 2 direct is 5.0, 0 -> 1 -> 2 is 4 + 2 = 6.0, so direct 5.0 is optimal
    assert dist[2] == 5.0
    # 0 -> 3 via 0 -> 2 -> 3 is 5 + 3 = 8.0 vs 0 -> 3 direct is 8.0
    assert dist[3] == 8.0


def test_path_reconstruction(sample_graph):
    dist, pred, _ = dijkstra_shortest_path(sample_graph, 0)
    path_to_2 = reconstruct_path(pred, 2)
    assert path_to_2 == [0, 2]


def test_metric_matrix_computation(sample_graph):
    dist_mat, path_mat, _ = compute_metric_distance_matrix(sample_graph, [0, 1, 2, 3])
    assert dist_mat[(0, 2)] == 5.0
    assert dist_mat[(2, 0)] == 5.0  # Undirected symmetry
    assert path_mat[(0, 1)] == [0, 1]
