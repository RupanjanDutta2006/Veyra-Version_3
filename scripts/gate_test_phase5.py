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

def test_phase5():
    print("=== Gate P5 (Gates G9 & G11): Durable Revision Store & Honest Replay Rebuild ===")
    failures = []

    # 1. Run revision and replay pytest suite in repo_b
    tests = [
        "backend/tests/test_revision_store_restart.py",
        "backend/tests/test_truth_sealing.py",
        "backend/tests/test_replay_modes.py",
        "backend/tests/test_day34_time_contract_revision_store.py"
    ]
    cmd = f"python -m pytest {' '.join(tests)} -q"
    code, out, err = run(cmd, cwd=REPO_B)
    if code != 0:
        failures.append(f"Revision & Replay tests failed (code {code}):\n{out}\n{err}")
    else:
        summary_line = [l for l in out.splitlines() if "passed" in l]
        print(f"[PASS] All revision store and replay tests passed: {summary_line[-1] if summary_line else out[:60]}")

    # 2. Test Historical Replay CLI
    hist_cmd = "python scripts/replay_historical.py --mode historical --fixtures artifacts/immutable_forecast_truth_fixture"
    code, out, err = run(hist_cmd, cwd=REPO_B)
    if code != 0 or "[PASS]" not in out:
        failures.append(f"Historical replay CLI failed:\n{out}\n{err}")
    else:
        print("[PASS] Historical replay CLI executed with immutable inputs and independent truth contract")

    # 3. Test Digital Twin Synthetic Replay CLI
    twin_cmd = "python scripts/replay_digital_twin.py --mode synthetic --fixtures artifacts/synthetic_twin_fixture"
    code, out, err = run(twin_cmd, cwd=REPO_B)
    if code != 0 or "[NOTICE]" not in out or "[PASS]" not in out:
        failures.append(f"Synthetic digital twin CLI failed:\n{out}\n{err}")
    else:
        print("[PASS] Synthetic digital twin CLI executed with explicit SYNTHETIC disclosure label")

    # 4. Verify invalid mode rejection
    invalid_cmd = "python scripts/replay_historical.py --mode synthetic"
    code, out, err = run(invalid_cmd, cwd=REPO_B)
    if code == 0:
        failures.append("Historical replay CLI unexpectedly accepted invalid mode 'synthetic'!")
    else:
        print("[PASS] Replay harness strictly rejects synthetic mode masquerading as historical")

    if failures:
        print("\n=== GATE P5 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATE P5 (GATES G9 & G11) COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase5()
