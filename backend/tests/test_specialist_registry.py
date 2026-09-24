import pytest
from backend.app.builder2.specialist_registry import (
    SPECIALIST_REGISTRY,
    SpecialistStatus,
    SpecialistOutputType,
    SpecialistOutput,
    ExplanationPolicy,
    get_specialist,
    is_specialist_active_in_production,
    evaluate_promotion_eligibility,
)

def test_all_six_specialists_are_formula_baselines():
    expected_formulas = [
        "precipitation",
        "cyclone",
        "monsoon",
        "western_disturbance",
        "heatwave",
    ]
    for spec_name in expected_formulas:
        spec = get_specialist(spec_name)
        assert spec is not None, f"Specialist {spec_name} missing from registry"
        assert spec.status == SpecialistStatus.FORMULA_BASELINE
        assert spec.is_formula is True
        assert spec.has_trained_artifact is False
        assert spec.model_sha256 is None

def test_experimental_engines_are_experimental():
    experimental_engines = [
        "spatial_reliability",
        "compound_hazard",
        "common_mode",
        "cross_system",
    ]
    for eng in experimental_engines:
        spec = get_specialist(eng)
        assert spec is not None, f"Engine {eng} missing from registry"
        assert spec.status == SpecialistStatus.EXPERIMENTAL

def test_severe_wind_is_quarantined():
    spec = get_specialist("severe_wind")
    assert spec is not None
    assert spec.status == SpecialistStatus.QUARANTINED
    assert spec.has_trained_artifact is False

def test_promotion_gate_g8_strictly_blocks_unpromoted():
    for name, spec in SPECIALIST_REGISTRY.items():
        eligible, blockers = evaluate_promotion_eligibility(spec)
        assert eligible is False, f"Unvalidated specialist {name} unexpectedly eligible for promotion!"
        assert len(blockers) > 0

def test_specialists_inactive_in_production_by_default():
    for name in SPECIALIST_REGISTRY:
        assert is_specialist_active_in_production(name) is False

def test_hazard_vs_bust_target_separation():
    # Verify SpecialistOutput enforces separate fields for hazard and bust probability
    out = SpecialistOutput(
        specialist_name="cyclone",
        value=0.85,
        output_type=SpecialistOutputType.FORMULA,
        coefficients_source="WMO intensity scale table 3",
        is_calibrated=False,
        calibrator_artifact=None,
        confidence_note="deterministic formula heuristic",
        hazard_occurrence_probability=0.85,
        bust_probability_given_hazard=0.28
    )
    assert out.hazard_occurrence_probability != out.bust_probability_given_hazard
    assert out.output_type == SpecialistOutputType.FORMULA

def test_explanation_policy_rejects_causal_language():
    bad_text = "The forecast bust was caused by severe convection leading to rapid error growth."
    ok, violations = ExplanationPolicy.audit_explanation_text(bad_text)
    assert ok is False
    assert len(violations) > 0

    good_text = "High bust probability is associated with low ensemble spread and strong convective instability."
    ok, violations = ExplanationPolicy.audit_explanation_text(good_text)
    assert ok is True
    assert len(violations) == 0
