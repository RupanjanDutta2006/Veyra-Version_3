"""Tests for common ReliabilityState contract (Blueprint Section 4 / Gate 1)."""

import json
import pytest
from pydantic import ValidationError

from backend.app.schemas.reliability_state import (
    ContinuousErrorDistribution,
    DecisionMode,
    EnsembleGeometry,
    EnsembleSummary,
    HazardPoint,
    OperationalReliabilityState,
    ReliabilityState,
)


@pytest.fixture
def nominal_reliability_state() -> ReliabilityState:
    """Fixture providing a valid nominal ReliabilityState object."""
    return ReliabilityState(
        forecast_identity="GEFS_20260920_00Z_DELHI_T2M_48H",
        issue_time="2026-09-20T00:00:00Z",
        location="Delhi",
        variable="temperature_2m",
        lead_hours=48,
        model_version="veyra-v3-challenger",
        forecast_values={"raw_celsius": 28.5, "transformed_kelvin": 301.65},
        ensemble_summary=EnsembleSummary(
            member_count=31,
            mean=301.65,
            std=1.24,
            min_val=299.15,
            max_val=304.15,
            spread_to_error_ratio=0.85,
            ensemble_cv=0.0041,
        ),
        ensemble_geometry=EnsembleGeometry(
            dispersion_metric=1.24,
            bimodality_coefficient=0.32,
            cluster_count=1,
            outlier_member_count=0,
        ),
        bust_probability=0.0569,
        continuous_error_distribution=ContinuousErrorDistribution(
            mean_error=0.15,
            mae=0.85,
            rmse=1.12,
            q10=-1.20,
            q50=0.10,
            q90=1.45,
            crps=0.62,
        ),
        hazard_type="HEATWAVE",
        hazard_probability=0.02,
        hazard_curve=[
            HazardPoint(lead_hours=24, hazard_prob=0.01, bust_prob=0.03),
            HazardPoint(lead_hours=48, hazard_prob=0.02, bust_prob=0.0569),
            HazardPoint(lead_hours=72, hazard_prob=0.05, bust_prob=0.089),
        ],
        survival_curve=[0.97, 0.9431, 0.911],
        expected_time_to_bust=144.0,
        expected_time_to_recovery=None,
        atmospheric_regime="PRE_MONSOON_CONVECTIVE",
        vertical_regime="WEAK_INVERSION",
        spatial_risk=0.045,
        propagation_score=0.12,
        ood_score=0.08,
        drift_score=0.04,
        missingness_score=0.0,
        calibration_health="NOMINAL",
        reference_health="VERIFIED",
        reliability_state=OperationalReliabilityState.STABLE,
        abstention_state=False,
        decision_mode=DecisionMode.NOMINAL,
        evidence={"primary_signal": "LOW_ENSEMBLE_SPREAD"},
        provenance={"model_sha256": "00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660"},
    )


def test_reliability_state_nominal_creation(nominal_reliability_state: ReliabilityState):
    """Verify nominal state passes all field validations and retains values."""
    state = nominal_reliability_state
    assert state.forecast_identity == "GEFS_20260920_00Z_DELHI_T2M_48H"
    assert state.lead_hours == 48
    assert state.bust_probability == 0.0569
    assert state.reliability_state == OperationalReliabilityState.STABLE
    assert state.abstention_state is False
    assert state.ensemble_summary.member_count == 31


def test_abstention_invariant_enforces_null_probability(nominal_reliability_state: ReliabilityState):
    """Verify that when abstention_state is True, bust_probability must be null."""
    state_dict = nominal_reliability_state.model_dump()
    state_dict["abstention_state"] = True
    state_dict["bust_probability"] = 0.45  # Contradicts abstention

    with pytest.raises(ValidationError) as exc:
        ReliabilityState.model_validate(state_dict)
    assert "bust_probability must be null when abstention_state is True" in str(exc.value)

    # Valid abstention: bust_probability is None
    state_dict["bust_probability"] = None
    state_dict["reliability_state"] = OperationalReliabilityState.ABSTAIN
    state_dict["decision_mode"] = DecisionMode.ABSTAIN_UNSUPPORTED
    valid_abstained = ReliabilityState.model_validate(state_dict)
    assert valid_abstained.bust_probability is None
    assert valid_abstained.abstention_state is True


