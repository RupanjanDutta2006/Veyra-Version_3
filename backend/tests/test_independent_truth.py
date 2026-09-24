"""Tests for Independent Truth Audit, Verification Latency, and Truth Sealing (Gate 9 / Phase J)."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import pytest

from backend.app.builder2.independent_truth_audit import (
    IndependentTruthAuditEngine,
    TruthSealingStatus,
    ReferenceSensitivityResult,
)


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def audit_manifest(repo_root):
    path = repo_root / "data" / "reference_audit_manifest.json"
    assert path.is_file(), f"reference_audit_manifest.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_truth_sealing_enforcement():
    """Verify cryptographic truth sealing blocks premature verification before latency expiry."""
    engine = IndependentTruthAuditEngine()
    now_utc = datetime.now(timezone.utc)

    # 1. IMD station rainfall (24h latency) tested at valid_time + 10 hours -> must be SEALED
    valid_time_recent = now_utc - timedelta(hours=10)
    seal_res = engine.check_truth_sealing("REF-IMD-RAIN-01", valid_time_recent, now_utc)
    assert seal_res.is_sealed is True
    assert seal_res.status == "SEALED"
    assert seal_res.latency_hours == 24

    # 2. IMD station rainfall (24h latency) tested at valid_time + 30 hours -> must be UNLOCKED
    valid_time_matured = now_utc - timedelta(hours=30)
    unseal_res = engine.check_truth_sealing("REF-IMD-RAIN-01", valid_time_matured, now_utc)
    assert unseal_res.is_sealed is False
    assert unseal_res.status == "UNLOCKED"

    # 3. ERA5 reanalysis (120h latency) tested at valid_time + 48 hours -> must be SEALED
    era5_seal = engine.check_truth_sealing("REF-ERA5-01", valid_time_matured, now_utc)
    assert era5_seal.is_sealed is True
    assert era5_seal.status == "SEALED"
    assert era5_seal.latency_hours == 120


def test_sparse_reference_abstention():
    """Verify sparse station density triggers REFERENCE_UNAVAILABLE."""
    engine = IndependentTruthAuditEngine()

    # 0, 1, or 2 stations -> sparse
    for count in [0, 1, 2]:
        valid, status = engine.verify_station_density("Ladakh Sparse Valley", count)
        assert not valid
        assert status == "REFERENCE_UNAVAILABLE"

    # 3 or more stations -> certified
    for count in [3, 5, 25]:
        valid, status = engine.verify_station_density("Gangetic Plains", count)
        assert valid
        assert status == "VERIFIED"


def test_reference_audit_manifest_integrity(audit_manifest):
    """Verify independent truth audit manifest includes all required pairwise cross-validations."""
    audits = audit_manifest.get("pairwise_audits", {})
    expected_pairs = [
        "ERA5_vs_IMD_STATION_PRECIP",
        "ERA5_vs_IMD_STATION_TEMP",
        "ERA5_vs_RSMC_CYCLONE",
        "ERA5_vs_RADIOSONDE",
        "ERA5_vs_INSAT3D_SATELLITE",
    ]

    for pair in expected_pairs:
        assert pair in audits, f"Missing pairwise audit in manifest: {pair}"
        item = audits[pair]
        assert "mean_bias" in item or "mean_track_discrepancy_km" in item or "cape_bias_jkg" in item
        assert "sample_count" in item and item["sample_count"] >= 100
        assert "pearson_r" in item and item["pearson_r"] >= 0.80

    sens_summary = audit_manifest.get("reference_sensitivity_summary", {})
    assert sens_summary.get("max_brier_shift_across_references", 1.0) <= 0.030


def test_reference_sensitivity_evaluation():
    """Verify reference sensitivity evaluates Brier delta across primary and secondary truth."""
    engine = IndependentTruthAuditEngine()

    y_primary = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0] * 10
    # Secondary truth differs by 5%
    y_secondary = y_primary.copy()
    y_secondary[0] = 0
    y_secondary[10] = 1

    p_pred = [0.8, 0.2, 0.7, 0.9, 0.1, 0.3, 0.85, 0.15, 0.75, 0.25] * 10

    res = engine.evaluate_reference_sensitivity("PRECIPITATION", y_primary, y_secondary, p_pred)
    assert res.status == "ROBUST"
    assert res.delta_brier <= 0.030
    assert res.label_agreement_pct >= 90.0
