"""Model Evaluation Metrics, Reliability Diagrams, and Verification Report Generator.

Implements the official SIH26079 Evaluation and Calibration Framework (§11.1, §11.4, §18.1):
- Standard discrimination metrics: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC.
- Probabilistic scoring: Brier Score, Log-Loss (Binary Cross-Entropy).
- Reliability Diagrams & Calibration Curves: 10-bin uniform/quantile binning.
- Calibration Diagnostics: Expected Calibration Error (ECE), Maximum Calibration Error (MCE),
  and Calibration Slope & Intercept (logistic calibration / Platt scaling fit).
- Selective Prediction: Coverage-Risk curves and Forecaster Review Burden metrics.
"""
from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)


@dataclass
class ConfusionMatrix:
    """Detailed confusion matrix breakdown."""

    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0  # CRITICAL: Actual BUST predicted as Non-Bust

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass
class ReliabilityDiagram:
    """Binned reliability diagram / calibration curve data (§11.1)."""

    prob_pred: list[float]
    prob_true: list[float]
    bin_counts: list[int]
    bin_edges: list[float]
    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error

    def to_dict(self) -> dict[str, Any]:
        return {
            "prob_pred": [round(float(v), 4) for v in self.prob_pred],
            "prob_true": [round(float(v), 4) for v in self.prob_true],
            "bin_counts": [int(c) for c in self.bin_counts],
            "bin_edges": [round(float(e), 4) for e in self.bin_edges],
            "ece": round(float(self.ece), 4),
            "mce": round(float(self.mce), 4),
        }


@dataclass
class EvaluationReport:
    """Comprehensive evaluation metrics report for model validation and testing."""

    split_name: str
    sample_count: int
    bust_count: int
    non_bust_count: int
    bust_prevalence: float

    accuracy: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    roc_auc: Optional[float]
    pr_auc: Optional[float] = None
    brier_score: Optional[float] = None
    log_loss_value: Optional[float] = None

    # Calibration diagnostics (§11.1)
    calibration_slope: Optional[float] = None
    calibration_intercept: Optional[float] = None
    expected_calibration_error: Optional[float] = None
    max_calibration_error: Optional[float] = None
    reliability_diagram: Optional[ReliabilityDiagram] = None

    # Selective prediction & review burden (§11.4)
    coverage_risk_curve: Optional[list[dict[str, Any]]] = None
    review_burden: Optional[dict[str, Any]] = None

    confusion_matrix: ConfusionMatrix = field(default_factory=ConfusionMatrix)
    is_calibrated: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


