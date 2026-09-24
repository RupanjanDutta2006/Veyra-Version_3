"""Automated CI-Runnable Leakage Integration Tests.

Verifies the official SIH26079 Splitting & Leakage Protocol (§8.3, §10.4):
- Test 1: Future truth removal invariance (altering future ground truth does NOT change issue-time predictions).
- Test 2: Feature availability time causality (availability_time <= issue_time).
- Test 3: Strict forbidden ground truth fields enforcement (no ERA5/actual observations in feature columns).
- Test 4: Temporal causality monotonicity across train/val/test splits.
- Test 5: Event-grouping isolation (no cyclone episode spans across train/val/test).
- Test 6: Geographic region holdout spatial isolation (zero spatial overlap between train and held-out test).
- Test 7: Model-version holdout isolation (zero model version overlap between train and test).
- Test 8: Purge/embargo window enforcement (records within embargo delta are purged).
"""
import copy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import pytest

from backend.app.data.training_dataset import HistoricalTrainingRow
from backend.app.ml.feature_contract import (
    FORBIDDEN_GROUND_TRUTH_FIELDS,
    FeatureContract,
    FeatureLeakageError,
)
from backend.app.ml.splitting import (
    DatasetSplits,
    EventGroupedDataSplitter,
    EventLeakageError,
    ModelVersionHoldoutSplitter,
    MultiDimensionalHoldoutSplitter,
    RegionHoldoutSplitter,
    TemporalDataSplitter,
    TemporalLeakageError,
)


def _make_dummy_training_row(
    idx: int,
    issue_time: str,
    valid_time: str,
    location: str = "Kolkata",
    event_id: str = None,
    model_version: str = "gfs_v1",
    forecast_value: float = 25.0,
    reference_value: float = 26.0,
) -> HistoricalTrainingRow:
    """Helper to instantiate HistoricalTrainingRow with specified parameters."""
    error = abs(reference_value - forecast_value)
    bust_label = 1 if error > 2.5 else 0
    row = HistoricalTrainingRow(
        location=location,
        latitude=22.57,
        longitude=88.36,
        region="IN_EAST",
        variable="temperature_2m",
        issue_time=issue_time,
        valid_time=valid_time,
        lead_hours=24,
        forecast_value=forecast_value,
        reference_value=reference_value,
        unit="degC",
        error=error,
        absolute_error=error,
        season="monsoon",
        month=8,
        bust_label=bust_label,
        bust_threshold=2.5,
        metadata={"event_id": event_id, "model_version": model_version} if (event_id or model_version) else {},
    )
    row.model_version = model_version
    row.event_id = event_id or ""
    return row


# =========================================================================
# 1. FUTURE TRUTH REMOVAL INVARIANCE
# =========================================================================

def test_future_truth_removal_invariance():
    """TEST 1: Altering or removing future ground truth does NOT change issue-time prediction features."""
    contract = FeatureContract()

    # Original features with valid availability_time <= issue_time
    raw_features = {
        "ensemble_mean": 298.15,
        "ensemble_std": 1.45,
        "surface_pressure": 101325.0,
        "availability_time": "2026-08-27T00:00:00Z",
    }
    issue_time = "2026-08-27T00:00:00Z"

    validated_1 = contract.validate_features(
        raw_features,
        issue_time=issue_time,
        availability_time=raw_features["availability_time"],
    )

    # Simulate presence of future ground truth in data stream (which must be filtered out)
    dirty_features = copy.deepcopy(raw_features)
    dirty_features["era5_actual"] = 305.2  # Future truth
    dirty_features["actual_observation"] = 304.8  # Future truth

    # Cleaned validation must strip forbidden fields and produce identical feature values
    cleaned = contract.filter_forbidden_fields(dirty_features)
    assert "era5_actual" not in cleaned
    assert "actual_observation" not in cleaned

    validated_2 = contract.validate_features(
        cleaned,
        issue_time=issue_time,
        availability_time=cleaned["availability_time"],
    )

    assert validated_1 == validated_2


# =========================================================================
# 2. FEATURE AVAILABILITY TIME CAUSALITY
# =========================================================================

