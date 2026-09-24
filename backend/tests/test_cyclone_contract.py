"""Unit Tests for Tropical Cyclone Operational Contract (Gate 4 / Phase E).

Verifies:
- CycloneReliabilityOutput schema conformance
- Strict null-safety: Landfall fields evaluate to None when non-landfall
- CycloneIssueFeatures boundaries and validation
- Intensity category and basin enum constants
- Target manifest and historical event catalogue loading and invariants
"""

import pytest
from pydantic import ValidationError

from backend.app.contracts.cyclone_contract import (
    CycloneBasin,
    CycloneCategory,
    CycloneIssueFeatures,
    CycloneReliabilityOutput,
    load_cyclone_event_catalogue,
    load_cyclone_target_manifest,
)


def test_cyclone_reliability_output_valid():
    """Test valid output creation with active landfall fields."""
    output = CycloneReliabilityOutput(
        hazard="CYCLONE",
        track_failure_probability=0.22,
        intensity_failure_probability=0.18,
        rapid_intensification_failure_probability=0.12,
        landfall_location_failure_probability=0.25,
        landfall_timing_failure_probability=0.15,
        conformal_track_uncertainty_radius_km=115.4,
        overall_reliability=0.81,
        evidence=["Track spread 85km at lead +48h", "Basin: BAY_OF_BENGAL"],
        ood=False,
        provenance={"model_version": "CYCLONE_RELIABILITY_V1"},
    )
    assert output.hazard == "CYCLONE"
    assert output.track_failure_probability == 0.22
    assert output.landfall_location_failure_probability == 0.25
    assert output.conformal_track_uncertainty_radius_km == 115.4
    assert output.overall_reliability == 0.81


def test_non_landfall_null_safety():
    """Test that landfall fields default to None for non-landfall tracks."""
    output = CycloneReliabilityOutput(
        hazard="CYCLONE",
        track_failure_probability=0.15,
        intensity_failure_probability=0.20,
        rapid_intensification_failure_probability=0.08,
        landfall_location_failure_probability=None,
        landfall_timing_failure_probability=None,
        conformal_track_uncertainty_radius_km=95.0,
    )
    assert output.landfall_location_failure_probability is None
    assert output.landfall_timing_failure_probability is None
    assert output.track_failure_probability is not None


def test_hazard_name_invariant():
    """Test that hazard must be 'CYCLONE'."""
    with pytest.raises(ValidationError):
        CycloneReliabilityOutput(
            hazard="PRECIPITATION",  # Invalid for cyclone specialist
            track_failure_probability=0.2,
        )


def test_cyclone_issue_features_validation():
    """Test validation rules and bounds for cyclone issue features."""
    valid_features = CycloneIssueFeatures(
        lead_hours=48,
        basin=CycloneBasin.BAY_OF_BENGAL,
        forecast_lat=18.5,
        forecast_lon=86.2,
        forward_speed_kmh=18.0,
        ensemble_track_spread_km=85.0,
        forecast_max_wind_ms=45.0,
        ensemble_intensity_spread_ms=5.5,
        vertical_wind_shear_ms=12.0,
        forecast_landfall=True,
        distance_to_coast_km=140.0,
    )
    assert valid_features.lead_hours == 48
    assert valid_features.basin == CycloneBasin.BAY_OF_BENGAL
    assert valid_features.forecast_landfall is True

    # Negative spread should raise ValidationError
    with pytest.raises(ValidationError):
        CycloneIssueFeatures(
            lead_hours=48,
            basin=CycloneBasin.BAY_OF_BENGAL,
            forecast_lat=18.5,
            forecast_lon=86.2,
            ensemble_track_spread_km=-10.0,
            forecast_max_wind_ms=30.0,
            ensemble_intensity_spread_ms=5.0,
        )


def test_load_manifest_and_catalogue_valid():
    """Verify cyclone target manifest and event catalogue load and validate invariants."""
    manifest = load_cyclone_target_manifest()
    assert manifest["hazard"] == "CYCLONE"
    assert manifest["gate"] == "Gate 4"
    assert len(manifest["targets"]) >= 5

    catalogue = load_cyclone_event_catalogue()
    assert catalogue["hazard"] == "CYCLONE"
    assert len(catalogue["cyclones"]) >= 8
    # Verify canonical cyclone FANI is present
    cyclone_names = [c["cyclone_name"] for c in catalogue["cyclones"]]
    assert "FANI" in cyclone_names
    assert "AMPHAN" in cyclone_names
    assert "BIPARJOY" in cyclone_names
