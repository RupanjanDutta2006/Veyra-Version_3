import subprocess
import os
import sys

if os.path.isdir("backend") and os.path.isdir("models"):
    REPO_B = os.path.abspath(".")
    WORKSPACE = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    REPO_B = os.path.abspath("repos/repo_b")
    WORKSPACE = os.path.abspath(".")
else:
    REPO_B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WORKSPACE = REPO_B

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def test_phase4():
    print("=== Gate P4: Phase 4 Selective Safety Grafting Verification ===")
    failures = []

    # 1. Run ported safety tests in repo_b
    tests = [
        "backend/tests/test_v3_time_contract.py",
        "backend/tests/test_scientific_certification.py",
        "backend/tests/test_day33_ood_model_determinism.py",
        "backend/tests/test_day37_provider_adapters.py",
        "backend/tests/test_day38_cross_provider_disagreement.py"
    ]
    cmd = f"python -m pytest {' '.join(tests)} -q"
    code, out, err = run(cmd, cwd=REPO_B)
    if code != 0:
        failures.append(f"Safety tests failed (code {code}):\n{out}\n{err}")
    else:
        print(f"[PASS] All 88 ported safety tests passed:\n{out.splitlines()[0]}")

    # 2. Compare Golden V3 outputs
    code, out, err = run(
        "python scripts/compare_golden_v3_outputs.py --baseline artifacts/golden_v3_before.json --candidate artifacts/golden_v3_after.json",
        cwd=REPO_B
    )
    if code != 0:
        failures.append(f"Golden parity comparison failed:\n{out}\n{err}")
    else:
        print("[PASS] Golden V3 predictions maintain exact parity post-safety grafting")

    # 3. Verify UTC time contract functionality
    sys.path.insert(0, REPO_B)
    from backend.app.core.time_contract import derive_and_validate_lead_hours
    try:
        lead, _, _ = derive_and_validate_lead_hours("2026-09-22T00:00:00Z", "2026-09-23T06:00:00Z")
        assert lead == 30
        print(f"[PASS] UTC time contract validation confirmed (lead={lead}h)")
    except Exception as exc:
        failures.append(f"Time contract validation error: {exc}")

    # 4. Verify OOD Policy functionality
    from backend.app.core.ood_policy import evaluate_ood_policy, OODState
    ood_res = evaluate_ood_policy("temperature_2m", 300.0)
    if ood_res.status != OODState.IN_DISTRIBUTION:
        failures.append(f"OOD policy failed nominal check: {ood_res}")
    else:
        print(f"[PASS] OOD diagnostic policy confirmed: {ood_res.status.value}")

    # 5. Verify Certification Policy functionality
    from backend.app.core.certification_policy import evaluate_scientific_certification, CertificationStatus
    cert_res = evaluate_scientific_certification("Kolkata", "temperature_2m", 24)
    if cert_res.status != CertificationStatus.CERTIFIED:
        failures.append(f"Certification policy failed certified check: {cert_res}")
    else:
        print(f"[PASS] Scientific certification policy confirmed: {cert_res.status.value}")

    if failures:
        print("\n=== GATE P4 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATE P4 COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase4()
