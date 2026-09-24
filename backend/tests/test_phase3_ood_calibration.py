"""Phase 3 Comprehensive Test Suite: OOD, Calibration & Abstention Layer.

Verifies:
- Task F2: Reliability diagrams, calibration slope/intercept, log-loss, ECE, MCE.
- Task F4: Split conformal prediction intervals, conditional coverage, method declaration.
- Task F5: Multi-signal OOD scoring (feature distance, regime novelty, KS/Wasserstein drift).
- Task F6: Explicit NORMAL / UNUSUAL / OOD / ABSTAIN state machine per §11.3.
- Task F7: Coverage-risk curves, retained-case risk, and forecaster review burden.
- Task E8: Multi-dimensional holdouts (region holdouts, model-version holdouts).
"""
import math
import numpy as np
import pytest

from backend.app.data.training_dataset import HistoricalTrainingRow
from backend.app.ml.conformal import (
    METHOD_DECLARATION,
    ConformalCoverageReport,
    ConformalInterval,
    SplitConformalPredictor,
)
from backend.app.ml.evaluation import (
    EvaluationReport,
    ModelEvaluator,
    ReliabilityDiagram,
)
from backend.app.ml.splitting import (
    ModelVersionHoldoutSplitter,
    MultiDimensionalHoldoutSplitter,
    RegionHoldoutSplitter,
)
from backend.app.safety.abstention import (
    CoverageRiskPoint,
    SafetyAssessment,
    SafetyEvaluator,
    compute_coverage_risk_curve,
)
from backend.app.safety.ood_detector import (
    OODDetector,
    OODResult,
    OODState,
)
from backend.app.schemas.prediction import ReasonCode, RiskLevel, TrustState
from backend.app.services.base import FeatureResult, ModelResult, WeatherResult


# =========================================================================
# 1. OOD DETECTOR: MULTI-SIGNAL SCORING & STATE VOCABULARY (§11.3, F5, F6)
# =========================================================================

def test_ood_detector_nominal_normal_state():
    """Verify that nominal feature vectors produce NORMAL state with ood_score < 0.35."""
    detector = OODDetector()
    nominal_features = {
        "ensemble_mean": 298.15,
        "ensemble_std": 1.5,
        "surface_pressure": 101325.0,
        "wind_speed_10m": 4.5,
        "relative_humidity_2m": 65.0,
        "lead_hours": 72.0,
    }
    result = detector.evaluate(nominal_features, regime_context={"blocking_index": 0.0})
    assert isinstance(result, OODResult)
    assert result.state == OODState.NORMAL
    assert result.ood_score < 0.35
    assert result.feature_distance < 0.20


def test_ood_detector_unusual_tail_state():
    """Verify that moderate anomalies trigger UNUSUAL state with caution banner (0.35 <= score < 0.65)."""
    detector = OODDetector()
    # Shift several features by ~2.5 - 3.0 standard deviations
    unusual_features = {
        "ensemble_mean": 320.0,  # Hot tail
        "ensemble_std": 4.5,     # Elevated spread
        "surface_pressure": 98000.0,
        "wind_speed_10m": 12.0,
        "lead_hours": 72.0,
    }
    result = detector.evaluate(unusual_features, regime_context={"blocking_index": 1.8})
    assert result.state in (OODState.UNUSUAL, OODState.OOD)
    assert result.ood_score >= 0.35
    assert len(result.dominant_drivers) > 0


def test_ood_detector_extreme_ood_and_abstain():
    """Verify that extreme atmospheric anomalies trigger OOD or ABSTAIN states (score >= 0.65)."""
    detector = OODDetector()
    extreme_features = {
        "ensemble_mean": 350.0,     # Unprecedented heat
        "ensemble_std": 10.0,       # Extreme ensemble divergence
        "surface_pressure": 92000.0, # Deep cyclonic low
        "wind_speed_10m": 35.0,     # Hurricane-force wind
        "lead_hours": 240.0,
    }
    regime_ctx = {
        "blocking_index": 4.0,
        "rossby_wave_activity_index": 3.5,
        "jet_latitude": 60.0,
        "is_cyclonic_episode": True,
    }
    result = detector.evaluate(extreme_features, regime_context=regime_ctx)
    assert result.state in (OODState.OOD, OODState.ABSTAIN)
    assert result.ood_score >= 0.65
    assert "cyclonic_vortex_regime" in result.dominant_drivers


