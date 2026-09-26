"""Phase 2 Scientific Integrity & Anti-Leakage Contract Test Suite.

Validates:
1. Strict 18-field canonical row schema parsing and rejection of missing fields.
2. Temporal anti-leakage invariant enforcement (t_feat <= t_issue < t_valid <= t_obs).
3. Exact 50-dimensional feature shape and type validation.
4. Deterministic physical bust evaluation (|fcst - obs| > thresh).
5. Single-class subset handling in historical replay (no fabricated scores).
6. Mathematical consistency and weight sum validation of the Phase 2 scorecard.
7. End-to-end integrity of benchmark dataset test fixtures.
"""
import copy
import json
from pathlib import Path
import pytest
import numpy as np

from scripts.replay_historical import (
    MANDATORY_CANONICAL_FIELDS,
    parse_and_validate_record,
    evaluate_predictions,
    compute_expected_calibration_error,
)
from scripts.generate_scorecard import build_scorecard
from scripts.generate_benchmark_dataset import compute_canonical_row_hash

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_500_PATH = REPO_ROOT / "backend" / "tests" / "fixtures" / "ml" / "benchmark_dataset_500.json"


@pytest.fixture
def valid_canonical_record():
    """Returns a valid 18-field canonical record."""
    feats = [0.0] * 50
    feats[0] = 300.5
    feats[1] = 300.5
    feats[2] = 1.2
    feats[32] = 24.0
    feats[47] = 1.0
    feats[49] = 0.15

    ep_id = "EP-2024-H2-000001-DEL-24h"
    issue_t = "2024-07-01T00:00:00Z"
    valid_t = "2024-07-02T00:00:00Z"
    feat_t = "2024-06-30T23:30:00Z"
    obs_t = "2024-07-02T00:15:00Z"
    fcst_val = 300.5
    obs_val = 301.2
    thresh = 3.0
    obs_bust = 0

    row_hash = compute_canonical_row_hash(
        episode_id=ep_id,
        station_id="DEL",
        issue_time=issue_t,
        valid_time=valid_t,
        fcst_val=fcst_val,
        obs_val=obs_val,
        obs_bust=obs_bust,
    )

    return {
        "episode_id": ep_id,
        "station_or_grid_id": "DEL",
        "provider": "NOAA_GEFSv12",
        "model_cycle": issue_t,
        "issue_time_utc": issue_t,
        "valid_time_utc": valid_t,
        "feature_availability_time_utc": feat_t,
        "observation_availability_time_utc": obs_t,
        "forecast_features": feats,
        "forecast_value": fcst_val,
        "observed_value": obs_val,
        "observation_source": "IMD_AWS_GROUND_TRUTH",
        "hazard_threshold": thresh,
        "observed_bust": obs_bust,
        "source_file_hash": "a" * 64,
        "row_hash": row_hash,
        "dataset_version": "v3.0.0-phase2",
        "quality_flags": {
            "qc_passed": True,
            "anti_leakage_verified": True,
            "evidence_class": "REPRODUCED_SYNTHETIC_FIXTURE",
        },
        "lead_hours": 24,
        "hazard_type": "heatwave",
        "region": "indo_gangetic_plains",
    }


def test_valid_canonical_record_parses_successfully(valid_canonical_record):
    """Verify that a valid canonical record parses without error."""
    feat_vec, obs_bust, horizon, hazard, reg, ood = parse_and_validate_record(valid_canonical_record)
    assert len(feat_vec) == 50
    assert obs_bust == 0
    assert horizon == "short_24_48h"
    assert hazard == "heatwave"
    assert reg == "indo_gangetic_plains"
    assert ood == pytest.approx(0.15)


def test_lookahead_feature_rejection(valid_canonical_record):
    """Verify that feature availability after issue time (look-ahead) is strictly rejected."""
    rec = copy.deepcopy(valid_canonical_record)
    # Temporal violation: features available AFTER issue time
    rec["feature_availability_time_utc"] = "2024-07-01T01:00:00Z"
    rec["issue_time_utc"] = "2024-07-01T00:00:00Z"

    with pytest.raises(ValueError, match="Temporal anti-leakage invariant violated"):
        parse_and_validate_record(rec)


def test_future_observation_rejection(valid_canonical_record):
    """Verify that observation availability before valid time or issue >= valid is strictly rejected."""
    rec = copy.deepcopy(valid_canonical_record)
    # Temporal violation: issue time >= valid time
    rec["issue_time_utc"] = "2024-07-02T00:00:00Z"
    rec["valid_time_utc"] = "2024-07-02T00:00:00Z"

    with pytest.raises(ValueError, match="Temporal anti-leakage invariant violated"):
        parse_and_validate_record(rec)

    # Temporal violation: observation available before valid time
    rec2 = copy.deepcopy(valid_canonical_record)
    rec2["observation_availability_time_utc"] = "2024-07-01T23:00:00Z"
    rec2["valid_time_utc"] = "2024-07-02T00:00:00Z"

    with pytest.raises(ValueError, match="Temporal anti-leakage invariant violated"):
        parse_and_validate_record(rec2)


