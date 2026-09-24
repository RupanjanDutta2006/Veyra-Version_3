"""Tests for Recovery Engine and operational state machine transitions (Gate 2 / Phase C)."""

import pytest
from backend.app.builder2.hazard_engine import HazardTrajectoryEngine
from backend.app.schemas.reliability_state import (
    DecisionMode,
    HazardPoint,
    OperationalReliabilityState,
)


def test_state_machine_transition_ladder():
    """Verify state transitions according to bust probability thresholds."""
    engine = HazardTrajectoryEngine()

    # BUST threshold (>= 0.70)
    state, decision, abstained = engine.determine_lifecycle_state(
        bust_prob=0.75, ood_score=0.1, missingness_score=0.0, drift_score=0.1, recovery_prob=0.1
    )
    assert state == OperationalReliabilityState.BUST
    assert decision == DecisionMode.HUMAN_OVERRIDE_REQUIRED
    assert abstained is False

    # FAILURE_PRONE (>= 0.50)
    state, decision, abstained = engine.determine_lifecycle_state(
        bust_prob=0.55, ood_score=0.1, missingness_score=0.0, drift_score=0.1, recovery_prob=0.1
    )
    assert state == OperationalReliabilityState.FAILURE_PRONE
    assert decision == DecisionMode.CONSERVATIVE_DISPATCH

    # DEGRADING vs RECOVERING (>= 0.30)
    state_deg, _, _ = engine.determine_lifecycle_state(
        bust_prob=0.35, ood_score=0.1, missingness_score=0.0, drift_score=0.1, recovery_prob=0.2
    )
    assert state_deg == OperationalReliabilityState.DEGRADING

    state_rec, _, _ = engine.determine_lifecycle_state(
        bust_prob=0.35, ood_score=0.1, missingness_score=0.0, drift_score=0.1, recovery_prob=0.7
    )
    assert state_rec == OperationalReliabilityState.RECOVERING

    # WATCHING (>= 0.15)
    state_watch, decision, _ = engine.determine_lifecycle_state(
        bust_prob=0.18, ood_score=0.05, missingness_score=0.0, drift_score=0.05, recovery_prob=0.5
    )
    assert state_watch == OperationalReliabilityState.WATCHING
    assert decision == DecisionMode.NOMINAL

    # STABLE (< 0.15)
    state_stable, decision, _ = engine.determine_lifecycle_state(
        bust_prob=0.05, ood_score=0.02, missingness_score=0.0, drift_score=0.02, recovery_prob=0.9
    )
    assert state_stable == OperationalReliabilityState.STABLE
    assert decision == DecisionMode.NOMINAL


def test_safe_abstention_transitions():
    """Verify OOD novelty or missingness triggers ABSTAIN and ABSTAIN_UNSUPPORTED."""
    engine = HazardTrajectoryEngine()

    # OOD detection
    state_ood, decision_ood, abstained_ood = engine.determine_lifecycle_state(
        bust_prob=0.20, ood_score=0.85, missingness_score=0.0, drift_score=0.0, recovery_prob=0.5
    )
    assert state_ood == OperationalReliabilityState.ABSTAIN
    assert decision_ood == DecisionMode.ABSTAIN_UNSUPPORTED
    assert abstained_ood is True

    # Missing data
    state_miss, decision_miss, abstained_miss = engine.determine_lifecycle_state(
        bust_prob=0.20, ood_score=0.10, missingness_score=0.40, drift_score=0.0, recovery_prob=0.5
    )
    assert state_miss == OperationalReliabilityState.ABSTAIN
    assert decision_miss == DecisionMode.ABSTAIN_UNSUPPORTED
    assert abstained_miss is True


def test_recovery_dynamics_post_peak_drop():
    """Verify recovery engine recognizes post-peak bust probability reduction."""
    engine = HazardTrajectoryEngine()

    # Trajectory peaking at 48h (0.60) then dropping to 0.15 at 120h
    pts = [
        HazardPoint(lead_hours=24, hazard_prob=0.3, bust_prob=0.30),
        HazardPoint(lead_hours=48, hazard_prob=0.6, bust_prob=0.60),
        HazardPoint(lead_hours=72, hazard_prob=0.4, bust_prob=0.35),
        HazardPoint(lead_hours=96, hazard_prob=0.2, bust_prob=0.20),
        HazardPoint(lead_hours=120, hazard_prob=0.15, bust_prob=0.15),
    ]

    time_to_rec, rec_prob = engine.evaluate_recovery_dynamics(pts, OperationalReliabilityState.DEGRADING)
    assert time_to_rec == 72.0  # 120h - 48h
    assert rec_prob > 0.50
