"""Safety, OOD Detection, and Abstention Layer.

Implements the official SIH26079 Safety & Abstention Architecture (§11.3, §11.4):
- Explicit OOD State Vocabulary: NORMAL, UNUSUAL, OOD, ABSTAIN.
- Dynamic OOD scoring via OODDetector.
- High-confidence / Moderate / Low / Abstained trust state mapping.
- Coverage-risk curve evaluation and forecaster review burden metrics.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from backend.app.safety.ood_detector import OODDetector, OODResult, OODState
from backend.app.schemas.prediction import ReasonCode, RiskLevel, TrustState
from backend.app.services.base import (
    BaseSafetyService,
    FeatureResult,
    ModelResult,
    WeatherResult,
)


@dataclass
class SafetyAssessment:
    """Standard safety evaluation output controlling final trust state, OOD status, and abstention."""

    bust_probability: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    trust_state: TrustState = TrustState.UNAVAILABLE
    abstain: bool = True
    reason_codes: list[str] = field(
        default_factory=lambda: [ReasonCode.MODEL_NOT_READY.value]
    )
    ood_state: OODState = OODState.NORMAL
    ood_score: Optional[float] = None
    is_gray_band: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


# Alias for consistency
SafetyResult = SafetyAssessment


@dataclass
class CoverageRiskPoint:
    """Single point on an abstention policy coverage-risk curve."""

    rejection_threshold: float
    coverage: float  # Fraction of retained predictions: N_retained / N_total
    retained_count: int
    abstained_count: int
    abstention_rate: float  # N_abstained / N_total
    risk: float  # Brier score or error rate on retained predictions
    high_confidence_error_rate: float  # Errors on retained cases where p > 0.5
    review_burden_cases: int  # Cases sent for human review


def compute_coverage_risk_curve(
    y_true: Union[List[int], np.ndarray],
    y_prob: Union[List[float], np.ndarray],
    uncertainty_or_ood_scores: Optional[Union[List[float], np.ndarray]] = None,
    threshold_steps: int = 10,
) -> List[CoverageRiskPoint]:
    """Compute empirical coverage-risk curve across varying abstention thresholds (§11.4).

    As the abstention threshold becomes more strict, coverage decreases while
    risk (error on retained cases) should ideally decrease, quantifying the
    selective prediction capability of the sentinel.
    """
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.asarray(y_prob, dtype=float)
    n_total = len(y_t)
    if n_total == 0:
        return []

    # If no explicit uncertainty/OOD score is supplied, use distance from certainty: 1 - 2*|p - 0.5|
    if uncertainty_or_ood_scores is None:
        scores = 1.0 - 2.0 * np.abs(y_p - 0.5)
    else:
        scores = np.asarray(uncertainty_or_ood_scores, dtype=float)

    curve: List[CoverageRiskPoint] = []
    # Thresholds from 0.05 to 0.95
    rejection_thresholds = np.linspace(0.05, 0.95, threshold_steps)

    for thresh in rejection_thresholds:
        # Retain cases whose uncertainty/OOD score is below threshold
        retained_mask = scores < thresh
        n_retained = int(np.sum(retained_mask))
        n_abstained = n_total - n_retained

        cov = round(n_retained / n_total, 4)
        abst_rate = round(n_abstained / n_total, 4)

        if n_retained > 0:
            retained_true = y_t[retained_mask]
            retained_prob = y_p[retained_mask]
            # Brier risk on retained cases
            risk = float(np.mean((retained_prob - retained_true) ** 2))

            # High confidence error: predicted p >= 0.5 but true == 0, or p < 0.5 but true == 1
            high_conf_mask = (retained_prob >= 0.70) | (retained_prob <= 0.30)
            if np.sum(high_conf_mask) > 0:
                hc_preds = (retained_prob[high_conf_mask] >= 0.5).astype(int)
                hc_true = retained_true[high_conf_mask]
                hc_errors = float(np.mean(hc_preds != hc_true))
            else:
                hc_errors = 0.0
        else:
            risk = 0.0
            hc_errors = 0.0

        curve.append(
            CoverageRiskPoint(
                rejection_threshold=round(float(thresh), 3),
                coverage=cov,
                retained_count=n_retained,
                abstained_count=n_abstained,
                abstention_rate=abst_rate,
                risk=round(risk, 4),
                high_confidence_error_rate=round(hc_errors, 4),
                review_burden_cases=n_abstained,
            )
        )

    return curve


class SafetyEvaluator(BaseSafetyService):
    """Evaluates data validity, ML model availability, and safety criteria to decide on abstention."""

    def __init__(self, ood_detector: Optional[OODDetector] = None):
        self.ood_detector = ood_detector or OODDetector()

    def evaluate(
        self,
        weather_result: Optional[WeatherResult] = None,
        feature_result: Optional[FeatureResult] = None,
        model_result: Optional[ModelResult] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> SafetyAssessment:
        """Perform safety evaluation across all pipeline stages.

        If any upstream dependency (weather data, features, or model) is unavailable or unready,
        safely ABSTAIN with trust_state=UNAVAILABLE, bust_probability=None, and appropriate reason codes.
        """
        # 1. Weather Data Stage Check
        if weather_result is not None:
            if not weather_result.is_available or weather_result.error:
                if weather_result.quality_flags and weather_result.quality_flags.get("invalid_location"):
                    reason = ReasonCode.INVALID_LOCATION.value
                elif weather_result.quality_flags and weather_result.quality_flags.get("network_error"):
                    reason = ReasonCode.DATA_UNAVAILABLE.value
                elif weather_result.metadata and "status" in weather_result.metadata:
                    reason = weather_result.metadata["status"]
                elif weather_result.quality_flags and weather_result.quality_flags.get("qc_passed") is False:
                    reason = ReasonCode.QC_FAILED.value
                else:
                    reason = ReasonCode.DATA_NOT_READY.value

                meta = {"error": weather_result.error} if weather_result.error else {}
                meta["color_band"] = "GRAY"
                return SafetyAssessment(
                    bust_probability=None,
                    risk_level=None,
                    trust_state=TrustState.UNAVAILABLE,
                    abstain=True,
                    reason_codes=[reason],
                    ood_state=OODState.ABSTAIN,
                    is_gray_band=True,
                    metadata=meta,
                )

            # Near-threshold data quality ambiguity (§7.4, C10)
            if weather_result.quality_flags and (
                weather_result.quality_flags.get("near_threshold_qc")
                or weather_result.quality_flags.get("marginal_data_quality")
            ):
                return SafetyAssessment(
                    bust_probability=None,
                    risk_level=None,
                    trust_state=TrustState.UNAVAILABLE,
                    abstain=True,
                    reason_codes=["NEAR_THRESHOLD_DATA_QUALITY", ReasonCode.QC_FAILED.value],
                    ood_state=OODState.ABSTAIN,
                    is_gray_band=True,
                    metadata={"error": "Near-threshold data quality ambiguity; assigned GRAY band", "color_band": "GRAY"},
                )

        # 2. Feature Pipeline Stage Check
        if feature_result is not None:
            if not feature_result.is_ready or feature_result.error:
                if feature_result.metadata and "status" in feature_result.metadata:
                    reason = feature_result.metadata["status"]
                else:
                    reason = ReasonCode.FEATURES_NOT_READY.value

                meta = {"error": feature_result.error} if feature_result.error else {}
                meta["color_band"] = "GRAY"
                return SafetyAssessment(
                    bust_probability=None,
                    risk_level=None,
                    trust_state=TrustState.UNAVAILABLE,
                    abstain=True,
                    reason_codes=[reason],
                    ood_state=OODState.ABSTAIN,
                    is_gray_band=True,
                    metadata=meta,
                )

        # 3. Model Inference Stage Check
        if model_result is None or not model_result.is_ready or model_result.probability is None:
            reason = (
                model_result.metadata.get("status", ReasonCode.MODEL_NOT_READY.value)
                if (model_result and model_result.metadata)
                else ReasonCode.MODEL_NOT_READY.value
            )
            meta = {"error": model_result.error} if (model_result and model_result.error) else {}
            meta["color_band"] = "GRAY"
            return SafetyAssessment(
                bust_probability=None,
                risk_level=None,
                trust_state=TrustState.UNAVAILABLE,
                abstain=True,
                reason_codes=[reason],
                ood_state=OODState.ABSTAIN,
                is_gray_band=True,
                metadata=meta,
            )

        # 4. Valid Model Result Evaluation
        probability = model_result.probability

        # Boundary check
        if not (0.0 <= probability <= 1.0):
            return SafetyAssessment(
                bust_probability=None,
                risk_level=None,
                trust_state=TrustState.ABSTAINED,
                abstain=True,
                reason_codes=[ReasonCode.QC_FAILED.value],
                ood_state=OODState.ABSTAIN,
                metadata={"error": f"Invalid probability out of bounds: {probability}"},
            )

        # Map categorical risk level
        risk_level = self._map_risk_level(probability)

        # 5. OOD Evaluation per §11.3
        ood_result: Optional[OODResult] = None
        if feature_result and feature_result.features:
            regime_ctx = {}
            if feature_result.metadata:
                regime_ctx = feature_result.metadata.get("regime_context", {})
            ood_result = self.ood_detector.evaluate(
                features=feature_result.features,
                regime_context=regime_ctx,
            )

        combined_metadata = dict(model_result.metadata or {})
        if ood_result is not None:
            combined_metadata["ood_evaluation"] = ood_result.to_dict()
            combined_metadata["ood_score"] = ood_result.ood_score
            combined_metadata["ood_state"] = ood_result.state.value

            # Policy decisions based on OOD State
            if ood_result.state == OODState.ABSTAIN:
                return SafetyAssessment(
                    bust_probability=None,
                    risk_level=None,
                    trust_state=TrustState.ABSTAINED,
                    abstain=True,
                    reason_codes=[ReasonCode.OOD_ABSTAIN.value],
                    ood_state=OODState.ABSTAIN,
                    ood_score=ood_result.ood_score,
                    metadata=combined_metadata,
                )
            elif ood_result.state == OODState.OOD:
                return SafetyAssessment(
                    bust_probability=probability,
                    risk_level=risk_level,
                    trust_state=TrustState.LOW_CONFIDENCE,
                    abstain=False,
                    reason_codes=[ReasonCode.OOD_DETECTED.value],
                    ood_state=OODState.OOD,
                    ood_score=ood_result.ood_score,
                    metadata=combined_metadata,
                )
            elif ood_result.state == OODState.UNUSUAL:
                combined_metadata["caution_banner"] = True
                return SafetyAssessment(
                    bust_probability=probability,
                    risk_level=risk_level,
                    trust_state=TrustState.MODERATE_CONFIDENCE,
                    abstain=False,
                    reason_codes=[ReasonCode.SUCCESS.value],
                    ood_state=OODState.UNUSUAL,
                    ood_score=ood_result.ood_score,
                    metadata=combined_metadata,
                )

        # Default NORMAL state
        return SafetyAssessment(
            bust_probability=probability,
            risk_level=risk_level,
            trust_state=TrustState.HIGH_CONFIDENCE,
            abstain=False,
            reason_codes=[ReasonCode.SUCCESS.value],
            ood_state=OODState.NORMAL,
            ood_score=ood_result.ood_score if ood_result else 0.0,
            metadata=combined_metadata,
        )

    @staticmethod
    def create_error_assessment(
        reason_code: ReasonCode = ReasonCode.INTERNAL_ERROR,
        error_message: Optional[str] = None,
    ) -> SafetyAssessment:
        """Construct a failsafe abstention response for unexpected errors."""
        return SafetyAssessment(
            bust_probability=None,
            risk_level=None,
            trust_state=TrustState.UNAVAILABLE,
            abstain=True,
            reason_codes=[reason_code.value],
            ood_state=OODState.ABSTAIN,
            metadata={"error": error_message} if error_message else {},
        )

    @staticmethod
    def _map_risk_level(prob: float) -> RiskLevel:
        """Map a calibrated probability to a categorical risk level."""
        if prob < 0.20:
            return RiskLevel.LOW
        elif prob < 0.50:
            return RiskLevel.MEDIUM
        elif prob < 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
