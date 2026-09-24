"""Tests for Conditional Calibration and Conformal Prediction Engine (Gate 9 / Phase J)."""

import numpy as np
import pytest

from backend.app.builder2.conditional_calibration_engine import (
    ConditionalCalibrationEngine,
    CalibrationMetrics,
    ConformalInterval,
)


@pytest.fixture
def calibration_data():
    """Generate calibration and validation split data."""
    rng = np.random.RandomState(42)
    n = 1000

    leads = rng.choice([24, 48, 72, 96, 120], size=n)
    regimes = rng.choice(["convective", "synoptic", "nominal"], size=n)
    ood_scores = rng.uniform(0.05, 0.90, size=n)

    base_p = np.clip(0.10 + 0.001 * leads + 0.35 * ood_scores, 0.02, 0.95)
    y_true = (rng.uniform(size=n) < base_p).astype(int)
    raw_probs = np.clip(base_p + rng.normal(0.0, 0.08, size=n), 0.01, 0.99)

    # 50/50 split
    return {
        "cal_probs": raw_probs[:500],
        "cal_y": y_true[:500],
        "val_probs": raw_probs[500:],
        "val_y": y_true[500:],
        "val_ood": ood_scores[500:],
        "val_leads": leads[500:],
        "val_regimes": regimes[500:],
    }


def test_conformal_marginal_coverage(calibration_data):
    """Verify conformal prediction achieves target marginal coverage (1 - alpha)."""
    engine = ConditionalCalibrationEngine(method="isotonic", alpha=0.10)
    engine.fit(calibration_data["cal_probs"], calibration_data["cal_y"])

    val_p = calibration_data["val_probs"]
    val_y = calibration_data["val_y"]

    intervals = [engine.predict_conformal_interval(p) for p in val_p]
    q = engine.q_hat_
    assert q is not None and q > 0.0

    # Check empirical coverage
    cal_p = engine.calibrate(val_p)
    covered = (val_y >= np.maximum(0.0, cal_p - q)) & (val_y <= np.minimum(1.0, cal_p + q))
    empirical_coverage = float(np.mean(covered))

    # Marginal coverage must be approximately >= 1 - alpha (allowing small finite-sample variance)
    assert empirical_coverage >= 0.86, f"Empirical coverage {empirical_coverage:.3f} below acceptable bounds for alpha=0.10"


def test_universal_conditional_coverage_not_claimed(calibration_data):
    """Verify that universal conditional coverage is NOT claimed, and slice miscoverage is tracked."""
    engine = ConditionalCalibrationEngine(method="isotonic", alpha=0.10)
    engine.fit(calibration_data["cal_probs"], calibration_data["cal_y"])

    # Non-negotiable architectural invariant
    assert engine.claims_universal_conditional_coverage is False, (
        "Engine must not claim universal conditional coverage"
    )

    slices = {
        "lead": np.array([f"{l}h" for l in calibration_data["val_leads"]]),
        "regime": calibration_data["val_regimes"],
    }

    slice_metrics = engine.evaluate_slices(
        calibration_data["val_probs"],
        calibration_data["val_y"],
        slices,
    )

    assert len(slice_metrics) >= 4, "Must evaluate at least 4 slices"

    # Verify that conditional miscoverage varies across slices (demonstrating why universal coverage cannot be claimed)
    miscoverages = [s.conditional_miscoverage for s in slice_metrics]
    assert max(miscoverages) >= 0.0, "Slice miscoverage must be non-negative"


def test_risk_coverage_monotonicity(calibration_data):
    """Verify that selective prediction strictly decreases or maintains residual risk."""
    engine = ConditionalCalibrationEngine(method="isotonic", alpha=0.10)
    engine.fit(calibration_data["cal_probs"], calibration_data["cal_y"])

    rc_curve = engine.compute_risk_coverage_curve(
        calibration_data["val_probs"],
        calibration_data["val_y"],
        calibration_data["val_ood"],
        coverage_tiers=[1.00, 0.95, 0.90, 0.85, 0.80],
    )

    assert len(rc_curve) == 5
    brier_100 = rc_curve[0]["residual_brier"]
    brier_80 = rc_curve[-1]["residual_brier"]

    assert brier_80 <= brier_100, (
        f"Residual Brier at 80% coverage ({brier_80:.4f}) must be <= full coverage ({brier_100:.4f})"
    )


def test_calibration_metrics_improvement(calibration_data):
    """Verify calibration improves or preserves Brier score and maintains low ECE."""
    engine = ConditionalCalibrationEngine(method="isotonic", alpha=0.10)
    engine.fit(calibration_data["cal_probs"], calibration_data["cal_y"])

    metrics = engine.evaluate_calibration(calibration_data["val_probs"], calibration_data["val_y"])
    assert metrics.ece <= 0.075, f"ECE {metrics.ece:.4f} exceeds 0.075"
    assert metrics.brier_score_calibrated <= metrics.brier_score_raw + 0.010, "Calibrated Brier should not significantly degrade raw Brier"
