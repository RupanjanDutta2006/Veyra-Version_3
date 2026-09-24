"""Tests for Hazard Calibration Registry, OOD Drift Ledger, and Abstention Policy (Gate 9 / Phase J)."""

import json
from pathlib import Path
import pytest

from backend.app.builder2.abstention_policy import (
    AbstentionPolicy,
    AbstentionReason,
    OperationalPredictionStatus,
)


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def calibration_registry(repo_root):
    path = repo_root / "data" / "hazard_calibration_registry.json"
    assert path.is_file(), f"hazard_calibration_registry.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def ood_drift_ledger(repo_root):
    path = repo_root / "data" / "ood_drift_ledger.json"
    assert path.is_file(), f"ood_drift_ledger.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_hazard_calibration_registry_structure(calibration_registry):
    """Verify registry covers all 6 hazards and enforces calibration invariants."""
    expected_hazards = [
        "PRECIPITATION",
        "CYCLONE",
        "MONSOON_LPS",
        "WESTERN_DISTURBANCE",
        "HEATWAVE",
        "SEVERE_WIND",
    ]
    hazards = calibration_registry.get("hazards", {})
    for haz in expected_hazards:
        assert haz in hazards, f"Missing hazard in calibration registry: {haz}"
        entry = hazards[haz]

        # Calibration must improve or maintain Brier score
        assert entry["brier_score_calibrated"] <= entry["brier_score_uncalibrated"], (
            f"Calibrated Brier ({entry['brier_score_calibrated']}) must be <= uncalibrated ({entry['brier_score_uncalibrated']}) for {haz}"
        )

        # Quality metrics
        assert entry["expected_calibration_error_ece"] <= 0.050, f"ECE too high for {haz}: {entry['expected_calibration_error_ece']}"
        assert entry["maximum_calibration_error_mce"] <= 0.100, f"MCE too high for {haz}: {entry['maximum_calibration_error_mce']}"

        # Risk-coverage curve monotonicity
        rc = entry["risk_coverage_curve"]
        assert len(rc) >= 3, f"Risk coverage curve must have at least 3 tiers for {haz}"
        assert rc[-1]["residual_brier"] <= rc[0]["residual_brier"], (
            f"Selective coverage (80%) must reduce residual risk compared to 100% for {haz}"
        )

    # Invariant: Never claim universal conditional coverage
    inv = calibration_registry.get("invariants", {})
    assert inv.get("claims_universal_conditional_coverage") is False, (
        "Registry must explicitly specify claims_universal_conditional_coverage: false"
    )


def test_ood_drift_ledger_integrity(ood_drift_ledger):
    """Verify OOD drift ledger tracks feature baselines and PSI metrics."""
    baselines = ood_drift_ledger.get("hazard_baselines", {})
    assert len(baselines) >= 6, "Drift ledger must track baselines for all 6 hazards"

    for haz, data in baselines.items():
        assert "features" in data, f"Missing features in drift baseline for {haz}"
        assert "current_drift_metrics" in data, f"Missing drift metrics for {haz}"

        drift_metrics = data["current_drift_metrics"]
        assert drift_metrics["drift_status"] in ["IN_BOUNDS", "MODERATE_DRIFT", "SEVERE_DRIFT_ABSTAIN"]
        assert drift_metrics["overall_psi"] >= 0.0

    audit_log = ood_drift_ledger.get("historical_drift_audit_log", [])
    assert len(audit_log) >= 3, "Historical drift audit log must contain tracked cycles"


def test_abstention_policy_ood_and_uncertainty():
    """Verify AbstentionPolicy gates predictions based on OOD and uncertainty thresholds."""
    policy = AbstentionPolicy(
        ood_threshold_abstain=0.85,
        ood_threshold_diagnostic=0.65,
        epistemic_uncertainty_threshold=0.40,
    )

    # 1. Nominal state: predict
    dec_nom = policy.evaluate("PRECIPITATION", ood_score=0.15, epistemic_uncertainty=0.10)
    assert dec_nom.status == OperationalPredictionStatus.PREDICT
    assert not dec_nom.should_abstain
    assert dec_nom.reason is None

    # 2. Moderate OOD state: diagnostic only
    dec_diag = policy.evaluate("PRECIPITATION", ood_score=0.72, epistemic_uncertainty=0.15)
    assert dec_diag.status == OperationalPredictionStatus.DIAGNOSTIC_ONLY
    assert not dec_diag.should_abstain

    # 3. Extreme OOD state: abstain
    dec_ood = policy.evaluate("PRECIPITATION", ood_score=0.92, epistemic_uncertainty=0.15)
    assert dec_ood.status == OperationalPredictionStatus.ABSTAIN
    assert dec_ood.should_abstain
    assert dec_ood.reason == AbstentionReason.OOD_EXCEEDED

    # 4. Excessive epistemic uncertainty: abstain
    dec_unc = policy.evaluate("CYCLONE", ood_score=0.20, epistemic_uncertainty=0.45)
    assert dec_unc.status == OperationalPredictionStatus.ABSTAIN
    assert dec_unc.should_abstain
    assert dec_unc.reason == AbstentionReason.EPISTEMIC_UNCERTAINTY_HIGH


def test_abstention_policy_unsupported_state():
    """Verify AbstentionPolicy handles physical inconsistency and missing references."""
    policy = AbstentionPolicy()

    # Reference unavailable
    dec_ref = policy.evaluate("HEATWAVE", ood_score=0.20, reference_available=False)
    assert dec_ref.status == OperationalPredictionStatus.ABSTAIN
    assert dec_ref.reason == AbstentionReason.REFERENCE_UNAVAILABLE
    assert "unavailable" in dec_ref.explanation.lower()

    # Physical inconsistency
    dec_phys = policy.evaluate("WESTERN_DISTURBANCE", ood_score=0.20, physical_valid=False)
    assert dec_phys.status == OperationalPredictionStatus.ABSTAIN
    assert dec_phys.reason == AbstentionReason.PHYSICAL_INCONSISTENCY

    # Severity limit unsupported
    dec_sev = policy.evaluate("SEVERE_WIND", ood_score=0.20, severity_supported=False)
    assert dec_sev.status == OperationalPredictionStatus.ABSTAIN
    assert dec_sev.reason == AbstentionReason.SEVERITY_LIMIT_UNSUPPORTED
