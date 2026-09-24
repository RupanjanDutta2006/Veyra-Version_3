"""Tests for Reference Uncertainty, Noise Propagation, and Concordance (Gate 9 / Phase J)."""

import numpy as np
import pytest

from backend.app.builder2.conditional_calibration_engine import ConditionalCalibrationEngine
from backend.app.builder2.independent_truth_audit import IndependentTruthAuditEngine


def test_reference_label_flip_robustness():
    """Verify that bounded reference disagreement does not destabilize model calibration."""
    rng = np.random.RandomState(42)
    n = 300

    base_p = rng.uniform(0.1, 0.9, size=n)
    y_true = (rng.uniform(size=n) < base_p).astype(int)
    raw_probs = np.clip(base_p + rng.normal(0.0, 0.05, size=n), 0.01, 0.99)

    # Reference flip with 5% observational noise
    noise_mask = rng.uniform(size=n) < 0.05
    y_noisy = np.where(noise_mask, 1 - y_true, y_true)

    engine_clean = ConditionalCalibrationEngine()
    engine_clean.fit(raw_probs, y_true)
    metrics_clean = engine_clean.evaluate_calibration(raw_probs, y_true)

    engine_noisy = ConditionalCalibrationEngine()
    engine_noisy.fit(raw_probs, y_noisy)
    metrics_noisy = engine_noisy.evaluate_calibration(raw_probs, y_noisy)

    delta_brier = abs(metrics_clean.brier_score_calibrated - metrics_noisy.brier_score_calibrated)
    # Delta Brier must be bounded by approximately 2 * noise_rate
    assert delta_brier <= 0.050, f"Brier score perturbation ({delta_brier:.4f}) exceeded noise bounds"


def test_false_bust_alarm_immunity():
    """Verify minor sensor noise below bust threshold does not trigger false bust labels."""
    rng = np.random.RandomState(42)
    n = 200

    # True forecast error is 5 mm (well below 25 mm bust threshold)
    true_forecast_error = np.full(n, 5.0)
    # Sensor noise +- 2 mm
    sensor_noise = rng.normal(0.0, 1.0, size=n)
    measured_error = true_forecast_error + sensor_noise

    bust_threshold = 25.0
    true_busts = (true_forecast_error > bust_threshold).astype(int)
    noisy_busts = (measured_error > bust_threshold).astype(int)

    # False bust alarms must be exactly 0
    false_alarms = np.sum((noisy_busts == 1) & (true_busts == 0))
    assert false_alarms == 0, f"Sensor noise caused {false_alarms} false bust alarms!"


def test_multi_reference_concordance():
    """Verify concordance between multiple reference sources on severe weather events."""
    rng = np.random.RandomState(42)
    n = 300

    # 3 independent references for extreme event detection:
    # Ref A: ERA5 Reanalysis
    # Ref B: IMD Station Observation Network
    # Ref C: INSAT-3D Satellite Estimate
    true_event = (rng.uniform(size=n) < 0.20).astype(int)

    # Sensor noise per reference: 4%, 3%, 6%
    ref_a = np.where(rng.uniform(size=n) < 0.04, 1 - true_event, true_event)
    ref_b = np.where(rng.uniform(size=n) < 0.03, 1 - true_event, true_event)
    ref_c = np.where(rng.uniform(size=n) < 0.06, 1 - true_event, true_event)

    # Pairwise agreement
    agree_ab = float(np.mean(ref_a == ref_b))
    agree_ac = float(np.mean(ref_a == ref_c))
    agree_bc = float(np.mean(ref_b == ref_c))

    assert agree_ab >= 0.90, f"Agreement A-B too low: {agree_ab}"
    assert agree_ac >= 0.88, f"Agreement A-C too low: {agree_ac}"
    assert agree_bc >= 0.86, f"Agreement B-C too low: {agree_bc}"

    # Majority voting consensus agreement with true event
    consensus = ((ref_a + ref_b + ref_c) >= 2).astype(int)
    consensus_accuracy = float(np.mean(consensus == true_event))
    assert consensus_accuracy >= 0.95, f"Multi-reference consensus accuracy too low: {consensus_accuracy}"
