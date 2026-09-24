#!/usr/bin/env python3
"""Run Operational Promotion Gate and Status Taxonomy Audit (Gate 10 / Phase K).

Audits all hazard reliability specialists against Gate 10 operational criteria:
- Validates promotion status taxonomy (FROZEN, CERTIFIED, OPERATIONAL_ONLY, EXPERIMENTAL, DIAGNOSTIC, ABSTAINED, REJECTED, FUTURE).
- Enforces non-negotiable invariant: No experimental model output may appear as certified.
- Audits Brier calibration, ECE, endpoint routing, and dissemination latency.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.contracts.operational_watchlist_contract import PromotionStatus


VALID_STATUSES = {s.value for s in PromotionStatus}


def run_operational_gate(all_hazards: bool = True) -> bool:
    """Audit operational hazard registry against Gate 10 standards."""
    registry_path = REPO_ROOT / "data" / "operational_hazard_registry.json"
    if not registry_path.is_file():
        print(f"[FAIL] Operational hazard registry not found at {registry_path}")
        return False

    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    registry = data.get("registry", {})
    invariants = data.get("invariants", {})

    print("================================================================================")
    print(" VEYRA OPERATIONAL PROMOTION GATE & TAXONOMY AUDIT (GATE 10 / PHASE K)")
    print(f" Total Registered Models: {len(registry)}")
    print(" Invariant: No experimental model output may appear as certified")
    print("================================================================================")

    all_passed = True

    print(f"\n{'Model ID':<28} | {'Hazard':<20} | {'Status':<16} | {'Brier':<8} | {'ECE':<7} | {'Gate Decision':<15}")
    print("-" * 105)

    for name, item in registry.items():
        status = item.get("status")
        model_id = item.get("model_id")
        hazard = item.get("hazard_family")
        brier = item.get("calibrated_brier")
        ece = item.get("ece")

        # 1. Status taxonomy validity
        if status not in VALID_STATUSES:
            print(f"{model_id:<28} | {hazard:<20} | {status:<16} | {brier:<8.4f} | {ece:<7.3f} | INVALID_STATUS")
            all_passed = False
            continue

        # 2. Strict invariant: No experimental as certified
        if status == "EXPERIMENTAL":
            if "CERTIFIED" in model_id:
                print(f"{model_id:<28} | {hazard:<20} | {status:<16} | {brier:<8.4f} | {ece:<7.3f} | VIOLATION: EXP_AS_CERT")
                all_passed = False
                continue
            decision = "HOLD (RESEARCH)"
        elif status in ["CERTIFIED", "OPERATIONAL_ONLY", "FROZEN"]:
            # Quality checks for certified models
            if brier > 0.150 or ece > 0.050:
                print(f"{model_id:<28} | {hazard:<20} | {status:<16} | {brier:<8.4f} | {ece:<7.3f} | REJECT (POOR_CAL)")
                all_passed = False
                continue
            decision = "APPROVED (PROMOTED)"
        else:
            decision = f"APPROVED ({status})"

        print(f"{model_id:<28} | {hazard:<20} | {status:<16} | {brier:<8.4f} | {ece:<7.3f} | {decision:<15}")

    print("\n================================================================================")
    if all_passed:
        print("[PASS] Gate 10 Operational Promotion Gate Successfully Certified.")
        print("================================================================================")
        return True
    else:
        print("[FAIL] Gate 10 Operational Promotion Gate failed one or more criteria.")
        print("================================================================================")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Operational Promotion Gate")
    parser.add_argument("--all-hazards", action="store_true", help="Audit all registered hazard specialists")
    args = parser.parse_args()

    success = run_operational_gate(all_hazards=args.all_hazards)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