def test_feature_availability_time_causality():
    """TEST 2: Features with availability_time > issue_time trigger FeatureLeakageError."""
    contract = FeatureContract()

    valid_features = {"ensemble_mean": 298.15, "lead_hours": 24}
    # Availability 2 hours after issue_time -> LEAKAGE
    with pytest.raises(FeatureLeakageError, match="leakage detected"):
        contract.validate_features(
            valid_features,
            issue_time="2026-08-27T00:00:00Z",
            availability_time="2026-08-27T02:00:00Z",
        )

    # Availability exactly equal to issue_time -> SAFE
    safe_features = contract.validate_features(
        valid_features,
        issue_time="2026-08-27T00:00:00Z",
        availability_time="2026-08-27T00:00:00Z",
    )
    assert safe_features["ensemble_mean"] == 298.15


# =========================================================================
# 3. STRICT FORBIDDEN GROUND TRUTH FIELDS ENFORCEMENT
# =========================================================================

def test_strict_forbidden_ground_truth_fields():
    """TEST 3: None of FORBIDDEN_GROUND_TRUTH_FIELDS can pass feature contract validation."""
    contract = FeatureContract()

    for forbidden_col in FORBIDDEN_GROUND_TRUTH_FIELDS:
        features = {
            "ensemble_mean": 298.15,
            forbidden_col: 100.0,
        }
        with pytest.raises(FeatureLeakageError, match="[Ff]orbidden ground truth"):
            contract.validate_features(
                features,
                issue_time="2026-08-27T00:00:00Z",
                availability_time="2026-08-27T00:00:00Z",
            )


# =========================================================================
# 4. TEMPORAL CAUSALITY MONOTONICITY
# =========================================================================

def test_temporal_causality_monotonicity():
    """TEST 4: TemporalDataSplitter strictly enforces max(train) <= min(val) <= min(test)."""
    splitter = TemporalDataSplitter(train_ratio=0.60, val_ratio=0.20, test_ratio=0.20)

    rows = [
        _make_dummy_training_row(i, f"2026-08-{i:02d}T00:00:00Z", f"2026-08-{i+1:02d}T00:00:00Z")
        for i in range(1, 21)
    ]

    splits = splitter.split(rows)

    train_max = max(datetime.fromisoformat(r.issue_time.replace("Z", "+00:00")) for r in splits.train_rows)
    val_min = min(datetime.fromisoformat(r.issue_time.replace("Z", "+00:00")) for r in splits.val_rows)
    val_max = max(datetime.fromisoformat(r.issue_time.replace("Z", "+00:00")) for r in splits.val_rows)
    test_min = min(datetime.fromisoformat(r.issue_time.replace("Z", "+00:00")) for r in splits.test_rows)

    assert train_max <= val_min, f"Train max {train_max} > Val min {val_min}"
    assert val_max <= test_min, f"Val max {val_max} > Test min {test_min}"


# =========================================================================
# 5. EVENT-GROUPING ISOLATION
# =========================================================================

def test_event_grouping_isolation():
    """TEST 5: EventGroupedDataSplitter ensures no weather event spans across train/val/test."""
    splitter = EventGroupedDataSplitter(
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
        event_key="event_id",
        holdout_event_ids=["cyclone_amphan_2020"],
    )

    rows = []
    # 5 rows for cyclone_amphan
    for i in range(1, 6):
        rows.append(_make_dummy_training_row(i, f"2026-05-{15+i:02d}T00:00:00Z", f"2026-05-{16+i:02d}T00:00:00Z", event_id="cyclone_amphan_2020"))
    # 5 rows for monsoon_depression
    for i in range(6, 11):
        rows.append(_make_dummy_training_row(i, f"2026-07-{i:02d}T00:00:00Z", f"2026-07-{i+1:02d}T00:00:00Z", event_id="monsoon_depression_2020"))
    # 10 generic rows
    for i in range(11, 21):
        rows.append(_make_dummy_training_row(i, f"2026-08-{i:02d}T00:00:00Z", f"2026-08-{i+1:02d}T00:00:00Z"))

    splits = splitter.split(rows)

    train_events = {r.metadata.get("event_id") for r in splits.train_rows if r.metadata.get("event_id")}
    val_events = {r.metadata.get("event_id") for r in splits.val_rows if r.metadata.get("event_id")}
    test_events = {r.metadata.get("event_id") for r in splits.test_rows if r.metadata.get("event_id")}

    assert not train_events.intersection(val_events)
    assert not val_events.intersection(test_events)
    assert not train_events.intersection(test_events)
    assert "cyclone_amphan_2020" in test_events


