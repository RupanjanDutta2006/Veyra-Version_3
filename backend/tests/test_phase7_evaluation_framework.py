"""Comprehensive Verification Test Suite for Phase 7 Evaluation Framework.

Tests all 7 audit items per §18.1 and Research Files 081–089:
- J2: Log-loss, calibration slope/intercept, reliability diagrams, ECE/MCE.
- J3: Operational warning lead-time gain vs spread-only baseline (24/48/72h).
- J4: Spatial/object metrics (FSS, object IoU, centroid error, top-k recall).
- J5: Safety/selective prediction (coverage-risk curve, retained-case Brier/PR-AUC, high-conf error).
- J6: Multi-dimensional stratification (season, lead, region, variable, regime).
- J8: Operational burden (false alerts/cycle, persistence, flicker, review hours).
- J9: Explanation quality (attribution stability, perturbation fidelity, forecaster agreement).
"""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.ml.evaluation import ModelEvaluator
from backend.app.ml.evaluation_framework import (
    ComprehensiveEvaluationReport,
    VeyraEvaluationFramework,
    compute_safety_coverage_risk_metrics,
    compute_warning_lead_time_gain,
)
from backend.app.ml.explanation_quality import (
    ExplanationQualityEvaluator,
    compute_fidelity_drop,
    compute_forecaster_agreement,
    compute_spearman_rank_correlation,
    compute_top_k_jaccard,
)
from backend.app.ml.operational_burden import (
    OperationalBurdenEvaluator,
    compute_alert_persistence_and_flicker,
    compute_fixed_budget_recall,
)
from backend.app.ml.spatial_metrics import (
    compute_area_fraction_error,
    compute_centroid_error,
    compute_fss,
    compute_haversine_distance,
    compute_object_iou,
    compute_top_k_spatial_recall,
    evaluate_spatial_grid,
)
from backend.app.ml.stratified_eval import (
    StratifiedEvaluator,
    month_to_season,
)
from backend.app.services.evaluation_service import EvaluationIntegrationService


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# J2: Calibration & Probability Quality Tests
# ==============================================================================

def test_j2_log_loss_and_reliability_diagram():
    """Verify log-loss, ECE, MCE, and reliability diagram binning."""
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1, 0, 1])
    y_prob = np.array([0.1, 0.2, 0.15, 0.05, 0.85, 0.9, 0.8, 0.95, 0.3, 0.75])

    report = ModelEvaluator.evaluate(y_true, y_prob, split_name="test")

    assert report.log_loss_value is not None
    assert report.log_loss_value > 0.0
    assert report.brier_score is not None
    assert report.reliability_diagram is not None
    assert len(report.reliability_diagram.bin_counts) == 10
    assert report.expected_calibration_error is not None
    assert report.expected_calibration_error >= 0.0
    assert report.max_calibration_error is not None
    assert report.max_calibration_error >= report.expected_calibration_error


def test_j2_calibration_slope_and_intercept():
    """Verify Platt calibration slope and intercept fitting."""
    rng = np.random.RandomState(42)
    y_true = rng.binomial(1, 0.3, size=200)
    # Well-calibrated probabilities
    y_prob = np.clip(y_true * 0.6 + rng.uniform(0.1, 0.3, size=200), 0.01, 0.99)

    slope, intercept = ModelEvaluator.compute_calibration_slope_intercept(y_true, y_prob)

    assert slope is not None
    assert intercept is not None
    # Slope should be positive for positively correlated predictions
    assert slope > 0.0


# ==============================================================================
# J3: Warning Lead-Time Gain vs Spread-Only Baseline Tests
# ==============================================================================

