"""
generate_datasets.py
Generates realistic, reproducible synthetic benchmark datasets:
- Medium Dataset (35 parcels, 15 delivery nodes)
- Large Dataset (100 parcels, 30 delivery nodes)
- Metropolitan City Scenario (50 parcels, 20 distinct urban zones)
"""

import json
import random

def generate_dataset(
    name: str,
    num_nodes: int,
    num_parcels: int,
    vehicle_capacity_weight: int,
    vehicle_capacity_volume: int,
    output_path: str,
    seed: int = 42
):
    random.seed(seed)
    # Generate nodes on a 25km x 25km urban grid
    nodes = []
    depot_x, depot_y = 12.5, 12.5
    nodes.append({
        "id": 0,
        "name": "Central Logistics Hub",
        "x": depot_x,
        "y": depot_y,
        "is_depot": True,
        "address": "Hub 0, Gateway Ave"
    })

    district_names = [
        "Financial District", "Harbor Point", "Silicon Alley", "University Campus",
        "Westend Mall", "Metro General Hospital", "Civic Center", "Industrial Park",
        "Greenwood Residential", "Riverfront Esplanade", "Highland Heights",
        "Airport Cargo Hub", "Lakeside Estates", "Tech Corridor", "Old Town Plaza",
        "Commerce Square", "Suburban North", "South Gate", "Sunset Boulevard",
        "Pineview Gardens", "Medical Research Center", "Eastside Terminal"
    ]

    for i in range(1, num_nodes):
        name_str = district_names[i % len(district_names)] + f" #{i}"
        nodes.append({
            "id": i,
            "name": name_str,
            "x": round(random.uniform(1.0, 24.0), 2),
            "y": round(random.uniform(1.0, 24.0), 2),
            "is_depot": False,
            "address": f"{random.randint(10, 990)} {name_str}"
        })

    # Generate realistic connected road network edges
    # Connect each node to its 3 nearest neighbors to ensure planar road graph connectivity
    edges = []
    edge_set = set()

    def dist(n1, n2):
        return round(((n1["x"] - n2["x"])**2 + (n1["y"] - n2["y"])**2)**0.5, 2)

    for i in range(num_nodes):
        # find closest neighbors
        candidates = []
        for j in range(num_nodes):
            if i != j:
                candidates.append((dist(nodes[i], nodes[j]), j))
        candidates.sort()

        # Connect to 3-4 closest
        k_neighbors = min(4, len(candidates))
        for d, j in candidates[:k_neighbors]:
            edge_key = tuple(sorted((i, j)))
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                road_types = ["Highway", "Avenue", "Blvd", "Expressway", "Way"]
                edges.append({
                    "u": edge_key[0],
                    "v": edge_key[1],
                    "distance": max(1.0, round(d * 1.15, 2)),  # road factor 1.15x euclidean
                    "road_name": f"{nodes[edge_key[0]]['name'][:8]}-{nodes[edge_key[1]]['name'][:8]} {random.choice(road_types)}"
                })

    # Generate parcels
    parcels = []
    for p_idx in range(1, num_parcels + 1):
        dest = random.randint(1, num_nodes - 1)
        priority = random.choices([1, 2, 3, 4, 5], weights=[0.25, 0.30, 0.25, 0.12, 0.08])[0]
        # tighter deadlines for higher priorities
        if priority >= 4:
            deadline = round(random.uniform(1.0, 4.0), 1)
            base_val = random.randint(40, 90)
        elif priority == 3:
            deadline = round(random.uniform(3.0, 8.0), 1)
            base_val = random.randint(25, 50)
        else:
            deadline = round(random.uniform(6.0, 24.0), 1)
            base_val = random.randint(10, 30)

        weight = random.randint(2, 12)
        volume = random.randint(2, 14)

        parcels.append({
            "id": f"P{p_idx:03d}",
            "destination_node": dest,
            "weight": weight,
            "volume": volume,
            "priority": priority,
            "deadline_hours": deadline,
            "base_value": base_val
        })

    data = {
        "name": name,
        "vehicle_capacity_weight": vehicle_capacity_weight,
        "vehicle_capacity_volume": vehicle_capacity_volume,
        "depot_id": 0,
        "nodes": nodes,
        "edges": edges,
        "parcels": parcels
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {output_path}: {num_nodes} nodes, {len(edges)} edges, {num_parcels} parcels.")


if __name__ == "__main__":
    generate_dataset("Medium Suburban Territory (N=35)", 15, 35, 60, 80, "data/medium_dataset.json", seed=101)
    generate_dataset("Metropolitan City Scenario (N=50)", 20, 50, 75, 100, "data/city_courier_scenario.json", seed=202)
    generate_dataset("Large Commercial Logistics (N=100)", 35, 100, 150, 200, "data/large_dataset.json", seed=303)
