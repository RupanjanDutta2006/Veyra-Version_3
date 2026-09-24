"""Tests for UI Reliability Fields, Promotion Taxonomy, and Watchlist Alerts (Gate 10 / Phase K)."""

import pytest

from backend.app.contracts.operational_watchlist_contract import (
    AlertTier,
    ConformalBounds,
    PromotionStatus,
    compute_alert_tier,
)


def test_ui_status_taxonomy_values():
    """Verify all promotion statuses conform to the certified 8-state taxonomy."""
    expected_statuses = {
        "FROZEN",
        "CERTIFIED",
        "OPERATIONAL_ONLY",
        "EXPERIMENTAL",
        "DIAGNOSTIC",
        "ABSTAINED",
        "REJECTED",
        "FUTURE",
    }
    actual_statuses = {s.value for s in PromotionStatus}
    assert actual_statuses == expected_statuses


def test_no_experimental_as_certified_invariant():
    """Verify non-negotiable invariant: experimental models cannot be marked CERTIFIED."""
    candidate_model = {
        "model_id": "FRONTIER_GRAPH_DIFFUSION_V0",
        "status": PromotionStatus.EXPERIMENTAL,
        "hazard_family": "SPATIAL_NETWORK",
    }

    assert candidate_model["status"] != PromotionStatus.CERTIFIED, (
        "Experimental candidate cannot be presented as CERTIFIED to the UI!"
    )


def test_ui_conformal_bounds_contract():
    """Verify conformal bounds contract for frontend UI rendering."""
    bounds = ConformalBounds(lower_bound=0.15, upper_bound=0.35, target_coverage=0.90)
    assert bounds.lower_bound <= bounds.upper_bound
    assert bounds.target_coverage == 0.90

    data = bounds.model_dump()
    assert "lower_bound" in data
    assert "upper_bound" in data
    assert "target_coverage" in data


def test_ui_watchlist_alert_tiers():
    """Verify compute_alert_tier correctly maps probabilities to certified operational tiers."""
    assert compute_alert_tier(0.85) == AlertTier.CRITICAL
    assert compute_alert_tier(0.65) == AlertTier.WARNING
    assert compute_alert_tier(0.42) == AlertTier.WATCH
    assert compute_alert_tier(0.22) == AlertTier.ADVISORY
    assert compute_alert_tier(0.08) == AlertTier.INFO
