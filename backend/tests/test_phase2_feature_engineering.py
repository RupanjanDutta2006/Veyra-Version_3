"""Unit & Integration Tests for Phase 2 Feature Engineering.

Verifies:
- D2: Cycle-revision trajectory features (multi-cycle Deltas, accel, sign flips, trend)
- D3: Monsoon and synoptic regime context features (blocking, jet, transition proximity, cyclonic flag)
- D4: Historical analog similarity features (distance, hit rate, bust frequency, event exclusion)
- D5: Static and contextual features (regions, model version, grid, elevation)
- D6: Quality and safety signals (staleness, missing members, composite quality score)
- D7: availability_time <= issue_time hard enforcement
- D8: Forbidden ground-truth leakage guard
"""

from datetime import datetime, timezone
import pytest
import numpy as np

from backend.app.data.training_dataset import HistoricalTrainingRow
from backend.app.ml.feature_contract import (
    DataLeakageError,
    FORBIDDEN_GROUND_TRUTH_FIELDS,
    assert_no_leakage,
    validate_feature_vector,
    validate_issue_time_safety,
)
from backend.app.ml.features import (
    FeaturePipeline,
    InferenceSafeFeatureExtractor,
    classify_india_region,
    compute_quality_signals,
    compute_revision_trajectory_features,
)
from backend.app.ml.regime_features import (
    MonsoonPhase,
    compute_blocking_index,
    compute_cyclonic_regime_flag,
    compute_jet_state,
    compute_regime_transition_proximity,
    compute_rossby_wave_index,
    determine_monsoon_phase,
    extract_regime_features,
)
from backend.app.schemas.weather import CanonicalForecastRecord
from backend.app.services.analog_service import (
    HistoricalAnalogCase,
    HistoricalAnalogService,
)


# ---------------------------------------------------------------------------
# D2: Cycle-Revision Trajectory Features
# ---------------------------------------------------------------------------

def test_revision_trajectory_single_cycle_fallback():
    """Verify that when no prior cycles exist, revision features default cleanly to 0.0."""
    revs = compute_revision_trajectory_features(
        target_val=25.0,
        target_std=1.5,
        target_valid_time="2026-08-25T12:00:00Z",
        target_issue_time="2026-08-24T00:00:00Z",
        prior_records=None,
    )
    assert revs["forecast_delta_6h"] == 0.0
    assert revs["forecast_delta_24h"] == 0.0
    assert revs["forecast_revision_mag_6h"] == 0.0
    assert revs["revision_accel_6h"] == 0.0
    assert revs["revision_sign_flips"] == 0.0
    assert revs["has_revision_history"] == 0.0


def test_revision_trajectory_multi_cycle_calculation():
    """Verify cycle-to-cycle revision features for identical valid target time."""
    target_valid = "2026-08-25T12:00:00Z"
    target_issue = "2026-08-24T12:00:00Z"  # Latest issue cycle (lead 24h)

    # Earlier issue cycles for the exact same valid target:
    # 6 hours prior: issue 2026-08-24T06:00:00Z (lead 30h), mean was 23.0
    # 12 hours prior: issue 2026-08-24T00:00:00Z (lead 36h), mean was 21.0
    # 24 hours prior: issue 2026-08-23T12:00:00Z (lead 48h), mean was 20.0
    priors = [
        {
            "valid_time": target_valid,
            "issue_time": "2026-08-24T06:00:00Z",
            "forecast_value": 23.0,
            "ensemble_std": 1.2,
        },
        {
            "valid_time": target_valid,
            "issue_time": "2026-08-24T00:00:00Z",
            "forecast_value": 21.0,
            "ensemble_std": 1.4,
        },
        {
            "valid_time": target_valid,
            "issue_time": "2026-08-23T12:00:00Z",
            "forecast_value": 20.0,
            "ensemble_std": 1.8,
        },
    ]

    revs = compute_revision_trajectory_features(
        target_val=25.0,
        target_std=1.0,
        target_valid_time=target_valid,
        target_issue_time=target_issue,
        prior_records=priors,
    )

    assert revs["has_revision_history"] == 1.0
    # Delta 6h: 25.0 - 23.0 = +2.0
    assert revs["forecast_delta_6h"] == 2.0
    assert revs["forecast_revision_mag_6h"] == 2.0
    # Delta 24h: 25.0 - 20.0 = +5.0
    assert revs["forecast_delta_24h"] == 5.0
    # Spread delta 6h: 1.0 - 1.2 = -0.2
    assert revs["ensemble_spread_delta_6h"] == -0.2
    # Revision acceleration: (25.0 - 23.0) - (23.0 - 21.0) = 2.0 - 2.0 = 0.0
    assert revs["revision_accel_6h"] == 0.0
    # Trend should be positive (20 -> 21 -> 23 -> 25)
    assert revs["revision_trend"] > 0.0


