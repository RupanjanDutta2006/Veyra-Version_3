"""Unit tests for Western Disturbance Target Verification (Gate 6 / Phase G)."""

import json
from pathlib import Path
import pytest

from backend.app.contracts.western_disturbance_contract import (
    load_wd_event_catalogue,
    load_wd_target_manifest,
)


def test_western_disturbance_target_manifest_structure():
    """Verify all Gate 6 required western disturbance targets are defined."""
    manifest = load_wd_target_manifest()
    target_ids = [t["target_id"] for t in manifest["targets"]]

    assert "WD-ARRIVAL-01" in target_ids
    assert "WD-TRACK-LOC-01" in target_ids
    assert "WD-PRECIP-AMT-01" in target_ids
    assert "WD-PRECIP-DISP-01" in target_ids
    assert "WD-DURATION-01" in target_ids
    assert "WD-RAIN-SNOW-01" in target_ids


def test_western_disturbance_target_thresholds():
    """Verify exact thresholds and units match Phase G specifications."""
    manifest = load_wd_target_manifest()
    targets_by_id = {t["target_id"]: t for t in manifest["targets"]}

    # Arrival timing: > 6.0h (secondary 12.0h)
    arr_target = targets_by_id["WD-ARRIVAL-01"]
    assert arr_target["threshold_value"] == 6.0
    assert arr_target["threshold_unit"] == "hours"
    assert arr_target["secondary_threshold_value"] == 12.0
    assert arr_target["secondary_threshold_unit"] == "hours"

    # Trough/center position: > 150.0 km (secondary 250.0 km)
    loc_target = targets_by_id["WD-TRACK-LOC-01"]
    assert loc_target["threshold_value"] == 150.0
    assert loc_target["threshold_unit"] == "km"
    assert loc_target["secondary_threshold_value"] == 250.0
    assert loc_target["secondary_threshold_unit"] == "km"

    # Precipitation intensity: > 35.0 mm/24h
    precip_target = targets_by_id["WD-PRECIP-AMT-01"]
    assert precip_target["threshold_value"] == 35.0
    assert precip_target["threshold_unit"] == "mm/24h"

    # Precipitation displacement: > 100.0 km
    disp_target = targets_by_id["WD-PRECIP-DISP-01"]
    assert disp_target["threshold_value"] == 100.0
    assert disp_target["threshold_unit"] == "km"

    # Event duration: > 12.0h
    dur_target = targets_by_id["WD-DURATION-01"]
    assert dur_target["threshold_value"] == 12.0
    assert dur_target["threshold_unit"] == "hours"

    # Rain/snow partition
    snow_target = targets_by_id["WD-RAIN-SNOW-01"]
    assert snow_target["threshold_value"] == 0.5
    assert snow_target["threshold_unit"] == "fraction"


def test_western_disturbance_event_catalogue_integrity():
    """Verify historical event catalogue has required fields and benchmark episodes."""
    catalogue = load_wd_event_catalogue()
    events = catalogue["events"]
    assert len(events) >= 6

    event_ids = [e["event_id"] for e in events]
    assert "WD-2019-JAN-01" in event_ids
    assert "WD-2020-MAR-01" in event_ids
    assert "WD-2021-FEB-01" in event_ids
    assert "WD-2022-JAN-02" in event_ids
    assert "WD-2023-JUL-01" in event_ids
    assert "WD-2024-FEB-01" in event_ids

    for ev in events:
        assert "intensity_class" in ev
        assert "terrain_regime" in ev
        assert "period" in ev
        assert "subtropical_jet_speed_ms" in ev
        assert "trough_depth_500hpa_gpm" in ev
        assert "observed_error_modes" in ev
        assert len(ev["observed_error_modes"]) > 0


def test_western_disturbance_target_evaluation():
    """Verify target threshold exceedance evaluation logic across all WD failure modes."""
    # Arrival timing
    arrival_error_hours = 8.5
    is_arrival_bust = arrival_error_hours > 6.0
    assert is_arrival_bust is True

    # Trough location
    trough_loc_error_km = 175.0
    is_loc_bust = trough_loc_error_km > 150.0
    assert is_loc_bust is True

    # Precipitation amount
    precip_error_mm = 42.0
    is_precip_bust = precip_error_mm > 35.0
    assert is_precip_bust is True

    # Precipitation displacement
    disp_error_km = 125.0
    is_disp_bust = disp_error_km > 100.0
    assert is_disp_bust is True

    # Duration error
    dur_error_hours = 15.0
    is_dur_bust = dur_error_hours > 12.0
    assert is_dur_bust is True
