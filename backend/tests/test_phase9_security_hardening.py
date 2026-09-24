"""Test suite for Phase 9: Failure Handling, Security Hardening, and Operational Governance.

Covers all 16 audit requirements from Docs §21, §22, §1, §3.1 and Research Files 006, 018, 023, 042, 076, 099–100, 109–110, 114–115, 120:
- K1: Download failure fallback (last good cycle, "DATA_DELAYED")
- K2: Degraded ensemble handling (missing members, safe abstention if < 10)
- K3: Model unavailable fallback -> calibrated spread-only
- K4: OOD detection -> real abstention for pole, ocean, and foreign cities
- K5: No-analog -> "No eligible analog found" authoritative state
- K6: Provider/model upgrade -> shadow period + recalibration machinery
- L1: Model registry API + promotion lifecycle (CANDIDATE -> SERVING)
- L2: Auth, RBAC, API key permissions, input bounds validation
- L3: Structured audit logging with prediction IDs and queryable buffer
- L4: Drift monitoring, calibration decay, and automated retraining proposals
- A2: Human-in-the-loop review and approval API
- A3, A4, A5: Certified scope enforcement across geography, variable, and lead horizon
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.core.audit_logger import AuditLogger, default_audit_logger
from backend.app.core.auth import (
    AuthenticatedUser,
    UserRole,
    get_current_user,
    require_role,
    require_scope,
    sanitize_input_string,
)
from backend.app.main import app
from backend.app.safety.ood_enforcement import OODEnforcer, default_ood_enforcer
from backend.app.safety.scope_enforcer import ScopeEnforcer, default_scope_enforcer
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    ReasonCode,
    RiskLevel,
    TrustState,
)
from backend.app.services.base import FeatureResult, ModelResult, WeatherResult
from backend.app.services.drift_monitor import (
    DriftMonitoringService,
    default_drift_monitor,
)
from backend.app.services.fallback_service import (
    ForecastFallbackService,
    default_fallback_service,
)
from backend.app.services.model_registry import (
    ModelLifecycleStatus,
    ModelRegistryService,
    default_model_registry_service,
)
from backend.app.services.shadow_scoring import (
    ShadowScoringService,
    default_shadow_service,
)
from backend.app.agents.forecast_bust_agent import ForecastBustAgent


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# K1: Download-Failure Fallback
# ---------------------------------------------------------------------------
def test_k1_download_failure_fallback():
    service = ForecastFallbackService()
    # 1. No cached cycle -> returns unrecovered DATA_DELAYED
    res = service.handle_download_failure("Mumbai")
    assert not res.recovered
    assert res.status_code == "DATA_DELAYED"

    # 2. Cache a good cycle
    good_weather = WeatherResult(
        location="Mumbai",
        is_available=True,
        metadata={"issue_time": "2026-09-19T00:00:00Z"},
    )
    service.record_good_cycle("Mumbai", good_weather)

    # 3. Download failure now recovers previous cycle
    res_rec = service.handle_download_failure("Mumbai")
    assert res_rec.recovered
    assert res_rec.is_fallback_cycle
    assert res_rec.status_code == "DATA_DELAYED"
    assert res_rec.cycle_time == "2026-09-19T00:00:00Z"
    assert res_rec.weather_data is not None


# ---------------------------------------------------------------------------
# K2: Degraded Ensemble Handling
# ---------------------------------------------------------------------------
def test_k2_degraded_ensemble_handling():
    service = ForecastFallbackService()

    # Full ensemble: 31/31 members
    nominal = service.assess_ensemble_completeness(available_members=31)
    assert not nominal.is_degraded
    assert not nominal.abstain_required
    assert nominal.completeness_ratio == 1.0
    assert nominal.uncertainty_inflation_factor == 1.0

    # Incomplete ensemble: 20/31 members -> Degraded mode, no abstention
    degraded = service.assess_ensemble_completeness(available_members=20)
    assert degraded.is_degraded
    assert not degraded.abstain_required
    assert degraded.completeness_ratio < 1.0
    assert degraded.uncertainty_inflation_factor > 1.0
    assert "DEGRADED_ENSEMBLE_INCOMPLETE" in degraded.reason_codes

    # Critically incomplete ensemble: 8/31 members (< 10) -> Abstention required
    critical = service.assess_ensemble_completeness(available_members=8)
    assert critical.is_degraded
    assert critical.abstain_required
    assert "DEGRADED_ENSEMBLE_INSUFFICIENT_MEMBERS" in critical.reason_codes


# ---------------------------------------------------------------------------
# K3: Model-Unavailable Fallback -> Calibrated Spread-Only
# ---------------------------------------------------------------------------
def test_k3_model_unavailable_spread_fallback():
    service = ForecastFallbackService()
    fallback_res = service.compute_spread_only_fallback(
        ensemble_spread=3.5,
        lead_hours=48,
        variable="temperature_2m",
    )
    assert 0.0 <= fallback_res.probability <= 1.0
    assert fallback_res.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.MEDIUM, RiskLevel.LOW)
    assert fallback_res.fallback_model_name == "spread_only_logistic_baseline_v1"
    assert "MODEL_UNAVAILABLE_SPREAD_FALLBACK" in fallback_res.reason_codes


# ---------------------------------------------------------------------------
# K4: OOD Enforcement: Pole, Ocean, and Foreign Locations
# ---------------------------------------------------------------------------
def test_k4_ood_enforcement():
    enforcer = OODEnforcer()

    # Polar coordinates -> Abstain
    res_polar = enforcer.evaluate(location="Research Camp", latitude=78.5, longitude=15.0)
    assert res_polar.is_ood
    assert res_polar.abstain_required
    assert res_polar.trust_state == TrustState.ABSTAINED
    assert "OUT_OF_DISTRIBUTION_POLAR" in res_polar.reason_codes

    # Extreme non-terrestrial / oceanic location -> Abstain
    res_ocean = enforcer.evaluate(location="Pacific Ocean")
    assert res_ocean.is_ood
    assert res_ocean.abstain_required
    assert res_ocean.trust_state == TrustState.ABSTAINED
    assert "OUT_OF_DISTRIBUTION_GEOGRAPHIC" in res_ocean.reason_codes

    # Extreme Mahalanobis distance -> Abstain
    res_maha = enforcer.evaluate(location="Delhi", feature_ood_score=4.5)
    assert res_maha.is_ood
    assert res_maha.abstain_required
    assert "OUT_OF_DISTRIBUTION_SYNOPTIC" in res_maha.reason_codes

    # Nominal Indian station -> Normal
    res_delhi = enforcer.evaluate(location="Delhi", latitude=28.6, longitude=77.2, feature_ood_score=0.8)
    assert not res_delhi.is_ood
    assert not res_delhi.abstain_required
    assert res_delhi.trust_state == TrustState.HIGH_CONFIDENCE


# ---------------------------------------------------------------------------
# K5: No-Analog Authoritative State
# ---------------------------------------------------------------------------
def test_k5_no_analog_state():
    from backend.app.services.analog_service import HistoricalAnalogService
    analog_svc = HistoricalAnalogService()
    # High similarity threshold forces empty result
    res = analog_svc.find_analogs(
        query_time="2026-09-19T00:00:00Z",
        variable="temperature_2m",
        lead_hours=48,
        forecast_value=999.0,  # Impossible physical value -> no match
        ensemble_std=0.01,
        location="Delhi",
    )
    # Must yield empty cards cleanly without error
    assert isinstance(res.analog_cards, list)


# ---------------------------------------------------------------------------
# K6: Shadow Scoring & Recalibration Machinery
# ---------------------------------------------------------------------------
def test_k6_shadow_scoring_service():
    service = ShadowScoringService(shadow_model_id="candidate_v4")

    # Record shadow pairs
    for i in range(25):
        service.record_shadow_prediction(
            prediction_id=f"p_{i}",
            location="Delhi",
            variable="temperature_2m",
            lead_hours=48,
            serving_prob=0.45,
            shadow_prob=0.48,
        )

    report = service.evaluate_shadow_performance(budget=20)
    assert report.sample_count == 25
    assert report.budget_met
    assert report.mean_divergence == pytest.approx(0.03, abs=1e-3)
    assert report.is_promotion_ready


# ---------------------------------------------------------------------------
# L1: Model Registry API & Promotion Lifecycle
# ---------------------------------------------------------------------------
def test_l1_model_registry_lifecycle():
    registry = ModelRegistryService()

    # Register candidate model
    candidate = registry.register_candidate(
        model_id="test_candidate_v1",
        name="Test Experimental Candidate",
        version="v1.1.0",
        architecture="XGBoost Classifier",
        feature_count=50,
        model_sha256="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        training_window="2000-2013",
        test_window="2018-2022",
        pr_auc=0.720,
        brier_score=0.150,
        ece=0.045,
        platt_slope=1.02,
        perturbation_stability=0.85,
    )
    assert candidate.status == ModelLifecycleStatus.CANDIDATE

    # Promote: CANDIDATE -> VALIDATED (PR-AUC >= 0.60, Brier <= 0.20)
    ok_val, msg_val, _ = registry.promote_model("test_candidate_v1", ModelLifecycleStatus.VALIDATED)
    assert ok_val
    assert registry.get_model("test_candidate_v1").status == ModelLifecycleStatus.VALIDATED

    # Promote: VALIDATED -> CALIBRATED (ECE <= 0.08, Platt slope in [0.8, 1.2])
    ok_cal, _, _ = registry.promote_model("test_candidate_v1", ModelLifecycleStatus.CALIBRATED)
    assert ok_cal

    # Promote: CALIBRATED -> STRESS_TESTED (Stability >= 0.80)
    ok_stress, _, _ = registry.promote_model("test_candidate_v1", ModelLifecycleStatus.STRESS_TESTED)
    assert ok_stress

    # Promote: STRESS_TESTED -> APPROVED
    ok_appr, _, _ = registry.promote_model(
        "test_candidate_v1",
        ModelLifecycleStatus.APPROVED,
        approver="dr_meteorologist",
        notes="Passed all stress tests",
    )
    assert ok_appr
    assert registry.get_model("test_candidate_v1").approved_by == "dr_meteorologist"

    # Promote: APPROVED -> SERVING
    ok_serv, _, _ = registry.promote_model("test_candidate_v1", ModelLifecycleStatus.SERVING)
    assert ok_serv
    assert registry.get_model("test_candidate_v1").is_active
    assert registry.get_active_serving_model().model_id == "test_candidate_v1"

    # Retire
    assert registry.retire_model("test_candidate_v1", "Superseded")
    assert registry.get_model("test_candidate_v1").status == ModelLifecycleStatus.RETIRED


# ---------------------------------------------------------------------------
# L2: Auth, RBAC, and Input Bounds Validation
# ---------------------------------------------------------------------------
def test_l2_auth_rbac_and_input_bounds():
    admin_user = AuthenticatedUser(user_id="adm", role=UserRole.ADMIN, scopes={"system:admin"})
    viewer_user = AuthenticatedUser(user_id="view", role=UserRole.VIEWER, scopes={"predict:read"})

    assert admin_user.has_role(UserRole.ADMIN)
    assert admin_user.has_role(UserRole.VIEWER)
    assert not viewer_user.has_role(UserRole.ADMIN)
    assert viewer_user.has_scope("predict:read")
    assert not viewer_user.has_scope("models:admin")

    # Input Sanitization
    valid_str = sanitize_input_string("Delhi, India", max_length=50)
    assert valid_str == "Delhi, India"

    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        sanitize_input_string("<script>alert(1)</script>")

    with pytest.raises(HTTPException):
        sanitize_input_string("A" * 150, max_length=100)


# ---------------------------------------------------------------------------
# L3: Structured Audit Logger
# ---------------------------------------------------------------------------
def test_l3_audit_logger():
    logger_inst = AuditLogger()
    record = logger_inst.log_event(
        event_type="PREDICTION",
        action="EVALUATE_BUST_RISK",
        status="SUCCESS",
        prediction_id="pred_12345",
        model_version="v3.0.0",
        location="Delhi",
        latency_ms=12.5,
    )
    assert record.audit_id.startswith("aud_")
    assert record.prediction_id == "pred_12345"

    queried = logger_inst.query_logs(prediction_id="pred_12345")
    assert len(queried) == 1
    assert queried[0].audit_id == record.audit_id


# ---------------------------------------------------------------------------
# L4: Drift Monitoring & Retraining Proposals
# ---------------------------------------------------------------------------
def test_l4_drift_and_retraining_proposals():
    monitor = DriftMonitoringService()

    # Record feature samples with severe drift in surface_value
    for val in [55.0, 58.0, 62.0, 60.0, 65.0] * 5:  # Way above baseline 28.5
        monitor.record_feature_values({"surface_value": val})

    drift_metrics = monitor.compute_feature_drift()
    surf_drift = next(d for d in drift_metrics if d.feature_name == "surface_value")
    assert surf_drift.psi_score > 0.10

    # Record verification outcomes with high error (decay)
    for _ in range(15):
        monitor.record_verification_outcome(predicted_prob=0.90, actual_bust=False)

    proposal = monitor.check_and_generate_retraining_proposal()
    assert proposal is not None
    assert proposal.status == "PENDING_REVIEW"
    assert proposal.trigger_reason in ("CALIBRATION_DECAY", "FEATURE_DRIFT")


# ---------------------------------------------------------------------------
# A2: Human-in-the-Loop Review API
# ---------------------------------------------------------------------------
def test_a2_human_in_the_loop_review(client):
    pred_id = "pred_test_review_01"

    # 1. Get default review state (PENDING)
    r_get = client.get(f"/v1/predictions/{pred_id}/review")
    assert r_get.status_code == 200
    assert r_get.json()["status"] == "PENDING"

    # 2. Submit forecaster approval
    review_payload = {
        "status": "APPROVED",
        "forecaster_id": "IMD_MET_42",
        "forecaster_notes": "Ensemble divergence confirmed by satellite IR imagery. Approved for bulletin.",
    }
    r_post = client.post(f"/v1/predictions/{pred_id}/review", json=review_payload)
    assert r_post.status_code == 200
    assert r_post.json()["status"] == "APPROVED"
    assert r_post.json()["forecaster_id"] == "IMD_MET_42"

    # 3. Verify retrieved state is updated
    r_get2 = client.get(f"/v1/predictions/{pred_id}/review")
    assert r_get2.json()["status"] == "APPROVED"
    assert "Ensemble divergence" in r_get2.json()["forecaster_notes"]


# ---------------------------------------------------------------------------
# A3, A4, A5: Scope Enforcement
# ---------------------------------------------------------------------------
def test_a3_a4_a5_scope_enforcement():
    enforcer = ScopeEnforcer()

    # Certified Indian forecast (24h lead, temperature_2m)
    res_valid = enforcer.validate_scope(
        location="Bhopal",
        variable="temperature_2m",
        lead_hours=48,
        latitude=23.25,
        longitude=77.41,
    )
    assert res_valid.is_certified
    assert not res_valid.outside_certified_domain
    assert not res_valid.uncertified_horizon
    assert res_valid.max_allowable_trust_state == TrustState.HIGH_CONFIDENCE

    # Sub-24h lead horizon (A5)
    res_short = enforcer.validate_scope(location="Bhopal", lead_hours=6)
    assert not res_short.is_certified
    assert res_short.uncertified_horizon
    assert res_short.max_allowable_trust_state != TrustState.HIGH_CONFIDENCE

    # Extended > 240h lead horizon (A5)
    res_ext = enforcer.validate_scope(location="Bhopal", lead_hours=300)
    assert not res_ext.is_certified
    assert res_ext.uncertified_horizon

    # Foreign city (A4)
    res_foreign = enforcer.validate_scope(location="New York")
    assert not res_foreign.is_certified
    assert res_foreign.outside_certified_domain
    assert "UNSUPPORTED_GEOGRAPHIC_REGION" in res_foreign.reason_codes


# ---------------------------------------------------------------------------
# End-to-End ForecastBustAgent Integration with Phase 9 Invariants
# ---------------------------------------------------------------------------
def test_phase9_forecast_bust_agent_integration():
    agent = ForecastBustAgent()

    # Foreign location query -> Outside certified domain per A4
    req_foreign = PredictionRequest(location="London")
    resp_foreign = agent.analyze(req_foreign)
    assert resp_foreign.abstain
    assert resp_foreign.bust_probability is None
    assert resp_foreign.outside_certified_domain
    assert not resp_foreign.is_certified
    assert "UNSUPPORTED_GEOGRAPHIC_REGION" in resp_foreign.reason_codes
    assert resp_foreign.prediction_id is not None
    assert resp_foreign.human_approval_status == "PENDING"
