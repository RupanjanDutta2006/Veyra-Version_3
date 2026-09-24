import os
import json
import hashlib
import joblib
import numpy as np

WORKSPACE = os.path.abspath(".")
REPO_B = os.path.join(WORKSPACE, "repos", "repo_b")
REPO_A = os.path.join(WORKSPACE, "repos", "repo_a")
MANIFESTS = os.path.join(WORKSPACE, "manifests")
ARTIFACTS = os.path.join(WORKSPACE, "artifacts")

os.makedirs(ARTIFACTS, exist_ok=True)
os.makedirs(MANIFESTS, exist_ok=True)

MODEL_PATH = os.path.join(REPO_B, "models", "v3", "lightgbm_v3_challenger.joblib")
CALIBRATOR_PATH = os.path.join(REPO_B, "models", "v3", "probability_calibrator_v3.joblib")
FEATURES_PATH = os.path.join(REPO_B, "models", "v3", "feature_names.json")

EXPECTED_MODEL_SHA = "00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660"
EXPECTED_CALIBRATOR_SHA = "9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    print("=== STARTING PHASE 3: FROZEN INCUMBENT ARTIFACT REPAIR ===")

    # Step 3.1 & 3.2: Verify canonical artifact hashes on disk
    m_sha = sha256_file(MODEL_PATH)
    c_sha = sha256_file(CALIBRATOR_PATH)
    f_sha = sha256_file(FEATURES_PATH)

    print(f"Model SHA256:      {m_sha}")
    print(f"Calibrator SHA256: {c_sha}")
    print(f"Features SHA256:   {f_sha}")

    assert m_sha == EXPECTED_MODEL_SHA, f"Model SHA mismatch: {m_sha}"
    assert c_sha == EXPECTED_CALIBRATOR_SHA, f"Calibrator SHA mismatch: {c_sha}"

    with open(FEATURES_PATH, "r", encoding="utf-8") as f:
        features = json.load(f)
    assert len(features) == 50, f"Expected 50 features, got {len(features)}"
    print(f"Verified 50 features in {FEATURES_PATH}")

    # Step 3.6: Authoritative release manifest binding all artifacts to base commit 82eded8
    release_manifest = {
        "release_id": "veyra-v3.0.0-release-candidate",
        "manifest_schema_version": "v1.0.0",
        "generation_timestamp": "2026-09-22T00:15:00Z",
        "git_provenance": {
            "base_commit_sha": "82eded8194151e37fb9b3eecf273010dc62d7b29",
            "integration_branch": "integration/sih-round2-selective-merge",
            "strategy": "base_commit_provenance"
        },
        "model_artifact": {
            "path": "models/v3/lightgbm_v3_challenger.joblib",
            "sha256": EXPECTED_MODEL_SHA,
            "version": "veyra-v3-benchmark-lightgbm",
            "decision_threshold": 0.060
        },
        "calibrator_artifact": {
            "path": "models/v3/probability_calibrator_v3.joblib",
            "sha256": EXPECTED_CALIBRATOR_SHA,
            "type": "IsotonicRegression",
            "method": "isotonic"
        },
        "feature_contract": {
            "feature_count": 50,
            "feature_schema_version": "veyra-50-features-v3.0",
            "feature_names_reference": "models/v3/feature_names.json",
            "sha256": f_sha
        },
        "scientific_policies": {
            "certification_policy_version": "v3.0.0-frozen-benchmark",
            "certified_station_count": 25,
            "certified_variables": [
                "temperature_2m",
                "wind_speed_10m",
                "surface_pressure"
            ],
            "max_certified_lead_hours": 240,
            "ood_policy_version": "v3.0.0-physical-support",
            "time_contract_version": "v3.0.0-utc-temporal-invariants",
            "revision_store_schema_version": "v1.0.0-sqlite-wal"
        },
        "operational_horizons": {
            "supported_max_lead_hours": 384,
            "certified_max_lead_hours": 240,
            "extended_uncertified_horizon": "264h-384h"
        },
        "evidence_boundaries": {
            "training_holdout": "2017-2019 NOAA GEFSv12 benchmark",
            "post_2019_certified": False,
            "unseen_station_certified": False,
            "n5_historical_n31_live_equivalence_certified": False
        },
        "threshold_consolidation": {
            "v3_challenger_incumbent": 0.060,
            "day4_legacy_baseline": 0.280,
            "rule": "Active prediction route uses v3_challenger (0.060); Day 4 is baseline comparator only"
        }
    }

    # Save to repo_b/backend/app/core/release_manifest.json and manifests/v3_release_manifest.json
    core_dir = os.path.join(REPO_B, "backend", "app", "core")
    os.makedirs(core_dir, exist_ok=True)
    with open(os.path.join(core_dir, "release_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(release_manifest, f, indent=2)
    with open(os.path.join(MANIFESTS, "v3_release_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(release_manifest, f, indent=2)
    print("Saved authoritative release_manifest.json in core and manifests.")

    # Port release_manifest.py into repo_b
    rm_py_source = os.path.join(REPO_A, "backend", "app", "core", "release_manifest.py")
    rm_py_dest = os.path.join(REPO_B, "backend", "app", "core", "release_manifest.py")
    if os.path.exists(rm_py_source):
        with open(rm_py_source, "r", encoding="utf-8") as f:
            code = f.read()
        # Adapt default manifest path if needed
        with open(rm_py_dest, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Ported release_manifest.py into {rm_py_dest}")

    # Step 3.9: Golden Input / Prediction Baseline
    print("Computing Golden V3 Before output fixture...")
    model = joblib.load(MODEL_PATH)
    calibrator = joblib.load(CALIBRATOR_PATH)

    np.random.seed(42)
    golden_input = np.random.randn(5, 50).astype(np.float32)

    raw_preds = model.predict(golden_input)
    cal_preds = calibrator.predict(raw_preds)

    golden_output = {
        "seed": 42,
        "input_shape": [5, 50],
        "raw_predictions": [float(x) for x in raw_preds],
        "calibrated_predictions": [float(x) for x in cal_preds],
        "feature_count": 50,
        "model_type": type(model).__name__,
        "calibrator_type": type(calibrator).__name__,
        "model_sha256": m_sha,
        "calibrator_sha256": c_sha,
        "features_sha256": f_sha,
        "v3_threshold": 0.060
    }

    golden_path = os.path.join(ARTIFACTS, "golden_v3_before.json")
    with open(golden_path, "w", encoding="utf-8") as f:
        json.dump(golden_output, f, indent=2)
    print(f"Generated Golden V3 output baseline at: {golden_path}")
    print(f"  Raw predictions: {[round(x, 4) for x in golden_output['raw_predictions']]}")
    print(f"  Calibrated predictions: {[round(x, 4) for x in golden_output['calibrated_predictions']]}")

    print("=== PHASE 3 EXECUTION COMPLETE ===")

if __name__ == "__main__":
    main()
