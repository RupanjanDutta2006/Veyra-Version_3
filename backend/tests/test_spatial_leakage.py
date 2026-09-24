"""Unit tests for Spatial Anti-Leakage Invariants (Gate 8 / Phase I)."""

import pytest
from pydantic import ValidationError

from backend.app.contracts.spatial_contract import SpatialIssueFeatures
from backend.app.builder2.spatial_reliability_engine import SpatialReliabilitySpecialist


def test_spatial_issue_features_strict_predictors():
    """Verify issue features schema only accepts legitimate issue-time predictors."""
    # Forbidden predictors: observed_val, station_error, ground_truth_bust
    features = SpatialIssueFeatures(
        lead_hours=48,
        variable="precipitation",
        station_forecasts={"DELHI": 25.0, "MUMBAI": 45.0},
        station_spreads={"DELHI": 3.0, "MUMBAI": 5.0},
        synoptic_flow_u_ms=5.0,
        synoptic_flow_v_ms=2.0,
    )
    assert not hasattr(features, "observed_val")
    assert not hasattr(features, "station_error")
    assert not hasattr(features, "ground_truth_bust")


def test_spatial_rejection_of_negative_spreads():
    """Verify validation error when negative ensemble spread is provided."""
    with pytest.raises(ValidationError):
        SpatialIssueFeatures(
            lead_hours=24,
            variable="precipitation",
            station_forecasts={"DELHI": 20.0},
            station_spreads={"DELHI": -2.5},
        )


def test_spatial_engine_uses_only_issue_time_inputs():
    """Verify SpatialReliabilitySpecialist executes strictly on issue-time features."""
    specialist = SpatialReliabilitySpecialist()
    stn_fc = {s: 30.0 for s in specialist.station_ids}
    stn_spr = {s: 3.5 for s in specialist.station_ids}

    features = SpatialIssueFeatures(
        lead_hours=72,
        variable="temperature_2m",
        station_forecasts=stn_fc,
        station_spreads=stn_spr,
    )
    output = specialist.predict(features)

    # Output only contains prospective probabilities and evidence, no ground truth
    assert output.hazard == "SPATIAL_NETWORK"
    assert len(output.station_bust_probabilities) == 25
    for p in output.station_bust_probabilities.values():
        assert 0.0 <= p <= 1.0