# ---------------------------------------------------------------------------
# D3: Monsoon & Regime Context Features
# ---------------------------------------------------------------------------

def test_determine_monsoon_phase():
    """Verify seasonal monsoon phase classification."""
    # Winter (Jan 15)
    dt_winter = datetime(2026, 1, 15, tzinfo=timezone.utc)
    assert determine_monsoon_phase(dt_winter) == MonsoonPhase.NON_MONSOON_WINTER

    # Pre-monsoon summer (April 10)
    dt_summer = datetime(2026, 4, 10, tzinfo=timezone.utc)
    assert determine_monsoon_phase(dt_summer) == MonsoonPhase.PRE_MONSOON_SUMMER

    # Onset (June 5)
    dt_onset = datetime(2026, 6, 5, tzinfo=timezone.utc)
    assert determine_monsoon_phase(dt_onset) == MonsoonPhase.MONSOON_ONSET

    # Active Monsoon (July 20)
    dt_active = datetime(2026, 7, 20, tzinfo=timezone.utc)
    assert determine_monsoon_phase(dt_active, surface_pressure_hpa=1002.0) == MonsoonPhase.MONSOON_ACTIVE

    # Monsoon Break (July 20 with anomalous high pressure and low wind)
    assert determine_monsoon_phase(
        dt_active, surface_pressure_hpa=1013.0, wind_speed_ms=1.5, latitude=22.0
    ) == MonsoonPhase.MONSOON_BREAK

    # Retreat (October 15)
    dt_retreat = datetime(2026, 10, 15, tzinfo=timezone.utc)
    assert determine_monsoon_phase(dt_retreat) == MonsoonPhase.MONSOON_RETREAT


def test_compute_blocking_index():
    """Verify anticyclonic blocking index detects persistent high pressure stagnation."""
    # Normal / low pressure -> 0.0 blocking
    assert compute_blocking_index(surface_pressure_hpa=1005.0) == 0.0

    # Elevated surface pressure + wind stagnation -> high blocking index
    b_high = compute_blocking_index(surface_pressure_hpa=1025.0, wind_speed_ms=1.5)
    assert b_high > 0.8
    assert b_high <= 1.0


def test_compute_cyclonic_regime_flag():
    """Verify cyclonic disturbance detection under deep depression."""
    # Normal atmospheric state -> 0.0
    assert compute_cyclonic_regime_flag(surface_pressure_hpa=1012.0, wind_speed_ms=4.0) == 0.0

    # Deep cyclonic depression: P < 1004 hPa and wind > 8 m/s -> 1.0
    assert compute_cyclonic_regime_flag(surface_pressure_hpa=994.0, wind_speed_ms=18.0) == 1.0