# =========================================================================
# 6. REGION HOLDOUT SPATIAL ISOLATION
# =========================================================================

def test_region_holdout_spatial_isolation():
    """TEST 6: RegionHoldoutSplitter guarantees zero spatial overlap between train/val and test."""
    splitter = RegionHoldoutSplitter(held_out_regions=["Kolkata"])

    rows = []
    # Kolkata rows
    for i in range(1, 6):
        rows.append(_make_dummy_training_row(i, f"2026-08-{i:02d}T00:00:00Z", f"2026-08-{i+1:02d}T00:00:00Z", location="Kolkata"))
    # Delhi rows
    for i in range(6, 11):
        rows.append(_make_dummy_training_row(i, f"2026-08-{i:02d}T00:00:00Z", f"2026-08-{i+1:02d}T00:00:00Z", location="Delhi"))
    # Mumbai rows
    for i in range(11, 16):
        rows.append(_make_dummy_training_row(i, f"2026-08-{i:02d}T00:00:00Z", f"2026-08-{i+1:02d}T00:00:00Z", location="Mumbai"))

    splits = splitter.split(rows)

    train_locs = {r.location for r in splits.train_rows}
    val_locs = {r.location for r in splits.val_rows}
    test_locs = {r.location for r in splits.test_rows}

    assert "Kolkata" in test_locs
    assert "Kolkata" not in train_locs
    assert "Kolkata" not in val_locs


# =========================================================================
# 7. MODEL VERSION HOLDOUT ISOLATION
# =========================================================================

def test_model_version_holdout_isolation():
    """TEST 7: ModelVersionHoldoutSplitter guarantees zero version overlap between train and test."""
    splitter = ModelVersionHoldoutSplitter(held_out_model_versions=["gfs_v16_upgrade"])

    rows = []
    # gfs_v15 baseline
    for i in range(1, 11):
        r = _make_dummy_training_row(i, f"2026-08-{i:02d}T00:00:00Z", f"2026-08-{i+1:02d}T00:00:00Z")
        r.model_version = "gfs_v15"
        rows.append(r)
    # gfs_v16 upgrade
    for i in range(11, 16):
        r = _make_dummy_training_row(i, f"2026-08-{i:02d}T00:00:00Z", f"2026-08-{i+1:02d}T00:00:00Z")
        r.model_version = "gfs_v16_upgrade"
        rows.append(r)

    splits = splitter.split(rows)

    train_vers = {getattr(r, "model_version", None) for r in splits.train_rows}
    test_vers = {getattr(r, "model_version", None) for r in splits.test_rows}

    assert "gfs_v16_upgrade" in test_vers
    assert "gfs_v16_upgrade" not in train_vers


# =========================================================================
# 8. TEMPORAL EMBARGO PURGE
# =========================================================================

def test_temporal_embargo_purge():
    """TEST 8: Embargo window purges observations within embargo delta of split boundaries."""
    # 7-day embargo
    splitter = TemporalDataSplitter(train_ratio=0.60, val_ratio=0.20, test_ratio=0.20, embargo_days=7)

    # 100 consecutive daily rows to ensure sufficient rows survive 7-day embargo
    base_t = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    rows = [
        _make_dummy_training_row(
            i,
            (base_t + timedelta(days=i)).isoformat(),
            (base_t + timedelta(days=i+1)).isoformat(),
        )
        for i in range(100)
    ]

    splits = splitter.split(rows)

    assert splits.purged_rows_count > 0, "Expected embargo to purge rows near partition boundaries"
    train_max = datetime.fromisoformat(splits.train_rows[-1].issue_time.replace("Z", "+00:00"))
    val_min = datetime.fromisoformat(splits.val_rows[0].issue_time.replace("Z", "+00:00"))

    assert (val_min - train_max) >= timedelta(days=7), "Embargo between train and val must be at least 7 days"

