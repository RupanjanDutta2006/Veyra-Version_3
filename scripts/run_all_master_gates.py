"""Master Gate Orchestrator for Veyra SIH Round-2 Integration Roadmap.

Executes all compulsory gate tests across every phase in sequential order:
- Step 1: Clone and Workspace Setup
- Phase 0: Freeze and Inventory (Gate P0-0)
- Phase 1: Truth Alignment & Claim Register (Gate P0-1)
- Phase 2: Base Selection & Branch Controls (Gate P0-2)
- Phase 3: Incumbent Artifact Repair (Gates G1–G3)
- Phase 4: Selective Safety Grafting (Gate P4 / G4–G7)
- Phase 5: Durable Revision Store & Honest Replay (Gates G9, G11)
- Phase 6: Specialist Containment & Promotion Boundary (Gate G8)
- Phase 7: CI, Reproducibility & Release Consolidation (Gates G14–G17)
- Phase 8: Submission Readiness & Final Acceptance Gate
"""
import subprocess
import time
import sys
import os

if os.path.isdir("backend") and os.path.isdir("models"):
    WORKSPACE = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    WORKSPACE = os.path.abspath("repos/repo_b")
else:
    WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GATE_STEPS = [
    ("Step 1: Workspace & Repositories Setup", "python scripts/gate_test_step1.py"),
    ("Phase 0: Freeze and Inventory (Gate P0-0)", "python scripts/gate_test_phase0.py"),
    ("Phase 1: Truth Alignment & Claim Register (Gate P0-1)", "python scripts/validate_claim_register.py --input manifests/claim_register.csv"),
    ("Phase 2: Base Selection & Branch Controls (Gate P0-2)", "python scripts/gate_test_phase2.py"),
    ("Phase 3: Incumbent Artifact Repair (Gates G1-G3)", "python scripts/gate_test_phase3.py"),
    ("Phase 4: Selective Safety Grafting (Gate P4)", "python scripts/gate_test_phase4.py"),
    ("Phase 5: Revision Store & Replay Rebuild (Gates G9, G11)", "python scripts/gate_test_phase5.py"),
    ("Phase 6: Specialist Containment & Boundaries (Gate G8)", "python scripts/gate_test_phase6.py"),
    ("Phase 7: Test, CI & Release Consolidation (Gates G14-G17)", "python scripts/gate_test_phase7.py"),
    ("Phase 8: Final Master Submission Gate", "python scripts/gate_test_phase8.py"),
]

def run_command(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=WORKSPACE)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def main():
    print("================================================================================")
    print("      VEYRA SIH ROUND-2 MASTER ROADMAP ACCEPTANCE GATE RUNNER                   ")
    print("================================================================================\n")
    start_total = time.time()
    failed = []

    for name, cmd in GATE_STEPS:
        print(f">>> RUNNING: {name} ...")
        t0 = time.time()
        code, out, err = run_command(cmd)
        elapsed = time.time() - t0

        if code != 0:
            print(f"  [FAILED] ({elapsed:.2f}s) Return code: {code}")
            print(f"  Output:\n{out}\n{err}")
            failed.append((name, out, err))
            break
        else:
            # Print last non-empty line of output
            lines = [l for l in out.splitlines() if l.strip()]
            summary = lines[-1] if lines else "Passed"
            print(f"  [PASSED] ({elapsed:.2f}s) -> {summary}\n")

    total_time = time.time() - start_total
    print("================================================================================")
    if failed:
        print(f"RESULT: FAILED AT {failed[0][0]} (Total time: {total_time:.2f}s)")
        sys.exit(1)
    else:
        print(f"RESULT: ALL 10 GATES PASSED WITH 100% SUCCESS! (Total time: {total_time:.2f}s)")
        print("Authoritative release candidate ready: sih-round2-submission-v1.0.0")
        print("================================================================================")
        sys.exit(0)

if __name__ == "__main__":
    main()
