import os
import sys
import json
import subprocess
import joblib
import numpy as np

if os.path.isdir("backend") and os.path.isdir("models"):
    REPO_B = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    REPO_B = os.path.abspath("repos/repo_b")
else:
    REPO_B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if os.path.isdir("artifacts"):
    ARTIFACTS = os.path.abspath("artifacts")
else:
    ARTIFACTS = os.path.join(REPO_B, "artifacts")

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def test_phase3():
    print("=== Gate G1–G3: Phase 3 Artifact Repair & Incumbent Verification ===")
    failures = []

    # 1. Run verify_artifacts.py in repo_b
    code, out, err = run("python scripts/verify_artifacts.py", cwd=REPO_B)
    if code != 0:
        failures.append(f"scripts/verify_artifacts.py failed with code {code}:\n{out}\n{err}")
    else:
        print("[PASS] scripts/verify_artifacts.py exited 0 with all checks matched")

    # 2. Verify release_manifest.py validator
    sys.path.insert(0, REPO_B)
    from backend.app.core.release_manifest import validate_release_manifest
    manifest_path = os.path.join(REPO_B, "backend", "app", "core", "release_manifest.json")
    val_res = validate_release_manifest(manifest_path, verify_artifacts_on_disk=True)
    if not val_res.is_valid:
        failures.append(f"Release manifest validation failed: {val_res.errors}")
    else:
        print(f"[PASS] Authoritative release manifest validated: {val_res.verified_contracts}")

    # 3. Verify Golden Parity (G2)
    golden_path = os.path.join(ARTIFACTS, "golden_v3_before.json")
    if not os.path.exists(golden_path):
        golden_path = os.path.join(REPO_B, "artifacts", "golden_v3_before.json")
    if not os.path.exists(golden_path):
        failures.append(f"Missing golden fixture: {golden_path}")
    else:
        with open(golden_path, "r", encoding="utf-8") as f:
            golden = json.load(f)

        model_path = os.path.join(REPO_B, "models", "v3", "lightgbm_v3_challenger.joblib")
        cal_path = os.path.join(REPO_B, "models", "v3", "probability_calibrator_v3.joblib")

        model = joblib.load(model_path)
        calibrator = joblib.load(cal_path)

        np.random.seed(golden["seed"])
        test_input = np.random.randn(*golden["input_shape"]).astype(np.float32)

        raw = model.predict(test_input)
        cal = calibrator.predict(raw)

        raw_diff = np.max(np.abs(raw - np.array(golden["raw_predictions"])))
        cal_diff = np.max(np.abs(cal - np.array(golden["calibrated_predictions"])))

        if raw_diff > 1e-6:
            failures.append(f"Golden raw prediction parity failed: max diff {raw_diff}")
        else:
            print(f"[PASS] Golden raw prediction parity verified (max diff {raw_diff:.8f})")

        if cal_diff > 1e-6:
            failures.append(f"Golden calibrated prediction parity failed: max diff {cal_diff}")
        else:
            print(f"[PASS] Golden calibrated prediction parity verified (max diff {cal_diff:.8f})")

    # 4. Model Authority & Thresholds (G3)
    from backend.app.builder2.v3_model_adapter import V3_OPERATIONAL_THRESHOLD, V3_MODEL_VERSION
    if V3_OPERATIONAL_THRESHOLD != 0.060:
        failures.append(f"Operational threshold is {V3_OPERATIONAL_THRESHOLD}, expected 0.060")
    else:
        print(f"[PASS] Authoritative threshold verified: {V3_OPERATIONAL_THRESHOLD} ({V3_MODEL_VERSION})")

    if failures:
        print("\n=== GATE G1-G3 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATES G1–G3 COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase3()