def test_ood_distribution_drift_ks_and_wasserstein():
    """Verify Kolmogorov-Smirnov and Wasserstein drift metrics between distributions."""
    ref_vals = np.random.normal(loc=25.0, scale=3.0, size=200)
    same_vals = np.random.normal(loc=25.0, scale=3.0, size=200)
    shifted_vals = np.random.normal(loc=40.0, scale=5.0, size=200)

    # Identical distribution -> low KS and Wasserstein
    ks_same = OODDetector.compute_distribution_drift_ks(same_vals, ref_vals)
    w_same = OODDetector.compute_wasserstein_distance(same_vals, ref_vals)
    assert ks_same < 0.25
    assert w_same < 2.0

    # Shifted distribution -> high KS and Wasserstein
    ks_shifted = OODDetector.compute_distribution_drift_ks(shifted_vals, ref_vals)
    w_shifted = OODDetector.compute_wasserstein_distance(shifted_vals, ref_vals)
    assert ks_shifted > 0.70
    assert w_shifted > 10.0


# =========================================================================
# 2. SAFETY EVALUATOR: STATE MACHINE INTEGRATION (§11.3, F6)
# =========================================================================

def test_safety_evaluator_ood_normal_transition():
    """NORMAL state -> High confidence prediction with calibrated probability."""
    evaluator = SafetyEvaluator()
    feat_res = FeatureResult(
        location="Kolkata",
        features={"ensemble_mean": 298.15, "ensemble_std": 1.5, "lead_hours": 24},
        is_ready=True,
    )
    model_res = ModelResult(probability=0.15, is_ready=True)

    assessment = evaluator.evaluate(feature_result=feat_res, model_result=model_res)
    assert assessment.abstain is False
    assert assessment.bust_probability == 0.15
    assert assessment.ood_state == OODState.NORMAL
    assert assessment.trust_state == TrustState.HIGH_CONFIDENCE


def test_safety_evaluator_ood_unusual_transition():
    """UNUSUAL state -> Moderate confidence with caution banner."""
    evaluator = SafetyEvaluator()
    feat_res = FeatureResult(
        location="Kolkata",
        features={"ensemble_mean": 322.0, "ensemble_std": 4.5, "lead_hours": 72},
        is_ready=True,
        metadata={"regime_context": {"blocking_index": 2.0}},
    )
    model_res = ModelResult(probability=0.45, is_ready=True)

    assessment = evaluator.evaluate(feature_result=feat_res, model_result=model_res)
    assert assessment.abstain is False
    assert assessment.ood_state == OODState.UNUSUAL
    assert assessment.trust_state == TrustState.MODERATE_CONFIDENCE
    assert assessment.metadata.get("caution_banner") is True


def test_safety_evaluator_ood_abstain_transition():
    """ABSTAIN state -> bust_probability set to None, OOD_ABSTAIN reason code."""
    evaluator = SafetyEvaluator()
    # Extremely anomalous features that breach abstain threshold
    feat_res = FeatureResult(
        location="Kolkata",
        features={
            "ensemble_mean": 360.0,
            "ensemble_std": 15.0,
            "surface_pressure": 85000.0,
            "wind_speed_10m": 45.0,
            "lead_hours": 240.0,
        },
        is_ready=True,
        metadata={"regime_context": {"blocking_index": 5.0, "rossby_wave_activity_index": 4.0, "is_cyclonic_episode": True}},
    )
    model_res = ModelResult(probability=0.92, is_ready=True)

    assessment = evaluator.evaluate(feature_result=feat_res, model_result=model_res)
    assert assessment.abstain is True
    assert assessment.bust_probability is None
    assert assessment.trust_state == TrustState.ABSTAINED
    assert ReasonCode.OOD_ABSTAIN.value in assessment.reason_codes
    assert assessment.ood_state == OODState.ABSTAIN


# =========================================================================
# 3. SPLIT CONFORMAL PREDICTION INTERVALS (§11.2, F4)
# =========================================================================

def test_split_conformal_predictor_calibration_and_intervals():
    """Verify conformal calibration quantile and bounded prediction interval construction."""
    predictor = SplitConformalPredictor(confidence_level=0.90)
    assert predictor.is_calibrated is False

    # Synthetic calibration set (n=100)
    np.random.seed(42)
    y_true = np.random.binomial(1, 0.25, 100)
    y_prob = np.clip(y_true * 0.7 + np.random.uniform(0.05, 0.25, 100), 0.0, 1.0)

    predictor.calibrate(y_true, y_prob)
    assert predictor.is_calibrated is True
    assert predictor.calibrated_quantile is not None
    assert 0.0 < predictor.calibrated_quantile < 1.0

    # Predict interval for a single test point
    interval = predictor.predict_interval(probability=0.35)
    assert isinstance(interval, ConformalInterval)
    assert interval.probability == 0.35
    assert 0.0 <= interval.lower_bound <= interval.probability
    assert interval.probability <= interval.upper_bound <= 1.0
    assert interval.bandwidth == round(interval.upper_bound - interval.lower_bound, 4)
    assert interval.method == METHOD_DECLARATION


