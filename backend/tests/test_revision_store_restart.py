import os
import tempfile
import pytest
from backend.app.core.revision_store import RevisionStore, RevisionRecord

def test_revision_store_disk_restart_survivability():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        # Step 1: Open store, write records
        store1 = RevisionStore(db_path=db_path)
        rec1 = RevisionRecord(
            canonical_location="Kolkata",
            variable="temperature_2m",
            valid_time="2026-09-22T12:00:00Z",
            issue_time="2026-09-21T00:00:00Z",
            lead_hours=36,
            forecast_value=302.5,
            ensemble_mean=302.1,
            ensemble_spread=1.1,
            bust_probability=0.045,
            model_version="veyra-v3-benchmark-lightgbm",
            provider_source="noaa_gefs_v12"
        )
        rec2 = RevisionRecord(
            canonical_location="Kolkata",
            variable="temperature_2m",
            valid_time="2026-09-22T12:00:00Z",
            issue_time="2026-09-21T06:00:00Z",
            lead_hours=30,
            forecast_value=303.0,
            ensemble_mean=302.7,
            ensemble_spread=0.9,
            bust_probability=0.052,
            model_version="veyra-v3-benchmark-lightgbm",
            provider_source="noaa_gefs_v12"
        )
        assert store1.record_revision(rec1) is True
        assert store1.record_revision(rec2) is True
        # Verify idempotency
        assert store1.record_revision(rec1) is True

        # Simulate process shutdown
        del store1

        # Step 2: Restart service with a fresh store instance pointing to same file
        store2 = RevisionStore(db_path=db_path)
        history = store2.get_trajectory_points(
            canonical_location="Kolkata",
            variable="temperature_2m",
            valid_time="2026-09-22T12:00:00Z"
        )
        assert len(history) == 2
        # Chronological order
        assert history[0].issue_time == "2026-09-21T00:00:00Z"
        assert history[1].issue_time == "2026-09-21T06:00:00Z"

        # Previous revision query
        prev = store2.get_previous_revision(
            canonical_location="Kolkata",
            variable="temperature_2m",
            valid_time="2026-09-22T12:00:00Z",
            current_issue_time="2026-09-21T06:00:00Z"
        )
        assert prev is not None
        assert prev.issue_time == "2026-09-21T00:00:00Z"
        assert prev.forecast_value == 302.5
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
