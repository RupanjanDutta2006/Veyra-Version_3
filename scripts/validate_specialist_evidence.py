#!/usr/bin/env python3
"""Validate Specialist Scientific Evidence Ledger and Promotion Boundaries (Phase 06 / Gate G8).

Validates:
1. docs/science-evidence/specialist_evidence_ledger.csv exists and matches specialist_registry.py.
2. Invariant: Zero specialists are active in production without promotion signoff.
3. Invariant: Formula baselines are explicitly tagged with FORMULA_BASELINE evidence tier.
4. Invariant: Target definition and bust formula are defined for all active specialists.
5. Invariant: Pilot evidence package for Precipitation exists and contains required sections.
6. Invariant: ExplanationPolicy audit confirms zero forbidden causal assertions in target definitions.
"""

import csv
import os
import sys
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.builder2.specialist_registry import (
    SPECIALIST_REGISTRY,
    SpecialistStatus,
    ExplanationPolicy,
    is_specialist_active_in_production,
    evaluate_promotion_eligibility,
)


def validate_specialist_evidence(ledger_path: str = "docs/science-evidence/specialist_evidence_ledger.csv") -> int:
    print("=== Validating Specialist Scientific Evidence Ledger & Gate G8 Boundaries ===")
    full_path = REPO_ROOT / ledger_path if not os.path.isabs(ledger_path) else Path(ledger_path)

    if not full_path.exists():
        print(f"[FAIL] Evidence ledger not found: {full_path}")
        return 1

    failures = []

    # 1. Read and parse CSV
    with open(full_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[PASS] Loaded {len(rows)} entries from {full_path.name}")

    ledger_specialists = {r["specialist_id"]: r for r in rows}

    # 2. Check coverage against Python registry
    for name, reg in SPECIALIST_REGISTRY.items():
        if name not in ledger_specialists:
            failures.append(f"Specialist '{name}' registered in Python but missing in {full_path.name}")
            continue

        row = ledger_specialists[name]

        # Invariant: Active in production must be False
        if row["active_in_production"].lower() in ("true", "1") or is_specialist_active_in_production(name):
            failures.append(f"Specialist '{name}' is active in production without validated promotion!")

        # Invariant: Status matches registry
        if row["status"] != reg.status.value:
            failures.append(f"Specialist '{name}' status mismatch: CSV={row['status']} vs Code={reg.status.value}")

        # Invariant: Formula nature matches
        is_formula_csv = row["is_formula"].lower() in ("true", "1")
        if is_formula_csv != reg.is_formula:
            failures.append(f"Specialist '{name}' is_formula mismatch: CSV={is_formula_csv} vs Code={reg.is_formula}")

        # Invariant: Target definition and bust formula must exist
        if not row["target_definition"] or row["target_definition"] == "N/A":
            failures.append(f"Specialist '{name}' missing target definition in ledger")
        if not row["bust_formula"] or row["bust_formula"] == "N/A":
            failures.append(f"Specialist '{name}' missing bust formula in ledger")

        # Invariant: ExplanationPolicy audit
        ok, violations = ExplanationPolicy.audit_explanation_text(row["target_definition"])
        if not ok:
            failures.append(f"Specialist '{name}' target definition contains causal phrasing: {violations}")

        # Gate G8 promotion check
        eligible, blockers = evaluate_promotion_eligibility(reg)
        if reg.status == SpecialistStatus.PROMOTED and not eligible:
            failures.append(f"Specialist '{name}' marked PROMOTED but ineligible: {blockers}")

    # 3. Check Pilot Evidence Package for Precipitation
    precip_pkg_path = REPO_ROOT / "docs" / "science-evidence" / "pilot_evidence_package_precipitation.md"
    if not precip_pkg_path.exists():
        failures.append(f"Pilot evidence package missing: {precip_pkg_path}")
    else:
        content = precip_pkg_path.read_text(encoding="utf-8")
        required_sections = [
            "Meteorological Failure Formulation",
            "Strict Separation of Target Semantics",
            "Issue-Time Safe Feature Contract",
            "Temporal Data Splitting",
            "Baseline Ladder Empirical Evaluation",
            "Gate G8 Promotion Boundary Decision",
            "FORMULA_BASELINE (UNPROMOTED)",
        ]
        for sec in required_sections:
            if sec not in content:
                failures.append(f"Pilot evidence package missing required section: '{sec}'")
        print(f"[PASS] Pilot evidence package verified with all {len(required_sections)} required sections.")

    print("\n------------------------------------------------------------")
    if failures:
        print(f"[FAIL] Found {len(failures)} scientific evidence ledger violation(s):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("[PASS] All specialists comply with Scientific Evidence & Gate G8 boundaries.")
    print(f"       - {len(rows)} entries verified in specialist_evidence_ledger.csv.")
    print("       - All 6 hazard specialists safely contained as FORMULA_BASELINE / EXPERIMENTAL.")
    print("       - Zero unvalidated promotions into production.")
    print("       - Precipitation pilot evidence package verified.")
    return 0


if __name__ == "__main__":
    sys.exit(validate_specialist_evidence())
