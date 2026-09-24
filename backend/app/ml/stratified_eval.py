"""Stratified Evaluation Engine for Forecast-Bust Sentinel (§18.1, File 086, File 089).

Disaggregates model performance across all operational meteorological dimensions:
- Season: DJF (Winter), MAM (Pre-Monsoon), JJAS (Southwest Monsoon), ON (Post-Monsoon).
- Lead horizon: 24h, 48h, 72h, 120h, 240h.
- Geographic Region: IN_NORTH, IN_SOUTH, IN_WEST, IN_EAST, IN_CENTRAL, IN_NORTHEAST.
- Weather Variable: 2m_temperature, 10m_wind_speed, total_precipitation, geopotential_height_500hPa.
- Synoptic Regime: ACTIVE_MONSOON, BREAK_MONSOON, WESTERN_DISTURBANCE, CYCLONIC, QUIET.
- Forecast Provider: GEFS, ECMWF, WB2.
- Model Version: v1.0, v2.0, v3.0.
"""
from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional, Union
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)


MIN_SAMPLES_SUFFICIENT = 30
MIN_BUSTS_SUFFICIENT = 5


@dataclass
class StratumMetrics:
    """Evaluation metrics for a single slice / stratum."""

    dimension: str  # e.g. "season", "lead_time_hours", "region", "variable", "regime"
    stratum_value: str  # e.g. "JJAS", "48h", "IN_NORTH", "2m_temperature"
    sample_count: int
    bust_count: int
    bust_prevalence: float
    status: str  # "SUFFICIENT" or "SPARSE"

    pr_auc: Optional[float] = None
    roc_auc: Optional[float] = None
    brier_score: Optional[float] = None
    log_loss_value: Optional[float] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    ece: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "stratum_value": self.stratum_value,
            "sample_count": self.sample_count,
            "bust_count": self.bust_count,
            "bust_prevalence": round(self.bust_prevalence, 4),
            "status": self.status,
            "pr_auc": round(self.pr_auc, 4) if self.pr_auc is not None else None,
            "roc_auc": round(self.roc_auc, 4) if self.roc_auc is not None else None,
            "brier_score": round(self.brier_score, 4) if self.brier_score is not None else None,
            "log_loss_value": round(self.log_loss_value, 4) if self.log_loss_value is not None else None,
            "accuracy": round(self.accuracy, 4) if self.accuracy is not None else None,
            "precision": round(self.precision, 4) if self.precision is not None else None,
            "recall": round(self.recall, 4) if self.recall is not None else None,
            "f1_score": round(self.f1_score, 4) if self.f1_score is not None else None,
            "ece": round(self.ece, 4) if self.ece is not None else None,
        }


@dataclass
class StratifiedEvaluationReport:
    """Comprehensive multi-dimensional stratification report."""

    total_samples: int
    total_busts: int
    dimensions: list[str]
    strata: dict[str, list[StratumMetrics]] = field(default_factory=dict)
    sparse_strata_count: int = 0
    worst_performing_strata: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_samples": self.total_samples,
            "total_busts": self.total_busts,
            "dimensions": self.dimensions,
            "strata": {dim: [s.to_dict() for s in s_list] for dim, s_list in self.strata.items()},
            "sparse_strata_count": self.sparse_strata_count,
            "worst_performing_strata": self.worst_performing_strata,
        }


def month_to_season(month: int) -> str:
    """Map calendar month (1-12) to Indian meteorological season."""
    if month in (12, 1, 2):
        return "DJF"  # Winter
    elif month in (3, 4, 5):
        return "MAM"  # Pre-monsoon
    elif month in (6, 7, 8, 9):
        return "JJAS"  # Southwest Monsoon
    elif month in (10, 11):
        return "ON"  # Post-monsoon
    return "UNKNOWN"