def test_state_machine_enum_values():
    """Verify all 7 lifecycle states from the roadmap are represented."""
    expected_states = {"STABLE", "WATCHING", "DEGRADING", "FAILURE_PRONE", "ABSTAIN", "BUST", "RECOVERING"}
    actual_states = {s.value for s in OperationalReliabilityState}
    assert actual_states == expected_states


def test_continuous_error_distribution_quantiles(nominal_reliability_state: ReliabilityState):
    """Verify continuous error distribution maintains ordering q10 <= q50 <= q90."""
    dist = nominal_reliability_state.continuous_error_distribution
    assert dist is not None
    assert dist.q10 <= dist.q50 <= dist.q90


def test_serialization_and_deserialization_roundtrip(nominal_reliability_state: ReliabilityState):
    """Verify complete JSON round-trip preserves all fields without truncation."""
    json_str = nominal_reliability_state.model_dump_json()
    parsed = json.loads(json_str)

    reconstructed = ReliabilityState.model_validate(parsed)
    assert reconstructed.forecast_identity == nominal_reliability_state.forecast_identity
    assert reconstructed.bust_probability == nominal_reliability_state.bust_probability
    assert len(reconstructed.hazard_curve) == 3


def test_failure_memory_episode_creation_and_retrieval():
    """Verify FailureMemoryStore stores episodes and retrieves analogs with support counts."""
    from backend.app.builder2.failure_memory import FailureEpisode, FailureMemoryStore
    from backend.app.contracts.hazard_contracts import HazardFamily

    store = FailureMemoryStore()
    episodes = [
        FailureEpisode(
            episode_id="ep_001",
            hazard_family=HazardFamily.HEATWAVE,
            issue_time="2024-05-15T00:00:00Z",
            location="Delhi",
            lead_hours=48,
            forecast_state_vector=[0.8, 0.4, 0.1, 0.9],
            observed_error=4.2,
            bust_label=1,
            severity="SEVERE",
            motif_id="MOTIF_HEAT_DOMING",
        ),
        FailureEpisode(
            episode_id="ep_002",
            hazard_family=HazardFamily.HEATWAVE,
            issue_time="2024-05-20T00:00:00Z",
            location="Delhi",
            lead_hours=48,
            forecast_state_vector=[0.85, 0.42, 0.12, 0.88],
            observed_error=3.8,
            bust_label=1,
            severity="MODERATE",
            motif_id="MOTIF_HEAT_DOMING",
        ),
        FailureEpisode(
            episode_id="ep_003",
            hazard_family=HazardFamily.PRECIPITATION,
            issue_time="2024-07-10T00:00:00Z",
            location="Mumbai",
            lead_hours=24,
            forecast_state_vector=[0.1, 0.9, 0.8, 0.2],
            observed_error=65.0,
            bust_label=1,
            severity="CATASTROPHIC",
            motif_id="MOTIF_MESOSCALE_CONVECTIVE",
        ),
    ]
    store.add_episodes(episodes)
    assert store.count() == 3

    # Query for Heatwave at 48h lead
    query = [0.82, 0.41, 0.11, 0.9]
    res = store.retrieve_analogs(
        query_vector=query,
        hazard=HazardFamily.HEATWAVE,
        lead_hours=48,
        top_k=2,
    )

    assert res.sample_support_count == 2
    assert res.historical_failure_frequency == 1.0
    assert res.matches[0].episode.episode_id in {"ep_001", "ep_002"}
    assert res.matches[0].similarity_score > 0.8
    assert res.analog_uncertainty_score < 1.0


def test_failure_memory_empty_store_returns_safe_defaults():
    """Verify empty FailureMemoryStore returns sample_support_count=0 and uncertainty=1.0."""
    from backend.app.builder2.failure_memory import FailureMemoryStore
    from backend.app.contracts.hazard_contracts import HazardFamily

    store = FailureMemoryStore()
    res = store.retrieve_analogs(query_vector=[0.5, 0.5], hazard=HazardFamily.CYCLONE)
    assert res.sample_support_count == 0
    assert res.historical_failure_frequency is None
    assert res.analog_uncertainty_score == 1.0