class ModelEvaluator:
    """Evaluates classification performance, probability calibration, and false negatives."""

    @staticmethod
    def compute_reliability_diagram(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        n_bins: int = 10,
    ) -> ReliabilityDiagram:
        """Compute binned empirical reliability diagram, ECE, and MCE (§11.1)."""
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        prob_pred: list[float] = []
        prob_true: list[float] = []
        bin_counts: list[int] = []

        total_samples = len(y_true)
        ece_accum = 0.0
        max_cal_err = 0.0

        for b in range(n_bins):
            lower = bin_edges[b]
            upper = bin_edges[b + 1]
            if b == n_bins - 1:
                mask = (y_prob >= lower) & (y_prob <= upper)
            else:
                mask = (y_prob >= lower) & (y_prob < upper)

            count = int(np.sum(mask))
            bin_counts.append(count)

            if count > 0:
                p_mean = float(np.mean(y_prob[mask]))
                y_mean = float(np.mean(y_true[mask]))
                prob_pred.append(round(p_mean, 4))
                prob_true.append(round(y_mean, 4))

                diff = abs(y_mean - p_mean)
                ece_accum += diff * (count / total_samples)
                if diff > max_cal_err:
                    max_cal_err = diff
            else:
                # Midpoint for empty bins
                prob_pred.append(round((lower + upper) / 2.0, 4))
                prob_true.append(0.0)

        return ReliabilityDiagram(
            prob_pred=prob_pred,
            prob_true=prob_true,
            bin_counts=bin_counts,
            bin_edges=[round(float(e), 4) for e in bin_edges],
            ece=round(ece_accum, 4),
            mce=round(max_cal_err, 4),
        )

    @staticmethod
    def compute_calibration_slope_intercept(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        eps: float = 1e-5,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Fit Platt / logistic calibration slope and intercept on logit scale.

        logit(y) ~ a * logit(p) + b
        Ideal calibrated: slope a = 1.0, intercept b = 0.0.
        """
        if len(np.unique(y_true)) < 2:
            return None, None

        # Clip probabilities to avoid log(0)
        p_clipped = np.clip(y_prob, eps, 1.0 - eps)
        logit_p = np.log(p_clipped / (1.0 - p_clipped))

        try:
            from sklearn.linear_model import LogisticRegression

            clf = LogisticRegression(solver="lbfgs", C=1e5, max_iter=200)
            clf.fit(logit_p.reshape(-1, 1), y_true)
            slope = round(float(clf.coef_[0][0]), 4)
            intercept = round(float(clf.intercept_[0]), 4)
            return slope, intercept
        except Exception:
            return None, None

    @classmethod
    def evaluate(
        cls,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        split_name: str = "validation",
        decision_threshold: float = 0.5,
        ood_scores: Optional[np.ndarray] = None,
        is_calibrated: bool = False,
    ) -> EvaluationReport:
        """Compute comprehensive evaluation metrics for binary bust prediction."""
        y_t = np.array(y_true, dtype=np.int64)
        y_p = np.array(y_proba, dtype=np.float64)
        y_pred = (y_p >= decision_threshold).astype(np.int64)

        n = len(y_t)
        n_bust = int(np.sum(y_t == 1))
        n_non_bust = int(np.sum(y_t == 0))
        prevalence = round(n_bust / n, 4) if n > 0 else 0.0

        # Confusion Matrix
        tp = int(np.sum((y_t == 1) & (y_pred == 1)))
        fp = int(np.sum((y_t == 0) & (y_pred == 1)))
        tn = int(np.sum((y_t == 0) & (y_pred == 0)))
        fn = int(np.sum((y_t == 1) & (y_pred == 0)))
        cm = ConfusionMatrix(true_positives=tp, false_positives=fp, true_negatives=tn, false_negatives=fn)

        # Accuracy
        acc = round((tp + tn) / n, 4) if n > 0 else 0.0

        # Precision & Recall
        prec = round(tp / (tp + fp), 4) if (tp + fp) > 0 else None
        rec = round(tp / (tp + fn), 4) if (tp + fn) > 0 else None

        # F1 Score
        if prec is not None and rec is not None and (prec + rec) > 0:
            f1 = round(2.0 * (prec * rec) / (prec + rec), 4)
        else:
            f1 = 0.0 if (prec is not None or rec is not None) else None

        # ROC-AUC (requires both classes)
        has_both_classes = len(np.unique(y_t)) > 1
        if has_both_classes:
            try:
                auc_val = round(float(roc_auc_score(y_t, y_p)), 4)
            except Exception:
                auc_val = None
            try:
                pr_auc_val = round(float(average_precision_score(y_t, y_p)), 4)
            except Exception:
                pr_auc_val = None
        else:
            auc_val = None
            pr_auc_val = None

        # Brier Score Loss: mean squared difference between P(bust) and binary label
        try:
            brier = round(float(brier_score_loss(y_t, y_p)), 4)
        except Exception:
            brier = None

        # Log Loss (Binary Cross-Entropy)
        try:
            p_safe = np.clip(y_p, 1e-15, 1.0 - 1e-15)
            log_loss_val = round(float(log_loss(y_t, p_safe)), 4)
        except Exception:
            log_loss_val = None

        # Calibration Diagnostics (§11.1)
        rel_diag: Optional[ReliabilityDiagram] = None
        cal_slope: Optional[float] = None
        cal_intercept: Optional[float] = None
        ece_val: Optional[float] = None
        mce_val: Optional[float] = None

        if n >= 5:
            rel_diag = cls.compute_reliability_diagram(y_t, y_p, n_bins=10)
            ece_val = rel_diag.ece
            mce_val = rel_diag.mce
            cal_slope, cal_intercept = cls.compute_calibration_slope_intercept(y_t, y_p)

        # Coverage-Risk & Review Burden (§11.4)
        from backend.app.safety.abstention import compute_coverage_risk_curve

        coverage_risk_points = compute_coverage_risk_curve(
            y_true=y_t,
            y_prob=y_p,
            uncertainty_or_ood_scores=ood_scores,
            threshold_steps=10,
        )
        cov_risk_list = [
            {
                "rejection_threshold": p.rejection_threshold,
                "coverage": p.coverage,
                "risk": p.risk,
                "abstention_rate": p.abstention_rate,
                "high_confidence_error_rate": p.high_confidence_error_rate,
                "review_burden_cases": p.review_burden_cases,
            }
            for p in coverage_risk_points
        ]

        review_burden_info = {
            "total_cases": n,
            "decision_threshold": decision_threshold,
            "ambiguous_cases_count": int(np.sum((y_p >= 0.35) & (y_p <= 0.65))),
            "ambiguous_fraction": round(float(np.mean((y_p >= 0.35) & (y_p <= 0.65))), 4) if n > 0 else 0.0,
            "estimated_review_burden_hours": round(float(np.sum((y_p >= 0.35) & (y_p <= 0.65))) * 0.25, 2),  # ~15 min / review
        }

        return EvaluationReport(
            split_name=split_name,
            sample_count=n,
            bust_count=n_bust,
            non_bust_count=n_non_bust,
            bust_prevalence=prevalence,
            accuracy=acc,
            precision=prec,
            recall=rec,
            f1_score=f1,
            roc_auc=auc_val,
            pr_auc=pr_auc_val,
            brier_score=brier,
            log_loss_value=log_loss_val,
            calibration_slope=cal_slope,
            calibration_intercept=cal_intercept,
            expected_calibration_error=ece_val,
            max_calibration_error=mce_val,
            reliability_diagram=rel_diag,
            coverage_risk_curve=cov_risk_list,
            review_burden=review_burden_info,
            confusion_matrix=cm,
            is_calibrated=is_calibrated,
        )
