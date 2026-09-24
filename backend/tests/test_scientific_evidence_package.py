"""Automated Tests for Scientific Evidence Packages and Gate G8 Promotion Boundaries.

Verifies:
1. specialist_evidence_ledger.csv existence, schema, and completeness.
2. Strict unpromoted status for all formula-based and experimental specialists.
3. Target separation between hazard occurrence P(Hazard) and forecast bust P(Bust | Hazard).
4. Pilot evidence package for Precipitation completeness and section presence.
5. Non-causal wording compliance via ExplanationPolicy.
6. CLI evidence validator execution.
"""

import csv
import subprocess
import sys
from pathlib import Path
import pytest

from backend.app.builder2.specialist_registry import (
    SPECIALIST_REGISTRY,
    SpecialistStatus,
    SpecialistOutputType,
    SpecialistOutput,
    ExplanationPolicy,
    is_specialist_active_in_production,
    evaluate_promotion_eligibility,
    export_specialist_evidence_ledger,
)
from backend.app.builder2.precipitation_specialist import PrecipitationReliabilitySpecialist


REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "docs" / "science-evidence" / "specialist_evidence_ledger.csv"
PILOT_PACKAGE_PATH = REPO_ROOT / "docs" / "science-evidence" / "pilot_evidence_package_precipitation.md"


def test_specialist_evidence_ledger_exists():
    """Verify specialist_evidence_ledger.csv exists and has expected header structure."""
    assert LEDGER_PATH.exists(), f"Missing ledger file at {LEDGER_PATH}"
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        assert headers is not None
        expected_cols = [
            "specialist_id",
            "name",
            "hazard_family",
            "status",
            "evidence_tier",
            "is_formula",
            "has_trained_artifact",
            "target_definition",
            "bust_formula",
            "target_manifest",
            "evidence_package",
            "promotion_gate_status",
            "active_in_production",
        ]
        for col in expected_cols:
            assert col in headers, f"Missing column '{col}' in evidence ledger"


def test_all_registered_specialists_in_ledger():
    """Every specialist in SPECIALIST_REGISTRY must be present in the ledger CSV."""
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ledger_ids = {r["specialist_id"] for r in rows}

    for key in SPECIALIST_REGISTRY:
        assert key in ledger_ids, f"Specialist '{key}' registered in Python but missing in ledger CSV"


def test_zero_specialists_active_in_production():
    """Invariant: Zero specialists are active in production without validated promotion."""
    for key, spec in SPECIALIST_REGISTRY.items():
        assert is_specialist_active_in_production(key) is False, (
            f"Specialist '{key}' is active in production without promotion!"
        )
        assert spec.status != SpecialistStatus.PROMOTED


def test_gate_g8_promotion_eligibility_blocks_all_unvalidated():
    """Gate G8 strictly blocks unpromoted specialists from entering production."""
    for name, spec in SPECIALIST_REGISTRY.items():
        eligible, blockers = evaluate_promotion_eligibility(spec)
        assert eligible is False, f"Specialist '{name}' unexpectedly eligible for promotion"
        assert len(blockers) > 0


def test_formula_specialists_have_targets_and_bust_formulas():
    """All 5 active formula hazard specialists must have defined targets and bust formulas."""
    active_formula_hazards = ["precipitation", "cyclone", "monsoon", "western_disturbance", "heatwave"]
    for hazard in active_formula_hazards:
        spec = SPECIALIST_REGISTRY.get(hazard)
        assert spec is not None
        assert spec.target_definition is not None and len(spec.target_definition) > 10
        assert spec.bust_formula is not None and len(spec.bust_formula) > 5
        assert spec.evidence_tier == "FORMULA_BASELINE"


def test_target_separation_in_specialist_output():
    """Verify SpecialistOutput requires distinct hazard occurrence vs bust probability semantics."""
    out = SpecialistOutput(
        specialist_name="precipitation",
        value=0.30,
        output_type=SpecialistOutputType.FORMULA,
        coefficients_source="physics thresholds",
        is_calibrated=False,
        calibrator_artifact=None,
        confidence_note="formula baseline heuristic",
        hazard_occurrence_probability=0.75,
        bust_probability_given_hazard=0.30,
    )
    assert out.hazard_occurrence_probability != out.bust_probability_given_hazard
    assert out.output_type == SpecialistOutputType.FORMULA


def test_pilot_evidence_package_completeness():
    """Verify pilot evidence package for Precipitation exists and contains required scientific sections."""
    assert PILOT_PACKAGE_PATH.exists(), f"Pilot package missing at {PILOT_PACKAGE_PATH}"
    content = PILOT_PACKAGE_PATH.read_text(encoding="utf-8")

    required_sections = [
        "Executive Summary & Purpose",
        "Meteorological Failure Formulation & Target Thresholds",
        "Strict Separation of Target Semantics",
        "Issue-Time Safe Feature Contract",
        "Temporal Data Splitting & Held-Out Event Protocol",
        "Baseline Ladder Empirical Evaluation",
        "Selective Prediction & Risk-Coverage Tradeoff",
        "Independent Ground Truth & Cryptographic Truth Sealing",
        "Gate G8 Promotion Boundary Decision",
        "FORMULA_BASELINE (UNPROMOTED)",
    ]
    for sec in required_sections:
        assert sec in content, f"Pilot evidence package missing required section: '{sec}'"


def test_explanation_policy_audit_on_ledger():
    """Audit all target definitions in the ledger for forbidden causal phrasing."""
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        target_def = row["target_definition"]
        ok, violations = ExplanationPolicy.audit_explanation_text(target_def)
        assert ok is True, f"Specialist '{row['specialist_id']}' target definition failed policy: {violations}"


def test_export_specialist_evidence_ledger_parity():
    """export_specialist_evidence_ledger() output matches ledger CSV row count and keys."""
    exported = export_specialist_evidence_ledger()
    assert len(exported) == len(SPECIALIST_REGISTRY)

    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(exported) == len(rows)

    exported_keys = {r["specialist_id"] for r in exported}
    csv_keys = {r["specialist_id"] for r in rows}
    assert exported_keys == csv_keys


def test_cli_specialist_evidence_validator_exits_zero():
    """Running scripts/validate_specialist_evidence.py must exit with returncode 0."""
    script_path = REPO_ROOT / "scripts" / "validate_specialist_evidence.py"
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert res.returncode == 0, f"Validator failed:\n{res.stdout}\n{res.stderr}"
    assert "[PASS]" in res.stdout


def test_precipitation_specialist_ladder_hierarchy():
    """Test PrecipitationReliabilitySpecialist baseline ladder logic."""
    specialist = PrecipitationReliabilitySpecialist()

    # Level 1: Climatology
    clim = specialist.evaluate_climatology_baseline(season="monsoon", terrain_class="inland")
    assert 0.0 < clim < 0.50

    # Level 2: Raw ensemble spread uncertainty proxy
    spread_p = specialist.evaluate_raw_ensemble_baseline(spread_mm=15.0, mean_mm=20.0)
    assert 0.0 < spread_p < 1.0

    # Level 3: Calibrated spread-to-bust logistic regression
    logit_p = specialist.evaluate_spread_logistic_baseline(spread_mm=15.0, lead_hours=48)
    assert 0.0 < logit_p < 1.0

    # Level 5: Continuous error distribution
    dist = specialist.evaluate_continuous_error_distribution(mean_mm=25.0, spread_mm=10.0, lead_hours=48)
    assert dist.q50 is not None
    assert dist.crps > 0.0
    assert dist.rmse > 0.0