def test_regime_transition_proximity():
    """Verify proximity function peaks at boundary dates and decays mid-season."""
    # Exactly on pre-monsoon boundary (March 1) -> proximity = 1.0
    dt_bound = datetime(2026, 3, 1, tzinfo=timezone.utc)
    assert compute_regime_transition_proximity(dt_bound) == 1.0

    # 10 days away -> proximity exp(-1) ≈ 0.3679
    dt_10d = datetime(2026, 3, 11, tzinfo=timezone.utc)
    prox_10d = compute_regime_transition_proximity(dt_10d)
    assert 0.30 <= prox_10d <= 0.40


def test_extract_regime_features_dictionary():
    """Verify complete regime feature dictionary output."""
    dt = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    feats = extract_regime_features(
        valid_dt=dt,
        surface_pressure_hpa=1000.0,
        wind_speed_ms=6.5,
        latitude=22.57,
        longitude=88.36,
    )
    assert "monsoon_phase_code" in feats
    assert "blocking_index" in feats
    assert "rossby_wave_index" in feats
    assert "jet_state" in feats
    assert "regime_transition_proximity" in feats
    assert "cyclonic_regime_flag" in feats
    assert feats["is_monsoon_active"] == 1.0


# ---------------------------------------------------------------------------
# D4: Historical Analog Service
# ---------------------------------------------------------------------------

def test_analog_service_finds_similar_cases():
    """Verify historical analog retrieval returns valid cards and metrics."""
    service = HistoricalAnalogService()
    # Query case: Kolkata pre-monsoon heatwave scenario (42°C, moderate spread)
    result = service.find_analogs(
        query_time="2026-05-15T00:00:00Z",
        variable="temperature_2m",
        lead_hours=48,
        forecast_value=43.0,
        ensemble_std=1.1,
        location="Delhi",
        top_k=2,
    )

    assert result.status == "SUCCESS"
    assert result.similarity_score > 0.5
    assert result.top_k_count == 2
    assert len(result.analog_cards) == 2
    assert result.bust_frequency is not None
    assert 0.0 <= result.bust_frequency <= 1.0


def test_analog_service_strict_event_exclusion():
    """Verify that cases within ±14 days of the query are strictly excluded to prevent same-event leakage."""
    archive = [
        HistoricalAnalogCase(
            case_id="SAME-EVENT",
            timestamp="2026-05-10T00:00:00Z",  # 5 days prior (inside 14-day exclusion window!)
            location="Delhi",
            variable="temperature_2m",
            lead_hours=48,
            forecast_value=40.0,
            ensemble_mean=40.0,
            ensemble_std=1.0,
            regime="HEATWAVE",
            bust_label=1,
            description="Same event",
            lessons_learned="Excluded",
        ),
        HistoricalAnalogCase(
            case_id="VALID-PRIOR-YEAR",
            timestamp="2025-05-10T00:00:00Z",  # 1 year prior (valid!)
            location="Delhi",
            variable="temperature_2m",
            lead_hours=48,
            forecast_value=40.0,
            ensemble_mean=40.0,
            ensemble_std=1.0,
            regime="HEATWAVE",
            bust_label=0,
            description="Prior year",
            lessons_learned="Valid",
        ),
    ]

    service = HistoricalAnalogService(archive=archive, event_exclusion_days=14)
    result = service.find_analogs(
        query_time="2026-05-15T00:00:00Z",
        variable="temperature_2m",
        lead_hours=48,
        forecast_value=40.0,
        ensemble_std=1.0,
        location="Delhi",
    )

    assert result.status == "SUCCESS"
    card_ids = [c.case_id for c in result.analog_cards]
    assert "SAME-EVENT" not in card_ids
    assert "VALID-PRIOR-YEAR" in card_ids


