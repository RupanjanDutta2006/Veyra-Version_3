"""Operational Burden and Alert Fatigue Metrics (§18.1, File 080, File 088).

Implements operational warning burden metrics:
- False alerts per forecast cycle (alarming without bust occurrence).
- Alert persistence & flicker rate (warning flip-flop across sequential cycles).
- Forecaster review-time estimates (hours spent reviewing flagged / ambiguous cases).
- Recall at fixed alert budgets (5%, 10%, 20% alert budgets).
"""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


MINUTES_PER_ALERT_REVIEW = 15.0  # 15 minutes per flagged case for forecaster review


@dataclass
class OperationalBurdenReport:
    """Comprehensive forecaster operational burden report (§18.1)."""

    total_samples: int
    total_cycles: int
    decision_threshold: float
    total_alerts: int
    false_alerts: int
    false_alerts_per_cycle: float
    alert_rate: float
    alert_persistence_rate: Optional[float]
    alert_flicker_rate: Optional[float]
    estimated_review_time_hours: float
    estimated_review_hours_per_cycle: float
    recall_at_5pct_budget: float
    recall_at_10pct_budget: float
    recall_at_20pct_budget: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_samples": self.total_samples,
            "total_cycles": self.total_cycles,
            "decision_threshold": round(self.decision_threshold, 4),
            "total_alerts": self.total_alerts,
            "false_alerts": self.false_alerts,
            "false_alerts_per_cycle": round(self.false_alerts_per_cycle, 4),
            "alert_rate": round(self.alert_rate, 4),
            "alert_persistence_rate": round(self.alert_persistence_rate, 4) if self.alert_persistence_rate is not None else None,
            "alert_flicker_rate": round(self.alert_flicker_rate, 4) if self.alert_flicker_rate is not None else None,
            "estimated_review_time_hours": round(self.estimated_review_time_hours, 2),
            "estimated_review_hours_per_cycle": round(self.estimated_review_hours_per_cycle, 2),
            "recall_at_5pct_budget": round(self.recall_at_5pct_budget, 4),
            "recall_at_10pct_budget": round(self.recall_at_10pct_budget, 4),
            "recall_at_20pct_budget": round(self.recall_at_20pct_budget, 4),
        }


def compute_fixed_budget_recall(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    budget_pct: float,
) -> float:
    """Compute recall when exactly budget_pct fraction of cases are flagged as alerts.

    Args:
        y_true: Binary ground truth labels (1=bust).
        y_prob: Model predicted probabilities.
        budget_pct: Fraction of total cases allowed to alert (e.g. 0.05, 0.10, 0.20).

    Returns:
        Recall at fixed alert budget in [0.0, 1.0].
    """
    y_t = np.asarray(y_true, dtype=np.int64)
    y_p = np.asarray(y_prob, dtype=np.float64)

    total_busts = int(np.sum(y_t == 1))
    if total_busts == 0:
        return 1.0

    n = len(y_t)
    if n == 0:
        return 0.0

    # Number of cases to flag
    k = max(1, int(round(n * budget_pct)))
    # Top-k indices by predicted probability
    top_k_indices = np.argsort(y_p)[::-1][:k]

    busts_caught = int(np.sum(y_t[top_k_indices] == 1))
    return float(busts_caught / total_busts)


def compute_alert_persistence_and_flicker(
    trajectories: list[list[bool]],
) -> Tuple[Optional[float], Optional[float]]:
    """Compute alert persistence and flicker rate across sequential forecast updates.

    Args:
        trajectories: List of boolean sequences [alert_t0, alert_t1, alert_t2, ...],
                      each representing sequential forecasts for the same valid verification time.

    Returns:
        (persistence_rate, flicker_rate)
    """
    total_active_transitions = 0
    persisted_transitions = 0
    total_state_transitions = 0
    flicker_transitions = 0

    for seq in trajectories:
        if len(seq) < 2:
            continue
        for i in range(len(seq) - 1):
            curr_state = seq[i]
            next_state = seq[i + 1]
            total_state_transitions += 1

            if curr_state != next_state:
                flicker_transitions += 1

            if curr_state:  # Alert was active
                total_active_transitions += 1
                if next_state:  # Alert persisted
                    persisted_transitions += 1

    persistence_rate = (
        float(persisted_transitions / total_active_transitions)
        if total_active_transitions > 0
        else None
    )
    flicker_rate = (
        float(flicker_transitions / total_state_transitions)
        if total_state_transitions > 0
        else None
    )

    return persistence_rate, flicker_rate


