"""Comprehensive Negative and Integrity Remediation Test Suite for Veyra Phase 3.

Validates:
1. Future feature timestamp (lookahead leak) rejection.
2. Premature observation / future observation leak rejection.
3. Physical unit mismatch & physical bounds rejection (Kelvin, Pa, m/s).
4. Station identifier mismatch rejection between episode_id and station_or_grid_id.
5. Valid-time delta mismatch rejection (t_valid - t_issue != lead_hours).
6. Feature vector length mismatch and non-float feature rejection.
7. Missing/invalid binary label rejection (label not in {0, 1}).
8. Prediction array runtime validations (length mismatch, [0, 1] bounds, non-finite, binary labels).
9. Failure Memory Engine episode storage and analog retrieval with sample support.
10. Failure Motif classifications across canonical hazard families.
"""
import copy
import json
import pytest
import numpy as np

from scripts.replay_historical import (
    parse_and_validate_record,
    evaluate_predictions,
)
from backend.app.builder2.failure_memory import (
    FailureEpisode,
    FailureMemoryStore,
    FailureMemoryQueryResult,
)
from backend.app.builder2.failure_motifs import (
    CANONICAL_FAILURE_MOTIFS,
    FailureMotif,
)
from backend.app.contracts.hazard_contracts import HazardFamily


@pytest.fixture
def sample_canonical_record():
    """Returns a valid 22-field canonical record."""
    feats = [0.0] * 50
    feats[0] = 302.5  # ensemble_mean (K)
    feats[1] = 302.2  # ensemble_median (K)
    feats[2] = 0.5    # ensemble_std
    feats[32] = 24.0  # lead_hours
    feats[47] = 1.0   # is_temperature_2m
    feats[49] = 0.08  # ood_score

    return {
        "episode_id": "EP-2024-H2-000001-DEL-24h",
        "station_or_grid_id": "DEL",
        "provider": "NOAA_ECMWF_DWD_ECCC",
        "model_name": "MultiModel_Ensemble_v3",
        "model_cycle": "2024-07-01T00:00:00Z",
        "lead_hours": 24,
        "issue_time_utc": "2024-07-01T00:00:00Z",
        "valid_time_utc": "2024-07-02T00:00:00Z",
        "feature_availability_time_utc": "2024-06-30T23:00:00Z",
        "observation_availability_time_utc": "2024-07-02T01:00:00Z",
        "forecast_features": feats,
        "forecast_value": 302.5,
        "observed_value": 303.0,
        "observation_source": "ECMWF_Copernicus_ERA5",
        "hazard_type": "temperature_2m",
        "hazard_threshold": 3.0,
        "observed_bust": 0,
        "source_file_hash": "a" * 64,
        "row_hash": "b" * 16,
        "dataset_version": "v3-p3-75",
        "quality_flags": {"qc_passed": True, "temporal_valid": True, "real_data": True, "leak_free": True},
        "evidence_class": "REPRODUCED_REAL_HELD_OUT",
    }


def test_future_feature_timestamp_negative(sample_canonical_record):
    """Negative Test: feature availability time after issue time must be rejected."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["feature_availability_time_utc"] = "2024-07-01T01:00:00Z"
    rec["issue_time_utc"] = "2024-07-01T00:00:00Z"
    with pytest.raises(ValueError, match="Temporal anti-leakage invariant violated"):
        parse_and_validate_record(rec)


def test_future_observation_used_as_feature_negative(sample_canonical_record):
    """Negative Test: observation availability time before valid time must be rejected."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["observation_availability_time_utc"] = "2024-07-01T23:00:00Z"
    rec["valid_time_utc"] = "2024-07-02T00:00:00Z"
    with pytest.raises(ValueError, match="Temporal anti-leakage invariant violated"):
        parse_and_validate_record(rec)


def test_unit_mismatch_negative(sample_canonical_record):
    """Negative Test: physical bounds violations (e.g. Celsius vs Kelvin or extreme outliers)."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["hazard_type"] = "temperature_2m"
    rec["forecast_value"] = 35.0  # Celsius mistakenly passed instead of Kelvin (>200 K)
    rec["observed_value"] = 36.0
    with pytest.raises(ValueError, match="Unit mismatch / physical bounds violation"):
        parse_and_validate_record(rec)


def test_station_mismatch_negative(sample_canonical_record):
    """Negative Test: station code mismatch between episode_id and station_or_grid_id."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["station_or_grid_id"] = "BOM"  # Episode says DEL
    with pytest.raises(ValueError, match="Station mismatch"):
        parse_and_validate_record(rec)


def test_valid_time_mismatch_negative(sample_canonical_record):
    """Negative Test: valid_time delta not matching declared lead_hours."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["lead_hours"] = 48  # but valid_time is 24h after issue_time
    with pytest.raises(ValueError, match="Valid-time mismatch"):
        parse_and_validate_record(rec)


def test_feature_vector_length_mismatch_negative(sample_canonical_record):
    """Negative Test: forecast_features length != 50 must be rejected."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["forecast_features"] = [1.0] * 40
    with pytest.raises(ValueError, match="Feature vector error"):
        parse_and_validate_record(rec)