def test_analog_service_strict_temporal_direction():
    """Verify that future cases (t_case >= t_query) can NEVER be returned as analogs."""
    archive = [
        HistoricalAnalogCase(
            case_id="FUTURE-CASE",
            timestamp="2026-08-01T00:00:00Z",  # Future relative to query
            location="Delhi",
            variable="temperature_2m",
            lead_hours=24,
            forecast_value=30.0,
            ensemble_mean=30.0,
            ensemble_std=1.0,
            regime="NORMAL",
            bust_label=1,
            description="Future",
            lessons_learned="Future",
        ),
    ]
    service = HistoricalAnalogService(archive=archive)
    result = service.find_analogs(
        query_time="2026-06-01T00:00:00Z",
        variable="temperature_2m",
        lead_hours=24,
        forecast_value=30.0,
        ensemble_std=1.0,
    )
    assert result.status == "NO_ELIGIBLE_ANALOG"
    assert len(result.analog_cards) == 0


def test_analog_service_no_eligible_analog_graceful_handling():
    """Verify that when no eligible analog exists, service returns NO_ELIGIBLE_ANALOG without error (§21)."""
    service = HistoricalAnalogService(archive=[])
    result = service.find_analogs(
        query_time="2026-06-01T00:00:00Z",
        variable="temperature_2m",
        lead_hours=24,
        forecast_value=30.0,
        ensemble_std=1.0,
    )
    assert result.status == "NO_ELIGIBLE_ANALOG"
    assert result.similarity_score == 0.0
    assert result.bust_frequency is None
    assert result.analog_cards == []


# ---------------------------------------------------------------------------
# D5: Static & Contextual Regional Features
# ---------------------------------------------------------------------------

def test_classify_india_region():
    """Verify geographic regional encoding for Indian benchmark stations."""
    # Delhi: North India
    delhi = classify_india_region(lat=28.6139, lon=77.2090, location="Delhi")
    assert delhi["is_region_north"] == 1.0
    assert delhi["is_coastal"] == 0.0
    assert delhi["elevation_m"] == 216.0

    # Mumbai: West India + Coastal
    mumbai = classify_india_region(lat=19.0760, lon=72.8777, location="Mumbai")
    assert mumbai["is_region_west"] == 1.0
    assert mumbai["is_coastal"] == 1.0
    assert mumbai["elevation_m"] == 10.0

    # Kolkata: East India + Coastal
    kolkata = classify_india_region(lat=22.5726, lon=88.3639, location="Kolkata")
    assert kolkata["is_region_east"] == 1.0
    assert kolkata["is_coastal"] == 1.0

    # Bengaluru: South India, elevated
    bengaluru = classify_india_region(lat=12.9716, lon=77.5946, location="Bengaluru")
    assert bengaluru["is_region_south"] == 1.0
    assert bengaluru["elevation_m"] == 920.0


# ---------------------------------------------------------------------------
# D6: Quality & Safety Signals
# ---------------------------------------------------------------------------

def test_compute_quality_signals():
    """Verify staleness, missing members, and composite quality score."""
    issue_time = "2026-08-20T00:00:00Z"
    now_time = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)  # 12h later

    # Full ensemble, fresh
    q_full = compute_quality_signals(
        issue_time=issue_time,
        availability_time=issue_time,
        member_count=31,
        has_gaps=False,
        current_time=now_time,
    )
    assert q_full["data_staleness_hours"] == 12.0
    assert q_full["missing_member_ratio"] == 0.0
    assert q_full["has_missing_steps"] == 0.0
    assert q_full["composite_quality_score"] > 0.9

    # Depleted ensemble (only 15 members out of 31) + gaps
    q_depleted = compute_quality_signals(
        issue_time=issue_time,
        availability_time=issue_time,
        member_count=15,
        has_gaps=True,
        current_time=now_time,
    )
    assert q_depleted["missing_member_ratio"] > 0.5
    assert q_depleted["has_missing_steps"] == 1.0
    assert q_depleted["composite_quality_score"] < q_full["composite_quality_score"]


# ---------------------------------------------------------------------------
# D7 & D8: availability_time <= issue_time & Leakage Guards
# ---------------------------------------------------------------------------

