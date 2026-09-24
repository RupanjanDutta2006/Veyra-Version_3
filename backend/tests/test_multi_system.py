"""Tests for Cross-System Transferability and Alignment (Gate 10 / Phase K)."""

import json
from pathlib import Path
import numpy as np
import pytest

from backend.app.builder2.cross_system_transfer_engine import CrossSystemTransferEngine


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def cross_system_evidence(repo_root):
    path = repo_root / "data" / "cross_system_evidence.json"
    assert path.is_file(), f"cross_system_evidence.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_cross_system_evidence_schema(cross_system_evidence):
    """Verify cross-system evidence covers all 6 hazards and required transfer systems."""
    hazards = cross_system_evidence.get("transfer_evidence_by_hazard", {})
    expected_hazards = [
        "PRECIPITATION",
        "CYCLONE",
        "MONSOON_LPS",
        "WESTERN_DISTURBANCE",
        "HEATWAVE",
        "SEVERE_WIND",
    ]

    for haz in expected_hazards:
        assert haz in hazards, f"Missing hazard in transfer evidence: {haz}"
        entry = hazards[haz]
        assert entry["incumbent_system"] == "ECMWF_IFS_025"
        transfers = entry["transfers"]
        for target in ["NOAA_GFS_025", "NCMRWF_UM_012", "OPEN_METEO_GEFS"]:
            assert target in transfers, f"Missing target system {target} for {haz}"
            t_data = transfers[target]
            assert t_data["delta_brier"] <= 0.035, f"Transfer degradation too high for {haz} -> {target}: {t_data['delta_brier']}"
            assert t_data["transfer_status"] == "CERTIFIED_TRANSFER"


def test_cross_system_transfer_engine_evaluation():
    """Verify CrossSystemTransferEngine computes accurate transfer Brier and status."""
    engine = CrossSystemTransferEngine(max_transfer_brier_delta=0.035)
    rng = np.random.RandomState(42)
    n = 400

    base_p = rng.uniform(0.1, 0.8, size=n)
    y_true = (rng.uniform(size=n) < base_p).astype(int)

    # Well-aligned transfer target: slight systematic noise
    p_src = np.clip(base_p + rng.normal(0.0, 0.04, size=n), 0.01, 0.99)
    p_tgt = np.clip(base_p + 0.02 + rng.normal(0.0, 0.05, size=n), 0.01, 0.99)

    res = engine.evaluate_transfer(
        source_system="ECMWF_IFS_025",
        target_system="NOAA_GFS_025",
        hazard_family="PRECIPITATION",
        source_probs=p_src,
        target_raw_probs=p_tgt,
        y_true=y_true,
    )

    assert res.is_transfer_certified is True
    assert res.status == "CERTIFIED_TRANSFER"
    assert res.delta_brier <= 0.035


def test_cross_system_transfer_engine_rejection_on_excessive_delta():
    """Verify transfer engine flags RECALIBRATION_REQUIRED when delta exceeds threshold."""
    engine = CrossSystemTransferEngine(max_transfer_brier_delta=0.035)
    rng = np.random.RandomState(42)
    n = 300

    y_true = np.zeros(n)
    p_src = np.full(n, 0.05)
    # Target system severely miscalibrated
    p_tgt = np.full(n, 0.85)

    res = engine.evaluate_transfer(
        source_system="ECMWF_IFS_025",
        target_system="EXPERIMENTAL_SYSTEM",
        hazard_family="CYCLONE",
        source_probs=p_src,
        target_raw_probs=p_tgt,
        y_true=y_true,
    )

    assert res.is_transfer_certified is False
    assert res.status == "RECALIBRATION_REQUIRED"
    assert res.delta_brier > 0.035
