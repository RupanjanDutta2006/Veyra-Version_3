# Test V3 UTC Time Contract & Temporal Leakage Prevention
import pytest
from datetime import datetime, timezone
from backend.app.core.time_contract import (
    parse_utc_timestamp,
    format_utc_timestamp,
    derive_and_validate_lead_hours,
    is_certified_lead_horizon,
    MAX_CERTIFIED_LEAD_HOURS,
    MAX_SUPPORTED_LEAD_HOURS
)

def test_parse_utc_timestamp_iso_z():
    dt = parse_utc_timestamp("2026-09-22T06:00:00Z")
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 6

def test_parse_utc_timestamp_naive_defaults_to_utc():
    dt = parse_utc_timestamp("2026-09-22T06:00:00")
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 6

def test_parse_utc_timestamp_offset_converts_to_utc():
    # +05:30 11:30 should convert to 06:00 UTC
    dt = parse_utc_timestamp("2026-09-22T11:30:00+05:30")
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 6
    assert dt.minute == 0

def test_derive_and_validate_lead_hours_success():
    issue = "2026-09-22T00:00:00Z"
    valid = "2026-09-23T12:00:00Z"
    lead, c_issue, c_valid = derive_and_validate_lead_hours(issue, valid)
    assert lead == 36
    assert c_issue == "2026-09-22T00:00:00Z"
    assert c_valid == "2026-09-23T12:00:00Z"

def test_derive_and_validate_lead_hours_rejects_reversed_time():
    issue = "2026-09-22T12:00:00Z"
    valid = "2026-09-22T06:00:00Z"
    with pytest.raises(ValueError, match="strictly after"):
        derive_and_validate_lead_hours(issue, valid)

def test_derive_and_validate_lead_hours_rejects_zero_lead():
    issue = "2026-09-22T00:00:00Z"
    valid = "2026-09-22T00:00:00Z"
    with pytest.raises(ValueError):
        derive_and_validate_lead_hours(issue, valid)

def test_derive_and_validate_lead_hours_rejects_beyond_max():
    issue = "2026-09-22T00:00:00Z"
    valid = "2026-10-15T00:00:00Z" # > 500h
    with pytest.raises(ValueError, match="exceeds"):
        derive_and_validate_lead_hours(issue, valid)

def test_is_certified_lead_horizon():
    assert is_certified_lead_horizon(24) is True
    assert is_certified_lead_horizon(240) is True
    assert is_certified_lead_horizon(264) is False
    assert is_certified_lead_horizon(0) is False
