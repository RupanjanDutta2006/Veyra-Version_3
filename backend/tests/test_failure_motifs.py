"""Tests for Failure Motifs catalog and classification engine (Gate 2 / Phase C)."""

import json
from pathlib import Path
import pytest

from backend.app.builder2.failure_motifs import (
    CANONICAL_FAILURE_MOTIFS,
    FailureMotif,
    MotifClassifier,
)
from backend.app.contracts.hazard_contracts import HazardFamily

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_motif_catalog_coverage():
    """Verify all 6 core hazard families are represented in canonical motifs."""
    assert len(CANONICAL_FAILURE_MOTIFS) == 6
    families = {m.hazard_family for m in CANONICAL_FAILURE_MOTIFS}
    expected = {
        HazardFamily.HEATWAVE,
        HazardFamily.PRECIPITATION,
        HazardFamily.WESTERN_DISTURBANCE,
        HazardFamily.CYCLONE,
        HazardFamily.MONSOON_LPS,
        HazardFamily.SEVERE_WIND,
    }
    assert families == expected


def test_motif_catalog_disk_file_integrity():
    """Verify data/motifs/motif_catalog.json exists and contains identical motif IDs."""
    catalog_path = REPO_ROOT / "data" / "motifs" / "motif_catalog.json"
    assert catalog_path.is_file(), "data/motifs/motif_catalog.json must exist"

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "motifs" in data
    assert len(data["motifs"]) == 6
    disk_ids = {m["motif_id"] for m in data["motifs"]}
    code_ids = {m.motif_id for m in CANONICAL_FAILURE_MOTIFS}
    assert disk_ids == code_ids


def test_motif_classifier_accurate_match():
    """Verify classifier identifies heat dome archetype given conforming trajectory & precursors."""
    classifier = MotifClassifier()
    heat_traj = [0.12, 0.28, 0.58, 0.88, 0.98]
    precursors = ["HIGH_Z500_ANOMALY", "SUBSIDENCE_WARMING", "CLEAR_SKY_SOLAR_EXCESS"]

    matches = classifier.classify(
        trajectory=heat_traj,
        precursor_signals=precursors,
        hazard_family=HazardFamily.HEATWAVE,
    )

    assert len(matches) > 0
    top = matches[0]
    assert top.motif_id == "MOTIF-HEAT-DOMING"
    assert top.similarity_score > 0.70
    assert len(top.precursors_matched) == 3


def test_motif_classifier_hazard_isolation():
    """Verify classifier respects hazard family filter."""
    classifier = MotifClassifier()
    matches = classifier.classify(
        trajectory=[0.1, 0.5, 0.9],
        precursor_signals=["ELEVATED_CAPE"],
        hazard_family=HazardFamily.HEATWAVE,
    )
    # Even if CAPE is present, HEATWAVE filter should only consider heatwave motifs
    for m in matches:
        assert m.hazard_family == HazardFamily.HEATWAVE
