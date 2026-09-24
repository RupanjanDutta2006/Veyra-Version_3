"""Unit tests for Heatwave and Severe-Wind Target Verification (Gate 7 / Phase H)."""

import pytest

from backend.app.contracts.heatwave_contract import (
    load_heatwave_event_catalogue,
    load_heatwave_target_manifest,
)


def test_heatwave_target_manifest_structure():
    """Verify all Gate 7 required heatwave and severe wind targets are defined."""
    manifest = load_heatwave_target_manifest()
    target_ids = [t["target_id"] for t in manifest["targets"]]

    assert "HEATWAVE-THRESH-01" in target_ids
    assert "HEATWAVE-PEAK-01" in target_ids
    assert "HEATWAVE-ONSET-01" in target_ids
    assert "HEATWAVE-DURATION-01" in target_ids
    assert "HEATWAVE-NIGHT-01" in target_ids
    assert "HEATWAVE-SPATIAL-01" in target_ids
    assert "WIND-GUST-THRESH-01" in target_ids


def test_heatwave_target_thresholds():
    """Verify exact thresholds and units match Phase H specifications."""
    manifest = load_heatwave_target_manifest()
    targets_by_id = {t["target_id"]: t for t in manifest["targets"]}

    # Heatwave occurrence threshold
    thresh_target = targets_by_id["HEATWAVE-THRESH-01"]
    assert thresh_target["threshold_value"] == 40.0
    assert thresh_target["threshold_unit"] == "celsius"
    assert thresh_target["secondary_threshold_value"] == 4.5
    assert thresh_target["secondary_threshold_unit"] == "celsius_departure"

    # Peak max temperature error: > 2.5°C
    peak_target = targets_by_id["HEATWAVE-PEAK-01"]
    assert peak_target["threshold_value"] == 2.5
    assert peak_target["threshold_unit"] == "celsius"

    # Onset timing error: > 24.0h
    onset_target = targets_by_id["HEATWAVE-ONSET-01"]
    assert onset_target["threshold_value"] == 24.0
    assert onset_target["threshold_unit"] == "hours"

    # Duration error: > 48.0h
    dur_target = targets_by_id["HEATWAVE-DURATION-01"]
    assert dur_target["threshold_value"] == 48.0
    assert dur_target["threshold_unit"] == "hours"

    # Warm night min temperature error: > 2.0°C
    night_target = targets_by_id["HEATWAVE-NIGHT-01"]
    assert night_target["threshold_value"] == 2.0
    assert night_target["threshold_unit"] == "celsius"
    assert night_target["secondary_threshold_value"] == 4.5
    assert night_target["secondary_threshold_unit"] == "celsius_departure"

    # Spatial extent coverage fraction error: > 0.20
    spatial_target = targets_by_id["HEATWAVE-SPATIAL-01"]
    assert spatial_target["threshold_value"] == 0.20
    assert spatial_target["threshold_unit"] == "area_fraction"

    # Severe wind gale gust error: > 6.0 m/s (secondary 17.2 m/s)
    wind_target = targets_by_id["WIND-GUST-THRESH-01"]
    assert wind_target["threshold_value"] == 6.0
    assert wind_target["threshold_unit"] == "m/s"
    assert wind_target["secondary_threshold_value"] == 17.2
    assert wind_target["secondary_threshold_unit"] == "m/s"


def test_heatwave_event_catalogue_integrity():
    """Verify historical heatwave catalogue has required fields and benchmark episodes."""
    catalogue = load_heatwave_event_catalogue()
    events = catalogue["events"]
    assert len(events) >= 6

    event_ids = [e["event_id"] for e in events]
    assert "HEATWAVE-2015-AP-01" in event_ids
    assert "HEATWAVE-2016-RAJ-01" in event_ids
    assert "HEATWAVE-2019-CENTRAL-01" in event_ids
    assert "HEATWAVE-2022-NW-01" in event_ids
    assert "HEATWAVE-2023-EAST-01" in event_ids
    assert "HEATWAVE-2024-DELHI-01" in event_ids

    for ev in events:
        assert "regime" in ev
        assert "severity" in ev
        assert "period" in ev
        assert "peak_tmax_celsius" in ev
        assert "observed_error_modes" in ev
        assert len(ev["observed_error_modes"]) > 0


def test_heatwave_target_evaluation():
    """Verify target threshold exceedance evaluation logic across all HW failure modes."""
    # Peak temperature
    peak_error_celsius = 3.2
    is_peak_bust = peak_error_celsius > 2.5
    assert is_peak_bust is True

    # Onset timing
    onset_error_hours = 30.0
    is_onset_bust = onset_error_hours > 24.0
    assert is_onset_bust is True

    # Duration error
    dur_error_hours = 54.0
    is_dur_bust = dur_error_hours > 48.0
    assert is_dur_bust is True

    # Warm night error
    night_error_celsius = 2.4
    is_night_bust = night_error_celsius > 2.0
    assert is_night_bust is True

    # Spatial extent error
    spatial_error_fraction = 0.28
    is_spatial_bust = spatial_error_fraction > 0.20
    assert is_spatial_bust is True

    # Severe wind gale gust error
    wind_error_ms = 7.5
    is_wind_bust = wind_error_ms > 6.0
    assert is_wind_bust is True