class OperationalBurdenEvaluator:
    """Evaluates forecaster workload, warning fatigue, and alert budget efficiency."""

    @classmethod
    def evaluate(
        cls,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        cycle_ids: Optional[list[Union[str, int]]] = None,
        decision_threshold: float = 0.5,
        sequential_trajectories: Optional[list[list[bool]]] = None,
        minutes_per_review: float = MINUTES_PER_ALERT_REVIEW,
    ) -> OperationalBurdenReport:
        """Run comprehensive operational burden evaluation."""
        y_t = np.asarray(y_true, dtype=np.int64)
        y_p = np.asarray(y_prob, dtype=np.float64)

        n = len(y_t)
        if n == 0:
            return OperationalBurdenReport(
                total_samples=0,
                total_cycles=0,
                decision_threshold=decision_threshold,
                total_alerts=0,
                false_alerts=0,
                false_alerts_per_cycle=0.0,
                alert_rate=0.0,
                alert_persistence_rate=None,
                alert_flicker_rate=None,
                estimated_review_time_hours=0.0,
                estimated_review_hours_per_cycle=0.0,
                recall_at_5pct_budget=0.0,
                recall_at_10pct_budget=0.0,
                recall_at_20pct_budget=0.0,
            )

        alerts = y_p >= decision_threshold
        total_alerts = int(np.sum(alerts))
        false_alerts = int(np.sum(alerts & (y_t == 0)))
        alert_rate = float(total_alerts / n)

        # Cycles
        if cycle_ids is not None and len(cycle_ids) == n:
            unique_cycles = len(set(cycle_ids))
        else:
            # Fallback: estimate cycles assuming ~24 forecasts per cycle (e.g. 24h lead steps)
            unique_cycles = max(1, int(round(n / 24.0)))

        false_alerts_per_cycle = float(false_alerts / unique_cycles) if unique_cycles > 0 else 0.0

        # Review time: each flagged alert takes minutes_per_review
        total_review_hours = (total_alerts * minutes_per_review) / 60.0
        review_hours_per_cycle = total_review_hours / unique_cycles if unique_cycles > 0 else 0.0

        # Persistence & flicker
        pers_rate, flick_rate = None, None
        if sequential_trajectories is not None:
            pers_rate, flick_rate = compute_alert_persistence_and_flicker(sequential_trajectories)

        # Recall at fixed alert budgets
        r_5 = compute_fixed_budget_recall(y_t, y_p, budget_pct=0.05)
        r_10 = compute_fixed_budget_recall(y_t, y_p, budget_pct=0.10)
        r_20 = compute_fixed_budget_recall(y_t, y_p, budget_pct=0.20)

        return OperationalBurdenReport(
            total_samples=n,
            total_cycles=unique_cycles,
            decision_threshold=decision_threshold,
            total_alerts=total_alerts,
            false_alerts=false_alerts,
            false_alerts_per_cycle=false_alerts_per_cycle,
            alert_rate=alert_rate,
            alert_persistence_rate=pers_rate,
            alert_flicker_rate=flick_rate,
            estimated_review_time_hours=total_review_hours,
            estimated_review_hours_per_cycle=review_hours_per_cycle,
            recall_at_5pct_budget=r_5,
            recall_at_10pct_budget=r_10,
            recall_at_20pct_budget=r_20,
        )
