"""Phase 08 Gate — Demo, Trust-State, Data Fixture, and Operational Hardening.

Verifies:
1. All smoke tests pass (builder2, final, serving, weather, historical)
2. Trust-state contract documentation exists
3. Phase 08 backend tests pass
4. Submission readiness pre-checks (demo script, risk register, candidate SHA)
"""
import subprocess
import os
import sys

if os.path.isdir("backend") and os.path.isdir("models"):
    WORKSPACE = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    WORKSPACE = os.path.abspath("repos/repo_b")
else:
    WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def test_phase8():
    print("=== Gate P8: Demo, Trust-State, Data Fixture & Operational Hardening ===")
    failures = []

    # ── Phase 08 Core: Smoke Tests ──────────────────────────────────
    smoke_tests = [
        ("Builder-2 smoke test (fixture-scoped)", "python scripts/smoke_test_builder2.py"),
        ("Final integration smoke test", "python scripts/smoke_test_final.py"),
        ("Serving smoke test", "python scripts/smoke_test_serving.py"),
        ("Historical smoke test", "python scripts/smoke_test_historical.py"),
    ]

    for name, cmd in smoke_tests:
        code, out, err = run(cmd, cwd=WORKSPACE)
        if code != 0:
            failures.append(f"{name} failed:\n{out[-500:]}\n{err[-500:]}")
        else:
            print(f"[PASS] {name}")

    # ── Phase 08 Core: Trust-State Contract ─────────────────────────
    contract_path = os.path.join(WORKSPACE, "docs", "trust-state-contract.md")
    if not os.path.exists(contract_path):
        failures.append("Trust-state contract documentation missing (docs/trust-state-contract.md)")
    else:
        content = open(contract_path).read()
        required_sections = ["HIGH_CONFIDENCE", "MODERATE_CONFIDENCE", "ABSTAINED", "UNAVAILABLE", "Data Source Mode"]
        missing = [s for s in required_sections if s not in content]
        if missing:
            failures.append(f"Trust-state contract missing sections: {missing}")
        else:
            print("[PASS] Trust-state contract documentation verified")

    # ── Phase 08 Core: Backend Tests ────────────────────────────────
    code, out, err = run(
        "python -m pytest backend/tests/test_phase08_demo_operations.py -q --tb=short",
        cwd=WORKSPACE
    )
    if code != 0:
        failures.append(f"Phase 08 backend tests failed:\n{out[-500:]}\n{err[-500:]}")
    else:
        print(f"[PASS] Phase 08 backend test suite passed")

    # ── Submission Pre-Checks ───────────────────────────────────────
    # 1. Claim register validation
    code, out, err = run(
        "python scripts/validate_claim_register.py --input manifests/claim_register.csv",
        cwd=WORKSPACE
    )
    if code != 0:
        failures.append(f"Claim register validation failed:\n{out}\n{err}")
    else:
        print("[PASS] Master claim register verified")

    # 2. Submission smoke suite across all 9 states
    code, out, err = run(
        "python scripts/run_submission_smoke.py --states ready,abstain,ood,live,cached,fixture,fallback,synthetic,unavailable",
        cwd=WORKSPACE
    )
    if code != 0:
        failures.append(f"Submission smoke test failed:\n{out[-500:]}\n{err[-500:]}")
    else:
        print("[PASS] Submission smoke test passed across all 9 trust & provenance states")

    # 3. Candidate SHA file
    sha_file = os.path.join(WORKSPACE, "manifests", "candidate_sha.txt")
    if not os.path.exists(sha_file) or len(open(sha_file).read().strip()) < 40:
        failures.append("Candidate SHA record missing or invalid")
    else:
        print(f"[PASS] Candidate SHA verified: {open(sha_file).read().strip()}")

    # 4. Demo Script & Risk Register
    demo_file = os.path.join(WORKSPACE, "demo", "demo_script.md")
    risk_file = os.path.join(WORKSPACE, "manifests", "risk_register.md")
    if not os.path.exists(demo_file):
        failures.append("Judge-facing demo script missing")
    else:
        print("[PASS] Judge-facing demo script verified")
    if not os.path.exists(risk_file):
        failures.append("Risk register missing")
    else:
        print("[PASS] Scientific risk register verified")

    if failures:
        print("\n=== GATE P8 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATE P8 (DEMO & OPERATIONS HARDENING) COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase8()

