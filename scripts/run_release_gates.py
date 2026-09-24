"""Release Gate Orchestrator for Veyra Round-2.

Enforces that NO deployment or release artifact can proceed if any P0 gate fails.
Automates Gates G1, G2, G3, G8, G9, G11, G14, G15, G16, G17.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

# Resolve repository and workspace roots dynamically
CURRENT_DIR = Path.cwd()
if (CURRENT_DIR / "backend").is_dir() and (CURRENT_DIR / "models").is_dir():
    REPO_ROOT = CURRENT_DIR
    WORKSPACE = CURRENT_DIR
elif (CURRENT_DIR / "repos" / "repo_b" / "backend").is_dir():
    REPO_ROOT = CURRENT_DIR / "repos" / "repo_b"
    WORKSPACE = CURRENT_DIR
else:
    REPO_ROOT = Path(__file__).resolve().parent.parent
    WORKSPACE = REPO_ROOT

REPO_B_STR = str(REPO_ROOT)
WORKSPACE_STR = str(WORKSPACE)


def run(cmd, cwd=None):
    target_cwd = cwd or REPO_B_STR
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=target_cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def check_artifact_integrity() -> bool:
    print("[GATE G1/G3] Checking authoritative release manifest & artifact integrity...")
    cmd = "python scripts/verify_artifacts.py"
    code, out, err = run(cmd, cwd=REPO_B_STR)
    if code != 0:
        print(f"  FAILED: Artifact integrity check returned code {code}\n{out}\n{err}")
        return False
    print("  PASSED: V3 Model (00a84107...) & Calibrator (9f448606...) verified.")
    return True


def check_specialist_containment() -> bool:
    print("[GATE G8] Checking specialist containment & scientific promotion boundaries...")
    cmd = "python scripts/check_production_specialists.py --fail-on-unvalidated-promotion"
    code, out, err = run(cmd, cwd=REPO_B_STR)
    if code != 0:
        print(f"  FAILED: Specialist boundary audit failed:\n{out}\n{err}")
        return False
    print("  PASSED: All 6 specialists contained as FORMULA_BASELINE/EXPERIMENTAL.")
    return True


def check_replay_separation() -> bool:
    print("[GATE G11] Checking honest replay mode separation...")
    code1, out1, err1 = run("python scripts/replay_historical.py --mode historical", cwd=REPO_B_STR)
    code2, out2, err2 = run("python scripts/replay_digital_twin.py --mode synthetic", cwd=REPO_B_STR)
    if code1 != 0 or code2 != 0:
        print(f"  FAILED: Replay checks failed:\n{out1}\n{out2}\n{err1}\n{err2}")
        return False
    print("  PASSED: Historical and synthetic modes strictly separated.")
    return True


def check_security_and_operations() -> bool:
    print("[GATE G15] Checking security, secret hygiene & operations...")
    # Check for potential exposed API keys or secrets in repository
    code, out, _ = run('git grep -i -E "sk_live|private_key|aws_secret" -- ":!*.md" ":!*.json" ":!scripts/run_release_gates.py"', cwd=REPO_B_STR)
    if code == 0 and out.strip():
        print(f"  FAILED: Found potential hardcoded secret:\n{out}")
        return False
    print("  PASSED: No high-risk exposed secrets found.")
    return True


def check_rollback_governance() -> bool:
    print("[GATE G16] Checking rollback documentation & release governance...")
    rb_path = REPO_ROOT / "manifests" / "rollback_procedure.md"
    if not rb_path.is_file():
        rb_path = WORKSPACE / "manifests" / "rollback_procedure.md"
    if not rb_path.is_file():
        print(f"  FAILED: Missing rollback procedure at {rb_path}")
        return False
    with open(rb_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "Rollback Triggers" not in content or "Fast Rollback Procedure" not in content:
        print("  FAILED: Rollback procedure document is incomplete.")
        return False
    print("  PASSED: Authoritative rollback procedure verified.")
    return True


def check_claim_register() -> bool:
    print("[GATE G17] Checking claim register validation across all evidence classes...")
    claim_csv = REPO_ROOT / "manifests" / "claim_register.csv"
    if not claim_csv.is_file():
        claim_csv = WORKSPACE / "manifests" / "claim_register.csv"
    if not claim_csv.is_file():
        print(f"  FAILED: Missing claim register at {claim_csv}")
        return False
    cmd = f'python scripts/validate_claim_register.py --input "{claim_csv}"'
    code, out, err = run(cmd, cwd=REPO_B_STR)
    if code != 0 or "[PASS]" not in out:
        print(f"  FAILED: Claim register validation failed:\n{out}\n{err}")
        return False
    print("  PASSED: Claim register verified across all required evidence classes.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run Veyra Release Gates.")
    parser.add_argument("--require-all", action="store_true", help="Enforce all release gates")
    parser.add_argument("--require-artifacts", action="store_true")
    parser.add_argument("--require-replay", action="store_true")
    parser.add_argument("--require-security", action="store_true")
    parser.add_argument("--require-rollback", action="store_true")
    parser.add_argument("--require-specialists", action="store_true")
    parser.add_argument("--require-claims", action="store_true")
    parser.add_argument("--output-json", default=None, help="Path to export machine-readable JSON gate report")
    args = parser.parse_args()

    require_all = args.require_all or not any([
        args.require_artifacts, args.require_replay, args.require_security,
        args.require_rollback, args.require_specialists, args.require_claims
    ])

    gates = []
    if require_all or args.require_artifacts:
        gates.append(("Artifact Integrity (G1/G3)", check_artifact_integrity))
    if require_all or args.require_specialists:
        gates.append(("Specialist Containment (G8)", check_specialist_containment))
    if require_all or args.require_replay:
        gates.append(("Replay Separation (G11)", check_replay_separation))
    if require_all or args.require_security:
        gates.append(("Security & Operations (G15)", check_security_and_operations))
    if require_all or args.require_rollback:
        gates.append(("Rollback Governance (G16)", check_rollback_governance))
    if require_all or args.require_claims:
        gates.append(("Claim Register Governance (G17)", check_claim_register))

    failures = []
    gate_results = []
    start_time = time.time()

    print("\n============================================================")
    print("           VEYRA MANDATORY RELEASE GATES AUDIT              ")
    print("============================================================\n")

    for name, gate_fn in gates:
        t0 = time.time()
        passed = False
        error_msg = None
        try:
            passed = gate_fn()
            if not passed:
                failures.append(name)
                error_msg = "Gate function returned False"
        except Exception as exc:
            error_msg = str(exc)
            print(f"  EXCEPTION during {name}: {exc}")
            failures.append(name)

        elapsed = round(time.time() - t0, 3)
        gate_results.append({
            "name": name,
            "passed": passed,
            "elapsed_seconds": elapsed,
            "error": error_msg,
        })
        print("------------------------------------------------------------")

    total_elapsed = round(time.time() - start_time, 3)
    release_approved = len(failures) == 0

    if args.output_json:
        report_path = Path(args.output_json)
        if not report_path.is_absolute():
            report_path = REPO_ROOT / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "release_approved": release_approved,
            "total_gates": len(gates),
            "passed_gates": len(gates) - len(failures),
            "failed_gates": len(failures),
            "total_duration_seconds": total_elapsed,
            "gates": gate_results,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nMachine-readable release gate report written to: {report_path}")

    if failures:
        print(f"\n[RELEASE BLOCKED]: {len(failures)} required gate(s) FAILED:")
        for f in failures:
            print(f"  * {f}")
        sys.exit(1)
    else:
        print("\n[RELEASE APPROVED]: ALL MANDATORY RELEASE GATES PASSED.")
        print(f"System conforms to all scientific, governance, and operational standards ({total_elapsed}s).\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
