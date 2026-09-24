"""Unit tests for Common-Mode Failure Detection and Ablation (Gate 8 / Phase I)."""

import pytest
from backend.app.contracts.spatial_contract import CommonModeIndicatorType
from backend.app.builder2.common_mode_detector import CommonModeFailureDetector


@pytest.fixture
def common_mode_detector():
    return CommonModeFailureDetector(min_coherent_stations=5, cmsi_threshold=0.40)


def test_common_mode_detection_positive(common_mode_detector):
    """Verify common-mode alert triggers when >= 5 stations concurrently fail."""
    # 7 stations with high bust probability
    probs = {f"STN_{i}": 0.15 for i in range(25)}
    for s in ["STN_0", "STN_1", "STN_2", "STN_3", "STN_4", "STN_5", "STN_6"]:
        probs[s] = 0.75

    out = common_mode_detector.detect_common_mode(probs, variable="temperature_2m")
    assert out.common_mode_detected is True
    assert out.severity_index >= 0.40
    assert len(out.participating_stations) == 7
    assert out.indicator_type == CommonModeIndicatorType.HEAT_DOME_BIAS


def test_common_mode_detection_negative_isolated(common_mode_detector):
    """Verify common-mode alert does NOT trigger for isolated single-station failure."""
    # Only 2 stations failing
    probs = {f"STN_{i}": 0.15 for i in range(25)}
    probs["STN_0"] = 0.85
    probs["STN_1"] = 0.80

    out = common_mode_detector.detect_common_mode(probs, variable="precipitation")
    assert out.common_mode_detected is False
    assert out.severity_index < 0.40
    assert len(out.participating_stations) == 2
    assert out.indicator_type is None


def test_common_mode_indicator_types(common_mode_detector):
    """Verify correct indicator type assignment for convective vs synoptic precipitation."""
    probs = {f"STN_{i}": 0.70 for i in range(8)}
    for i in range(8, 25):
        probs[f"STN_{i}"] = 0.15

    # Synoptic flow > 15 m/s -> SYNOPTIC_PHASE_LOCK
    out_synoptic = common_mode_detector.detect_common_mode(
        probs, variable="precipitation", synoptic_flow_speed_ms=18.0
    )
    assert out_synoptic.indicator_type == CommonModeIndicatorType.SYNOPTIC_PHASE_LOCK

    # Synoptic flow <= 15 m/s -> CONVECTIVE_BREAKDOWN
    out_convective = common_mode_detector.detect_common_mode(
        probs, variable="precipitation", synoptic_flow_speed_ms=8.0
    )
    assert out_convective.indicator_type == CommonModeIndicatorType.CONVECTIVE_BREAKDOWN


def test_common_mode_ablation_comparison(common_mode_detector):
    """Verify ablation analysis demonstrates positive sensitivity delta."""
    probs = {f"STN_{i}": 0.15 for i in range(25)}
    for i in range(6):
        probs[f"STN_{i}"] = 0.70

    res = common_mode_detector.run_ablation_comparison(probs, variable="precipitation")
    assert res["baseline_common_mode_detected"] is True
    assert res["ablated_common_mode_detected"] is False
    assert res["cmsi_sensitivity_delta"] > 0.0
    assert res["participating_stations_count"] == 6