def test_j3_warning_lead_time_gain():
    """Verify lead-time gain computation against ensemble spread-only baseline."""
    # 3 bust events tracked at 24h, 48h, 72h, 120h lead
    veyra_leads = [
        ("ev1", 120.0, 0.30),
        ("ev1", 72.0, 0.65),  # Veyra flags at 72h
        ("ev1", 48.0, 0.80),
        ("ev1", 24.0, 0.90),
        ("ev2", 72.0, 0.40),
        ("ev2", 48.0, 0.70),  # Veyra flags at 48h
        ("ev2", 24.0, 0.85),
        ("ev3", 48.0, 0.35),
        ("ev3", 24.0, 0.75),  # Veyra flags at 24h
    ]

    # Spread baseline flags later (e.g. higher spread only at short lead)
    spread_leads = [
        ("ev1", 120.0, 1.2),
        ("ev1", 72.0, 1.5),
        ("ev1", 48.0, 2.5),  # Spread flags at 48h
        ("ev1", 24.0, 3.2),
        ("ev2", 72.0, 1.1),
        ("ev2", 48.0, 1.8),
        ("ev2", 24.0, 2.8),  # Spread flags at 24h
        ("ev3", 48.0, 1.0),
        ("ev3", 24.0, 1.5),  # Spread does not cross 90th pct (cut ~2.7)
    ]

    report = compute_warning_lead_time_gain(
        veyra_leads,
        spread_leads,
        threshold_veyra=0.50,
        threshold_spread_pct=0.70,
    )

    assert report.total_bust_events == 3
    assert report.median_lead_time_gain_hours >= 0.0
    assert report.pct_flagged_24h_veyra == 1.0  # All 3 events flagged at >= 24h
    assert report.pct_flagged_48h_veyra == pytest.approx(2 / 3, 0.01)
    assert report.pct_flagged_72h_veyra == pytest.approx(1 / 3, 0.01)
    assert report.lead_time_gain_24h_gain_pct >= 0.0


# ==============================================================================
# J4: Spatial and Object Metrics Tests
# ==============================================================================

def test_j4_fractions_skill_score():
    """Verify Fractions Skill Score (FSS) properties across neighborhood scales."""
    # 10x10 grid with a centered 2x2 event
    obs = np.zeros((10, 10))
    obs[4:6, 4:6] = 1.0

    # Perfect forecast
    fss_perfect = compute_fss(obs, obs, threshold=0.5, window_size=3)
    assert fss_perfect == 1.0

    # Slightly displaced forecast (1 pixel right)
    pred_shifted = np.zeros((10, 10))
    pred_shifted[4:6, 5:7] = 1.0

    fss_scale3 = compute_fss(pred_shifted, obs, threshold=0.5, window_size=3)
    fss_scale5 = compute_fss(pred_shifted, obs, threshold=0.5, window_size=5)

    # FSS should increase with larger neighborhood window
    assert 0.0 <= fss_scale3 <= 1.0
    assert fss_scale5 >= fss_scale3


def test_j4_object_iou_and_centroid_error():
    """Verify object IoU and centroid displacement error."""
    # 20x20 grid
    obs = np.zeros((20, 20))
    obs[5:10, 5:10] = 1.0  # 5x5 box = 25 pixels

    pred = np.zeros((20, 20))
    pred[5:10, 8:13] = 1.0  # 5x5 box shifted by 3 columns

    iou = compute_object_iou(pred, obs, threshold=0.5)
    # Overlap is 5 rows x 2 cols = 10. Union is 25 + 25 - 10 = 40. IoU = 10/40 = 0.25
    assert iou == pytest.approx(0.25, 0.01)

    c_err = compute_centroid_error(pred, obs, threshold=0.5)
    assert c_err == pytest.approx(3.0, 0.01)  # Shifted 3 cols horizontally


def test_j4_top_k_spatial_recall():
    """Verify top-k regional recall."""
    y_prob = np.array([0.9, 0.8, 0.7, 0.2, 0.1])
    y_true = np.array([1, 0, 1, 1, 0])  # 3 busts total

    # Top-2 gives indices 0 and 1 -> busts caught = 1 out of 3 -> recall = 1/3
    rec_k2 = compute_top_k_spatial_recall(y_prob, y_true, k=2)
    assert rec_k2 == pytest.approx(1 / 3, 0.01)

    # Top-3 gives indices 0, 1, 2 -> busts caught = 2 out of 3 -> recall = 2/3
    rec_k3 = compute_top_k_spatial_recall(y_prob, y_true, k=3)
    assert rec_k3 == pytest.approx(2 / 3, 0.01)


def test_j4_evaluate_spatial_grid_report():
    """Verify high-level spatial grid evaluation report."""
    pred = np.random.uniform(0, 1, (15, 15))
    obs = np.random.binomial(1, 0.2, (15, 15))

    report = evaluate_spatial_grid(pred, obs, threshold=0.5, window_sizes=[3, 5])
    assert "3x3" in report.fss_by_scale
    assert "5x5" in report.fss_by_scale
    assert 0.0 <= report.mean_fss <= 1.0
    assert 0.0 <= report.object_iou <= 1.0
    assert 0.0 <= report.top_k_recall <= 1.0


# ==============================================================================
# J5: Safety and Selective Prediction Tests
# ==============================================================================

