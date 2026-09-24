"""Unit and integration tests for SpatialReliabilityService and metrics tracking."""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.app.core.metrics import ProcessMetrics, default_metrics
from backend.app.main import create_application
from backend.app.schemas.prediction import (
    CalibrationStatus,
    PredictionRequest,
    PredictionResponse,
    ReasonCode,
    RiskLevel,
    TrustState,
)
from backend.app.schemas.spatial import (
    SpatialReliabilityRequest,
    SpatialReliabilityResponse,
)
from backend.app.services.location_service import ResolvedLocation
from backend.app.services.spatial_reliability_service import SpatialReliabilityService


def test_process_metrics_spatial_tracking():
    """Verify that ProcessMetrics handles record_spatial_request correctly."""
    metrics = ProcessMetrics()
    metrics.record_spatial_request("SUCCESS", 25, 23, 2)
    metrics.record_spatial_request("PARTIAL", 5, 4, 1)

    snap = metrics.snapshot()
    assert "spatial_requests_total" in snap
    assert snap["spatial_requests_total"]["SUCCESS"] == 1
    assert snap["spatial_requests_total"]["PARTIAL"] == 1
    assert snap["spatial_locations_total"] == 30
    assert snap["spatial_valid_locations_total"] == 27
    assert snap["spatial_abstained_locations_total"] == 3

    metrics.reset()
    snap_after = metrics.snapshot()
    assert snap_after["spatial_requests_total"] == {}
    assert snap_after["spatial_locations_total"] == 0


def test_spatial_reliability_service_parallel_execution():
    """Verify that evaluate_spatial evaluates multiple locations in parallel and preserves order."""
    mock_loc_service = MagicMock()
    mock_agent = MagicMock()

    def mock_resolve(name):
        if name == "InvalidCity":
            return None
        return ResolvedLocation(
            original_input=name,
            name=name,
            latitude=28.61,
            longitude=77.20,
            country="India",
        )

    mock_loc_service.resolve.side_effect = mock_resolve

    def mock_analyze(req: PredictionRequest, **kwargs):
        return PredictionResponse(
            location=req.location,
            bust_probability=0.35,
            risk_level=RiskLevel.MEDIUM,
            trust_state=TrustState.HIGH_CONFIDENCE,
            abstain=False,
            reason_codes=[],
            calibration_status=CalibrationStatus.CALIBRATED.value,
            model_version="v3.0.0",
            data_version="2026-03-01",
            confidence_index=0.85,
            uncertainty_pct=15.0,
            ood_score=0.1,
            stability_index=0.9,
            dominant_risk_drivers=["dispersion"],
            decision_mode="ACTIONABLE",
        )

    mock_agent.analyze.side_effect = mock_analyze
    mock_agent.get_weather_data.return_value = None

    service = SpatialReliabilityService(
        location_service=mock_loc_service,
        agent_factory=lambda: mock_agent,
    )

    req = SpatialReliabilityRequest(
        locations=["Delhi", "Mumbai", "InvalidCity", "Delhi"],
        variable="temperature_2m",
        lead_hours=48,
    )

    resp = service.evaluate_spatial(req)

    assert isinstance(resp, SpatialReliabilityResponse)
    assert len(resp.points) == 4
    # Check 1:1 ordering
    assert resp.points[0].location == "Delhi"
    assert resp.points[0].bust_probability == 0.35
    assert not resp.points[0].abstain

    assert resp.points[1].location == "Mumbai"
    assert resp.points[1].bust_probability == 0.35

    assert resp.points[2].location == "InvalidCity"
    assert resp.points[2].abstain is True
    assert resp.points[2].bust_probability is None

    assert resp.points[3].location == "Delhi"
    assert resp.points[3].bust_probability == 0.35

    assert resp.summary.total_locations == 4
    assert resp.summary.available_locations == 3
    assert resp.summary.abstained_locations == 1


def test_spatial_endpoint_via_client():
    """Verify POST /v1/spatial/reliability responds successfully without blocking."""
    app = create_application()
    client = TestClient(app)

    payload = {
        "locations": ["Delhi", "Mumbai"],
        "variable": "temperature_2m",
        "lead_hours": 24,
    }
    response = client.post("/v1/spatial/reliability", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "points" in data
    assert len(data["points"]) == 2
    assert "summary" in data
