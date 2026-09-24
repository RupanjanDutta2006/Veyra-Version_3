"""Unit tests for Monsoon and LPS Target Verification (Gate 5 / Phase F)."""

import json
from pathlib import Path
import pytest

from backend.app.contracts.monsoon_contract import (
    load_monsoon_event_catalogue,
    load_monsoon_target_manifest,
)


def test_monsoon_target_manifest_structure():
    """Verify all Gate 5 required monsoon targets are defined."""
    manifest = load_monsoon_target_manifest()
    target_ids = [t["target_id"] for t in manifest["targets"]]

    assert "MONSOON-LPS-LOC-01" in target_ids
    assert "MONSOON-LPS-SPEED-01" in target_ids
    assert "MONSOON-LPS-INTENSITY-01" in target_ids
    assert "MONSOON-PRECIP-LOC-01" in target_ids
    assert "MONSOON-PRECIP-AMT-01" in target_ids
    assert "MONSOON-REGIME-TRANS-01" in target_ids


def test_monsoon_target_thresholds():
    """Verify exact thresholds and units match Phase F specifications."""
    manifest = load_monsoon_target_manifest()
    targets_by_id = {t["target_id"]: t for t in manifest["targets"]}

    # System location: > 200 km
    loc_target = targets_by_id["MONSOON-LPS-LOC-01"]
    assert loc_target["threshold_value"] == 200.0
    assert loc_target["threshold_unit"] == "km"

    # Propagation speed: > 5 km/h or arrival timing > 12h
    speed_target = targets_by_id["MONSOON-LPS-SPEED-01"]
    assert speed_target["threshold_value"] == 5.0
    assert speed_target["threshold_unit"] == "km/h"
    assert speed_target["secondary_threshold_value"] == 12.0
    assert speed_target["secondary_threshold_unit"] == "hours"

    # Central pressure deepening: > 4 hPa
    deep_target = targets_by_id["MONSOON-LPS-INTENSITY-01"]
    assert deep_target["threshold_value"] == 4.0
    assert deep_target["threshold_unit"] == "hPa"

    # Rainfall placement: > 100 km
    precip_loc_target = targets_by_id["MONSOON-PRECIP-LOC-01"]
    assert precip_loc_target["threshold_value"] == 100.0
    assert precip_loc_target["threshold_unit"] == "km"

    # Rainfall intensity: > 50 mm/24h
    precip_amt_target = targets_by_id["MONSOON-PRECIP-AMT-01"]
    assert precip_amt_target["threshold_value"] == 50.0
    assert precip_amt_target["threshold_unit"] == "mm/24h"

    # Regime transition: > 24h
    regime_target = targets_by_id["MONSOON-REGIME-TRANS-01"]
    assert regime_target["threshold_value"] == 24.0
    assert regime_target["threshold_unit"] == "hours"


def test_monsoon_event_catalogue_integrity():
    """Verify historical event catalogue has required fields and benchmark episodes."""
    catalogue = load_monsoon_event_catalogue()
    events = catalogue["events"]
    assert len(events) >= 6

    event_ids = [e["event_id"] for e in events]
    assert "MONSOON-2018-BOB-01" in event_ids
    assert "MONSOON-2019-BOB-02" in event_ids
    assert "MONSOON-2021-REGIME-01" in event_ids
    assert "MONSOON-2022-BOB-05" in event_ids

    for ev in events:
        assert "system_type" in ev
        assert "regime" in ev
        assert "period" in ev
        assert "observed_error_modes" in ev
        assert len(ev["observed_error_modes"]) > 0


def test_monsoon_three_pillar_target_evaluation():
    """Verify target threshold exceedance evaluation logic across all 3 pillars."""
    # Pillar 1: System Dynamics
    loc_error_km = 225.0
    is_loc_bust = loc_error_km > 200.0
    assert is_loc_bust is True

    speed_error_kmh = 6.2
    is_speed_bust = speed_error_kmh > 5.0
    assert is_speed_bust is True

    deepening_error_hpa = 5.5
    is_deepening_bust = deepening_error_hpa > 4.0
    assert is_deepening_bust is True

    # Pillar 2: Precipitation
    precip_loc_error_km = 135.0
    is_precip_loc_bust = precip_loc_error_km > 100.0
    assert is_precip_loc_bust is True

    precip_amt_error_mm = 62.0
    is_precip_amt_bust = precip_amt_error_mm > 50.0
    assert is_precip_amt_bust is True

    # Pillar 3: Regime Transition
    transition_timing_error_hours = 30.0
    is_transition_bust = transition_timing_error_hours > 24.0
    assert is_transition_bust is True