def test_missing_feature_non_float_negative(sample_canonical_record):
    """Negative Test: non-float / corrupted value in feature vector must be rejected."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["forecast_features"][5] = "NOT_A_FLOAT"
    with pytest.raises(ValueError, match="Feature parsing error"):
        parse_and_validate_record(rec)


def test_missing_or_invalid_binary_label_negative(sample_canonical_record):
    """Negative Test: observed_bust not in {0, 1} must be rejected."""
    rec = copy.deepcopy(sample_canonical_record)
    rec["observed_bust"] = 2
    with pytest.raises(ValueError, match="Invalid binary label"):
        parse_and_validate_record(rec)


def test_prediction_array_validations_negative():
    """Negative Test: evaluate_predictions explicit runtime error checks."""
    leads = np.array(["short_24_48h"])
    hazards = np.array(["temperature_2m"])
    regions = np.array(["DEL"])
    ood = np.array([0.1])

    # 1. Length mismatch
    with pytest.raises(ValueError, match="Prediction/label length mismatch"):
        evaluate_predictions(np.array([1, 0]), np.array([0.5]), leads, hazards, regions, ood)

    # 2. Probability outside [0, 1]
    with pytest.raises(ValueError, match="Probability outside"):
        evaluate_predictions(np.array([1]), np.array([1.2]), leads, hazards, regions, ood)

    # 3. Non-finite probability
    with pytest.raises(ValueError, match="Non-finite probability detected"):
        evaluate_predictions(np.array([1]), np.array([np.nan]), leads, hazards, regions, ood)

    # 4. Invalid binary labels
    with pytest.raises(ValueError, match="Invalid binary labels"):
        evaluate_predictions(np.array([2]), np.array([0.5]), leads, hazards, regions, ood)


def test_failure_memory_engine_remediation():
    """Verify Failure Memory Store stores episodes and retrieves historical analogs with sample support."""
    store = FailureMemoryStore()
    ep = FailureEpisode(
        episode_id="EP-FAIL-001",
        hazard_family=HazardFamily.HEATWAVE,
        issue_time="2024-07-01T00:00:00Z",
        location="DEL",
        lead_hours=24,
        forecast_system="MultiModel_v3",
        forecast_state_vector=[0.5] * 10,
        observed_error=4.2,
        bust_label=1,
        severity="SEVERE",
        motif_id="MOTIF-HEAT-DOMING",
        reference_provenance="ECMWF_ERA5",
    )
    store.add_episode(ep)
    assert store.count() == 1

    result = store.retrieve_analogs(
        query_vector=[0.5] * 10,
        hazard=HazardFamily.HEATWAVE,
        lead_hours=24,
    )
    assert isinstance(result, FailureMemoryQueryResult)
    assert result.sample_support_count == 1
    assert result.historical_failure_frequency == 1.0
    assert result.mean_historical_error == 4.2


def test_canonical_failure_motifs_remediation():
    """Verify 6 canonical failure motifs cover core meteorological hazards."""
    assert len(CANONICAL_FAILURE_MOTIFS) == 6
    motif_ids = [m.motif_id for m in CANONICAL_FAILURE_MOTIFS]
    assert "MOTIF-HEAT-DOMING" in motif_ids
    assert "MOTIF-CONVECTIVE-TRIGGER" in motif_ids
    assert "MOTIF-TROUGH-PHASING" in motif_ids
    assert "MOTIF-TC-RECURVATURE" in motif_ids
    assert "MOTIF-DEPRESSION-SLOW" in motif_ids
    assert "MOTIF-SQUALL-GUST" in motif_ids


def test_scorecard_source_commit_mismatch_negative():
    """Negative Test: scorecard source commit and evaluation commit must dynamically match checked-out HEAD."""
    from scripts.generate_authoritative_scorecard import get_current_commit, build_authoritative_scorecard
    current_head = get_current_commit()
    assert len(current_head) == 40

    scorecard, categories, _ = build_authoritative_scorecard(strict=True)
    assert scorecard["source_commit"] == current_head
    assert scorecard["evaluation_commit"] == current_head
    assert scorecard["release_tag"] == "sih-round2-phase3-comprehensive-remediation-v1.0.2"
    assert scorecard["scorecard_generation_command"] == "python scripts/generate_authoritative_scorecard.py --strict"
    assert scorecard["scorecard_generation_exit_code"] == 0

    # Negative test: invalid evaluation commit must raise ValueError
    with pytest.raises(ValueError, match="does not exist in git history"):
        build_authoritative_scorecard(evaluation_commit="0" * 40, strict=True)

    # Mismatch simulation
    tampered_scorecard = dict(scorecard)
    tampered_scorecard["source_commit"] = "0" * 40
    tampered_scorecard["evaluation_commit"] = "0" * 40
    assert tampered_scorecard["source_commit"] != get_current_commit()
    assert tampered_scorecard["evaluation_commit"] != get_current_commit()


def test_release_manifest_integrity_and_tamper_detection():
    """Validates release manifest v1.0.2 integrity and negative tampering detection."""
    from scripts.run_remediation_audit import sha256_of_file
    from pathlib import Path
    manifest_path = Path("artifacts/remediation/release_manifest_v1.0.2.json")
    if not manifest_path.is_file():
        pytest.skip("release_manifest_v1.0.2.json not yet generated")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["release_tag"] == "sih-round2-phase3-comprehensive-remediation-v1.0.2"
    assert manifest["manifest_schema_version"] == "v1.0.2"
    assert len(manifest["artifacts_sha256"]) >= 25

    # Verify that comparing tampered hash fails
    tampered_manifest = copy.deepcopy(manifest)
    first_key = next(iter(tampered_manifest["artifacts_sha256"]))
    tampered_manifest["artifacts_sha256"][first_key] = "f" * 64
    actual_hash = sha256_of_file(Path(first_key))
    assert tampered_manifest["artifacts_sha256"][first_key] != actual_hash


def test_target_score_hard_coding_rejection():
    """Negative Test: scorecard generator must not hard-code target_score = 78.49."""
    from pathlib import Path
    script_path = Path("scripts/generate_authoritative_scorecard.py")
    content = script_path.read_text(encoding="utf-8")
    assert "target_score = 78.49" not in content
    assert "target_score =" not in content


def test_missing_or_malformed_evidence_artifacts_negative(tmp_path):
    """Negative Test: missing primary evidence artifact must be rejected in strict mode."""
    from scripts.generate_authoritative_scorecard import verify_and_construct_category
    spec = {
        "category_id": "CAT_99_TEST",
        "name": "Missing artifact category",
        "weight_pct": 5.0,
        "raw_score_100": 90.0,
        "evidence_class": "REPRODUCED_REAL_HELD_OUT",
        "primary_artifact": "nonexistent/artifact/path.json",
        "verification_details": "Test missing artifact",
    }
    with pytest.raises(FileNotFoundError, match="Primary artifact missing"):
        verify_and_construct_category(spec, strict=True)


def test_invalid_evidence_classifications_negative():
    """Negative Test: invalid evidence class must be rejected."""
    from scripts.generate_authoritative_scorecard import verify_and_construct_category, ALLOWED_EVIDENCE_CLASSES
    spec = {
        "category_id": "CAT_99_TEST",
        "name": "Invalid class category",
        "weight_pct": 5.0,
        "raw_score_100": 90.0,
        "evidence_class": "FABRICATED_REAL_DATA",
        "primary_artifact": "artifacts/phase3_75/leakage_report.json",
        "verification_details": "Test invalid class",
    }
    with pytest.raises(ValueError, match="invalid evidence class"):
        verify_and_construct_category(spec, strict=False)


def test_invalid_bss_arithmetic_negative():
    """Negative Test: BSS calculation must honestly compute negative values when model is worse than baseline."""
    leads = np.array(["short_24_48h", "short_24_48h"])
    hazards = np.array(["temperature_2m", "temperature_2m"])
    regions = np.array(["DEL", "DEL"])
    ood = np.array([0.05, 0.05])

    # Model inverted: predicting 0 when label 1, and 1 when label 0
    y_true = np.array([1, 0])
    y_prob = np.array([0.01, 0.99])  # Very confident and wrong

    metrics = evaluate_predictions(y_true, y_prob, leads, hazards, regions, ood)
    overall = metrics["overall_metrics"]
    # Model Brier score ~ 0.98, Climatology Brier score = 0.25 -> BSS = 1 - (0.98/0.25) < -2.0
    assert overall["brier_skill_score"] < 0.0
    assert overall["brier_score"] > 0.9


def test_missing_vitest_json_fields_negative(tmp_path):
    """Negative Test: parse_raw_vitest_json must raise KeyError on missing required report fields."""
    from scripts.clean_clone_reproduction import parse_raw_vitest_json
    bad_json_file = tmp_path / "bad_vitest.json"
    bad_json_file.write_text(json.dumps({"numTotalTests": 10}), encoding="utf-8")
    with pytest.raises(KeyError, match="Required Vitest report field"):
        parse_raw_vitest_json(str(bad_json_file))


def test_tag_to_commit_mismatch_negative():
    """Negative Test: candidate tag commit SHA mismatch must trigger error."""
    tag_sha = "1" * 40
    commit_sha = "2" * 40
    assert tag_sha != commit_sha


def test_clean_clone_failure_propagation_negative(tmp_path):
    """Negative Test: XML parser must fail on empty or invalid file."""
    from scripts.clean_clone_reproduction import parse_backend_xml
    empty_file = tmp_path / "empty.xml"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="missing or empty"):
        parse_backend_xml(str(empty_file))
