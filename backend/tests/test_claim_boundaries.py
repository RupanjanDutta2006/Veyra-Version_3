import pytest
from backend.app.builder2.specialist_registry import (
    SPECIALIST_REGISTRY,
    SpecialistStatus,
    ExplanationPolicy,
)
from backend.app.core.certification_policy import (
    evaluate_scientific_certification,
    CertificationStatus,
)

def test_only_v3_benchmark_has_certification():
    # Only Kolkata temperature_2m at 24h is certified under frozen incumbent
    cert_res = evaluate_scientific_certification("Kolkata", "temperature_2m", 24)
    assert cert_res.status == CertificationStatus.CERTIFIED

    # Other variable or uncertified horizon
    uncert_res = evaluate_scientific_certification("Kolkata", "total_precipitation", 24)
    assert uncert_res.status != CertificationStatus.CERTIFIED

def test_specialists_cannot_claim_certification():
    for name, spec in SPECIALIST_REGISTRY.items():
        assert spec.status != SpecialistStatus.PROMOTED, (
            f"Specialist '{name}' cannot be marked PROMOTED without passing Gate G8!"
        )

def test_explanation_non_causal_enforcement():
    causal_examples = [
        "The model busted because of convective instability.",
        "Rapid temperature drop caused by cold front.",
        "Error growth leads to severe failure.",
    ]
    for text in causal_examples:
        ok, violations = ExplanationPolicy.audit_explanation_text(text)
        assert ok is False, f"Expected violation for causal text: '{text}'"

    non_causal_examples = [
        "High bust probability is associated with convective instability.",
        "Observed temperature anomalies are correlated with frontal passage.",
        "Error patterns are consistent with rapid baroclinic growth.",
    ]
    for text in non_causal_examples:
        ok, violations = ExplanationPolicy.audit_explanation_text(text)
        assert ok is True, f"Expected non-causal pass for text: '{text}'"
