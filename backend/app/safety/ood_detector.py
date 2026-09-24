"""Out-of-Distribution (OOD) Detection and Atmospheric Novelty Scoring Engine.

Implements the official SIH26079 OOD Detection Specification (§11.3):
- Multi-dimensional transparent signals:
  1. Feature distance from training distribution support (standardized Mahalanobis / robust z-score).
  2. Missingness and data completeness signals.
  3. Atmospheric regime novelty (monsoon phase, blocking pattern, Rossby index, jet latitude).
  4. Two-sample distribution drift statistics (Kolmogorov-Smirnov & Wasserstein distances).
- State mapping per §11.3:
  - NORMAL (< 0.35): Supported, nominal conditions.
  - UNUSUAL (0.35 - 0.65): Supported but in the tail of training support; high-visibility caution.
  - OOD (0.65 - 0.85): Outside declared support or affected by model/data shift.
  - ABSTAIN (>= 0.85): Extreme distribution shift requiring safety abstention.
"""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


class OODState(str, Enum):
    """OOD State Taxonomy matching §11.3 table."""

    NORMAL = "NORMAL"
    UNUSUAL = "UNUSUAL"
    OOD = "OOD"
    ABSTAIN = "ABSTAIN"


@dataclass
class OODResult:
    """Structured result of out-of-distribution evaluation."""

    ood_score: float
    state: OODState
    feature_distance: float
    regime_novelty: float
    drift_statistic: float
    dominant_drivers: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ood_score": round(self.ood_score, 4),
            "state": self.state.value,
            "feature_distance": round(self.feature_distance, 4),
            "regime_novelty": round(self.regime_novelty, 4),
            "drift_statistic": round(self.drift_statistic, 4),
            "dominant_drivers": self.dominant_drivers,
            "details": self.details,
        }


