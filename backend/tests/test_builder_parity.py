"""Tests for Builder 2 to Builder 1 Parity and Schema Compatibility (Gate 10 / Phase K)."""

import pytest

from backend.app.builder2.builder_parity_adapter import BuilderParityAdapter
from backend.app.contracts.operational_watchlist_contract import (
    ConformalBounds,
    PromotionStatus,
)


def test_builder_parity_certified_payload():
    """Verify certified specialist output correctly maps to Builder 1 payload with full parity."""
    bounds = ConformalBounds(lower_bound=0.12, upper_bound=0.28, target_coverage=0.90)
    payload = BuilderParityAdapter.adapt_specialist_output(
        hazard_family="PRECIPITATION",
        model_id="PRECIP_RELIABILITY_V1",
        model_version="1.0.0",
        failure_prob=0.20,
        epistemic_uncertainty=0.04,
        ood_score=0.15,
        conformal_bounds=bounds,
        status=PromotionStatus.CERTIFIED,
        location="MUMBAI",
        variable="precipitation_mm",
        lead_hours=48,
    )

    assert payload["hazard_family"] == "PRECIPITATION"
    assert payload["calibrated_probability"] == 0.20
    assert payload["epistemic_uncertainty"] == 0.04
    assert payload["ood_score"] == 0.15
    assert payload["status"] == "CERTIFIED"
    assert payload["is_abstained"] is False
    assert payload["conformal_interval"]["lower_bound"] == 0.12
    assert payload["conformal_interval"]["upper_bound"] == 0.28

    verification = BuilderParityAdapter.verify_parity(payload)
    assert verification.is_valid is True
    assert verification.status == "PARITY_VERIFIED"


def test_builder_parity_abstained_payload():
    """Verify abstained specialist output safely maps to null probability without fake defaults."""
    payload = BuilderParityAdapter.adapt_specialist_output(
        hazard_family="CYCLONE",
        model_id="CYCLONE_RELIABILITY_V1",
        model_version="1.0.0",
        failure_prob=None,
        epistemic_uncertainty=0.12,
        ood_score=0.92,
        conformal_bounds=None,
        status=PromotionStatus.ABSTAINED,
        location="PARADIP",
        variable="wind_speed_ms",
        lead_hours=72,
    )

    assert payload["calibrated_probability"] is None
    assert payload["is_abstained"] is True
    assert payload["risk_level"] == "ABSTAINED"
    assert payload["conformal_interval"] is None

    verification = BuilderParityAdapter.verify_parity(payload)
    assert verification.is_valid is True
    assert verification.status == "PARITY_VERIFIED"


def test_builder_parity_rejects_fake_defaults_on_abstention():
    """Verify parity validator rejects corrupt payloads containing fake numbers on abstention."""
    corrupt_payload = {
        "forecast_id": "FC_DELHI_temp_48h",
        "hazard_family": "HEATWAVE",
        "model_id": "HEATWAVE_RELIABILITY_V1",
        "model_version": "1.0.0",
        "status": "ABSTAINED",
        "calibrated_probability": 0.0,  # FAKE DEFAULT! Must be None
        "epistemic_uncertainty": 0.05,
        "ood_score": 0.95,
        "is_abstained": True,
        "provenance": {},
    }

    verification = BuilderParityAdapter.verify_parity(corrupt_payload)
    assert verification.is_valid is False
    assert verification.status == "CORRUPT_ABSTENTION"


def test_builder_parity_rejects_missing_fields():
    """Verify parity validator flags missing canonical fields."""
    incomplete_payload = {
        "forecast_id": "FC_DELHI_temp_48h",
        "hazard_family": "HEATWAVE",
        # Missing model_id, status, calibrated_probability, etc.
    }

    verification = BuilderParityAdapter.verify_parity(incomplete_payload)
    assert verification.is_valid is False
    assert verification.status == "MISSING_FIELDS"
    assert len(verification.missing_fields) > 0
