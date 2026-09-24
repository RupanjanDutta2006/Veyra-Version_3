"""Unit tests for Monsoon and Low-Pressure-System Contract (Gate 5 / Phase F)."""

import pytest
from pydantic import ValidationError

from backend.app.contracts.monsoon_contract import (
    MonsoonIssueFeatures,
    MonsoonRegimeState,
    MonsoonReliabilityOutput,
    MonsoonSystemType,
    load_monsoon_event_catalogue,
    load_monsoon_target_manifest,
)


def test_monsoon_enums():
    """Verify supported system types and regime states."""
    assert MonsoonSystemType.LOW_PRESSURE_AREA == "LOW_PRESSURE_AREA"
    assert MonsoonSystemType.DEPRESSION == "DEPRESSION"
    assert MonsoonSystemType.DEEP_DEPRESSION == "DEEP_DEPRESSION"
    assert MonsoonSystemType.MONSOON_DEPRESSION == "MONSOON_DEPRESSION"

    assert MonsoonRegimeState.ACTIVE_MONSOON == "ACTIVE_MONSOON"
    assert MonsoonRegimeState.BREAK_MONSOON == "BREAK_MONSOON"
    assert MonsoonRegimeState.NORMAL == "NORMAL"
    assert MonsoonRegimeState.TRANSITION_TO_ACTIVE == "TRANSITION_TO_ACTIVE"
    assert MonsoonRegimeState.TRANSITION_TO_BREAK == "TRANSITION_TO_BREAK"


def test_monsoon_issue_features_valid():
    """Verify valid construction of issue-time features."""
    features = MonsoonIssueFeatures(
        lead_hours=48,
        system_type=MonsoonSystemType.MONSOON_DEPRESSION,
        regime_state=MonsoonRegimeState.ACTIVE_MONSOON,
        forecast_lat=21.5,
        forecast_lon=86.2,
        central_pressure_hpa=992.0,
        pressure_tendency_hpa_24h=-6.0,
        forward_speed_kmh=18.0,
        ensemble_track_spread_km=85.0,
        vorticity_850hpa_s=1.5e-4,
        vertical_wind_shear_ms=12.0,
        moisture_flux_transport_kg_ms=650.0,
        forecast_rainfall_max_24h_mm=120.0,
        ensemble_rainfall_spread_mm=35.0,
        monsoon_trough_displacement_km=-40.0,
        offshore_trough_present=True,
    )
    assert features.lead_hours == 48
    assert features.system_type == MonsoonSystemType.MONSOON_DEPRESSION
    assert features.regime_state == MonsoonRegimeState.ACTIVE_MONSOON
    assert features.forecast_lat == 21.5
    assert features.central_pressure_hpa == 992.0
    assert features.offshore_trough_present is True


def test_monsoon_issue_features_bounds_validation():
    """Verify bounds enforcement on physical fields."""
    with pytest.raises(ValidationError):
        # Latitude out of bounds (> 38.0)
        MonsoonIssueFeatures(
            lead_hours=24,
            system_type=MonsoonSystemType.DEPRESSION,
            regime_state=MonsoonRegimeState.NORMAL,
            forecast_lat=45.0,
            forecast_lon=80.0,
            ensemble_track_spread_km=50.0,
            forecast_rainfall_max_24h_mm=50.0,
            ensemble_rainfall_spread_mm=10.0,
        )

    with pytest.raises(ValidationError):
        # Negative ensemble track spread
        MonsoonIssueFeatures(
            lead_hours=24,
            system_type=MonsoonSystemType.DEPRESSION,
            regime_state=MonsoonRegimeState.NORMAL,
            forecast_lat=20.0,
            forecast_lon=80.0,
            ensemble_track_spread_km=-10.0,
            forecast_rainfall_max_24h_mm=50.0,
            ensemble_rainfall_spread_mm=10.0,
        )


def test_monsoon_reliability_output_valid():
    """Verify valid construction of decomposed output schema."""
    output = MonsoonReliabilityOutput(
        hazard="MONSOON_LPS",
        system_location_failure_probability=0.22,
        propagation_speed_failure_probability=0.15,
        deepening_failure_probability=0.18,
        rainfall_placement_failure_probability=0.25,
        rainfall_intensity_failure_probability=0.28,
        regime_transition_failure_probability=0.12,
        overall_reliability=0.80,
        evidence=["Active monsoon spell with depression over Odisha"],
        ood=False,
        provenance={"model": "MONSOON_RELIABILITY_V1"},
    )
    assert output.hazard == "MONSOON_LPS"
    assert output.system_location_failure_probability == 0.22
    assert output.overall_reliability == 0.80


def test_monsoon_reliability_output_hazard_invariant():
    """Verify hazard field must strictly be 'MONSOON_LPS'."""
    with pytest.raises(ValidationError):
        MonsoonReliabilityOutput(hazard="CYCLONE")


def test_load_manifest_and_catalogue():
    """Verify disk loaders load and parse manifest and catalogue artifacts."""
    manifest = load_monsoon_target_manifest()
    assert manifest["hazard_family"] == "MONSOON_LPS"
    assert len(manifest["targets"]) == 6

    catalogue = load_monsoon_event_catalogue()
    assert catalogue["hazard_family"] == "MONSOON_LPS"
    assert len(catalogue["events"]) >= 6
