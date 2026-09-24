"""Test suite for Veyra Hazard Operational Contracts, Availability Matrix, and Manifests (Gate 0 / Phase A)."""

import hashlib
import json
from pathlib import Path
import pytest

from backend.app.contracts.hazard_contracts import (
    HazardFamily,
    OperationalStatus,
    load_hazard_availability_matrix,
    get_hazard_contract,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_hazard_availability_matrix_load_and_validate():
    """Verify hazard_availability_matrix.json loads and satisfies Pydantic schemas."""
    matrix = load_hazard_availability_matrix()
    assert matrix.version == "1.0.0"
    assert matrix.gate == "Gate 0"
    assert len(matrix.hazards) == 6

    # Verify all 6 core hazard families are represented
    found_families = {h.hazard_family for h in matrix.hazards}
    expected_families = {
        HazardFamily.PRECIPITATION,
        HazardFamily.CYCLONE,
        HazardFamily.MONSOON_LPS,
        HazardFamily.WESTERN_DISTURBANCE,
        HazardFamily.HEATWAVE,
        HazardFamily.SEVERE_WIND,
    }
    assert found_families == expected_families


def test_hazard_contract_properties_and_invariants():
    """Verify specific hazard contracts have valid physics, units, and latency."""
    precip = get_hazard_contract(HazardFamily.PRECIPITATION)
    assert precip is not None
    assert precip.dissemination_latency_hours > 0.0
    assert precip.ensemble.member_count == 31
    assert precip.ensemble.minimum_required_members >= 20
    assert precip.reference.verification_latency_days >= 1

    cyclone = get_hazard_contract(HazardFamily.CYCLONE)
    assert cyclone is not None
    assert cyclone.operational_status == OperationalStatus.PROXY
    assert cyclone.dissemination_latency_hours == 3.0

    heatwave = get_hazard_contract(HazardFamily.HEATWAVE)
    assert heatwave is not None
    assert heatwave.operational_status == OperationalStatus.OPERATIONAL
    assert heatwave.label_contract.threshold_plains_celsius == 40.0


def test_target_manifest_integrity():
    """Verify target_manifest.json exists and defines canonical non-leaking targets."""
    target_manifest_path = REPO_ROOT / "data" / "target_manifest.json"
    assert target_manifest_path.is_file(), "data/target_manifest.json must exist"

    with open(target_manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "targets" in data
    assert len(data["targets"]) >= 7

    target_names = {t["target_name"] for t in data["targets"]}
    assert "bust_95th_mad" in target_names
    assert "bust_precip_95th_mad" in target_names
    assert "bust_cyclone_track_intensity" in target_names
    assert "bust_lps_track_genesis" in target_names
    assert "bust_wd_arrival_precipitation" in target_names
    assert "bust_heatwave_threshold" in target_names
    assert "bust_gale_gust_exceedance" in target_names


def test_reference_manifest_integrity():
    """Verify reference_manifest.json defines authoritative ground truth sources."""
    ref_manifest_path = REPO_ROOT / "data" / "reference_manifest.json"
    assert ref_manifest_path.is_file(), "data/reference_manifest.json must exist"

    with open(ref_manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "references" in data
    ref_ids = {r["reference_id"] for r in data["references"]}
    assert "REF-ERA5-01" in ref_ids
    assert "REF-IMD-RAIN-01" in ref_ids
    assert "REF-IMD-TEMP-01" in ref_ids
    assert "REF-IMD-TC-01" in ref_ids
    assert "REF-GHCND-01" in ref_ids

    for ref in data["references"]:
        assert ref["dissemination_latency_days"] >= 0
        assert "canonical_units" in ref


def test_v3_certified_document_against_disk_artifacts():
    """Verify models/v3/V3_CERTIFIED.json matches actual model and calibrator files on disk."""
    cert_path = REPO_ROOT / "models" / "v3" / "V3_CERTIFIED.json"
    assert cert_path.is_file(), "models/v3/V3_CERTIFIED.json must exist"

    with open(cert_path, "r", encoding="utf-8") as f:
        cert = json.load(f)

    assert cert["status"] == "CERTIFIED"
    assert cert["gate"] == "Gate 0"

    # Check model sha
    model_file = REPO_ROOT / "models" / "v3" / cert["artifacts"]["model"]["filename"]
    assert model_file.is_file()
    actual_model_sha = hashlib.sha256(model_file.read_bytes()).hexdigest().lower()
    assert actual_model_sha == cert["artifacts"]["model"]["sha256"]

    # Check calibrator sha
    cal_file = REPO_ROOT / "models" / "v3" / cert["artifacts"]["calibrator"]["filename"]
    assert cal_file.is_file()
    actual_cal_sha = hashlib.sha256(cal_file.read_bytes()).hexdigest().lower()
    assert actual_cal_sha == cert["artifacts"]["calibrator"]["sha256"]

    # Check feature count
    feat_file = REPO_ROOT / "models" / "v3" / cert["artifacts"]["features"]["filename"]
    assert feat_file.is_file()
    with open(feat_file, "r", encoding="utf-8") as f:
        feats = json.load(f)
    assert len(feats) == cert["artifacts"]["features"]["feature_count"] == 50
