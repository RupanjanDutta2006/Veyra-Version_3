"""Unit tests for Western Disturbance Contract (Gate 6 / Phase G)."""

import pytest
from pydantic import ValidationError

from backend.app.contracts.western_disturbance_contract import (
    WDIssueFeatures,
    WDIntensityClass,
    WDReliabilityOutput,
    WDTerrainRegime,
    WDTroughTilt,
    load_wd_event_catalogue,
    load_wd_target_manifest,
)


def test_western_disturbance_enums():
    """Verify supported intensity classes, terrain regimes, and trough tilts."""
    assert WDIntensityClass.WEAK == "WEAK"
    assert WDIntensityClass.MODERATE == "MODERATE"
    assert WDIntensityClass.SEVERE_ACTIVE == "SEVERE_ACTIVE"

    assert WDTerrainRegime.HIMALAYAN_HIGH_ALTITUDE == "HIMALAYAN_HIGH_ALTITUDE"
    assert WDTerrainRegime.FOOTHILL_SUB_HIMALAYAN == "FOOTHILL_SUB_HIMALAYAN"
    assert WDTerrainRegime.INDO_GANGETIC_PLAINS == "INDO_GANGETIC_PLAINS"

    assert WDTroughTilt.POSITIVE == "POSITIVE"
    assert WDTroughTilt.NEUTRAL == "NEUTRAL"
    assert WDTroughTilt.NEGATIVE == "NEGATIVE"


def test_western_disturbance_issue_features_valid():
    """Verify valid construction of issue-time features."""
    features = WDIssueFeatures(
        lead_hours=48,
        intensity_class=WDIntensityClass.SEVERE_ACTIVE,
        terrain_regime=WDTerrainRegime.HIMALAYAN_HIGH_ALTITUDE,
        forecast_lat=34.2,
        forecast_lon=74.8,
        subtropical_jet_speed_ms=75.0,
        jet_core_lat_displacement_deg=-1.5,
        trough_depth_500hpa_gpm=5480.0,
        trough_tilt=WDTroughTilt.NEGATIVE,
        induced_low_present=True,
        ensemble_trough_spread_km=65.0,
        forecast_precip_max_24h_mm=85.0,
        ensemble_precip_spread_mm=22.0,
        forecast_duration_hours=48.0,
        freezing_level_m=2400.0,
        surface_temp_celsius=1.2,
        has_high_altitude_obs=True,
    )
    assert features.lead_hours == 48
    assert features.intensity_class == WDIntensityClass.SEVERE_ACTIVE
    assert features.terrain_regime == WDTerrainRegime.HIMALAYAN_HIGH_ALTITUDE
    assert features.trough_tilt == WDTroughTilt.NEGATIVE
    assert features.induced_low_present is True
    assert features.has_high_altitude_obs is True


def test_western_disturbance_issue_features_bounds_validation():
    """Verify bounds enforcement on physical fields."""
    with pytest.raises(ValidationError):
        # Latitude out of bounds (> 38.0)
        WDIssueFeatures(
            lead_hours=24,
            intensity_class=WDIntensityClass.MODERATE,
            terrain_regime=WDTerrainRegime.INDO_GANGETIC_PLAINS,
            forecast_lat=42.0,
            forecast_lon=75.0,
            ensemble_trough_spread_km=40.0,
            forecast_precip_max_24h_mm=30.0,
            ensemble_precip_spread_mm=10.0,
        )

    with pytest.raises(ValidationError):
        # Negative ensemble trough spread
        WDIssueFeatures(
            lead_hours=24,
            intensity_class=WDIntensityClass.MODERATE,
            terrain_regime=WDTerrainRegime.INDO_GANGETIC_PLAINS,
            forecast_lat=30.0,
            forecast_lon=75.0,
            ensemble_trough_spread_km=-15.0,
            forecast_precip_max_24h_mm=30.0,
            ensemble_precip_spread_mm=10.0,
        )


def test_western_disturbance_reliability_output_valid():
    """Verify valid construction of decomposed output schema."""
    output = WDReliabilityOutput(
        hazard="WESTERN_DISTURBANCE",
        arrival_failure_probability=0.20,
        track_location_failure_probability=0.18,
        precipitation_amount_failure_probability=0.24,
        precipitation_displacement_failure_probability=0.16,
        duration_failure_probability=0.12,
        rain_snow_partition_failure_probability=0.28,
        overall_reliability=0.82,
        evidence=["Active WD with negative tilt trough and high snowfall potential"],
        ood=False,
        provenance={"model": "WD_RELIABILITY_V1"},
    )
    assert output.hazard == "WESTERN_DISTURBANCE"
    assert output.arrival_failure_probability == 0.20
    assert output.rain_snow_partition_failure_probability == 0.28
    assert output.overall_reliability == 0.82


def test_western_disturbance_output_hazard_invariant():
    """Verify hazard field must strictly be 'WESTERN_DISTURBANCE'."""
    with pytest.raises(ValidationError):
        WDReliabilityOutput(hazard="MONSOON_LPS")


def test_load_manifest_and_catalogue():
    """Verify disk loaders load and parse manifest and catalogue artifacts."""
    manifest = load_wd_target_manifest()
    assert manifest["hazard_family"] == "WESTERN_DISTURBANCE"
    assert len(manifest["targets"]) == 6

    catalogue = load_wd_event_catalogue()
    assert catalogue["hazard_family"] == "WESTERN_DISTURBANCE"
    assert len(catalogue["events"]) >= 6
