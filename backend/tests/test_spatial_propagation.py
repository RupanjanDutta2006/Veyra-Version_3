"""Unit tests for Spatial Propagation and Risk Surface (Gate 8 / Phase I)."""

import pytest
import numpy as np

from backend.app.builder2.spatial_reliability_engine import SpatialReliabilitySpecialist
from backend.app.contracts.spatial_contract import MacroRegion, SpatialIssueFeatures


@pytest.fixture
def spatial_specialist():
    return SpatialReliabilitySpecialist()


@pytest.fixture
def nominal_spatial_features(spatial_specialist):
    stn_fc = {s: 25.0 for s in spatial_specialist.station_ids}
    stn_spr = {s: 2.8 for s in spatial_specialist.station_ids}
    return SpatialIssueFeatures(
        lead_hours=48,
        variable="precipitation",
        station_forecasts=stn_fc,
        station_spreads=stn_spr,
        synoptic_flow_u_ms=8.0,
        synoptic_flow_v_ms=4.0,
    )


def test_spatial_propagation_non_causal_invariant(spatial_specialist, nominal_spatial_features):
    """Verify spatial propagation is explicitly documented as non-causal empirical covariance."""
    out = spatial_specialist.predict(nominal_spatial_features)
    assert out.provenance.get("non_causal_certification") is True
    assert any("empirical covariance" in e for e in out.evidence)
    assert len(out.propagation_correlations) >= 4
    for corr in out.propagation_correlations.values():
        assert 0.0 < corr < 1.0


def test_spatial_regional_cluster_aggregation(spatial_specialist, nominal_spatial_features):
    """Verify regional cluster aggregation preserves local hotspots without flat averaging."""
    # Inject a local severe hotspot in Western Ghats (MUMBAI)
    hotspot_features = nominal_spatial_features.model_copy(deep=True)
    hotspot_features.station_spreads["MUMBAI"] = 12.0

    out = spatial_specialist.predict(hotspot_features)
    # Western Ghats cluster reliability should reflect the hotspot
    wg_rel = out.cluster_reliabilities[MacroRegion.WESTERN_GHATS.value]
    np_rel = out.cluster_reliabilities[MacroRegion.NORTHERN_PLAINS.value]
    assert wg_rel < np_rel  # Lower reliability in Western Ghats due to hotspot


def test_spatial_risk_surface_generation(spatial_specialist, nominal_spatial_features):
    """Verify continuous 2D spatial risk surface grid bounds and values."""
    out = spatial_specialist.predict(nominal_spatial_features)
    surface = out.spatial_risk_surface

    assert "bounds" in surface
    assert surface["bounds"]["min_lat"] == 8.0
    assert surface["bounds"]["max_lat"] == 36.0
    assert surface["points_count"] > 50

    for pt in surface["sample_grid"]:
        assert 8.0 <= pt["lat"] <= 36.0
        assert 68.0 <= pt["lon"] <= 96.0
        assert 0.0 <= pt["risk_prob"] <= 1.0


def test_spatial_baseline_ladder(spatial_specialist, nominal_spatial_features):
    """Verify Level 1, 2, 3 spatial baselines produce valid probabilities."""
    p_clim = spatial_specialist.evaluate_climatology_baseline(MacroRegion.NORTHERN_PLAINS, 48)
    assert 0.05 < p_clim < 0.50

    p_l2 = spatial_specialist.evaluate_distance_weighted_spread_baseline(
        "DELHI", nominal_spatial_features.station_spreads, 48
    )
    assert 0.01 < p_l2 < 0.99

    p_l3 = spatial_specialist.evaluate_spatial_logistic_baseline(
        "DELHI", nominal_spatial_features.station_spreads, 48
    )
    assert 0.01 < p_l3 < 0.99


def test_spatial_adversarial_stress_robustness(spatial_specialist, nominal_spatial_features):
    """Verify adversarial robustness under station dropout."""
    out = spatial_specialist.predict(nominal_spatial_features)
    assert out.adversarial_robustness_score >= 0.80
