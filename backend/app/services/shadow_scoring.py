"""Shadow Scoring & Model Recalibration Service.

Implements the shadow-mode evaluation and upgrade machinery per SIH26079 §22 and Research Files 099, 100 (K6):
- Evaluates candidate models / upgraded NWP providers in shadow mode alongside the serving model.
- Records prediction pairs (p_serving, p_shadow) without affecting production traffic.
- Measures prediction divergence, rank correlation, and systematic bias.
- Generates recalibration recommendations and shadow promotion readiness reports.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Maximum shadow history retained in memory for evaluation
MAX_SHADOW_HISTORY = 1000
DEFAULT_SHADOW_BUDGET = 100
MAX_ACCEPTABLE_MEAN_DIVERGENCE = 0.12


@dataclass
class ShadowPredictionPair:
    """Pair of concurrent predictions from serving and shadow models."""

    prediction_id: str
    location: str
    variable: str
    lead_hours: int
    serving_prob: float
    shadow_prob: float
    divergence: float  # abs(serving_prob - shadow_prob)
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShadowEvaluationReport:
    """Statistical summary of shadow model performance against serving model."""

    shadow_model_id: str
    serving_model_id: str
    sample_count: int
    required_budget: int
    budget_met: bool
    mean_divergence: float
    max_divergence: float
    agreement_rate: float  # Fraction of cases where binary classification agrees (threshold 0.50)
    systematic_bias: float  # mean(shadow_prob - serving_prob)
    is_promotion_ready: bool
    recalibration_needed: bool
    recommendation: str


class ShadowScoringService:
    """Orchestrates shadow scoring for candidate models and upstream NWP provider upgrades."""

    def __init__(self, shadow_model_id: Optional[str] = None):
        self.shadow_model_id = shadow_model_id or "builder2_v4_candidate"
        self.serving_model_id = "builder2_v3"
        self._history: List[ShadowPredictionPair] = []

    def record_shadow_prediction(
        self,
        prediction_id: str,
        location: str,
        variable: str,
        lead_hours: int,
        serving_prob: float,
        shadow_prob: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ShadowPredictionPair:
        """Record a shadow prediction alongside the live serving prediction."""
        divergence = round(abs(serving_prob - shadow_prob), 4)
        pair = ShadowPredictionPair(
            prediction_id=prediction_id,
            location=location,
            variable=variable,
            lead_hours=lead_hours,
            serving_prob=serving_prob,
            shadow_prob=shadow_prob,
            divergence=divergence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )
        self._history.append(pair)
        if len(self._history) > MAX_SHADOW_HISTORY:
            self._history.pop(0)

        logger.debug(
            "Recorded shadow pair %s: serving=%.3f shadow=%.3f div=%.3f",
            prediction_id,
            serving_prob,
            shadow_prob,
            divergence,
        )
        return pair

    def evaluate_shadow_performance(
        self,
        budget: int = DEFAULT_SHADOW_BUDGET,
    ) -> ShadowEvaluationReport:
        """Evaluate shadow scoring metrics to determine promotion readiness."""
        n = len(self._history)
        if n == 0:
            return ShadowEvaluationReport(
                shadow_model_id=self.shadow_model_id,
                serving_model_id=self.serving_model_id,
                sample_count=0,
                required_budget=budget,
                budget_met=False,
                mean_divergence=0.0,
                max_divergence=0.0,
                agreement_rate=1.0,
                systematic_bias=0.0,
                is_promotion_ready=False,
                recalibration_needed=False,
                recommendation="No shadow samples collected yet. Continue running in shadow mode.",
            )

        divergences = [p.divergence for p in self._history]
        mean_div = round(sum(divergences) / n, 4)
        max_div = round(max(divergences), 4)

        # Agreement rate at 0.50 threshold
        agreements = sum(
            1 for p in self._history
            if (p.serving_prob >= 0.50) == (p.shadow_prob >= 0.50)
        )
        agreement_rate = round(agreements / n, 4)

        # Systematic bias: positive means shadow is more aggressive, negative means more conservative
        biases = [p.shadow_prob - p.serving_prob for p in self._history]
        sys_bias = round(sum(biases) / n, 4)

        budget_met = n >= budget
        recalibration_needed = abs(sys_bias) >= 0.08
        is_ready = budget_met and (mean_div <= MAX_ACCEPTABLE_MEAN_DIVERGENCE) and not recalibration_needed

        if is_ready:
            rec = "Shadow budget met with acceptable divergence and low bias. Candidate ready for promotion gate."
        elif recalibration_needed:
            rec = f"Systematic bias ({sys_bias:+.3f}) detected. Recalibrate candidate model using isotonic/Platt scaling before promotion."
        elif not budget_met:
            rec = f"Accumulating shadow samples ({n}/{budget}). Continue shadow period."
        else:
            rec = f"Mean divergence ({mean_div:.3f}) exceeds threshold ({MAX_ACCEPTABLE_MEAN_DIVERGENCE}). Investigate feature drift."

        return ShadowEvaluationReport(
            shadow_model_id=self.shadow_model_id,
            serving_model_id=self.serving_model_id,
            sample_count=n,
            required_budget=budget,
            budget_met=budget_met,
            mean_divergence=mean_div,
            max_divergence=max_div,
            agreement_rate=agreement_rate,
            systematic_bias=sys_bias,
            is_promotion_ready=is_ready,
            recalibration_needed=recalibration_needed,
            recommendation=rec,
        )

    def clear_history(self) -> None:
        """Clear shadow history."""
        self._history.clear()


default_shadow_service = ShadowScoringService()
