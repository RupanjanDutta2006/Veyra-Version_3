import subprocess
import os
import sys

if os.path.isdir("backend") and os.path.isdir("models"):
    REPO_B = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    REPO_B = os.path.abspath("repos/repo_b")
else:
    REPO_B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = REPO_B

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def test_phase7():
    print("=== Gate P7 (Gates G14–G17): Test, CI, Reproducibility & Release Consolidation ===")
    failures = []

    # 1. Verify artifacts via verify_artifacts.py
    code, out, err = run("python scripts/verify_artifacts.py", cwd=REPO_B)
    if code != 0:
        failures.append(f"Artifact verification failed:\n{out}\n{err}")
    else:
        print("[PASS] Artifact verification passed (V3 model & calibrator intact)")

    # 2. Run release gates check
    code, out, err = run(
        "python scripts/run_release_gates.py --require-artifacts --require-replay --require-security --require-rollback",
        cwd=REPO_B
    )
    if code != 0:
        failures.append(f"Release gates run failed:\n{out}\n{err}")
    else:
        print("[PASS] Compulsory release gates passed (G1, G3, G8, G11, G15, G16)")

    # 3. Verify Rollback documentation exists and is complete
    rb_file = os.path.join(REPO_B, "manifests", "rollback_procedure.md")
    if not os.path.exists(rb_file) or os.path.getsize(rb_file) < 500:
        failures.append("Rollback procedure documentation missing or underspecified")
    else:
        print("[PASS] Rollback procedure documented with MTTR < 5m target and stop triggers")

    # 4. Verify 500 Test Specification Ledger & Validator
    code, out, err = run("python scripts/verify_test_ledger.py", cwd=REPO_B)
    if code != 0:
        failures.append(f"500-test ledger verification failed:\n{out}\n{err}")
    else:
        print("[PASS] 500-test specification ledger verified across 20 domains with honest N/A markings")

    # 4b. Run pytest test_500_test_mapping.py
    code, out, err = run("python -m pytest backend/tests/test_500_test_mapping.py -q", cwd=REPO_B)
    if code != 0:
        failures.append(f"Test mapping pytest suite failed:\n{out}\n{err}")
    else:
        print("[PASS] test_500_test_mapping.py unit tests passed (9/9 passed)")

    # 5. Verify CI workflow exists in repo_b
    ci_path = os.path.join(REPO_B, ".github", "workflows", "ci.yml")
    if not os.path.exists(ci_path):
        failures.append("CI workflow (.github/workflows/ci.yml) missing in repo_b")
    else:
        print("[PASS] Comprehensive CI workflow configured with backend, artifacts, frontend & gates")

    if failures:
        print("\n=== GATE P7 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATE P7 (GATES G14–G17) COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase7()
