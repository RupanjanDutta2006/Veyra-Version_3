import os
import shutil
import json
import joblib
import numpy as np

WORKSPACE = os.path.abspath(".")
REPO_A = os.path.join(WORKSPACE, "repos", "repo_a")
REPO_B = os.path.join(WORKSPACE, "repos", "repo_b")
ARTIFACTS = os.path.join(WORKSPACE, "artifacts")

def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Copied: {os.path.relpath(src, WORKSPACE)} -> {os.path.relpath(dst, WORKSPACE)}")

def main():
    print("=== STARTING PHASE 4: SELECTIVE SAFETY GRAFTING ===")

    # 1. Graft Schemas
    schema_files = [
        "certification.py",
        "ood.py",
        "disagreement.py",
        "provider_disagreement.py"
    ]
    for s in schema_files:
        src = os.path.join(REPO_A, "backend", "app", "schemas", s)
        dst = os.path.join(REPO_B, "backend", "app", "schemas", s)
        if os.path.exists(src):
            copy_file(src, dst)

    # 2. Graft Core Policies
    core_files = [
        "time_contract.py",
        "certification_policy.py",
        "ood_policy.py"
    ]
    for c in core_files:
        src = os.path.join(REPO_A, "backend", "app", "core", c)
        dst = os.path.join(REPO_B, "backend", "app", "core", c)
        if os.path.exists(src):
            copy_file(src, dst)

    # 3. Graft Services
    service_files = [
        "disagreement_service.py",
        "provider_disagreement_service.py"
    ]
    for s in service_files:
        src = os.path.join(REPO_A, "backend", "app", "services", s)
        dst = os.path.join(REPO_B, "backend", "app", "services", s)
        if os.path.exists(src):
            copy_file(src, dst)

    # 4. Port Tests
    test_files = [
        "test_scientific_certification.py",
        "test_day33_ood_model_determinism.py",
        "test_day37_provider_adapters.py",
        "test_day38_cross_provider_disagreement.py"
    ]
    for t in test_files:
        src = os.path.join(REPO_A, "backend", "tests", t)
        dst = os.path.join(REPO_B, "backend", "tests", t)
        if os.path.exists(src):
            copy_file(src, dst)

    # Create dedicated test_v3_time_contract.py in repo_b
    time_test_path = os.path.join(REPO_B, "backend", "tests", "test_v3_time_contract.py")
    time_test_content = """# Test V3 UTC Time Contract & Temporal Leakage Prevention
import pytest
from datetime import datetime, timezone
from backend.app.core.time_contract import (
    parse_utc_timestamp,
    format_utc_timestamp,
    derive_and_validate_lead_hours,
    is_certified_lead_horizon,
    MAX_CERTIFIED_LEAD_HOURS,
    MAX_SUPPORTED_LEAD_HOURS
)

def test_parse_utc_timestamp_iso_z():
    dt = parse_utc_timestamp("2026-09-22T06:00:00Z")
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 6

def test_parse_utc_timestamp_naive_defaults_to_utc():
    dt = parse_utc_timestamp("2026-09-22T06:00:00")
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 6

def test_parse_utc_timestamp_offset_converts_to_utc():
    # +05:30 11:30 should convert to 06:00 UTC
    dt = parse_utc_timestamp("2026-09-22T11:30:00+05:30")
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 6
    assert dt.minute == 0

def test_derive_and_validate_lead_hours_success():
    issue = "2026-09-22T00:00:00Z"
    valid = "2026-09-23T12:00:00Z"
    lead, c_issue, c_valid = derive_and_validate_lead_hours(issue, valid)
    assert lead == 36
    assert c_issue == "2026-09-22T00:00:00Z"
    assert c_valid == "2026-09-23T12:00:00Z"

def test_derive_and_validate_lead_hours_rejects_reversed_time():
    issue = "2026-09-22T12:00:00Z"
    valid = "2026-09-22T06:00:00Z"
    with pytest.raises(ValueError, match="strictly after"):
        derive_and_validate_lead_hours(issue, valid)

def test_derive_and_validate_lead_hours_rejects_zero_lead():
    issue = "2026-09-22T00:00:00Z"
    valid = "2026-09-22T00:00:00Z"
    with pytest.raises(ValueError):
        derive_and_validate_lead_hours(issue, valid)

def test_derive_and_validate_lead_hours_rejects_beyond_max():
    issue = "2026-09-22T00:00:00Z"
    valid = "2026-10-15T00:00:00Z" # > 500h
    with pytest.raises(ValueError, match="exceeds"):
        derive_and_validate_lead_hours(issue, valid)

def test_is_certified_lead_horizon():
    assert is_certified_lead_horizon(24) is True
    assert is_certified_lead_horizon(240) is True
    assert is_certified_lead_horizon(264) is False
    assert is_certified_lead_horizon(0) is False
"""
    with open(time_test_path, "w", encoding="utf-8") as f:
        f.write(time_test_content)
    print(f"Created dedicated time contract test at: {time_test_path}")

    # 5. Golden Parity Verification
    print("Verifying Golden V3 output parity post safety-grafting...")
    model_path = os.path.join(REPO_B, "models", "v3", "lightgbm_v3_challenger.joblib")
    cal_path = os.path.join(REPO_B, "models", "v3", "probability_calibrator_v3.joblib")
    golden_path = os.path.join(ARTIFACTS, "golden_v3_before.json")

    with open(golden_path, "r", encoding="utf-8") as f:
        golden = json.load(f)

    model = joblib.load(model_path)
    calibrator = joblib.load(cal_path)

    np.random.seed(golden["seed"])
    test_input = np.random.randn(*golden["input_shape"]).astype(np.float32)

    raw_candidate = model.predict(test_input)
    cal_candidate = calibrator.predict(raw_candidate)

    raw_diff = float(np.max(np.abs(raw_candidate - np.array(golden["raw_predictions"]))))
    cal_diff = float(np.max(np.abs(cal_candidate - np.array(golden["calibrated_predictions"]))))

    assert raw_diff < 1e-6, f"Golden raw output diff {raw_diff}"
    assert cal_diff < 1e-6, f"Golden calibrated output diff {cal_diff}"
    print(f"[PARITY GREEN] Raw diff: {raw_diff:.8f}, Calibrated diff: {cal_diff:.8f}")

    # Write golden_v3_after.json
    candidate_output = {
        "seed": golden["seed"],
        "input_shape": golden["input_shape"],
        "raw_predictions": [float(x) for x in raw_candidate],
        "calibrated_predictions": [float(x) for x in cal_candidate],
        "feature_count": 50,
        "model_type": type(model).__name__,
        "calibrator_type": type(calibrator).__name__,
        "raw_max_diff": raw_diff,
        "cal_max_diff": cal_diff,
        "parity_status": "EXACT_MATCH"
    }
    with open(os.path.join(ARTIFACTS, "golden_v3_after.json"), "w", encoding="utf-8") as f:
        json.dump(candidate_output, f, indent=2)

    print("=== PHASE 4 SELECTIVE SAFETY GRAFTING COMPLETE ===")

if __name__ == "__main__":
    main()