def test_conformal_conditional_coverage_reporting():
    """Verify conformal empirical coverage evaluation overall and stratified by lead and region."""
    predictor = SplitConformalPredictor(confidence_level=0.90)

    np.random.seed(42)
    n = 200
    y_true = np.random.binomial(1, 0.30, n)
    y_prob = np.clip(y_true * 0.6 + np.random.uniform(0.1, 0.3, n), 0.0, 1.0)

    # Calibrate on first half
    predictor.calibrate(y_true[:100], y_prob[:100])

    # Evaluate on second half with lead_hours and regions
    leads = np.random.choice([24, 48, 72, 120], size=100)
    regions = np.random.choice(["Kolkata", "Delhi", "Mumbai"], size=100)

    report = predictor.evaluate_coverage(
        y_true=y_true[100:],
        y_prob=y_prob[100:],
        lead_hours=leads,
        regions=regions,
    )

    assert isinstance(report, ConformalCoverageReport)
    assert report.nominal_coverage == 0.90
    assert 0.70 <= report.empirical_coverage <= 1.0
    assert len(report.conditional_coverage_by_lead) > 0
    assert len(report.conditional_coverage_by_region) > 0
    assert report.method_declaration == METHOD_DECLARATION


# =========================================================================
# 4. EVALUATION: RELIABILITY DIAGRAMS, SLOPE/INTERCEPT, LOG-LOSS (§11.1, F2)
# =========================================================================

def test_model_evaluator_reliability_diagram_and_ece():
    """Verify reliability diagram 10-bin computation, ECE, and MCE."""
    y_true = np.array([0, 0, 0, 0, 1, 0, 1, 1, 1, 1] * 10)
    y_prob = np.linspace(0.05, 0.95, 100)

    rel_diag = ModelEvaluator.compute_reliability_diagram(y_true, y_prob, n_bins=10)
    assert isinstance(rel_diag, ReliabilityDiagram)
    assert len(rel_diag.prob_pred) == 10
    assert len(rel_diag.prob_true) == 10
    assert len(rel_diag.bin_counts) == 10
    assert sum(rel_diag.bin_counts) == 100
    assert 0.0 <= rel_diag.ece <= 1.0
    assert 0.0 <= rel_diag.mce <= 1.0


def test_model_evaluator_calibration_slope_and_intercept():
    """Verify Platt/logistic calibration slope and intercept calculation."""
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1] * 10)
    y_prob = np.linspace(0.05, 0.95, 100)

    slope, intercept = ModelEvaluator.compute_calibration_slope_intercept(y_true, y_prob)
    assert slope is not None
    assert intercept is not None
    # For monotonically aligned probabilities and labels, slope should be positive
    assert slope > 0.0


def test_model_evaluator_full_report_with_phase3_metrics():
    """Verify comprehensive EvaluationReport contains all Phase 3 metrics."""
    y_true = np.array([0, 0, 0, 0, 1, 0, 1, 1, 1, 1] * 10)
    y_prob = np.linspace(0.05, 0.95, 100)

    report = ModelEvaluator.evaluate(
        y_true=y_true,
        y_proba=y_prob,
        split_name="test_holdout",
        decision_threshold=0.5,
        is_calibrated=True,
    )

    assert isinstance(report, EvaluationReport)
    assert report.is_calibrated is True
    assert report.brier_score is not None
    assert report.log_loss_value is not None
    assert report.calibration_slope is not None
    assert report.calibration_intercept is not None
    assert report.expected_calibration_error is not None
    assert report.reliability_diagram is not None
    assert report.coverage_risk_curve is not None
    assert len(report.coverage_risk_curve) > 0
    assert report.review_burden is not None
    assert "ambiguous_cases_count" in report.review_burden


# =========================================================================
# 5. COVERAGE-RISK & REVIEW BURDEN (§11.4, F7)
# =========================================================================

def test_coverage_risk_curve_computation():
    """Verify compute_coverage_risk_curve returns monotonic coverage progression and risk metrics."""
    y_true = np.array([0, 0, 0, 1, 0, 1, 1, 0, 1, 1] * 10)
    y_prob = np.array([0.1, 0.2, 0.3, 0.8, 0.4, 0.7, 0.9, 0.35, 0.85, 0.75] * 10)

    curve = compute_coverage_risk_curve(y_true, y_prob, threshold_steps=5)
    assert len(curve) == 5
    for pt in curve:
        assert isinstance(pt, CoverageRiskPoint)
        assert 0.0 <= pt.coverage <= 1.0
        assert 0.0 <= pt.abstention_rate <= 1.0
        assert pt.retained_count + pt.abstained_count == len(y_true)
        assert 0.0 <= pt.risk <= 1.0


