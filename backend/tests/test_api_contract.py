"""Tests for Operational API Contracts, Routing, and Header Propagation (Gate 10 / Phase K)."""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint_contract(client):
    """Verify health endpoint returns 200 with X-Request-ID and system status."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "x-request-id" in response.headers


def test_hazard_trajectory_endpoint_contract(client):
    """Verify hazard trajectory endpoint returns complete ReliabilityState."""
    response = client.get(
        "/v1/hazard/trajectory",
        params={
            "location": "DELHI",
            "variable": "precipitation_mm",
            "lead_hours": 48,
            "base_bust_prob": 0.12,
            "hazard_family": "PRECIPITATION",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "forecast_identity" in data
    assert "provenance" in data
    assert "hazard_curve" in data
    assert len(data["hazard_curve"]) > 0
    assert "survival_curve" in data
    assert "decision_mode" in data


def test_hazard_motifs_endpoint_contract(client):
    """Verify hazard motifs endpoint returns canonical FailureMotifs."""
    response = client.get("/v1/hazard/motifs", params={"hazard_family": "CYCLONE"})
    assert response.status_code == 200
    motifs = response.json()
    assert isinstance(motifs, list)
    if motifs:
        assert "motif_id" in motifs[0]
        assert "hazard_family" in motifs[0]


def test_hazard_episodes_endpoint_contract(client):
    """Verify hazard episodes endpoint returns historical analogs with uncertainty."""
    response = client.get(
        "/v1/hazard/episodes",
        params={"hazard_family": "HEATWAVE", "lead_hours": 48, "top_k": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert "sample_support_count" in data
    assert "analog_uncertainty_score" in data


def test_api_input_validation_contract(client):
    """Verify invalid input parameters trigger 422 Unprocessable Content."""
    # Negative lead_hours violates ge=0
    response = client.get(
        "/v1/hazard/trajectory",
        params={"location": "DELHI", "lead_hours": -12},
    )
    assert response.status_code == 422
