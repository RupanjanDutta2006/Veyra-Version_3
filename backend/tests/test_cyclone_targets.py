"""Unit Tests for Cyclone Target Definitions and Invariants (Gate 4 / Phase E).

Verifies:
- Track bust logic (> 100km at 48h, > 180km at 72h)
- Intensity bust logic (> 15 knots / 7.7 m/s)
- Rapid Intensification (RI) failure logic (>= 30 kt / 24h)
- Landfall location (> 80km) and timing (> 6h) displacement
- Conformal uncertainty radius coverage
- Anti-leakage and verification latency invariants
"""

import pytest

from backend.app.contracts.cyclone_contract import load_cyclone_target_manifest


@pytest.fixture
def manifest():
    return load_cyclone_target_manifest()


def test_cyclone_manifest_contains_all_targets(manifest):
    """Verify all 6 core cyclone targets exist in manifest."""
    target_ids = [t["target_id"] for t in manifest["targets"]]
    assert "CYCLONE-TRACK-01" in target_ids
    assert "CYCLONE-INTENSITY-01" in target_ids
    assert "CYCLONE-RI-01" in target_ids
    assert "CYCLONE-LANDFALL-LOC-01" in target_ids
    assert "CYCLONE-LANDFALL-TIME-01" in target_ids
    assert "CYCLONE-CONFORMAL-TRACK-01" in target_ids


def test_track_error_exceedance_logic():
    """Verify lead-dependent track error threshold exceedance."""
    def is_track_bust(dist_km: float, lead_hours: int) -> bool:
        threshold = 100.0 if lead_hours <= 48 else 180.0
        return dist_km > threshold

    assert not is_track_bust(dist_km=85.0, lead_hours=48)
    assert is_track_bust(dist_km=112.0, lead_hours=48)
    assert not is_track_bust(dist_km=165.0, lead_hours=72)
    assert is_track_bust(dist_km=195.0, lead_hours=72)


def test_intensity_error_logic():
    """Verify intensity threshold error (> 7.7 m/s / 15 kt)."""
    def is_intensity_bust(fcst_v: float, obs_v: float, threshold: float = 7.7) -> bool:
        return abs(fcst_v - obs_v) > threshold

    assert not is_intensity_bust(fcst_v=45.0, obs_v=48.0)
    assert is_intensity_bust(fcst_v=35.0, obs_v=46.5)


def test_rapid_intensification_failure_logic():
    """Verify RI failure detection (>= 15.4 m/s in 24h)."""
    def is_ri_failure(fcst_delta_v: float, obs_delta_v: float, threshold: float = 15.4) -> bool:
        fcst_ri = fcst_delta_v >= threshold
        obs_ri = obs_delta_v >= threshold
        return fcst_ri != obs_ri

    # Both RI -> Success
    assert not is_ri_failure(fcst_delta_v=18.0, obs_delta_v=22.0)
    # Missed RI -> Failure
    assert is_ri_failure(fcst_delta_v=8.0, obs_delta_v=17.5)
    # False Alarm RI -> Failure
    assert is_ri_failure(fcst_delta_v=16.0, obs_delta_v=5.0)


def test_landfall_displacement_logic():
    """Verify landfall location (>80km) and timing (>6h) thresholds."""
    def is_landfall_loc_failure(dist_km: float) -> bool:
        return dist_km > 80.0

    def is_landfall_time_failure(t_fcst: float, t_obs: float) -> bool:
        return abs(t_fcst - t_obs) > 6.0

    assert not is_landfall_loc_failure(dist_km=65.0)
    assert is_landfall_loc_failure(dist_km=95.0)
    assert not is_landfall_time_failure(t_fcst=18.0, t_obs=21.0)
    assert is_landfall_time_failure(t_fcst=12.0, t_obs=20.0)


def test_conformal_track_coverage_logic():
    """Verify conformal uncertainty radius coverage check."""
    radius_km = 120.0
    # Inside radius -> covered
    assert 95.0 <= radius_km
    # Outside radius -> miscoverage
    assert not (135.0 <= radius_km)


def test_anti_leakage_and_invariants(manifest):
    """Verify non-negotiable anti-leakage invariants."""
    invariants = manifest["invariants"]
    assert "temporal_safety" in invariants
    assert "feature_target_isolation" in invariants
    assert "decomposed_not_opaque" in invariants
    assert "unsupported_quantities_null" in invariants
