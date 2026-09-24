"""Tests for multi-horizon hazard curves, survival functions, and time-to-bust (Gate 2 / Phase C)."""

import pytest
from backend.app.builder2.hazard_engine import HazardTrajectoryEngine
from backend.app.contracts.hazard_contracts import HazardFamily
from backend.app.schemas.reliability_state import ReliabilityState


def test_hazard_curve_generation_and_bounds():
    """Verify hazard curve produces 10 horizons with bounded probabilities."""
    engine = HazardTrajectoryEngine()
    pts = engine.compute_hazard_curve(base_bust_prob=0.10, hazard_family=HazardFamily.HEATWAVE)

    assert len(pts) == 10
    leads = [p.lead_hours for p in pts]
    assert leads == [24, 48, 72, 96, 120, 144, 168, 192, 216, 240]

    for p in pts:
        assert 0.0 <= p.bust_prob <= 1.0
        assert 0.0 <= p.hazard_prob <= 1.0


def test_survival_curve_monotonicity_invariant():
    """Verify survival curve S(t) is strictly monotonically non-increasing."""
    engine = HazardTrajectoryEngine()
    pts = engine.compute_hazard_curve(base_bust_prob=0.12)
    survival = engine.compute_survival_curve(pts)

    assert len(survival) == len(pts)
    assert survival[0] <= 1.0

    for i in range(1, len(survival)):
        assert survival[i] <= survival[i - 1], f"Survival curve violated monotonicity at index {i}: {survival[i]} > {survival[i-1]}"


def test_expected_time_to_bust_calculation():
    """Verify expected time-to-bust returns plausible lead time in hours."""
    engine = HazardTrajectoryEngine()
    pts = engine.compute_hazard_curve(base_bust_prob=0.30)
    survival = engine.compute_survival_curve(pts)
    ttb = engine.compute_expected_time_to_bust(pts, survival)

    assert ttb is not None
    assert 24.0 <= ttb <= 240.0


def test_build_reliability_state_integration():
    """Verify engine constructs a valid ReliabilityState with hazard curves."""
    engine = HazardTrajectoryEngine()
    state = engine.build_reliability_state(
        forecast_identity="FC_MUMBAI_PRECIP_48H",
        issue_time="2026-09-20T00:00:00Z",
        location="Mumbai",
        variable="precipitation_amount",
        lead_hours=48,
        model_version="veyra-v3-challenger",
        base_bust_prob=0.25,
        ensemble_mean=45.0,
        ensemble_std=12.0,
        hazard_family=HazardFamily.PRECIPITATION,
    )

    assert isinstance(state, ReliabilityState)
    assert len(state.hazard_curve) == 10
    assert len(state.survival_curve) == 10
    assert state.hazard_type == "PRECIPITATION"
    assert state.abstention_state is False
    assert state.bust_probability == 0.25
