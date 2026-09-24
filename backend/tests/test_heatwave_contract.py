"""Unit tests for Heatwave and Severe-Wind Contract (Gate 7 / Phase H)."""

import pytest
from pydantic import ValidationError

from backend.app.contracts.heatwave_contract import (
    HeatwaveIssueFeatures,
    HeatwaveRegime,
    HeatwaveReliabilityOutput,
    HeatwaveSeverity,
    load_heatwave_event_catalogue,
    load_heatwave_target_manifest,
)


def test_heatwave_enums():
    """Verify supported regimes and severity categories."""
    assert HeatwaveRegime.CORE_HEATWAVE_ZONE == "CORE_HEATWAVE_ZONE"
    assert HeatwaveRegime.NORTHWEST_PLAINS == "NORTHWEST_PLAINS"
    assert HeatwaveRegime.COASTAL_PENINSULAR == "COASTAL_PENINSULAR"
    assert HeatwaveRegime.HILL_REGION == "HILL_REGION"

    assert HeatwaveSeverity.NORMAL == "NORMAL"
    assert HeatwaveSeverity.HEATWAVE == "HEATWAVE"
    assert HeatwaveSeverity.SEVERE_HEATWAVE == "SEVERE_HEATWAVE"


def test_heatwave_issue_features_valid():
    """Verify valid construction of issue-time features."""
    features = HeatwaveIssueFeatures(
        lead_hours=48,
        regime=HeatwaveRegime.CORE_HEATWAVE_ZONE,
        severity=HeatwaveSeverity.SEVERE_HEATWAVE,
        forecast_lat=26.5,
        forecast_lon=80.5,
        forecast_tmax_celsius=45.2,
        forecast_tmin_celsius=31.0,
        climatological_normal_tmax_celsius=39.0,
        departure_tmax_celsius=6.2,
        ensemble_tmax_spread_celsius=2.8,
        ensemble_tmin_spread_celsius=1.8,
        soil_moisture_fraction=0.08,
        temp_advection_850hpa_k_s=2.5e-5,
        forecast_duration_days=6.0,
        wind_gust_10m_ms=18.5,
        ensemble_gust_spread_ms=3.2,
        has_paired_wind_data=True,
    )
    assert features.lead_hours == 48
    assert features.regime == HeatwaveRegime.CORE_HEATWAVE_ZONE
    assert features.severity == HeatwaveSeverity.SEVERE_HEATWAVE
    assert features.forecast_tmax_celsius == 45.2
    assert features.has_paired_wind_data is True


def test_heatwave_issue_features_bounds_validation():
    """Verify bounds enforcement on physical fields."""
    with pytest.raises(ValidationError):
        # Temperature out of bounds (> 58.0°C)
        HeatwaveIssueFeatures(
            lead_hours=24,
            regime=HeatwaveRegime.NORTHWEST_PLAINS,
            severity=HeatwaveSeverity.HEATWAVE,
            forecast_lat=28.0,
            forecast_lon=76.0,
            forecast_tmax_celsius=65.0,
            ensemble_tmax_spread_celsius=2.0,
        )

    with pytest.raises(ValidationError):
        # Negative ensemble spread
        HeatwaveIssueFeatures(
            lead_hours=24,
            regime=HeatwaveRegime.NORTHWEST_PLAINS,
            severity=HeatwaveSeverity.HEATWAVE,
            forecast_lat=28.0,
            forecast_lon=76.0,
            forecast_tmax_celsius=42.0,
            ensemble_tmax_spread_celsius=-1.5,
        )

    with pytest.raises(ValidationError):
        # Invalid soil moisture (> 1.0)
        HeatwaveIssueFeatures(
            lead_hours=24,
            regime=HeatwaveRegime.NORTHWEST_PLAINS,
            severity=HeatwaveSeverity.HEATWAVE,
            forecast_lat=28.0,
            forecast_lon=76.0,
            forecast_tmax_celsius=42.0,
            ensemble_tmax_spread_celsius=2.0,
            soil_moisture_fraction=1.5,
        )


def test_heatwave_reliability_output_valid():
    """Verify valid construction of decomposed output schema."""
    output = HeatwaveReliabilityOutput(
        hazard="HEATWAVE",
        threshold_failure_probability=0.22,
        peak_temperature_failure_probability=0.26,
        onset_failure_probability=0.18,
        duration_failure_probability=0.15,
        warm_night_failure_probability=0.20,
        spatial_extent_failure_probability=0.17,
        severe_wind_failure_probability=0.30,
        overall_reliability=0.79,
        evidence=["Severe heatwave conditions over Core Zone with dry soil feedback"],
        ood=False,
        provenance={"model": "HEATWAVE_RELIABILITY_V1"},
    )
    assert output.hazard == "HEATWAVE"
    assert output.threshold_failure_probability == 0.22
    assert output.severe_wind_failure_probability == 0.30
    assert output.overall_reliability == 0.79


def test_heatwave_output_hazard_invariant():
    """Verify hazard field must strictly be 'HEATWAVE'."""
    with pytest.raises(ValidationError):
        HeatwaveReliabilityOutput(hazard="TROPICAL_CYCLONE")


def test_load_manifest_and_catalogue():
    """Verify disk loaders load and parse manifest and catalogue artifacts."""
    manifest = load_heatwave_target_manifest()
    assert manifest["hazard_family"] == "HEATWAVE"
    assert len(manifest["targets"]) == 7

    catalogue = load_heatwave_event_catalogue()
    assert catalogue["hazard_family"] == "HEATWAVE"
    assert len(catalogue["events"]) >= 6