def compute_stratum_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error for a stratum."""
    if len(y_true) == 0:
        return 0.0
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        mask = (y_prob >= bin_edges[b]) & (y_prob <= bin_edges[b + 1]) if b == n_bins - 1 else (y_prob >= bin_edges[b]) & (y_prob < bin_edges[b + 1])
        cnt = int(np.sum(mask))
        if cnt > 0:
            diff = abs(float(np.mean(y_true[mask])) - float(np.mean(y_prob[mask])))
            ece += diff * (cnt / n)
    return float(ece)


class StratifiedEvaluator:
    """Disaggregates forecast verification metrics across meteorological and operational strata."""

    STANDARD_DIMENSIONS = [
        "season",
        "lead_time_hours",
        "region",
        "variable",
        "regime",
        "provider",
        "model_version",
    ]

    @classmethod
    def evaluate_stratum(
        cls,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        dimension: str,
        stratum_value: str,
        decision_threshold: float = 0.5,
    ) -> StratumMetrics:
        """Compute metrics for a single slice of data."""
        y_t = np.asarray(y_true, dtype=np.int64)
        y_p = np.asarray(y_prob, dtype=np.float64)

        n = len(y_t)
        n_bust = int(np.sum(y_t == 1))
        prevalence = float(n_bust / n) if n > 0 else 0.0
        status = "SUFFICIENT" if (n >= MIN_SAMPLES_SUFFICIENT and n_bust >= MIN_BUSTS_SUFFICIENT) else "SPARSE"

        if n == 0:
            return StratumMetrics(
                dimension=dimension,
                stratum_value=stratum_value,
                sample_count=0,
                bust_count=0,
                bust_prevalence=0.0,
                status="EMPTY",
            )

        y_pred = (y_p >= decision_threshold).astype(np.int64)
        tp = int(np.sum((y_t == 1) & (y_pred == 1)))
        fp = int(np.sum((y_t == 0) & (y_pred == 1)))
        tn = int(np.sum((y_t == 0) & (y_pred == 0)))
        fn = int(np.sum((y_t == 1) & (y_pred == 0)))

        acc = float((tp + tn) / n)
        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2.0 * (prec * rec) / (prec + rec)) if (prec + rec) > 0 else 0.0

        # Probabilistic metrics
        has_both = len(np.unique(y_t)) > 1
        pr_auc: Optional[float] = None
        roc_auc: Optional[float] = None
        if has_both:
            try:
                pr_auc = float(average_precision_score(y_t, y_p))
            except Exception:
                pr_auc = None
            try:
                roc_auc = float(roc_auc_score(y_t, y_p))
            except Exception:
                roc_auc = None

        try:
            brier = float(brier_score_loss(y_t, y_p))
        except Exception:
            brier = None

        try:
            p_safe = np.clip(y_p, 1e-15, 1.0 - 1e-15)
            ll = float(log_loss(y_t, p_safe))
        except Exception:
            ll = None

        ece_val = compute_stratum_ece(y_t, y_p)

        return StratumMetrics(
            dimension=dimension,
            stratum_value=stratum_value,
            sample_count=n,
            bust_count=n_bust,
            bust_prevalence=prevalence,
            status=status,
            pr_auc=pr_auc,
            roc_auc=roc_auc,
            brier_score=brier,
            log_loss_value=ll,
            accuracy=acc,
            precision=prec,
            recall=rec,
            f1_score=f1,
            ece=ece_val,
        )

    @classmethod
    def evaluate_records(
        cls,
        records: list[dict[str, Any]],
        dimensions: Optional[list[str]] = None,
        target_field: str = "bust",
        prob_field: str = "p_bust",
        decision_threshold: float = 0.5,
    ) -> StratifiedEvaluationReport:
        """Run stratified evaluation over a collection of forecast verification records.

        Each record must contain `target_field`, `prob_field`, and dimension keys.
        """
        if dimensions is None:
            dimensions = cls.STANDARD_DIMENSIONS

        total_samples = len(records)
        total_busts = sum(1 for r in records if int(r.get(target_field, 0)) == 1)

        strata_by_dim: dict[str, list[StratumMetrics]] = {}
        sparse_count = 0
        worst_strata: list[dict[str, Any]] = []

        for dim in dimensions:
            # Group records by stratum value
            groups: dict[str, list[dict[str, Any]]] = {}
            for r in records:
                val = str(r.get(dim, "UNKNOWN"))
                if val not in groups:
                    groups[val] = []
                groups[val].append(r)

            stratum_metrics_list: list[StratumMetrics] = []
            for val, group in sorted(groups.items()):
                y_t = np.array([int(r[target_field]) for r in group], dtype=np.int64)
                y_p = np.array([float(r[prob_field]) for r in group], dtype=np.float64)

                m = cls.evaluate_stratum(
                    y_true=y_t,
                    y_prob=y_p,
                    dimension=dim,
                    stratum_value=val,
                    decision_threshold=decision_threshold,
                )
                stratum_metrics_list.append(m)
                if m.status == "SPARSE":
                    sparse_count += 1

                # Track slices with notable degradation (low PR-AUC or high Brier)
                if m.pr_auc is not None and m.sample_count >= 10:
                    worst_strata.append({
                        "dimension": dim,
                        "stratum": val,
                        "sample_count": m.sample_count,
                        "bust_count": m.bust_count,
                        "pr_auc": round(m.pr_auc, 4),
                        "brier_score": round(m.brier_score, 4) if m.brier_score is not None else None,
                    })

            strata_by_dim[dim] = stratum_metrics_list

        # Sort worst strata by pr_auc ascending
        worst_strata.sort(key=lambda x: x["pr_auc"])

        return StratifiedEvaluationReport(
            total_samples=total_samples,
            total_busts=total_busts,
            dimensions=dimensions,
            strata=strata_by_dim,
            sparse_strata_count=sparse_count,
            worst_performing_strata=worst_strata[:10],
        )
