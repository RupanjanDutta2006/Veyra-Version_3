import argparse
import json
import os
import sys
import numpy as np

def compare(baseline_path, candidate_path, tolerance=1e-5):
    print(f"Comparing Golden V3 Predictions:")
    print(f"  Baseline:  {baseline_path}")
    print(f"  Candidate: {candidate_path}")
    
    with open(baseline_path, "r", encoding="utf-8") as f:
        b = json.load(f)
    with open(candidate_path, "r", encoding="utf-8") as f:
        c = json.load(f)

    b_raw = np.array(b["raw_predictions"])
    c_raw = np.array(c["raw_predictions"])
    b_cal = np.array(b["calibrated_predictions"])
    c_cal = np.array(c["calibrated_predictions"])

    raw_diff = float(np.max(np.abs(b_raw - c_raw)))
    cal_diff = float(np.max(np.abs(b_cal - c_cal)))

    print(f"  Max Raw Diff:        {raw_diff:.10f}")
    print(f"  Max Calibrated Diff: {cal_diff:.10f}")

    if raw_diff > tolerance:
        print(f"[FAIL] Raw predictions exceed tolerance {tolerance}!")
        return 1
    if cal_diff > tolerance:
        print(f"[FAIL] Calibrated predictions exceed tolerance {tolerance}!")
        return 1

    print("[PASS] Golden V3 predictions 100% PARITY MAINTAINED.")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="artifacts/golden_v3_before.json")
    parser.add_argument("--candidate", default="artifacts/golden_v3_after.json")
    parser.add_argument("--tolerance", type=float, default=1e-5)
    args = parser.parse_args()
    sys.exit(compare(args.baseline, args.candidate, args.tolerance))
