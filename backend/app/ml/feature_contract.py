"""Authoritative Feature Contract & Leakage Guard for Veyra.

Enforces issue-time safety invariants:
1. Every feature must have an availability_time that is no later than the forecast issue_time.
   (Docs §9: "availability_time <= issue_time hard control")
2. Strictly forbids ground-truth observations, forecast errors, or future verification labels from entering X.
   (Docs §9, §10.4: "FORBIDDEN_GROUND_TRUTH_FIELDS guard")
3. Enforces finite, valid numerical types and deterministic schema ordering.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union
import math
import numpy as np


class FeatureContractError(ValueError):
    """Raised when a feature vector violates contract constraints (NaN, Inf, unknown type)."""


class DataLeakageError(FeatureContractError):
    """Raised when ground-truth fields or future data leak into feature extraction."""


FeatureLeakageError = DataLeakageError


# Prohibited ground-truth, reference observation, and future evaluation fields (§9, §10.4)
FORBIDDEN_GROUND_TRUTH_FIELDS: Set[str] = {
    "reference_value",
    "observed_value",
    "error",
    "forecast_error",
    "absolute_error",
    "bust_label",
    "bust_threshold",
    "reference_source",
    "is_ground_truth_label",
    "future_truth",
    "verification_value",
    "observed_max",
    "observed_min",
    "ground_truth",
    "era5_actual",
    "actual_observation",
    "actual_value",
    "ground_truth_value",
}

# Standardized temporal tolerance (seconds) for minor network/clock skew
CLOCK_SKEW_TOLERANCE_SECONDS: float = 60.0


def parse_iso_utc(ts: Union[str, datetime]) -> datetime:
    """Parse ISO 8601 string or datetime into UTC datetime."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    if isinstance(ts, str):
        cleaned = ts.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    raise TypeError(f"Expected str or datetime, got {type(ts)}")


def validate_issue_time_safety(
    issue_time: Union[str, datetime],
    availability_time: Optional[Union[str, datetime]] = None,
) -> bool:
    """Enforce the hard temporal constraint: availability_time <= issue_time.
    
    Parameters
    ----------
    issue_time : str or datetime
        Timestamp when the forecast was issued.
    availability_time : str or datetime, optional
        Timestamp when the data/feature became available. If None, assumes issue time.

    Returns
    -------
    bool
        True if valid.

    Raises
    ------
    DataLeakageError
        If availability_time > issue_time + tolerance.
    """
    if availability_time is None:
        return True

    dt_issue = parse_iso_utc(issue_time)
    dt_avail = parse_iso_utc(availability_time)

    diff_seconds = (dt_avail - dt_issue).total_seconds()
    if diff_seconds > CLOCK_SKEW_TOLERANCE_SECONDS:
        raise DataLeakageError(
            f"Temporal leakage detected: availability_time ({dt_avail.isoformat()}) "
            f"exceeds forecast issue_time ({dt_issue.isoformat()}) by {diff_seconds:.1f}s. "
            f"Constraint availability_time <= issue_time violated (§9)."
        )
    return True


def assert_no_leakage(data_dict: Dict[str, Any], context: str = "features") -> None:
    """Verify that forbidden ground-truth fields are not present with non-null values.

    Parameters
    ----------
    data_dict : dict
        Candidate feature or input dictionary.
    context : str
        Context string for error messaging.

    Raises
    ------
    DataLeakageError
        If any forbidden field contains non-null data.
    """
    leaked = []
    for field_name in FORBIDDEN_GROUND_TRUTH_FIELDS:
        if field_name in data_dict and data_dict[field_name] is not None:
            leaked.append(field_name)

    if leaked:
        raise DataLeakageError(
            f"Data leakage in {context}: forbidden ground truth fields {leaked} "
            f"present in candidate predictor dictionary. Predictions must use issue-time signals only (§9)."
        )


def validate_feature_vector(
    features: Dict[str, float],
    expected_names: Optional[List[str]] = None,
    allow_missing: bool = False,
) -> Dict[str, float]:
    """Validate numerical properties of a feature dictionary.

    - Verifies all values are finite (no NaN, no Inf).
    - Verifies no forbidden leakage fields.
    - If expected_names provided, ensures exact schema match.
    """
    assert_no_leakage(features, context="feature_vector")

    validated: Dict[str, float] = {}
    for k, v in features.items():
        if v is None:
            if not allow_missing:
                raise FeatureContractError(f"Feature '{k}' is None; missing values must be handled explicitly.")
            validated[k] = 0.0
            continue

        if k in ("availability_time", "issue_time", "valid_time", "location", "variable", "model_version", "region"):
            validated[k] = str(v)
            continue

        try:
            val = float(v)
        except (ValueError, TypeError) as exc:
            raise FeatureContractError(f"Feature '{k}' has non-numeric value: {v}") from exc

        if not math.isfinite(val):
            raise FeatureContractError(f"Feature '{k}' is non-finite (NaN or Inf): {val}")

        validated[k] = val

    if expected_names is not None:
        current_keys = set(validated.keys())
        expected_keys = set(expected_names)
        missing = expected_keys - current_keys
        extra = current_keys - expected_keys
        if missing and not allow_missing:
            raise FeatureContractError(f"Feature schema mismatch. Missing required features: {sorted(list(missing))}")
        if extra:
            raise FeatureContractError(f"Feature schema mismatch. Unexpected extra features: {sorted(list(extra))}")

    return validated


class FeatureContract:
    """Class wrapper for feature contract validation and leakage prevention (§9)."""

    def __init__(self, forbidden_fields: Optional[Set[str]] = None):
        self.forbidden_fields = forbidden_fields or FORBIDDEN_GROUND_TRUTH_FIELDS

    def validate_features(
        self,
        features: Dict[str, Any],
        issue_time: Union[str, datetime],
        availability_time: Optional[Union[str, datetime]] = None,
        expected_names: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Validate temporal causality and numeric contract on features."""
        validate_issue_time_safety(issue_time, availability_time)
        return validate_feature_vector(features, expected_names=expected_names, allow_missing=True)

    def filter_forbidden_fields(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Return shallow copy with all forbidden ground truth fields stripped."""
        return {k: v for k, v in data_dict.items() if k not in self.forbidden_fields}

