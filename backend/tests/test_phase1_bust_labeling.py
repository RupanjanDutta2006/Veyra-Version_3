"""Unit and Integration Tests for Phase 1: Bust Definition & Labeling Hardening.

Verifies closure of gaps B2, B3, B4, B5, B6, B7:
- B2: Sensitivity quantiles (q90, q95, q97.5, q99)
- B3: Near-threshold ambiguity flag
- B4: Continuous normalized error & severity classes (low, moderate, severe)
- B5: Fractions Skill Score (FSS) & object-aware spatial displacement verification
- B6: Event grouping (cyclone/monsoon episodes never split across train/test)
- B7: label_version presence in PredictionResponse & agent output
"""

import numpy as np
import pandas as pd
import pytest

from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.data.training_dataset import HistoricalTrainingRow
from backend.app.ml.label_engine import (
    CURRENT_LABEL_VERSION,
    BustLabelEngine,
    assign_lead_bin,
    compute_mad,
)
from backend.app.ml.spatial_labels import (
    calculate_fss,
    calculate_object_spatial_metrics,
    compute_neighborhood_fractions_2d,
    evaluate_spatial_bust,
)
from backend.app.ml.splitting import (
    DatasetSplits,
    EventGroupedDataSplitter,
    EventLeakageError,
    TemporalDataSplitter,
    TemporalLeakageError,
)
from backend.app.safety.abstention import SafetyAssessment, TrustState
from backend.app.schemas.prediction import PredictionResponse, RiskLevel
from backend.app.services.base import ModelResult, WeatherResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_training_df():
    """Create a controlled training dataframe with known error distribution."""
    np.random.seed(42)
    n = 200
    rows = []
    for i in range(n):
        lead = (i % 5) * 24 + 24
        var = ["temperature_2m", "wind_speed_10m"][i % 2]
        # Exponential base errors with occasional high outliers
        err = float(np.random.exponential(scale=1.5))
        if i in [15, 45, 95, 145, 195]:
            err += 10.0  # Force extreme busts

        rows.append({
            "location": "delhi",
            "variable": var,
            "lead_hours": lead,
            "forecast_abs_error": err,
            "forecast_value": 25.0 + i * 0.1,
            "truth_value": 25.0 + i * 0.1 - err,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# B2 & B4: Sensitivity Quantiles and Severity Classes
# ---------------------------------------------------------------------------


def test_mad_computation():
    """Verify MAD calculation with normal scaling."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    mad = compute_mad(data)
    assert mad > 0.0
    # For a constant array, MAD should be 0.0
    assert compute_mad(np.array([5.0, 5.0, 5.0])) == 0.0


def test_sensitivity_quantiles_monotonicity(sample_training_df):
    """B2: Test that sensitivity quantiles (q90, q95, q97.5, q99) maintain monotonic bust rates."""
    engine = BustLabelEngine(
        primary_quantile=0.95,
        sensitivity_quantiles=[0.90, 0.95, 0.975, 0.99],
    )
    df_labeled = engine.fit_transform(sample_training_df)

    # Invariant: Higher quantile threshold implies fewer or equal positive busts
    count_q90 = df_labeled["bust_label_q9"].sum()
    count_q95 = df_labeled["bust_label_q95"].sum()
    count_q975 = df_labeled["bust_label_q975"].sum()
    count_q99 = df_labeled["bust_label_q99"].sum()

    assert count_q90 >= count_q95 >= count_q975 >= count_q99
    assert count_q95 == df_labeled["bust_label"].sum()


def test_severity_classification_and_normalized_error(sample_training_df):
    """B4: Test continuous normalized error and severity classification (low, moderate, severe)."""
    engine = BustLabelEngine(primary_quantile=0.95)
    df_labeled = engine.fit_transform(sample_training_df)

    assert "normalized_error" in df_labeled.columns
    assert "severity" in df_labeled.columns

    # Verify severity values
    valid_severities = {"low", "moderate", "severe"}
    assert set(df_labeled["severity"].unique()).issubset(valid_severities)

    # Low severity rows must have bust_label == 0
    low_rows = df_labeled[df_labeled["severity"] == "low"]
    assert (low_rows["bust_label"] == 0).all()

    # Moderate and severe rows must have bust_label == 1
    mod_sev_rows = df_labeled[df_labeled["severity"].isin(["moderate", "severe"])]
    assert (mod_sev_rows["bust_label"] == 1).all()


# ---------------------------------------------------------------------------
# B3: Ambiguity Flag for Near-Threshold Cases
# ---------------------------------------------------------------------------


def test_ambiguity_flag_identification(sample_training_df):
    """B3: Test ambiguity flag for errors close to the threshold."""
    engine = BustLabelEngine(primary_quantile=0.95)
    engine.fit(sample_training_df)

    # Single evaluation tests:
    # 1. Very low error -> not ambiguous, low severity
    res_low = engine.evaluate_single(absolute_error=0.1, variable="temperature_2m", location="delhi")
    assert res_low.is_bust == 0
    assert res_low.severity == "low"
    assert res_low.ambiguity_flag is False

    # 2. Error exactly at threshold -> ambiguous, moderate severity
    thresh = res_low.threshold_value
    res_at_thresh = engine.evaluate_single(absolute_error=thresh, variable="temperature_2m", location="delhi")
    assert res_at_thresh.is_bust == 1
    assert res_at_thresh.ambiguity_flag is True
    assert res_at_thresh.severity == "moderate"

    # 3. Extreme error -> not ambiguous (well beyond threshold), severe
    res_extreme = engine.evaluate_single(absolute_error=thresh * 3.0, variable="temperature_2m", location="delhi")
    assert res_extreme.is_bust == 1
    assert res_extreme.severity == "severe"


# ---------------------------------------------------------------------------
# B5: Spatial FSS & Object-Aware Displacement
# ---------------------------------------------------------------------------


def test_fss_perfect_and_zero_skill():
    """B5: Test FSS boundary values (1.0 for perfect match, 0.0 for disjoint)."""
    grid_size = 20
    # Identical fields -> FSS = 1.0
    field = np.zeros((grid_size, grid_size))
    field[5:10, 5:10] = 10.0
    assert calculate_fss(field, field, threshold=5.0, window_size=3) == 1.0

    # Completely disjoint fields with window_size=1 -> FSS = 0.0
    f_disjoint = np.zeros((grid_size, grid_size))
    f_disjoint[0:3, 0:3] = 10.0

    r_disjoint = np.zeros((grid_size, grid_size))
    r_disjoint[15:18, 15:18] = 10.0

    fss_disjoint = calculate_fss(f_disjoint, r_disjoint, threshold=5.0, window_size=1)
    assert fss_disjoint == 0.0


def test_fss_increases_with_window_size():
    """B5: As neighborhood window size increases, FSS should monotonically increase for displaced event."""
    grid_size = 25
    f = np.zeros((grid_size, grid_size))
    r = np.zeros((grid_size, grid_size))

    # Forecast shifted by 3 grid cells from reference
    f[10:15, 10:15] = 20.0
    r[10:15, 13:18] = 20.0

    fss_w1 = calculate_fss(f, r, threshold=10.0, window_size=1)
    fss_w5 = calculate_fss(f, r, threshold=10.0, window_size=5)
    fss_w9 = calculate_fss(f, r, threshold=10.0, window_size=9)

    assert fss_w1 <= fss_w5 <= fss_w9


def test_spatial_bust_displacement_mitigation():
    """B5: Verify that small spatial displacement is mitigated and not classified as a total bust (§8.2)."""
    grid_size = 30
    f = np.zeros((grid_size, grid_size))
    r = np.zeros((grid_size, grid_size))

    # Event shifted by 2 grid cells (~50 km at 25km spacing)
    f[12:16, 12:16] = 25.0
    r[12:16, 14:18] = 25.0

    # fss_target=0.80 ensures raw FSS (~0.64) is below target (raw bust = 1),
    # but small displacement (50km <= 60km) triggers mitigation!
    res = evaluate_spatial_bust(
        f, r, threshold=15.0, window_size=3, grid_spacing_km=25.0, fss_target=0.80, displacement_tolerance_km=60.0
    )

    # Should be mitigated because displacement (50 km) <= tolerance (60 km)
    assert res.mean_centroid_displacement_km <= 60.0
    assert res.displacement_mitigated is True
    assert res.is_spatial_bust == 0


# ---------------------------------------------------------------------------
# B6: Event Grouping in Data Splitting
# ---------------------------------------------------------------------------


def _create_event_row(issue_time: str, valid_time: str, event_id: str) -> HistoricalTrainingRow:
    return HistoricalTrainingRow(
        location="Bhubaneswar",
        latitude=20.2961,
        longitude=85.8245,
        region="east_coast_india",
        variable="wind_speed_10m",
        issue_time=issue_time,
        valid_time=valid_time,
        lead_hours=24,
        forecast_value=35.0,
        reference_value=32.0,
        unit="m/s",
        error=3.0,
        absolute_error=3.0,
        season="monsoon",
        month=5,
        bust_label=0,
        bust_threshold=5.0,
        metadata={"event_id": event_id},
    )


def test_event_grouped_data_splitter():
    """B6: Test that all leads of a cyclone episode remain strictly in ONE partition."""
    # 3 events: cyclone_fani (early), cyclone_amphan (mid), cyclone_yaas (late)
    rows = [
        # Event 1: Fani (May 2019)
        _create_event_row("2019-05-01T00:00:00Z", "2019-05-02T00:00:00Z", "cyclone_fani"),
        _create_event_row("2019-05-02T00:00:00Z", "2019-05-03T00:00:00Z", "cyclone_fani"),
        _create_event_row("2019-05-03T00:00:00Z", "2019-05-04T00:00:00Z", "cyclone_fani"),
        # Event 2: Amphan (May 2020)
        _create_event_row("2020-05-16T00:00:00Z", "2020-05-17T00:00:00Z", "cyclone_amphan"),
        _create_event_row("2020-05-17T00:00:00Z", "2020-05-18T00:00:00Z", "cyclone_amphan"),
        _create_event_row("2020-05-18T00:00:00Z", "2020-05-19T00:00:00Z", "cyclone_amphan"),
        # Event 3: Yaas (May 2021)
        _create_event_row("2021-05-24T00:00:00Z", "2021-05-25T00:00:00Z", "cyclone_yaas"),
        _create_event_row("2021-05-25T00:00:00Z", "2021-05-26T00:00:00Z", "cyclone_yaas"),
        _create_event_row("2021-05-26T00:00:00Z", "2021-05-27T00:00:00Z", "cyclone_yaas"),
    ]

    splitter = EventGroupedDataSplitter(train_ratio=0.34, val_ratio=0.33, test_ratio=0.33)
    splits = splitter.split(rows)

    train_events = {r.metadata["event_id"] for r in splits.train_rows}
    val_events = {r.metadata["event_id"] for r in splits.val_rows}
    test_events = {r.metadata["event_id"] for r in splits.test_rows}

    # Invariant 1: No event appears in more than one partition
    assert len(train_events.intersection(val_events)) == 0
    assert len(val_events.intersection(test_events)) == 0
    assert len(train_events.intersection(test_events)) == 0

    # Invariant 2: Temporal causality holds
    assert splits.train_time_range[1] <= splits.val_time_range[0]
    assert splits.val_time_range[1] <= splits.test_time_range[0]


def test_temporal_splitter_embargo():
    """B6: Test temporal embargo / purge period between partitions."""
    rows = [
        _create_event_row("2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z", "e1"),
        _create_event_row("2020-01-05T00:00:00Z", "2020-01-06T00:00:00Z", "e1"),
        # Spanning into val partition:
        _create_event_row("2020-01-08T00:00:00Z", "2020-01-09T00:00:00Z", "e2"),  # within 7-day embargo of Jan 5 (purged)
        _create_event_row("2020-01-20T00:00:00Z", "2020-01-21T00:00:00Z", "e3"),  # valid val row after embargo
        _create_event_row("2020-01-22T00:00:00Z", "2020-01-23T00:00:00Z", "e3"),  # valid val row
        # Spanning into test partition:
        _create_event_row("2020-01-25T00:00:00Z", "2020-01-26T00:00:00Z", "e4"),  # within 7-day embargo of Jan 22 (purged)
        _create_event_row("2020-02-15T00:00:00Z", "2020-02-16T00:00:00Z", "e5"),  # valid test row after embargo
    ]

    splitter = TemporalDataSplitter(train_ratio=0.30, val_ratio=0.35, test_ratio=0.35, embargo_days=7)
    splits = splitter.split(rows)

    assert splits.purged_rows_count > 0
    # Ensure temporal invariant
    assert splits.train_rows[-1].issue_time <= splits.val_rows[0].issue_time
    assert splits.val_rows[-1].issue_time <= splits.test_rows[0].issue_time


# ---------------------------------------------------------------------------
# B7: label_version in PredictionResponse and ForecastBustAgent
# ---------------------------------------------------------------------------


def test_prediction_response_schema_fields():
    """B7: Verify label_version and Phase 1 fields exist in PredictionResponse schema."""
    resp = PredictionResponse(
        location="Kolkata",
        bust_probability=0.72,
        risk_level=RiskLevel.HIGH,
        trust_state=TrustState.HIGH_CONFIDENCE,
        abstain=False,
    )
    # Check default label_version
    assert resp.label_version == CURRENT_LABEL_VERSION
    data = resp.model_dump()
    assert "label_version" in data
    assert "ambiguity_flag" in data
    assert "severity" in data
    assert "normalized_error" in data
    assert "spatial_fss" in data
    assert "sensitivity_labels" in data


def test_forecast_bust_agent_populates_phase1_fields():
    """B7: Verify ForecastBustAgent.build_response populates all Phase 1 fields."""
    agent = ForecastBustAgent()
    safety = SafetyAssessment(
        abstain=False,
        bust_probability=0.72,
        risk_level=RiskLevel.HIGH,
        trust_state=TrustState.HIGH_CONFIDENCE,
        reason_codes=["SUCCESS"],
    )
    model_res = ModelResult(
        is_ready=True,
        probability=0.72,
        model_version="builder2_v3",
        metadata={
            "normalized_error": 2.45,
            "severity": "severe",
            "ambiguity_flag": False,
        },
    )
    weather_res = WeatherResult(
        location="Kolkata",
        is_available=True,
        data_version="NOAA_GEFS_v12",
        metadata={"lead_hours": 48},
    )

    resp = agent.build_response(
        location="Kolkata",
        safety_assessment=safety,
        model_result=model_res,
        weather_result=weather_res,
    )

    assert resp.label_version == CURRENT_LABEL_VERSION
    assert resp.severity == "severe"
    assert resp.normalized_error == 2.45
    assert resp.ambiguity_flag is False
    assert resp.sensitivity_labels is not None
    assert "q90" in resp.sensitivity_labels
    assert "q95" in resp.sensitivity_labels
    assert "q975" in resp.sensitivity_labels
    assert "q99" in resp.sensitivity_labels

    assert "q90" in resp.sensitivity_labels
    assert "q95" in resp.sensitivity_labels
    assert "q975" in resp.sensitivity_labels
    assert "q99" in resp.sensitivity_labels
