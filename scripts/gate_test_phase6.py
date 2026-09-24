import subprocess
import os
import sys

if os.path.isdir("backend") and os.path.isdir("models"):
    REPO_B = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    REPO_B = os.path.abspath("repos/repo_b")
else:
    REPO_B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def test_phase6():
    print("=== Gate P6 (Gate G8): Specialist Containment & Scientific Promotion Boundary ===")
    failures = []

    # 1. Run specialist tests in repo_b
    tests = [
        "backend/tests/test_specialist_registry.py",
        "backend/tests/test_experimental_feature_flags.py",
        "backend/tests/test_claim_boundaries.py",
        "backend/tests/test_scientific_evidence_package.py",
    ]
    cmd = f"python -m pytest {' '.join(tests)} -q"
    code, out, err = run(cmd, cwd=REPO_B)
    if code != 0:
        failures.append(f"Specialist containment tests failed (code {code}):\n{out}\n{err}")
    else:
        summary_line = [l for l in out.splitlines() if "passed" in l]
        print(f"[PASS] All specialist registry, evidence, and claim boundary tests passed: {summary_line[-1] if summary_line else out[:60]}")

    # 2. Run check_production_specialists CLI
    chk_cmd = "python scripts/check_production_specialists.py --fail-on-unvalidated-promotion"
    code, out, err = run(chk_cmd, cwd=REPO_B)
    if code != 0 or "[PASS]" not in out:
        failures.append(f"Specialist production boundary check failed:\n{out}\n{err}")
    else:
        print("[PASS] Production specialist boundary audit verified with zero unvalidated promotions")

    # 3. Run validate_specialist_evidence CLI
    evid_cmd = "python scripts/validate_specialist_evidence.py"
    code, out, err = run(evid_cmd, cwd=REPO_B)
    if code != 0 or "[PASS]" not in out:
        failures.append(f"Specialist evidence ledger validation failed:\n{out}\n{err}")
    else:
        print("[PASS] Specialist evidence ledger and pilot package verified")

    if failures:
        print("\n=== GATE P6 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATE P6 (GATE G8) COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase6()
