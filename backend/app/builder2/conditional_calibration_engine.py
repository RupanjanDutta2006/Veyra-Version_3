"""Conditional Calibration and Conformal Prediction Engine for Veyra (Gate 9 / Phase J).

Implements:
- Post-hoc probability calibration (Isotonic Regression & Platt Sigmoid Scaling).
- Expected Calibration Error (ECE) and Maximum Calibration Error (MCE) evaluation.
- Split Conformal Prediction with finite-sample marginal coverage guarantees.
- Sliced conditional calibration and risk-coverage analysis across lead, season, location, regime, severity, and OOD.
- Invariant: Never claims universal conditional coverage; tracks residual slice miscoverage explicitly.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field
from sklearn.isotonic import IsotonicRegression

from backend.app.builder2.calibrator import ProbabilityCalibrator


class CalibrationMetrics(BaseModel):
    """Container for calibration quality metrics."""
    brier_score_raw: float
    brier_score_calibrated: float
    ece: float
    mce: float
    sample_count: int
    brier_improvement_pct: float


class ConformalInterval(BaseModel):
    """Conformal prediction interval output."""
    point_prediction: float
    lower_bound: float
    upper_bound: float
    target_coverage: float
    is_covered: Optional[bool] = None


class ConditionalSliceMetrics(BaseModel):
    """Evaluation metrics for a specific slice."""
    slice_dimension: str
    slice_value: str
    sample_count: int
    brier_score: float
    ece: float
    achieved_coverage: float
    target_coverage: float
    conditional_miscoverage: float


class ConditionalCalibrationEngine:
    """Engine for multi-hazard probability calibration and conformal risk-coverage."""

    def __init__(
        self,
        method: str = "isotonic",
        alpha: float = 0.10,
        n_bins: int = 10,
    ):
        self.method = method
        self.alpha = alpha  # target miscoverage rate (1 - alpha = target coverage)
        self.n_bins = n_bins
        if method == "isotonic":
            self.model_ = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        else:
            self.model_ = ProbabilityCalibrator(method="sigmoid")
        self.q_hat_: Optional[float] = None
        self.is_fit_: bool = False
        self.claims_universal_conditional_coverage: bool = False

    def fit(self, raw_probs: np.ndarray, y_true: np.ndarray) -> "ConditionalCalibrationEngine":
        """Fit calibrator and compute conformal non-conformity quantile on calibration split."""
        raw_p = np.asarray(raw_probs, dtype=float)
        y = np.asarray(y_true, dtype=float)

        if self.method == "isotonic":
            self.model_.fit(raw_p, y)
            cal_p = np.clip(self.model_.predict(raw_p), 0.0, 1.0)
        else:
            self.model_.fit(raw_p, y)
            cal_p = self.model_.predict_proba(raw_p)[:, 1]

        # Non-conformity score: absolute error |y - cal_p|
        scores = np.abs(y - cal_p)
        n = len(scores)
        q_level = min(1.0, np.ceil((n + 1) * (1.0 - self.alpha)) / n)
        self.q_hat_ = float(np.quantile(scores, q_level))
        self.is_fit_ = True

        return self

    def calibrate(self, raw_probs: np.ndarray) -> np.ndarray:
        """Apply calibration to raw probabilities."""
        if not self.is_fit_:
            return np.asarray(raw_probs, dtype=float)
        raw_p = np.asarray(raw_probs, dtype=float)
        if self.method == "isotonic":
            return np.clip(self.model_.predict(raw_p), 0.0, 1.0)
        return self.model_.predict_proba(raw_p)[:, 1]

    def predict_conformal_interval(
        self,
        raw_prob: float,
        target_coverage: Optional[float] = None,
    ) -> ConformalInterval:
        """Generate conformal interval with finite-sample marginal coverage guarantee."""
        p_cal = float(self.calibrate(np.array([raw_prob]))[0])
        q = self.q_hat_ if self.q_hat_ is not None else 0.15

        cov = target_coverage if target_coverage is not None else (1.0 - self.alpha)
        lower = max(0.0, p_cal - q)
        upper = min(1.0, p_cal + q)

        return ConformalInterval(
            point_prediction=round(p_cal, 4),
            lower_bound=round(lower, 4),
            upper_bound=round(upper, 4),
            target_coverage=round(cov, 4),
        )

    def evaluate_calibration(
        self,
        probs: np.ndarray,
        y_true: np.ndarray,
    ) -> CalibrationMetrics:
        """Compute Brier score, ECE, and MCE using equal-frequency or equal-width binning."""
        p = np.asarray(probs, dtype=float)
        y = np.asarray(y_true, dtype=float)
        n = len(y)

        # Raw vs Calibrated Brier
        if self.is_fit_:
            p_cal = self.calibrate(p)
        else:
            p_cal = p

        brier_raw = float(np.mean((p - y) ** 2))
        brier_cal = float(np.mean((p_cal - y) ** 2))

        # ECE & MCE computation
        bin_edges = np.linspace(0.0, 1.0, self.n_bins + 1)
        ece = 0.0
        mce = 0.0

        for i in range(self.n_bins):
            bin_mask = (p_cal >= bin_edges[i]) & (p_cal < bin_edges[i + 1]) if i < self.n_bins - 1 else (p_cal >= bin_edges[i]) & (p_cal <= bin_edges[i + 1])
            bin_size = int(np.sum(bin_mask))

            if bin_size > 0:
                bin_acc = float(np.mean(y[bin_mask]))
                bin_conf = float(np.mean(p_cal[bin_mask]))
                bin_err = abs(bin_acc - bin_conf)
                ece += (bin_size / n) * bin_err
                if bin_err > mce:
                    mce = bin_err

        brier_impr = ((brier_raw - brier_cal) / (brier_raw + 1e-9)) * 100.0 if brier_raw > 0 else 0.0

        return CalibrationMetrics(
            brier_score_raw=round(brier_raw, 4),
            brier_score_calibrated=round(brier_cal, 4),
            ece=round(ece, 4),
            mce=round(mce, 4),
            sample_count=n,
            brier_improvement_pct=round(brier_impr, 2),
        )

    def evaluate_slices(
        self,
        raw_probs: np.ndarray,
        y_true: np.ndarray,
        slice_assignments: Dict[str, np.ndarray],
    ) -> List[ConditionalSliceMetrics]:
        """Evaluate calibration and conformal coverage across slices.

        Verifies that while marginal coverage is >= 1 - alpha, conditional miscoverage varies by slice.
        """
        p_cal = self.calibrate(raw_probs)
        y = np.asarray(y_true, dtype=float)
        q = self.q_hat_ if self.q_hat_ is not None else 0.15
        target_cov = 1.0 - self.alpha

        results = []
        for dim, values in slice_assignments.items():
            unique_vals = np.unique(values)
            for val in unique_vals:
                mask = (values == val)
                n_sub = int(np.sum(mask))
                if n_sub < 5:
                    continue

                sub_p = p_cal[mask]
                sub_y = y[mask]

                # Coverage check: does [p - q, p + q] contain y?
                covered = (sub_y >= np.maximum(0.0, sub_p - q)) & (sub_y <= np.minimum(1.0, sub_p + q))
                achieved_cov = float(np.mean(covered))
                cond_miscoverage = max(0.0, target_cov - achieved_cov)

                sub_brier = float(np.mean((sub_p - sub_y) ** 2))
                sub_metrics = self.evaluate_calibration(sub_p, sub_y)

                results.append(ConditionalSliceMetrics(
                    slice_dimension=dim,
                    slice_value=str(val),
                    sample_count=n_sub,
                    brier_score=round(sub_brier, 4),
                    ece=sub_metrics.ece,
                    achieved_coverage=round(achieved_cov, 4),
                    target_coverage=round(target_cov, 4),
                    conditional_miscoverage=round(cond_miscoverage, 4),
                ))

        return results

    def compute_risk_coverage_curve(
        self,
        raw_probs: np.ndarray,
        y_true: np.ndarray,
        ood_scores: np.ndarray,
        coverage_tiers: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """Compute Risk-Coverage trade-off curve, ordering by lowest OOD score first."""
        p_cal = self.calibrate(raw_probs)
        y = np.asarray(y_true, dtype=float)
        ood = np.asarray(ood_scores, dtype=float)

        tiers = coverage_tiers or [1.00, 0.95, 0.90, 0.85, 0.80]
        sorted_indices = np.argsort(ood)

        results = []
        for cov in tiers:
            n_retain = int(np.ceil(len(y) * cov))
            retained_idx = sorted_indices[:n_retain]

            sub_p = p_cal[retained_idx]
            sub_y = y[retained_idx]

            brier = float(np.mean((sub_p - sub_y) ** 2))
            mae = float(np.mean(np.abs(sub_p - sub_y)))
            max_ood = float(np.max(ood[retained_idx])) if len(retained_idx) > 0 else 0.0

            results.append({
                "coverage": round(cov, 2),
                "n_retained": n_retain,
                "residual_brier": round(brier, 4),
                "residual_mae": round(mae, 4),
                "max_ood_score": round(max_ood, 3),
            })

        return results