# =========================================================================
# 6. MULTI-DIMENSIONAL HOLDOUT SPLITTING (§10.4, E8)
# =========================================================================

def _make_split_row(idx: int, loc: str, issue_t: str, model_ver: str = "gfs_v1", ev_id: str = ""):
    row = HistoricalTrainingRow(
        location=loc,
        latitude=22.57,
        longitude=88.36,
        region="IN_EAST",
        variable="temperature_2m",
        issue_time=issue_t,
        valid_time=issue_t,
        lead_hours=24,
        forecast_value=25.0,
        reference_value=25.5,
        unit="degC",
        error=0.5,
        absolute_error=0.5,
        season="monsoon",
        month=8,
        bust_label=0,
        bust_threshold=2.5,
        metadata={"event_id": ev_id, "model_version": model_ver} if (ev_id or model_ver) else {},
    )
    row.model_version = model_ver
    row.event_id = ev_id
    return row


def test_region_holdout_splitter_execution():
    """Verify RegionHoldoutSplitter partitions held-out region exclusively into test."""
    splitter = RegionHoldoutSplitter(held_out_regions=["Kolkata"])
    rows = [
        _make_split_row(1, "Kolkata", "2026-08-01T00:00:00Z"),
        _make_split_row(2, "Kolkata", "2026-08-02T00:00:00Z"),
        _make_split_row(3, "Delhi", "2026-08-01T00:00:00Z"),
        _make_split_row(4, "Delhi", "2026-08-02T00:00:00Z"),
        _make_split_row(5, "Mumbai", "2026-08-01T00:00:00Z"),
        _make_split_row(6, "Mumbai", "2026-08-02T00:00:00Z"),
    ]
    splits = splitter.split(rows)
    assert len(splits.test_rows) == 2
    assert all(r.location == "Kolkata" for r in splits.test_rows)
    assert all(r.location != "Kolkata" for r in splits.train_rows)
    assert all(r.location != "Kolkata" for r in splits.val_rows)


def test_model_version_holdout_splitter_execution():
    """Verify ModelVersionHoldoutSplitter partitions held-out model versions exclusively into test."""
    splitter = ModelVersionHoldoutSplitter(held_out_model_versions=["gfs_v2_experimental"])
    rows = [
        _make_split_row(1, "Delhi", "2026-08-01T00:00:00Z", model_ver="gfs_v1"),
        _make_split_row(2, "Delhi", "2026-08-02T00:00:00Z", model_ver="gfs_v1"),
        _make_split_row(3, "Mumbai", "2026-08-01T00:00:00Z", model_ver="gfs_v1"),
        _make_split_row(4, "Mumbai", "2026-08-02T00:00:00Z", model_ver="gfs_v1"),
        _make_split_row(5, "Kolkata", "2026-08-01T00:00:00Z", model_ver="gfs_v2_experimental"),
    ]
    # Set model_version attribute
    rows[4].model_version = "gfs_v2_experimental"
    for r in rows[:4]:
        r.model_version = "gfs_v1"

    splits = splitter.split(rows)
    assert len(splits.test_rows) == 1
    assert getattr(splits.test_rows[0], "model_version", None) == "gfs_v2_experimental"


def test_multi_dimensional_holdout_splitter_execution():
    """Verify MultiDimensionalHoldoutSplitter combines region, event, and version holdouts."""
    splitter = MultiDimensionalHoldoutSplitter(
        held_out_regions=["Kolkata"],
        held_out_events=["cyclone_mocha"],
    )
    rows = [
        _make_split_row(1, "Delhi", "2026-08-01T00:00:00Z"),
        _make_split_row(2, "Delhi", "2026-08-02T00:00:00Z"),
        _make_split_row(3, "Mumbai", "2026-08-01T00:00:00Z"),
        _make_split_row(4, "Mumbai", "2026-08-02T00:00:00Z"),
        _make_split_row(5, "Kolkata", "2026-08-01T00:00:00Z"),  # Region holdout
        _make_split_row(6, "Delhi", "2026-08-03T00:00:00Z", ev_id="cyclone_mocha"),  # Event holdout
    ]
    splits = splitter.split(rows)
    assert len(splits.test_rows) == 2
    test_locs = {r.location for r in splits.test_rows}
    assert "Kolkata" in test_locs
    test_evs = {r.metadata.get("event_id") for r in splits.test_rows if r.metadata.get("event_id")}
    assert "cyclone_mocha" in test_evs