def test_j5_safety_coverage_risk_metrics():
    """Verify selective prediction, coverage-risk curves, and high-confidence error rate."""
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 0, 1])
    y_prob = np.array([0.05, 0.1, 0.15, 0.2, 0.9, 0.85, 0.8, 0.95, 0.5, 0.7])
    # 5th item is false positive (prob 0.9, true 0) with high uncertainty 0.85
    uncertainty = np.array([0.1, 0.1, 0.2, 0.1, 0.85, 0.15, 0.2, 0.1, 0.4, 0.2])

    report = compute_safety_coverage_risk_metrics(
        y_true=y_true,
        y_prob=y_prob,
        uncertainty_or_ood=uncertainty,
    )

    assert len(report.coverage_risk_curve) > 0
    assert report.retained_samples_count == 9  # Item 5 with 0.85 > 0.70 abstained
    assert report.overall_abstention_rate == pytest.approx(0.10, 0.01)
    assert report.retained_case_brier_score is not None
    assert report.risk_reduction_pct > 0.0  # Removing high-error sample reduces Brier


# ==============================================================================
# J6: Multi-Dimensional Stratification Tests
# ==============================================================================

def test_j6_stratified_evaluation():
    """Verify multi-dimensional stratification across season, lead, region, variable, regime."""
    records = []
    # Generate 100 synthetic verification records
    for i in range(100):
        records.append({
            "season": "JJAS" if i < 50 else "DJF",
            "lead_time_hours": "24h" if i % 2 == 0 else "72h",
            "region": "IN_NORTH" if i % 3 == 0 else "IN_SOUTH",
            "variable": "2m_temperature" if i % 4 == 0 else "total_precipitation",
            "regime": "ACTIVE_MONSOON" if i < 40 else "QUIET",
            "provider": "GEFS",
            "model_version": "v3.0.0",
            "bust": 1 if (i % 5 == 0) else 0,
            "p_bust": 0.8 if (i % 5 == 0) else 0.1,
        })

    report = StratifiedEvaluator.evaluate_records(records)

    assert report.total_samples == 100
    assert "season" in report.strata
    assert "lead_time_hours" in report.strata
    assert "region" in report.strata

    # Check season strata
    season_strata = {s.stratum_value: s for s in report.strata["season"]}
    assert "JJAS" in season_strata
    assert "DJF" in season_strata
    assert season_strata["JJAS"].sample_count == 50
    assert season_strata["DJF"].sample_count == 50
    assert season_strata["JJAS"].pr_auc is not None


def test_j6_month_to_season():
    """Verify Indian meteorological season mapping."""
    assert month_to_season(1) == "DJF"
    assert month_to_season(4) == "MAM"
    assert month_to_season(7) == "JJAS"
    assert month_to_season(10) == "ON"


# ==============================================================================
# J8: Operational Burden Tests
# ==============================================================================

def test_j8_operational_burden_metrics():
    """Verify false alerts per cycle, persistence, review time, and fixed-budget recall."""
    y_true = np.array([0, 1, 0, 0, 1, 0, 1, 0, 0, 0])
    y_prob = np.array([0.1, 0.9, 0.8, 0.2, 0.85, 0.7, 0.6, 0.1, 0.05, 0.3])
    cycle_ids = ["c1", "c1", "c1", "c1", "c1", "c2", "c2", "c2", "c2", "c2"]

    trajectories = [
        [True, True, True],   # Persisted 2 transitions
        [True, False, False], # Flickered
        [False, True, True],  # Flickered then persisted
    ]

    report = OperationalBurdenEvaluator.evaluate(
        y_true=y_true,
        y_prob=y_prob,
        cycle_ids=cycle_ids,
        decision_threshold=0.5,
        sequential_trajectories=trajectories,
    )

    assert report.total_samples == 10
    assert report.total_cycles == 2
    assert report.total_alerts == 5
    assert report.false_alerts == 2  # indices 2 (0.8) and 5 (0.7) are false positives
    assert report.false_alerts_per_cycle == 1.0  # 2 false alerts / 2 cycles
    assert report.alert_persistence_rate is not None
    assert report.alert_flicker_rate is not None
    assert report.estimated_review_time_hours == (5 * 15.0) / 60.0  # 1.25 hours
    assert report.recall_at_5pct_budget <= report.recall_at_20pct_budget


# ==============================================================================
# J9: Explanation Quality Tests
# ==============================================================================

