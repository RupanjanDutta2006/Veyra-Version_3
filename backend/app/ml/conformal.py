"""Split Conformal Prediction Engine for Forecast-Bust Uncertainty Intervals.

Implements the official SIH26079 Conformal Prediction Protocol (§11.2):
- Finite-sample coverage under exchangeability assumptions.
- Split-conformal calibration on held-out temporal validation blocks.
- Non-conformity scoring: s_i = |y_i - p_hat_i|.
- Conditional coverage evaluation across lead times (24h, 48h, 72h, 120h) and regions.
- Explicit method declaration:
  "Empirical or assumption-conditional coverage was evaluated; universal guarantees
   under nonstationary atmospheric shift are not claimed."
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


METHOD_DECLARATION: str = (
    "Empirical split-conformal prediction intervals under exchangeability assumption. "
    "Empirical or assumption-conditional coverage was evaluated; universal guarantees "
    "under nonstationary atmospheric shift are not claimed."
)


@dataclass
class ConformalInterval:
    """Bounded conformal prediction interval for a single forecast bust prediction."""

    probability: float
    lower_bound: float
    upper_bound: float
    bandwidth: float
    confidence_level: float
    alpha: float
    method: str = METHOD_DECLARATION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "probability": round(self.probability, 4),
            "lower_bound": round(self.lower_bound, 4),
            "upper_bound": round(self.upper_bound, 4),
            "bandwidth": round(self.bandwidth, 4),
            "confidence_level": round(self.confidence_level, 3),
            "alpha": round(self.alpha, 3),
            "method": self.method,
        }


@dataclass
class ConformalCoverageReport:
    """Comprehensive empirical and conditional coverage evaluation report (§11.2)."""

    nominal_coverage: float
    empirical_coverage: float
    sample_count: int
    mean_bandwidth: float
    conditional_coverage_by_lead: Dict[int, float] = field(default_factory=dict)
    conditional_coverage_by_region: Dict[str, float] = field(default_factory=dict)
    method_declaration: str = METHOD_DECLARATION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nominal_coverage": round(self.nominal_coverage, 3),
            "empirical_coverage": round(self.empirical_coverage, 4),
            "sample_count": self.sample_count,
            "mean_bandwidth": round(self.mean_bandwidth, 4),
            "conditional_coverage_by_lead": {
                int(k): round(v, 4) for k, v in self.conditional_coverage_by_lead.items()
            },
            "conditional_coverage_by_region": {
                str(k): round(v, 4) for k, v in self.conditional_coverage_by_region.items()
            },
            "method_declaration": self.method_declaration,
        }


class SplitConformalPredictor:
    """Split Conformal Predictor for calibrated probability bounds."""

    def __init__(self, confidence_level: float = 0.90):
        if not (0.50 < confidence_level < 1.0):
            raise ValueError(f"confidence_level must be in (0.50, 1.0), got {confidence_level}")
        self.confidence_level = confidence_level
        self.alpha = round(1.0 - confidence_level, 4)
        self.calibrated_quantile: Optional[float] = None
        self.n_calibration: int = 0
        self.is_calibrated: bool = False

    def calibrate(
        self,
        y_true: Union[List[int], np.ndarray],
        y_prob: Union[List[float], np.ndarray],
    ) -> "SplitConformalPredictor":
        """Calibrate non-conformity scores on a separate temporal validation/calibration set.

        Non-conformity score s_i = |y_i - p_hat_i|.
        Quantile level: ceil((n + 1) * (1 - alpha)) / n
        """
        y_t = np.asarray(y_true, dtype=int)
        y_p = np.asarray(y_prob, dtype=float)

        if len(y_t) != len(y_p):
            raise ValueError(f"Length mismatch: len(y_true)={len(y_t)} != len(y_prob)={len(y_p)}")
        n = len(y_t)
        if n < 5:
            raise ValueError(f"Need at least 5 calibration samples, got {n}")

        scores = np.abs(y_t - y_p)
        k = math.ceil((n + 1) * (1.0 - self.alpha))
        k = min(n, max(1, k))

        # 1-indexed k-th order statistic
        sorted_scores = np.sort(scores)
        q_hat = float(sorted_scores[k - 1])

        self.calibrated_quantile = q_hat
        self.n_calibration = n
        self.is_calibrated = True
        return self

    def predict_interval(self, probability: float) -> ConformalInterval:
        """Construct conformal prediction interval for a single probability estimate."""
        if not self.is_calibrated or self.calibrated_quantile is None:
            # Safe uncalibrated default: symmetric 0.15 margin
            q = 0.15
        else:
            q = self.calibrated_quantile

        lower = max(0.0, probability - q)
        upper = min(1.0, probability + q)
        bandwidth = upper - lower

        return ConformalInterval(
            probability=probability,
            lower_bound=round(lower, 4),
            upper_bound=round(upper, 4),
            bandwidth=round(bandwidth, 4),
            confidence_level=self.confidence_level,
            alpha=self.alpha,
            method=METHOD_DECLARATION,
        )

    def evaluate_coverage(
        self,
        y_true: Union[List[int], np.ndarray],
        y_prob: Union[List[float], np.ndarray],
        lead_hours: Optional[Union[List[int], np.ndarray]] = None,
        regions: Optional[Union[List[str], np.ndarray]] = None,
    ) -> ConformalCoverageReport:
        """Evaluate empirical and conditional coverage across test observations (§11.2)."""
        y_t = np.asarray(y_true, dtype=int)
        y_p = np.asarray(y_prob, dtype=float)
        n = len(y_t)
        if n == 0:
            return ConformalCoverageReport(
                nominal_coverage=self.confidence_level,
                empirical_coverage=0.0,
                sample_count=0,
                mean_bandwidth=0.0,
            )

        q = self.calibrated_quantile if (self.is_calibrated and self.calibrated_quantile is not None) else 0.15
        lowers = np.maximum(0.0, y_p - q)
        uppers = np.minimum(1.0, y_p + q)
        bandwidths = uppers - lowers

        # Empirical coverage: fraction of times true binary label y is contained in [lower, upper]
        # In probabilistic classification, coverage tests whether y_true is within thresholded interval
        covered = (y_t >= lowers) & (y_t <= uppers)
        overall_cov = float(np.mean(covered))

        # Conditional coverage by lead time
        cond_lead: Dict[int, float] = {}
        if lead_hours is not None and len(lead_hours) == n:
            leads_arr = np.asarray(lead_hours, dtype=int)
            for target_lead in [24, 48, 72, 96, 120, 144, 168]:
                mask = leads_arr == target_lead
                if np.sum(mask) > 0:
                    cond_lead[target_lead] = float(np.mean(covered[mask]))

        # Conditional coverage by region
        cond_region: Dict[str, float] = {}
        if regions is not None and len(regions) == n:
            reg_arr = np.asarray(regions, dtype=str)
            for reg in np.unique(reg_arr):
                mask = reg_arr == reg
                if np.sum(mask) > 0:
                    cond_region[str(reg)] = float(np.mean(covered[mask]))

        return ConformalCoverageReport(
            nominal_coverage=self.confidence_level,
            empirical_coverage=overall_cov,
            sample_count=n,
            mean_bandwidth=float(np.mean(bandwidths)),
            conditional_coverage_by_lead=cond_lead,
            conditional_coverage_by_region=cond_region,
            method_declaration=METHOD_DECLARATION,
        )
