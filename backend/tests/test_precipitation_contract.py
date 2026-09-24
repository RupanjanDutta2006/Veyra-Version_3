"""Unit Tests for Operational Precipitation Contract (Gate 3 / Phase D).

Verifies:
- PrecipitationReliabilityOutput schema conformance
- Strict null-safety for unsupported fields (timing, spatial, extreme tails)
- PrecipitationIssueFeatures boundaries and validation
- Accumulation windows (6h, 12h, 24h, 48h, 72h)
- Standard IMD rainfall intensity threshold constants
- Target manifest integrity and invariants
"""

import pytest
from pydantic import ValidationError

from backend.app.contracts.precipitation_contract import (
    PrecipitationAccumulationWindow,
    PrecipitationIntensityThreshold,
    PrecipitationIssueFeatures,
    PrecipitationOccurrenceFailureType,
    PrecipitationReliabilityOutput,
    load_precipitation_target_manifest,
)


def test_precipitation_reliability_output_valid():
    """Test valid output creation with all active fields."""
    output = PrecipitationReliabilityOutput(
        hazard="PRECIPITATION",
        occurrence_failure_probability=0.25,
        amount_failure_probability=0.30,
        heavy_rain_failure_probability=0.15,
        extreme_rain_failure_probability=0.04,
        timing_failure_probability=0.20,
        spatial_displacement_probability=0.18,
        overall_reliability=0.78,
        evidence=["Precipitation spread 12.5mm", "Wet member fraction 0.65"],
        ood=False,
        provenance={"model_version": "PRECIP_RELIABILITY_V1"},
    )
    assert output.hazard == "PRECIPITATION"
    assert output.occurrence_failure_probability == 0.25
    assert output.amount_failure_probability == 0.30
    assert output.overall_reliability == 0.78
    assert output.ood is False


def test_unsupported_quantities_remain_null():
    """Test that unsupported fields default to None and are never fabricated."""
    output = PrecipitationReliabilityOutput(
        hazard="PRECIPITATION",
        occurrence_failure_probability=0.12,
        amount_failure_probability=0.18,
        # timing and spatial intentionally omitted / unsupported
        timing_failure_probability=None,
        spatial_displacement_probability=None,
        extreme_rain_failure_probability=None,
    )
    assert output.timing_failure_probability is None
    assert output.spatial_displacement_probability is None
    assert output.extreme_rain_failure_probability is None


def test_hazard_name_invariant():
    """Test that hazard must be 'PRECIPITATION'."""
    with pytest.raises(ValidationError):
        PrecipitationReliabilityOutput(
            hazard="CYCLONE",  # Invalid for this specialist output
            occurrence_failure_probability=0.2,
        )


def test_precipitation_issue_features_validation():
    """Test validation rules for issue-time features."""
    valid_features = PrecipitationIssueFeatures(
        lead_hours=48,
        ensemble_mean_precip_mm=18.5,
        ensemble_median_precip_mm=17.0,
        ensemble_spread_precip_mm=6.2,
        ensemble_p90_precip_mm=26.4,
        wet_member_fraction=0.75,
        dry_member_fraction=0.25,
        heavy_exceedance_fraction=0.05,
        cape_proxy_jkg=1250.0,
        precipitable_water_mm=48.0,
        terrain_class="inland",
    )
    assert valid_features.lead_hours == 48
    assert valid_features.wet_member_fraction + valid_features.dry_member_fraction == 1.0

    # Negative precip should raise ValidationError
    with pytest.raises(ValidationError):
        PrecipitationIssueFeatures(
            lead_hours=24,
            ensemble_mean_precip_mm=-5.0,
            ensemble_median_precip_mm=0.0,
            ensemble_spread_precip_mm=2.0,
            ensemble_p90_precip_mm=5.0,
            wet_member_fraction=0.5,
            dry_member_fraction=0.5,
        )

    # Invalid fraction > 1.0 should raise ValidationError
    with pytest.raises(ValidationError):
        PrecipitationIssueFeatures(
            lead_hours=24,
            ensemble_mean_precip_mm=10.0,
            ensemble_median_precip_mm=10.0,
            ensemble_spread_precip_mm=2.0,
            ensemble_p90_precip_mm=15.0,
            wet_member_fraction=1.5,
            dry_member_fraction=0.5,
        )


def test_accumulation_windows_contract():
    """Verify supported accumulation horizons."""
    windows = [w.value for w in PrecipitationAccumulationWindow]
    assert "6h" in windows
    assert "12h" in windows
    assert "24h" in windows
    assert "48h" in windows
    assert "72h" in windows


def test_intensity_threshold_constants():
    """Verify IMD intensity threshold categories."""
    assert PrecipitationIntensityThreshold.NONE.value == "NONE"
    assert PrecipitationIntensityThreshold.LIGHT.value == "LIGHT"
    assert PrecipitationIntensityThreshold.MODERATE.value == "MODERATE"
    assert PrecipitationIntensityThreshold.HEAVY.value == "HEAVY"
    assert PrecipitationIntensityThreshold.VERY_HEAVY.value == "VERY_HEAVY"
    assert PrecipitationIntensityThreshold.EXTREMELY_HEAVY.value == "EXTREMELY_HEAVY"


def test_load_target_manifest_valid():
    """Verify target manifest loads and validates invariants."""
    manifest = load_precipitation_target_manifest()
    assert manifest["hazard"] == "PRECIPITATION"
    assert manifest["gate"] == "Gate 3"
    assert 24 in manifest["accumulation_windows_hours"]
    assert manifest["intensity_thresholds_mm"]["HEAVY"] == 64.5
    assert len(manifest["targets"]) >= 6