def test_j9_explanation_quality_metrics():
    """Verify explanation stability, perturbation fidelity, and forecaster agreement."""
    # Top-k Jaccard
    assert compute_top_k_jaccard(["A", "B", "C"], ["A", "B", "C"]) == 1.0
    assert compute_top_k_jaccard(["A", "B", "C"], ["A", "B", "D"]) == pytest.approx(2 / 4, 0.01)

    # Spearman rank correlation
    assert compute_spearman_rank_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0

    # Fidelity drop
    drop = compute_fidelity_drop(0.85, 0.35)
    assert drop == 0.50

    # Forecaster agreement
    m_reasons = [["REVISION_ACCEL", "SPREAD_BIAS"], ["JET_CORE"]]
    exp_reasons = [["REVISION_ACCEL"], ["BLOCKING_INDEX"]]
    agr = compute_forecaster_agreement(m_reasons, exp_reasons)
    assert agr == 0.5  # 1 out of 2 matches


def test_j9_explanation_evaluator_synthetic():
    """Verify synthetic explanation quality report generation."""
    report = ExplanationQualityEvaluator.evaluate_synthetic(sample_count=100)
    assert report.total_evaluated_cases == 100
    assert report.mean_attribution_stability >= 0.80
    assert report.mean_fidelity_drop > 0.10
    assert report.forecaster_agreement_rate >= 0.80
    assert report.summary_verdict == "PASS"


# ==============================================================================
# Comprehensive Evaluation Framework & API Endpoint Tests
# ==============================================================================

def test_veyra_evaluation_framework_full_run():
    """Verify end-to-end VeyraEvaluationFramework orchestrator."""
    rng = np.random.RandomState(42)
    y_true = rng.binomial(1, 0.1, size=200)
    y_prob = np.clip(y_true * 0.5 + rng.uniform(0.05, 0.3, size=200), 0.01, 0.99)

    report = VeyraEvaluationFramework.run_full_evaluation(
        y_true=y_true,
        y_prob=y_prob,
        model_name="veyra-v3",
        model_version="v3.0.0",
    )

    assert isinstance(report, ComprehensiveEvaluationReport)
    assert report.pr_auc > 0.0
    assert report.roc_auc > 0.5
    assert report.warning_lead_time_gain.median_lead_time_gain_hours > 0.0
    assert report.safety_coverage_risk.retained_samples_count <= 200
    assert report.operational_burden.total_samples == 200
    assert report.explanation_quality.summary_verdict == "PASS"

    d = report.to_dict()
    assert "discrimination_and_probability" in d
    assert "warning_lead_time_gain" in d
    assert "safety_coverage_risk" in d
    assert "operational_burden" in d
    assert "explanation_quality" in d


def test_evaluation_service_v3_comprehensive():
    """Verify EvaluationIntegrationService exposes comprehensive evaluation data."""
    service = EvaluationIntegrationService()
    v3_eval = service.get_v3_evaluation()

    assert v3_eval.model_name == "lightgbm_v3_challenger"
    assert v3_eval.metrics.log_loss is not None
    assert v3_eval.metrics.calibration_slope is not None
    assert v3_eval.metrics.warning_lead_time_gain_hours == 24.0
    assert v3_eval.comprehensive_evaluation is not None
    assert "warning_lead_time_gain" in v3_eval.comprehensive_evaluation
    assert "spatial_metrics" in v3_eval.comprehensive_evaluation


def test_api_comprehensive_evaluation_endpoint(client):
    """Verify GET /v1/model/evaluation/comprehensive endpoint."""
    response = client.get("/v1/model/evaluation/comprehensive?model=v3")
    assert response.status_code == 200
    data = response.json()

    assert "discrimination_and_probability" in data
    assert "warning_lead_time_gain" in data
    assert "spatial_metrics" in data
    assert "safety_coverage_risk" in data
    assert "stratified_evaluation" in data
    assert "operational_burden" in data
    assert "explanation_quality" in data

    # Verify key J2-J9 metrics
    assert data["discrimination_and_probability"]["brier_score"] == pytest.approx(0.053798, 1e-4)
    assert data["warning_lead_time_gain"]["median_lead_time_gain_hours"] == 24.0
    assert data["spatial_metrics"]["mean_fss"] > 0.8
    assert data["safety_coverage_risk"]["overall_abstention_rate"] == 0.042
    assert data["operational_burden"]["false_alerts_per_cycle"] == 18.5
    assert data["explanation_quality"]["summary_verdict"] == "PASS"
