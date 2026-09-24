"""Unit tests for Counterfactual Perturbation and Reliability Digital Twin (Gate 11 / Phase L)."""

import pytest

from backend.app.builder2.counterfactual_engine import (
    CounterfactualEngine,
    CrashTestResult,
)
from backend.app.builder2.digital_twin_engine import (
    DigitalTwinEngine,
    DigitalTwinReplayResult,
)


@pytest.fixture
def cf_engine():
    return CounterfactualEngine()


@pytest.fixture
def twin_engine():
    return DigitalTwinEngine()


def test_spread_perturbation_monotonicity(cf_engine):
    """Verify that increasing ensemble spread multiplier monotonically increases or maintains failure risk."""
    base_features = {"ensemble_spread": 12.5}
    base_bust_prob = 0.35

    steps = cf_engine.run_spread_perturbation(
        base_features=base_features,
        base_bust_prob=base_bust_prob,
        multipliers=[0.5, 1.0, 1.5, 2.0, 3.0],
    )

    assert len(steps) == 5
    for step in steps:
        assert step.is_monotonic is True
        assert 0.0 <= step.bust_probability <= 1.0

    # Probability at 3.0x spread should be strictly greater than at 0.5x spread
    assert steps[-1].bust_probability > steps[0].bust_probability


def test_lead_time_perturbation_monotonicity(cf_engine):
    """Verify that increasing forecast lead time monotonically increases failure risk."""
    base_bust_prob = 0.40
    leads = [24, 48, 72, 96, 120]

    steps = cf_engine.run_lead_time_perturbation(
        base_bust_prob=base_bust_prob,
        lead_hours_list=leads,
    )

    assert len(steps) == 5
    for step in steps:
        assert step.is_monotonic is True
        assert 0.0 <= step.bust_probability <= 1.0

    assert steps[-1].bust_probability > steps[0].bust_probability


def test_crash_resilience_on_negative_temperature(cf_engine):
    """Verify physical impossibility (negative Kelvin) triggers safe abstention without NaN/Inf."""
    result = cf_engine.run_crash_test(
        test_name="negative_kelvin_injection",
        variable="temperature_2m_k",
        extreme_value=-15.0,
        hazard="HEATWAVE",
    )

    assert isinstance(result, CrashTestResult)
    assert result.status == "PASS"
    assert result.action_taken == "ABSTAIN"
    assert result.abstention_reason == "PHYSICAL_INCONSISTENCY"
    assert result.contains_nan_or_inf is False


def test_crash_resilience_on_extreme_out_of_bounds(cf_engine):
    """Verify extreme atmospheric values trigger safe abstention without exception."""
    result = cf_engine.run_crash_test(
        test_name="extreme_cape_injection",
        variable="cape_proxy_jkg",
        extreme_value=8500.0,
        hazard="PRECIPITATION",
    )

    assert result.status == "PASS"
    assert result.action_taken == "ABSTAIN"
    assert result.abstention_reason == "OOD_EXCEEDED"
    assert result.contains_nan_or_inf is False


def test_digital_twin_replay_execution(twin_engine):
    """Verify digital twin replays historical episode across all 4 tiers."""
    result = twin_engine.replay_event(
        event_name="historical",
        compare_tiers=["raw", "v3", "certified-veyra", "frontier"],
    )

    assert isinstance(result, DigitalTwinReplayResult)
    assert len(result.cycles) == 6
    assert "raw" in result.tier_summaries
    assert "v3" in result.tier_summaries
    assert "certified-veyra" in result.tier_summaries
    assert "frontier" in result.tier_summaries

    # Certified Veyra provides 96h lead-time advantage with low Brier score
    cert_summary = result.tier_summaries["certified-veyra"]
    assert cert_summary.lead_time_advantage_hours >= 72.0
    assert cert_summary.brier_score < 0.15
    assert result.recommended_tier == "certified-veyra"

    # Frontier tier is marked is_simulation: True
    assert result.tier_summaries["frontier"].is_simulation is True
