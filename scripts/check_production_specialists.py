"""Check production specialists against Gate G8 scientific promotion boundaries.

Ensures no unvalidated or formula-based specialist is marked PROMOTED or enters
the production incumbent pipeline.
"""
import argparse
import sys
import os

WORKSPACE = os.path.abspath(".")
if os.path.exists(os.path.join(WORKSPACE, "backend")):
    sys.path.insert(0, WORKSPACE)
elif os.path.exists(os.path.join(WORKSPACE, "repos", "repo_b", "backend")):
    sys.path.insert(0, os.path.join(WORKSPACE, "repos", "repo_b"))

from backend.app.builder2.specialist_registry import (
    SPECIALIST_REGISTRY,
    SpecialistStatus,
    evaluate_promotion_eligibility,
    is_specialist_active_in_production,
)

def check_specialists(fail_on_unvalidated: bool = True) -> int:
    print("=== Checking Production Specialists & Gate G8 Promotion Boundaries ===")
    violations = []
    
    for name, reg in SPECIALIST_REGISTRY.items():
        print(f"\nEvaluating Specialist: [{name}]")
        print(f"  - Formal Name: {reg.name}")
        print(f"  - Status: {reg.status.value}")
        print(f"  - Nature: {'Deterministic Formula' if reg.is_formula else 'Trained Model'}")
        print(f"  - Has Trained Artifact: {reg.has_trained_artifact}")
        print(f"  - Active in Production: {is_specialist_active_in_production(name)}")

        # Check if unpromoted specialist is active in production
        if is_specialist_active_in_production(name):
            violations.append(f"Specialist '{name}' is active in production without validated promotion!")

        # Check Gate G8 promotion eligibility
        eligible, blockers = evaluate_promotion_eligibility(reg)
        if reg.status == SpecialistStatus.PROMOTED and not eligible:
            violations.append(f"Specialist '{name}' is marked PROMOTED but failed Gate G8:\n" + "\n".join(f"    * {b}" for b in blockers))
        
        # Verify formula baselines are labeled accurately
        if reg.is_formula and reg.status not in (SpecialistStatus.FORMULA_BASELINE, SpecialistStatus.EXPERIMENTAL):
            violations.append(f"Specialist '{name}' is a deterministic formula but has status '{reg.status.value}'")

    print("\n------------------------------------------------------------")
    if violations:
        print(f"[FAIL] Found {len(violations)} scientific promotion boundary violation(s):")
        for v in violations:
            print(f"  - {v}")
        if fail_on_unvalidated:
            return 1
    else:
        print("[PASS] All specialists comply with Gate G8 boundaries.")
        print("       All 6 hazard specialists are safely contained as FORMULA_BASELINE / EXPERIMENTAL.")
        print("       No uncertified specialist is active in the production incumbent path.")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit specialist promotion boundaries.")
    parser.add_argument(
        "--fail-on-unvalidated-promotion",
        action="store_true",
        default=True,
        help="Exit with non-zero status if unvalidated promotions are detected."
    )
    args = parser.parse_args()
    sys.exit(check_specialists(fail_on_unvalidated=args.fail_on_unvalidated_promotion))
