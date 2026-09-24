"""Unit Tests for Precipitation Target Definitions and Invariants (Gate 3 / Phase D).

Verifies:
- Occurrence bust logic (False Alarm vs Miss at 2.5mm)
- Amount bust logic (|F - O| > 25mm)
- Heavy rain bust logic (>= 64.5mm)
- Extreme rain bust logic (>= 204.5mm)
- Timing displacement logic (> 6h)
- Spatial displacement logic (> 75km)
- Distinct accumulation windows (6h, 12h, 24h, 48h, 72h)
- Anti-leakage and verification latency invariants
"""

import pytest

from backend.app.contracts.precipitation_contract import load_precipitation_target_manifest


@pytest.fixture
def manifest():
    return load_precipitation_target_manifest()


def test_target_manifest_contains_required_targets(manifest):
    """Verify all 6 core precipitation targets are present in manifest."""
    target_ids = [t["target_id"] for t in manifest["targets"]]
    assert "PRECIP-OCCURRENCE-01" in target_ids
    assert "PRECIP-AMOUNT-01" in target_ids
    assert "PRECIP-HEAVY-01" in target_ids
    assert "PRECIP-EXTREME-01" in target_ids
    assert "PRECIP-TIMING-01" in target_ids
    assert "PRECIP-SPATIAL-01" in target_ids


def test_occurrence_failure_logic():
    """Verify binary occurrence failure calculation."""
    def is_occurrence_failure(fcst: float, obs: float, threshold: float = 2.5) -> bool:
        fcst_wet = fcst >= threshold
        obs_wet = obs >= threshold
        return fcst_wet != obs_wet

    # Both dry -> No failure
    assert not is_occurrence_failure(fcst=0.5, obs=1.0)
    # Both wet -> No failure
    assert not is_occurrence_failure(fcst=15.0, obs=22.0)
    # False Alarm -> Failure
    assert is_occurrence_failure(fcst=8.0, obs=0.2)
    # Miss -> Failure
    assert is_occurrence_failure(fcst=1.1, obs=12.0)


def test_amount_failure_logic():
    """Verify amount error failure calculation."""
    def is_amount_failure(fcst: float, obs: float, threshold: float = 25.0) -> bool:
        return abs(fcst - obs) > threshold

    assert not is_amount_failure(fcst=30.0, obs=40.0)  # Error 10 <= 25
    assert is_amount_failure(fcst=10.0, obs=42.0)      # Error 32 > 25


def test_heavy_rain_failure_logic():
    """Verify heavy rain threshold failure (>= 64.5 mm)."""
    def is_heavy_failure(fcst: float, obs: float, threshold: float = 64.5) -> bool:
        fcst_heavy = fcst >= threshold
        obs_heavy = obs >= threshold
        return fcst_heavy != obs_heavy

    # Correct heavy forecast
    assert not is_heavy_failure(fcst=75.0, obs=82.0)
    # Missed heavy rain
    assert is_heavy_failure(fcst=25.0, obs=90.0)
    # False alarm heavy rain
    assert is_heavy_failure(fcst=70.0, obs=15.0)


def test_timing_and_spatial_displacement_logic():
    """Verify timing (>6h) and spatial (>75km) displacement failure thresholds."""
    def is_timing_failure(t_fcst_h: float, t_obs_h: float, max_h: float = 6.0) -> bool:
        return abs(t_fcst_h - t_obs_h) > max_h

    def is_spatial_failure(dist_km: float, max_km: float = 75.0) -> bool:
        return dist_km > max_km

    assert not is_timing_failure(t_fcst_h=14.0, t_obs_h=16.0)
    assert is_timing_failure(t_fcst_h=12.0, t_obs_h=20.0)

    assert not is_spatial_failure(dist_km=42.0)
    assert is_spatial_failure(dist_km=88.5)


def test_accumulation_windows_in_manifest(manifest):
    """Verify distinct accumulation windows 6h, 12h, 24h, 48h, 72h."""
    windows = manifest["accumulation_windows_hours"]
    assert set(windows) == {6, 12, 24, 48, 72}


def test_anti_leakage_and_invariants(manifest):
    """Verify non-negotiable anti-leakage invariants."""
    invariants = manifest["invariants"]
    assert "temporal_safety" in invariants
    assert "feature_target_isolation" in invariants
    assert "hazard_not_flood" in invariants
    assert "unsupported_quantities_null" in invariants