def test_validate_issue_time_safety_enforcement():
    """Verify that availability_time > issue_time raises DataLeakageError (§9, D7)."""
    issue_time = "2026-08-20T00:00:00Z"
    valid_avail = "2026-08-20T00:00:00Z"
    invalid_avail = "2026-08-20T04:00:00Z"  # 4 hours after issue time!

    assert validate_issue_time_safety(issue_time, valid_avail) is True

    with pytest.raises(DataLeakageError) as exc_info:
        validate_issue_time_safety(issue_time, invalid_avail)
    assert "Temporal leakage detected" in str(exc_info.value)
    assert "availability_time <= issue_time violated" in str(exc_info.value)


def test_extractor_enforces_availability_time_safety():
    """Verify InferenceSafeFeatureExtractor rejects future availability timestamps."""
    extractor = InferenceSafeFeatureExtractor()
    bad_record = {
        "issue_time": "2026-08-20T00:00:00Z",
        "availability_time": "2026-08-20T01:00:00Z",  # 1h in future
        "valid_time": "2026-08-21T00:00:00Z",
        "lead_hours": 24,
        "forecast_value": 25.0,
        "latitude": 28.6,
        "longitude": 77.2,
    }

    with pytest.raises(DataLeakageError):
        extractor.extract_raw_features(bad_record)


def test_forbidden_ground_truth_leakage_rejection():
    """Verify that forbidden ground truth fields raise DataLeakageError (§9, D8)."""
    for forbidden in FORBIDDEN_GROUND_TRUTH_FIELDS:
        bad_dict = {
            "forecast_value": 25.0,
            "lead_hours": 24,
            forbidden: 22.0,  # Leaked ground truth
        }
        with pytest.raises(DataLeakageError):
            assert_no_leakage(bad_dict)


# ---------------------------------------------------------------------------
# Enriched Feature Pipeline End-to-End
# ---------------------------------------------------------------------------

def test_enriched_feature_pipeline_fit_and_transform():
    """Verify FeaturePipeline(enriched=True) extracts and normalizes all Phase 2 features."""
    train_rows = [
        HistoricalTrainingRow(
            location="Delhi",
            latitude=28.6,
            longitude=77.2,
            region="northern_india",
            variable="temperature_2m",
            issue_time="2026-05-01T00:00:00Z",
            valid_time="2026-05-02T00:00:00Z",
            lead_hours=24,
            forecast_value=38.0,
            reference_value=37.5,
            unit="celsius",
            error=0.5,
            absolute_error=0.5,
            season="summer",
            month=5,
            bust_label=0,
            bust_threshold=3.0,
            forecast_source="NOAA_GEFS",
            reference_source="ERA5",
        ),
        HistoricalTrainingRow(
            location="Kolkata",
            latitude=22.5,
            longitude=88.3,
            region="eastern_india",
            variable="temperature_2m",
            issue_time="2026-05-01T00:00:00Z",
            valid_time="2026-05-02T00:00:00Z",
            lead_hours=24,
            forecast_value=42.0,
            reference_value=35.0,
            unit="celsius",
            error=7.0,
            absolute_error=7.0,
            season="summer",
            month=5,
            bust_label=1,
            bust_threshold=3.0,
            forecast_source="NOAA_GEFS",
            reference_source="ERA5",
        ),
    ]

    pipeline = FeaturePipeline(enriched=True).fit(train_rows)
    assert pipeline.is_fitted is True

    names = pipeline.get_feature_names()
    # Check that Phase 2 features are present
    assert "blocking_index" in names
    assert "rossby_wave_index" in names
    assert "jet_state" in names
    assert "regime_transition_proximity" in names
    assert "cyclonic_regime_flag" in names
    assert "analog_similarity_score" in names
    assert "is_region_north" in names
    assert "is_coastal" in names
    assert "composite_quality_score" in names
    assert "data_staleness_hours" in names

    X, y = pipeline.transform(train_rows)
    assert X.shape == (2, len(names))
    assert not np.isnan(X).any()
    assert not np.isinf(X).any()
    assert list(y) == [0, 1]
