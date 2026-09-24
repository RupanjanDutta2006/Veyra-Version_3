"""Unit tests for 25-Station Spatial Graph Topology (Gate 8 / Phase I)."""

import pytest
from backend.app.contracts.spatial_contract import (
    MacroRegion,
    load_spatial_network_topology,
)
from backend.app.builder2.spatial_reliability_engine import (
    SpatialReliabilitySpecialist,
    haversine_distance_km,
)


def test_spatial_network_topology_count_and_regions():
    """Verify exactly 25 canonical stations across 7 macro-regions."""
    topo = load_spatial_network_topology()
    assert topo["station_count"] == 25
    assert len(topo["stations"]) == 25
    assert len(topo["regions"]) == 7

    regions_in_nodes = set(s["region"] for s in topo["stations"])
    for reg in MacroRegion:
        assert reg.value in regions_in_nodes


def test_spatial_station_coordinates_and_bounds():
    """Verify all 25 stations have valid geographic coordinates and positive elevations."""
    topo = load_spatial_network_topology()
    for s in topo["stations"]:
        assert 6.0 <= s["latitude"] <= 38.0
        assert 68.0 <= s["longitude"] <= 98.0
        assert s["elevation_m"] >= 0.0
        assert len(s["synoptic_corridor"]) > 0


def test_spatial_distance_matrix_properties():
    """Verify distance matrix is symmetric, has zero diagonal, and satisfies triangle inequality."""
    specialist = SpatialReliabilitySpecialist()
    dist = specialist.dist_matrix
    n = specialist.n_stations

    assert n == 25
    assert dist.shape == (25, 25)

    # Diagonal is zero
    for i in range(n):
        assert dist[i, i] == 0.0

    # Symmetry
    for i in range(n):
        for j in range(i + 1, n):
            assert abs(dist[i, j] - dist[j, i]) < 1e-6

    # Triangle inequality on sample triplets
    for i in range(0, n, 5):
        for j in range(1, n, 5):
            for k in range(2, n, 5):
                assert dist[i, k] <= dist[i, j] + dist[j, k] + 1e-4


def test_spatial_adjacency_matrix_properties():
    """Verify spatial adjacency matrix has unit diagonal and non-negative weights."""
    specialist = SpatialReliabilitySpecialist()
    adj = specialist.adj_matrix
    n = specialist.n_stations

    for i in range(n):
        assert adj[i, i] == 1.0
        for j in range(n):
            assert 0.0 < adj[i, j] <= 1.0
