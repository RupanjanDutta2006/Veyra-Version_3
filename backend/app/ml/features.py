"""Leakage-Safe Feature Engineering Pipeline for Medium-Range Forecast Bust Prediction.

Docs §9, §9.1, Research Files 061-067:
Extracts features derivable strictly at forecast/issue time, enforcing the invariants:
1. NO reference observations, forecast errors, or ground truth labels in X.
2. availability_time <= issue_time hard enforcement (§9, D7).
3. Cycle-revision trajectory features across earlier issue cycles (D2).
4. Monsoon and synoptic regime context features (D3).
5. Historical analog similarity features with event exclusion (D4).
6. Static and contextual features: regional encoding, grid, elevation (D5).
7. Quality and safety signals: missingness, staleness, composite quality score (D6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union
import numpy as np

from backend.app.data.training_dataset import HistoricalTrainingRow
from backend.app.ml.feature_contract import (
    DataLeakageError,
    FORBIDDEN_GROUND_TRUTH_FIELDS,
    parse_iso_utc,
    validate_feature_vector,
    validate_issue_time_safety,
)
from backend.app.ml.regime_features import extract_regime_features
from backend.app.schemas.weather import CanonicalForecastRecord

if TYPE_CHECKING:
    from backend.app.services.analog_service import HistoricalAnalogService

# Backward-compatibility alias
FORBIDDEN_LEAKAGE_FIELDS = FORBIDDEN_GROUND_TRUTH_FIELDS
LeakageError = DataLeakageError

KNOWN_VARIABLES = [
    "temperature_2m",
    "surface_pressure",
    "wind_speed_10m",
    "relative_humidity_2m",
    "precipitation",
]

KNOWN_SEASONS = ["winter", "spring", "summer", "autumn"]


@dataclass
class FeatureSchema:
    """Standardized metadata definition of feature names and ordering."""

    version: str = "veyra-features-v2.0"
    feature_names: list[str] = field(default_factory=list)
    forbidden_fields: list[str] = field(default_factory=lambda: sorted(list(FORBIDDEN_GROUND_TRUTH_FIELDS)))


def classify_india_region(lat: float, lon: float, location: str = "") -> Dict[str, float]:
    """Classify Indian geographical sub-region and static orography/coastal context (§9, D5)."""
    loc_lower = (location or "").lower().strip()
    coastal_cities = {"mumbai", "kolkata", "chennai", "panaji", "kochi", "visakhapatnam", "puri", "mangalore"}
    is_coastal = 1.0 if loc_lower in coastal_cities or (8.0 <= lat <= 22.0 and (lon <= 73.5 or lon >= 80.0)) else 0.0

    is_north = 1.0 if lat >= 24.0 and 70.0 <= lon <= 82.0 else 0.0
    is_south = 1.0 if lat < 16.0 and 74.0 <= lon <= 81.0 else 0.0
    is_east = 1.0 if lon >= 82.0 and 16.0 <= lat <= 28.0 else 0.0
    is_west = 1.0 if lon < 75.0 and 16.0 <= lat <= 24.0 else 0.0
    is_central = 1.0 if (16.0 <= lat < 24.0 and 75.0 <= lon < 82.0) else 0.0

    # Approximate elevation proxy based on location / coordinates
    elev_m = 216.0  # Delhi default
    if loc_lower == "mumbai" or loc_lower == "kolkata" or loc_lower == "chennai" or loc_lower == "panaji":
        elev_m = 10.0
    elif loc_lower == "delhi":
        elev_m = 216.0
    elif loc_lower == "bengaluru" or loc_lower == "bangalore":
        elev_m = 920.0

    return {
        "is_region_north": is_north,
        "is_region_south": is_south,
        "is_region_east": is_east,
        "is_region_west": is_west,
        "is_region_central": is_central,
        "is_coastal": is_coastal,
        "elevation_m": float(elev_m),
        "grid_resolution": 0.25,
        "model_version_code": 1.0,  # NOAA GEFS v12
    }


def compute_quality_signals(
    issue_time: Union[str, datetime],
    availability_time: Optional[Union[str, datetime]] = None,
    member_count: int = 31,
    has_gaps: bool = False,
    current_time: Optional[datetime] = None,
) -> Dict[str, float]:
    """Compute data quality, staleness, and missingness signals (§9, D6)."""
    dt_issue = parse_iso_utc(issue_time)
    dt_now = current_time or datetime.now(timezone.utc)
    dt_avail = parse_iso_utc(availability_time) if availability_time else dt_issue

    staleness_hours = max(0.0, (dt_now - dt_issue).total_seconds() / 3600.0)
    latency_hours = max(0.0, (dt_avail - dt_issue).total_seconds() / 3600.0)
    missing_ratio = max(0.0, min(1.0, 1.0 - (float(member_count) / 31.0)))
    gap_flag = 1.0 if has_gaps else 0.0

    # Composite quality score in [0.0, 1.0]
    score = 1.0 - (0.5 * missing_ratio + 0.3 * min(1.0, staleness_hours / 48.0) + 0.2 * gap_flag)
    quality_score = round(float(np.clip(score, 0.0, 1.0)), 4)

    return {
        "data_staleness_hours": round(staleness_hours, 2),
        "missing_member_ratio": round(missing_ratio, 4),
        "data_latency_hours": round(latency_hours, 2),
        "has_missing_steps": gap_flag,
        "composite_quality_score": quality_score,
    }


def compute_revision_trajectory_features(
    target_val: float,
    target_std: float,
    target_valid_time: str,
    target_issue_time: str,
    prior_records: Optional[List[Union[CanonicalForecastRecord, dict[str, Any]]]] = None,
) -> Dict[str, float]:
    """Compute cycle-revision trajectory features across earlier issue cycles (§9.1, D2).

    Calculates:
    - forecast_delta_6h: mu(I) - mu(I - 6h)
    - forecast_delta_24h: mu(I) - mu(I - 24h)
    - forecast_revision_mag_6h: |Delta_6h|
    - forecast_revision_mag_24h: |Delta_24h|
    - ensemble_spread_delta_6h: sigma(I) - sigma(I - 6h)
    - ensemble_spread_delta_24h: sigma(I) - sigma(I - 24h)
    - revision_accel_6h: second difference
    - revision_sign_flips: directional flip count across cycles
    - revision_trend: slope across earlier cycles
    """
    default_revisions = {
        "forecast_delta_6h": 0.0,
        "forecast_delta_24h": 0.0,
        "forecast_revision_mag_6h": 0.0,
        "forecast_revision_mag_24h": 0.0,
        "ensemble_spread_delta_6h": 0.0,
        "ensemble_spread_delta_24h": 0.0,
        "revision_accel_6h": 0.0,
        "revision_sign_flips": 0.0,
        "revision_trend": 0.0,
        "has_revision_history": 0.0,
    }

    if not prior_records:
        return default_revisions

    try:
        dt_target_issue = parse_iso_utc(target_issue_time)
        dt_target_valid = parse_iso_utc(target_valid_time)
    except Exception:
        return default_revisions

    # Filter prior records for the exact same valid time issued strictly before target_issue_time
    matching_priors: List[Tuple[float, float, float]] = []  # (hours_before_target_issue, mean, std)

    for p in prior_records:
        p_dict = p if isinstance(p, dict) else (p.model_dump() if hasattr(p, "model_dump") else {})
        p_valid = p_dict.get("valid_time", "")
        p_issue = p_dict.get("issue_time", "")
        if not p_valid or not p_issue:
            continue

        try:
            p_dt_valid = parse_iso_utc(p_valid)
            p_dt_issue = parse_iso_utc(p_issue)
        except Exception:
            continue

        # Same valid target, issued earlier
        if p_dt_valid == dt_target_valid and p_dt_issue < dt_target_issue:
            hours_prior = (dt_target_issue - p_dt_issue).total_seconds() / 3600.0
            p_mean = float(p_dict.get("forecast_value", p_dict.get("value", p_dict.get("ensemble_mean", 0.0))))
            p_std = float(p_dict.get("ensemble_std", 0.0) or 0.0)
            matching_priors.append((hours_prior, p_mean, p_std))

    if not matching_priors:
        return default_revisions

    # Sort by hours_prior ascending
    matching_priors.sort(key=lambda x: x[0])

    # Find closest to 6h prior (within 3h-9h window)
    p6 = min(matching_priors, key=lambda x: abs(x[0] - 6.0)) if matching_priors else None
    p12 = min(matching_priors, key=lambda x: abs(x[0] - 12.0)) if len(matching_priors) > 1 else None
    p24 = min(matching_priors, key=lambda x: abs(x[0] - 24.0)) if matching_priors else None

    d6 = (target_val - p6[1]) if p6 and abs(p6[0] - 6.0) <= 6.0 else 0.0
    d24 = (target_val - p24[1]) if p24 and abs(p24[0] - 24.0) <= 12.0 else d6
    spread_d6 = (target_std - p6[2]) if p6 and abs(p6[0] - 6.0) <= 6.0 else 0.0
    spread_d24 = (target_std - p24[2]) if p24 and abs(p24[0] - 24.0) <= 12.0 else spread_d6

    # Second difference acceleration: (delta_6h) - (delta_prev)
    if p12 and p6:
        prev_delta = p6[1] - p12[1]
        accel_6h = d6 - prev_delta
    else:
        accel_6h = 0.0

    # Count sign flips
    means_seq = [p[1] for p in reversed(matching_priors)] + [target_val]
    diffs = [means_seq[i + 1] - means_seq[i] for i in range(len(means_seq) - 1)]
    sign_flips = sum(
        1 for i in range(len(diffs) - 1)
        if (diffs[i] > 1e-4 and diffs[i + 1] < -1e-4) or (diffs[i] < -1e-4 and diffs[i + 1] > 1e-4)
    )

    # Linear trend slope (mean change per hour)
    hours_seq = [-p[0] for p in reversed(matching_priors)] + [0.0]
    if len(hours_seq) >= 2:
        slope, _ = np.polyfit(hours_seq, means_seq, 1)
        trend = float(slope)
    else:
        trend = 0.0

    return {
        "forecast_delta_6h": round(float(d6), 4),
        "forecast_delta_24h": round(float(d24), 4),
        "forecast_revision_mag_6h": round(float(abs(d6)), 4),
        "forecast_revision_mag_24h": round(float(abs(d24)), 4),
        "ensemble_spread_delta_6h": round(float(spread_d6), 4),
        "ensemble_spread_delta_24h": round(float(spread_d24), 4),
        "revision_accel_6h": round(float(accel_6h), 4),
        "revision_sign_flips": float(sign_flips),
        "revision_trend": round(float(trend), 4),
        "has_revision_history": 1.0,
    }


class InferenceSafeFeatureExtractor:
    """Extracts raw numerical predictors from forecast or historical records."""

    def __init__(self, analog_service: Optional[HistoricalAnalogService] = None):
        if analog_service is None:
            from backend.app.services.analog_service import HistoricalAnalogService
            self.analog_service = HistoricalAnalogService()
        else:
            self.analog_service = analog_service

    @staticmethod
    def assert_no_leakage(data_dict: dict[str, Any]) -> None:
        """Verify that forbidden ground-truth fields are not present in candidate feature dict."""
        for forbidden in FORBIDDEN_GROUND_TRUTH_FIELDS:
            if forbidden in data_dict and data_dict[forbidden] is not None:
                raise DataLeakageError(
                    f"Forbidden leakage field '{forbidden}' found in candidate predictor dictionary (§9)."
                )

    def extract_raw_features(
        self,
        record: Union[HistoricalTrainingRow, CanonicalForecastRecord, dict[str, Any]],
    ) -> dict[str, float]:
        """Extract baseline 18 inference-safe numerical and cyclic features from a record.

        Maintains 100% backward compatibility with baseline models while enforcing
        availability_time <= issue_time (D7) and anti-leakage invariants (D8).
        """
        if isinstance(record, HistoricalTrainingRow):
            loc_lat = record.latitude
            loc_lon = record.longitude
            lead_h = float(record.lead_hours)
            fc_val = float(record.forecast_value)
            var_name = record.variable.lower()
            season_str = record.season.lower()
            issue_time_str = record.issue_time
            valid_time_str = record.valid_time
            month_val = record.month
            avail_time_str = getattr(record, "availability_time", None)
        elif isinstance(record, CanonicalForecastRecord):
            loc_lat = record.latitude
            loc_lon = record.longitude
            lead_h = float(record.lead_hours)
            fc_val = float(record.value if record.value is not None else (record.ensemble_mean or 0.0))
            var_name = record.variable.lower()
            issue_time_str = record.issue_time
            valid_time_str = record.valid_time
            avail_time_str = getattr(record, "availability_time", None)
            try:
                dt = datetime.fromisoformat(valid_time_str.replace("Z", "+00:00"))
                month_val = dt.month
            except Exception:
                month_val = 1
            season_str = "winter" if month_val in (12, 1, 2) else "spring" if month_val in (3, 4, 5) else "summer" if month_val in (6, 7, 8) else "autumn"
        elif isinstance(record, dict):
            loc_lat = float(record.get("latitude", 0.0))
            loc_lon = float(record.get("longitude", 0.0))
            lead_h = float(record.get("lead_hours", 0.0))
            fc_val = float(record.get("forecast_value", record.get("value", 0.0)))
            var_name = str(record.get("variable", "unknown")).lower()
            season_str = str(record.get("season", "unknown")).lower()
            issue_time_str = str(record.get("issue_time", ""))
            valid_time_str = str(record.get("valid_time", ""))
            avail_time_str = record.get("availability_time")
            month_val = int(record.get("month", 1))
        else:
            raise TypeError(f"Unsupported record type for feature extraction: {type(record)}")

        # Enforce temporal availability invariant (D7)
        if issue_time_str and avail_time_str:
            validate_issue_time_safety(issue_time_str, avail_time_str)

        # Parse hour from issue time for diurnal cycle
        try:
            issue_dt = datetime.fromisoformat(issue_time_str.replace("Z", "+00:00"))
            hour_val = issue_dt.hour
        except Exception:
            hour_val = 0

        # Base numerical features (18 baseline features)
        features: dict[str, float] = {
            "lead_hours": lead_h,
            "forecast_value": fc_val,
            "latitude": loc_lat,
            "longitude": loc_lon,
            "month": float(month_val),
            "sin_month": round(math.sin(2.0 * math.pi * month_val / 12.0), 4),
            "cos_month": round(math.cos(2.0 * math.pi * month_val / 12.0), 4),
            "sin_hour": round(math.sin(2.0 * math.pi * hour_val / 24.0), 4),
            "cos_hour": round(math.cos(2.0 * math.pi * hour_val / 24.0), 4),
        }

        # One-hot encode variables
        for v in KNOWN_VARIABLES:
            features[f"var_{v}"] = 1.0 if var_name == v else 0.0

        # One-hot encode seasons
        for s in KNOWN_SEASONS:
            features[f"season_{s}"] = 1.0 if season_str == s else 0.0

        return features

    def extract_enriched_features(
        self,
        record: Union[HistoricalTrainingRow, CanonicalForecastRecord, dict[str, Any]],
        prior_records: Optional[List[Union[CanonicalForecastRecord, dict[str, Any]]]] = None,
        include_regime: bool = True,
        include_analogs: bool = True,
    ) -> dict[str, float]:
        """Extract complete Phase 2 enriched feature representation.

        Includes:
        - Baseline 18 features (lead, value, lat/lon, cyclic month/hour, var, season)
        - Cycle-revision trajectory features (D2)
        - Synoptic regime and monsoon context features (D3)
        - Historical analog similarity features (D4)
        - Static / contextual regional features (D5)
        - Data quality and staleness signals (D6)
        - Temporal availability enforcement (D7)
        """
        # 1. Base features + temporal validation
        base_features = self.extract_raw_features(record)

        if isinstance(record, (HistoricalTrainingRow, CanonicalForecastRecord)):
            rec_dict = record.model_dump() if hasattr(record, "model_dump") else record.__dict__
        else:
            rec_dict = record

        issue_time_str = str(rec_dict.get("issue_time", ""))
        valid_time_str = str(rec_dict.get("valid_time", ""))
        avail_time_str = rec_dict.get("availability_time")
        loc_lat = float(rec_dict.get("latitude", 0.0))
        loc_lon = float(rec_dict.get("longitude", 0.0))
        loc_name = str(rec_dict.get("location", ""))
        var_name = str(rec_dict.get("variable", "temperature_2m")).lower()
        fc_val = float(rec_dict.get("forecast_value", rec_dict.get("value", 0.0)))
        ens_std = float(rec_dict.get("ensemble_std", 1.0) or 1.0)
        member_count = int(rec_dict.get("member_count", 31) or 31)

        try:
            valid_dt = parse_iso_utc(valid_time_str)
        except Exception:
            valid_dt = datetime.now(timezone.utc)

        enriched: dict[str, float] = dict(base_features)

        # 2. Cycle-revision trajectory (D2)
        rev_features = compute_revision_trajectory_features(
            target_val=fc_val,
            target_std=ens_std,
            target_valid_time=valid_time_str,
            target_issue_time=issue_time_str,
            prior_records=prior_records,
        )
        enriched.update(rev_features)

        # 3. Monsoon & Synoptic Regime Context (D3)
        if include_regime:
            press_hpa = fc_val if var_name == "surface_pressure" else None
            wind_ms = fc_val if var_name == "wind_speed_10m" else None
            regime_features = extract_regime_features(
                valid_dt=valid_dt,
                surface_pressure_hpa=press_hpa,
                wind_speed_ms=wind_ms,
                latitude=loc_lat,
                longitude=loc_lon,
            )
            enriched.update(regime_features)

        # 4. Analog Similarity Features (D4)
        if include_analogs and self.analog_service:
            analog_feats = self.analog_service.extract_analog_features(
                query_time=issue_time_str or valid_time_str,
                variable=var_name,
                lead_hours=int(base_features.get("lead_hours", 24)),
                forecast_value=fc_val,
                ensemble_std=ens_std,
                location=loc_name,
            )
            enriched.update(analog_feats)

        # 5. Static & Contextual Regional Features (D5)
        region_feats = classify_india_region(loc_lat, loc_lon, location=loc_name)
        enriched.update(region_feats)

        # 6. Quality & Safety Signals (D6)
        qual_feats = compute_quality_signals(
            issue_time=issue_time_str,
            availability_time=avail_time_str,
            member_count=member_count,
        )
        enriched.update(qual_feats)

        return enriched


class FeaturePipeline:
    """Standardized preprocessing pipeline fitting scaler parameters on TRAIN ONLY."""

    def __init__(self, enriched: bool = False):
        self.extractor = InferenceSafeFeatureExtractor()
        self.enriched = enriched
        self.feature_names: list[str] = []
        self.means: dict[str, float] = {}
        self.stds: dict[str, float] = {}
        self.is_fitted: bool = False
        self.schema = FeatureSchema(version="veyra-features-v2.0" if enriched else "veyra-features-v1.0")

    def fit(self, rows: list[HistoricalTrainingRow]) -> "FeaturePipeline":
        """Fit normalization parameters (mean, std) exclusively on the training split."""
        if not rows:
            raise ValueError("Cannot fit FeaturePipeline on empty dataset")

        if getattr(self, "enriched", False):
            raw_feature_dicts = [self.extractor.extract_enriched_features(row) for row in rows]
        else:
            raw_feature_dicts = [self.extractor.extract_raw_features(row) for row in rows]

        self.feature_names = sorted(list(raw_feature_dicts[0].keys()))
        self.schema.feature_names = self.feature_names

        # Compute mean and standard deviation for each feature on training partition
        for name in self.feature_names:
            vals = [d[name] for d in raw_feature_dicts]
            mean_val = float(np.mean(vals))
            std_val = float(np.std(vals))
            self.means[name] = mean_val
            # Guard against zero variance in binary one-hot features
            self.stds[name] = std_val if std_val > 1e-6 else 1.0

        self.is_fitted = True
        return self

    def transform(self, rows: list[HistoricalTrainingRow]) -> tuple[np.ndarray, np.ndarray]:
        """Transform rows into normalized feature matrix X and target vector y."""
        if not self.is_fitted:
            raise RuntimeError("FeaturePipeline must be fitted on training data before transform")

        X_rows: list[list[float]] = []
        y_vals: list[int] = []

        for row in rows:
            raw_dict = (
                self.extractor.extract_enriched_features(row)
                if getattr(self, "enriched", False)
                else self.extractor.extract_raw_features(row)
            )
            # Normalized feature vector in deterministic order
            norm_vector = [(raw_dict[col] - self.means[col]) / self.stds[col] for col in self.feature_names]
            X_rows.append(norm_vector)
            y_vals.append(int(row.bust_label))

        return np.array(X_rows, dtype=np.float64), np.array(y_vals, dtype=np.int64)

    def transform_inference(
        self,
        records: list[CanonicalForecastRecord],
        prior_records: Optional[list[CanonicalForecastRecord]] = None,
    ) -> np.ndarray:
        """Transform canonical forecast records into normalized feature matrix X for live inference."""
        if not self.is_fitted:
            raise RuntimeError("FeaturePipeline must be fitted on training data before transform_inference")

        X_rows: list[list[float]] = []
        for rec in records:
            raw_dict = (
                self.extractor.extract_enriched_features(rec, prior_records=prior_records)
                if getattr(self, "enriched", False)
                else self.extractor.extract_raw_features(rec)
            )
            norm_vector = [(raw_dict[col] - self.means[col]) / self.stds[col] for col in self.feature_names]
            X_rows.append(norm_vector)

        return np.array(X_rows, dtype=np.float64)

    def get_feature_names(self) -> list[str]:
        """Return deterministic list of feature names."""
        return self.feature_names.copy()