def test_missing_canonical_fields_rejection(valid_canonical_record):
    """Verify that omitting any of the 18 mandatory canonical fields raises ValueError."""
    for field in MANDATORY_CANONICAL_FIELDS:
        rec = copy.deepcopy(valid_canonical_record)
        del rec[field]
        with pytest.raises(ValueError, match=f"missing mandatory canonical field '{field}'"):
            parse_and_validate_record(rec)


def test_feature_vector_shape_and_type_validation(valid_canonical_record):
    """Verify that wrong feature vector dimension or invalid types are rejected."""
    rec = copy.deepcopy(valid_canonical_record)
    rec["forecast_features"] = [0.0] * 49  # 49 instead of 50

    with pytest.raises(ValueError, match="expected list of 50 floats"):
        parse_and_validate_record(rec)

    rec2 = copy.deepcopy(valid_canonical_record)
    rec2["forecast_features"] = ["invalid_str"] + [0.0] * 49

    with pytest.raises(ValueError, match="non-float feature detected"):
        parse_and_validate_record(rec2)


def test_deterministic_bust_evaluation_consistency(valid_canonical_record):
    """Verify that invalid observed_bust labels discordant with deterministic physical rule are rejected."""
    rec = copy.deepcopy(valid_canonical_record)
    rec["forecast_value"] = 300.0
    rec["observed_value"] = 305.0
    rec["hazard_threshold"] = 3.0
    # |300 - 305| = 5 > 3 -> expected bust is 1, but record says 0
    rec["observed_bust"] = 0

    with pytest.raises(ValueError, match="Bust label mismatch"):
        parse_and_validate_record(rec)


def test_single_class_subset_handling_in_replay():
    """Verify that evaluation on single-class subsets does not fabricate metrics or crash."""
    y_true_all_zeros = np.zeros(50, dtype=int)
    y_prob = np.full(50, 0.05, dtype=float)
    leads = np.array(["short_24_48h"] * 50, dtype=object)
    hazards = np.array(["heatwave"] * 50, dtype=object)
    regions = np.array(["general"] * 50, dtype=object)
    ood = np.full(50, 0.1, dtype=float)

    metrics = evaluate_predictions(y_true_all_zeros, y_prob, leads, hazards, regions, ood)
    ov = metrics["overall_metrics"]

    assert ov["evaluated_rows"] == 50
    assert ov["bust_prevalence"] == 0.0
    assert ov["roc_auc"] == "NOT_AVAILABLE (single_class)"
    assert ov["pr_auc"] == "NOT_AVAILABLE (single_class)"
    assert ov["log_loss"] == "NOT_AVAILABLE (single_class)"


def test_expected_calibration_error_computation():
    """Verify that ECE computes mathematically valid values in [0, 1]."""
    y_true = np.array([0, 0, 0, 1, 1, 1, 0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.15, 0.85, 0.9, 0.95, 0.05, 0.1, 0.8, 0.75])

    ece = compute_expected_calibration_error(y_true, y_prob, n_bins=5)
    assert 0.0 <= ece <= 1.0
    assert isinstance(ece, float)


def test_scorecard_mathematical_properties():
    """Verify that scorecard weights sum to 100.0% and calculation is mathematically sound."""
    scorecard, evidence = build_scorecard()

    assert scorecard["scorecard_version"] == "v3.0.1-phase2"
    assert scorecard["candidate_tag"] == "sih-round2-phase2-v1.0.1"
    assert scorecard["total_weight_pct"] == 100.0
    assert 0.0 <= scorecard["overall_weighted_score"] <= 100.0
    assert scorecard["final_disposition"] == "PHASE_2_APPROVED_FIXTURE_ONLY"
    assert scorecard["real_external_data_status"] == "NOT_AVAILABLE"

    # Verify weight sum across individual categories
    cat_weights = sum(c["weight_pct"] for c in scorecard["categories"])
    assert cat_weights == pytest.approx(100.0)

    # Verify weighted score matches sum of (weight * raw_score)
    expected_weighted = sum((c["weight_pct"] * c["raw_score_100"]) / 100.0 for c in scorecard["categories"])
    assert scorecard["overall_weighted_score"] == pytest.approx(expected_weighted, abs=1e-4)


def test_fixture_500_integrity_and_anti_leakage():
    """Verify that the 500-record test fixture is completely valid and free of leakage."""
    assert FIXTURE_500_PATH.is_file(), f"Missing fixture at {FIXTURE_500_PATH}"

    with open(FIXTURE_500_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) == 500

    seen_ids = set()
    for idx, rec in enumerate(records, start=1):
        feat_vec, obs_bust, horizon, hazard, reg, ood = parse_and_validate_record(rec, line_no=idx)
        assert len(feat_vec) == 50
        assert obs_bust in (0, 1)

        ep_id = rec["episode_id"]
        assert ep_id not in seen_ids, f"Duplicate episode_id: {ep_id}"
        seen_ids.add(ep_id)

        # Check row hash
        expected_hash = compute_canonical_row_hash(
            episode_id=ep_id,
            station_id=rec["station_or_grid_id"],
            issue_time=rec["issue_time_utc"],
            valid_time=rec["valid_time_utc"],
            fcst_val=rec["forecast_value"],
            obs_val=rec["observed_value"],
            obs_bust=obs_bust,
        )
        assert rec["row_hash"] == expected_hash, f"Row hash mismatch at row {idx}"