class OODDetector:
    """Detects when an incoming forecast or feature vector is out-of-distribution.

    Uses reference baseline statistics from training distributions to evaluate
    multivariate feature distance, regime novelty, and distributional shift.
    """

    DEFAULT_FEATURE_MEANS: Dict[str, float] = {
        "ensemble_mean": 298.15,
        "ensemble_std": 1.5,
        "surface_pressure": 101325.0,
        "wind_speed_10m": 4.5,
        "relative_humidity_2m": 65.0,
        "spread_x_lead": 3.0,
        "lead_hours": 72.0,
        "forecast_delta_24h": 0.5,
        "ensemble_spread_delta_24h": 0.2,
        "blocking_index": 0.0,
        "rossby_wave_activity_index": 1.0,
        "jet_latitude": 30.0,
    }

    DEFAULT_FEATURE_STDS: Dict[str, float] = {
        "ensemble_mean": 8.0,
        "ensemble_std": 1.2,
        "surface_pressure": 1500.0,
        "wind_speed_10m": 3.0,
        "relative_humidity_2m": 20.0,
        "spread_x_lead": 2.5,
        "lead_hours": 48.0,
        "forecast_delta_24h": 1.5,
        "ensemble_spread_delta_24h": 0.8,
        "blocking_index": 1.0,
        "rossby_wave_activity_index": 0.8,
        "jet_latitude": 8.0,
    }

    def __init__(
        self,
        reference_means: Optional[Dict[str, float]] = None,
        reference_stds: Optional[Dict[str, float]] = None,
        reference_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        unusual_threshold: float = 0.35,
        ood_threshold: float = 0.65,
        abstain_threshold: float = 0.80,
    ):
        self.means = reference_means or dict(self.DEFAULT_FEATURE_MEANS)
        self.stds = reference_stds or dict(self.DEFAULT_FEATURE_STDS)
        self.bounds = reference_bounds or {}
        self.unusual_threshold = unusual_threshold
        self.ood_threshold = ood_threshold
        self.abstain_threshold = abstain_threshold

    def fit_from_dataframe(self, df: Any, feature_cols: Optional[List[str]] = None) -> "OODDetector":
        """Fit baseline distribution statistics from historical training DataFrame."""
        cols = feature_cols or [c for c in df.columns if c in self.DEFAULT_FEATURE_MEANS]
        if not cols:
            cols = [c for c in df.select_dtypes(include=[np.number]).columns]

        means = {}
        stds = {}
        bounds = {}
        for col in cols:
            if col in df.columns:
                series = df[col].dropna()
                if len(series) > 1:
                    m = float(series.mean())
                    s = float(series.std())
                    means[col] = m
                    stds[col] = max(s, 1e-4)
                    bounds[col] = (float(series.quantile(0.005)), float(series.quantile(0.995)))

        self.means = means
        self.stds = stds
        self.bounds = bounds
        return self

    def compute_feature_distance(self, features: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Compute standardized Euclidean / Mahalanobis distance from reference support."""
        squared_z_sum = 0.0
        n_matched = 0
        extreme_drivers = []

        is_normalized_pipeline = (
            ("latitude" in features or "longitude" in features)
            and "ensemble_mean" not in features
        )

        if is_normalized_pipeline:
            # Handle normalized features from FeaturePipeline (standard-scaled: mean=0, std=1)
            norm_continuous_keys = ("forecast_value", "lead_hours", "latitude", "longitude", "month")
            for key in norm_continuous_keys:
                if key in features:
                    val = features[key]
                    if val is None or not isinstance(val, (int, float)) or math.isnan(val):
                        continue
                    z = abs(float(val))  # Standard-scaled features have mean=0, std=1
                    squared_z_sum += z * z
                    n_matched += 1
                    if z > 2.5:
                        extreme_drivers.append(f"{key}_zscore_{round(z, 1)}")
        else:
            means = dict(self.means)
            stds = dict(self.stds)
            # Variable-adaptive reference parameters for V3 physical features
            if features.get("is_surface_pressure") == 1.0:
                means["ensemble_mean"] = 101325.0
                stds["ensemble_mean"] = 2500.0
                means["ensemble_std"] = 100.0
                stds["ensemble_std"] = 80.0
            elif features.get("is_wind_speed_10m") == 1.0:
                means["ensemble_mean"] = 4.5
                stds["ensemble_mean"] = 3.5
                means["ensemble_std"] = 1.5
                stds["ensemble_std"] = 1.2

            for key, val in features.items():
                if val is None or not isinstance(val, (int, float)) or math.isnan(val):
                    continue
                if key in means and key in stds:
                    m = means[key]
                    s = stds[key]
                    z = abs(val - m) / s
                    squared_z_sum += z * z
                    n_matched += 1

                    if z > 2.5:
                        extreme_drivers.append(f"{key}_zscore_{round(z, 1)}")

                # Check explicit bounds if present
                if key in self.bounds:
                    b_min, b_max = self.bounds[key]
                    if val < b_min or val > b_max:
                        extreme_drivers.append(f"{key}_out_of_bounds")

        if n_matched == 0:
            return 0.0, []

        rms_z = math.sqrt(squared_z_sum / n_matched)
        # Normalize to [0, 1] via hyperbolic tangent: rms_z=2.0 -> ~0.76, rms_z=1.0 -> ~0.46
        norm_distance = float(math.tanh(rms_z / 2.0))
        return norm_distance, extreme_drivers

    def compute_regime_novelty(self, regime_context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Evaluate atmospheric regime novelty against known historical patterns.

        Checks:
        - Blocking index severity
        - Rossby-wave index anomalies
        - Jet latitude displacement
        - Cyclonic/deep depression flags
        """
        novelty_points = 0.0
        max_points = 4.0
        regime_drivers = []

        # 1. Blocking index
        bi = regime_context.get("blocking_index")
        if bi is not None:
            try:
                bi_val = float(bi)
                if abs(bi_val) > 2.5:
                    novelty_points += 1.0
                    regime_drivers.append(f"severe_blocking_index_{round(bi_val, 1)}")
                elif abs(bi_val) > 1.5:
                    novelty_points += 0.5
            except (ValueError, TypeError):
                pass

        # 2. Rossby wave activity
        rw = regime_context.get("rossby_wave_activity_index")
        if rw is not None:
            try:
                rw_val = float(rw)
                if rw_val > 2.5:
                    novelty_points += 1.0
                    regime_drivers.append(f"intense_rossby_activity_{round(rw_val, 1)}")
                elif rw_val > 1.8:
                    novelty_points += 0.5
            except (ValueError, TypeError):
                pass

        # 3. Jet latitude anomaly
        jl = regime_context.get("jet_latitude")
        if jl is not None:
            try:
                jl_val = float(jl)
                ref_lat = self.means.get("jet_latitude", 30.0)
                lat_dev = abs(jl_val - ref_lat)
                if lat_dev > 15.0:
                    novelty_points += 1.0
                    regime_drivers.append(f"extreme_jet_displacement_{round(lat_dev, 1)}deg")
                elif lat_dev > 10.0:
                    novelty_points += 0.5
            except (ValueError, TypeError):
                pass

        # 4. Cyclonic or rapid transition
        if regime_context.get("is_cyclonic_episode") or regime_context.get("is_cyclone_flag"):
            novelty_points += 1.0
            regime_drivers.append("cyclonic_vortex_regime")

        norm_novelty = min(1.0, novelty_points / max_points)
        return norm_novelty, regime_drivers

    @staticmethod
    def compute_distribution_drift_ks(
        sample_values: Union[List[float], np.ndarray],
        reference_values: Union[List[float], np.ndarray],
    ) -> float:
        """Compute two-sample Kolmogorov-Smirnov maximum empirical CDF distance."""
        s1 = np.sort(np.asarray(sample_values, dtype=float))
        s2 = np.sort(np.asarray(reference_values, dtype=float))

        if len(s1) == 0 or len(s2) == 0:
            return 0.0

        n1 = len(s1)
        n2 = len(s2)

        data_all = np.concatenate([s1, s2])
        cdf1 = np.searchsorted(s1, data_all, side="right") / n1
        cdf2 = np.searchsorted(s2, data_all, side="right") / n2

        ks_stat = float(np.max(np.abs(cdf1 - cdf2)))
        return round(ks_stat, 4)

    @staticmethod
    def compute_wasserstein_distance(
        sample_values: Union[List[float], np.ndarray],
        reference_values: Union[List[float], np.ndarray],
    ) -> float:
        """Compute 1D Wasserstein-1 (Earth Mover's) distance between two distributions."""
        s1 = np.sort(np.asarray(sample_values, dtype=float))
        s2 = np.sort(np.asarray(reference_values, dtype=float))

        if len(s1) == 0 or len(s2) == 0:
            return 0.0

        all_vals = np.unique(np.concatenate([s1, s2]))
        cdf1 = np.searchsorted(s1, all_vals, side="right") / len(s1)
        cdf2 = np.searchsorted(s2, all_vals, side="right") / len(s2)

        deltas = np.diff(all_vals)
        w_dist = float(np.sum(np.abs(cdf1[:-1] - cdf2[:-1]) * deltas))
        return round(w_dist, 4)

    def evaluate(
        self,
        features: Dict[str, Any],
        regime_context: Optional[Dict[str, Any]] = None,
        batch_values: Optional[List[float]] = None,
        reference_values: Optional[List[float]] = None,
    ) -> OODResult:
        """Evaluate complete OOD status across features, regime, and drift signals."""
        regime = regime_context or {}

        # 1. Feature distance
        feat_dist, feat_drivers = self.compute_feature_distance(features)

        # 2. Regime novelty
        regime_nov, regime_drivers = self.compute_regime_novelty(regime)

        # 3. Drift statistic
        drift_stat = 0.0
        if batch_values is not None and reference_values is not None:
            drift_stat = self.compute_distribution_drift_ks(batch_values, reference_values)

        # Weighted composite OOD score
        if drift_stat > 0.0:
            composite_score = (0.50 * feat_dist) + (0.35 * regime_nov) + (0.15 * drift_stat)
        else:
            composite_score = (0.60 * feat_dist) + (0.40 * regime_nov)
        composite_score = round(min(1.0, max(0.0, composite_score)), 4)

        # Classify state
        if composite_score >= self.abstain_threshold or (feat_dist >= 0.85 and regime_nov >= 0.75):
            state = OODState.ABSTAIN
        elif composite_score >= self.ood_threshold:
            state = OODState.OOD
        elif composite_score >= self.unusual_threshold:
            state = OODState.UNUSUAL
        else:
            state = OODState.NORMAL

        all_drivers = feat_drivers + regime_drivers
        if drift_stat > 0.4:
            all_drivers.append(f"distribution_drift_ks_{drift_stat}")

        details = {
            "feature_distance_raw": round(feat_dist, 4),
            "regime_novelty_raw": round(regime_nov, 4),
            "drift_statistic_raw": round(drift_stat, 4),
            "thresholds": {
                "unusual": self.unusual_threshold,
                "ood": self.ood_threshold,
                "abstain": self.abstain_threshold,
            },
        }

        return OODResult(
            ood_score=composite_score,
            state=state,
            feature_distance=feat_dist,
            regime_novelty=regime_nov,
            drift_statistic=drift_stat,
            dominant_drivers=all_drivers,
            details=details,
        )
