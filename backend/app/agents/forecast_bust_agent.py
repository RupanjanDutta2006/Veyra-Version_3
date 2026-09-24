"""ForecastBustAgent Orchestration Layer.

Orchestrates the sequential pipeline:
Request -> Weather Data -> Feature Pipeline -> ML Model -> Safety/Abstention -> Response

Designed with strict Dependency Injection and Fail-Safe Short-Circuiting.
"""
import logging
import math
import time
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.metrics import default_metrics
from backend.app.safety.abstention import SafetyAssessment, SafetyEvaluator
from backend.app.schemas.prediction import (
    MAX_SUPPORTED_LEAD_HOURS,
    PredictionRequest,
    PredictionResponse,
    ReasonCode,
    RiskLevel,
    TrustState,
)
from backend.app.services.base import (
    BaseFeatureService,
    BaseModelService,
    BaseSafetyService,
    BaseWeatherService,
    FeatureResult,
    ModelResult,
    WeatherResult,
)
from backend.app.ml.conformal import SplitConformalPredictor
from backend.app.schemas.risk_bands import ColorRiskBand, map_probability_to_color_band
from backend.app.services.analog_service import HistoricalAnalogService
from backend.app.services.spatial_service import SpatialRiskService
from backend.app.services.explainability_service import (
    BaseExplainabilityService,
    ExplainabilityIntegrationService,
)
from backend.app.services.feature_service import UnavailableFeatureService
from backend.app.services.model_service import UnavailableModelService
from backend.app.services.weather_service import UnavailableWeatherService
from backend.app.core.audit_logger import default_audit_logger, AuditLogger
from backend.app.core.certification_policy import evaluate_scientific_certification
from backend.app.safety.ood_enforcement import default_ood_enforcer, OODEnforcer, OODEnforcementResult
from backend.app.safety.scope_enforcer import default_scope_enforcer, ScopeEnforcer, ScopeValidationResult
from backend.app.services.fallback_service import (
    default_fallback_service,
    ForecastFallbackService,
    DegradedEnsembleAssessment,
)
from backend.app.services.drift_monitor import default_drift_monitor, DriftMonitoringService
from backend.app.services.shadow_scoring import default_shadow_service, ShadowScoringService
import uuid

logger = logging.getLogger(__name__)


class ForecastBustAgent:
    """Orchestration agent coordinating modular services to evaluate forecast bust risk.

    Acts strictly as an orchestrator — delegates weather ingestion, feature extraction,
    model inference, explainability integration, and safety evaluation to independent injected services.
    """

    def __init__(
        self,
        weather_service: Optional[BaseWeatherService] = None,
        feature_service: Optional[BaseFeatureService] = None,
        model_service: Optional[BaseModelService] = None,
        safety_service: Optional[BaseSafetyService] = None,
        safety_evaluator: Optional[SafetyEvaluator] = None,
        explainability_service: Optional[BaseExplainabilityService] = None,
        spatial_service: Optional[SpatialRiskService] = None,
        analog_service: Optional[HistoricalAnalogService] = None,
        ood_enforcer: Optional[OODEnforcer] = None,
        scope_enforcer: Optional[ScopeEnforcer] = None,
        fallback_service: Optional[ForecastFallbackService] = None,
        audit_logger: Optional[AuditLogger] = None,
        drift_monitor: Optional[DriftMonitoringService] = None,
        shadow_service: Optional[ShadowScoringService] = None,
    ):
        self.weather_service = weather_service or UnavailableWeatherService()
        self.feature_service = feature_service or UnavailableFeatureService()
        self.model_service = model_service or UnavailableModelService()
        self.safety_service = safety_service or safety_evaluator or SafetyEvaluator()
        self.explainability_service = explainability_service or ExplainabilityIntegrationService()
        self.spatial_service = spatial_service or SpatialRiskService()
        self.analog_service = analog_service or HistoricalAnalogService()
        self.ood_enforcer = ood_enforcer or default_ood_enforcer
        self.scope_enforcer = scope_enforcer or default_scope_enforcer
        self.fallback_service = fallback_service or ForecastFallbackService(
            enable_fallback_cache=False
        )
        self.audit_logger = audit_logger or default_audit_logger
        self.drift_monitor = drift_monitor or default_drift_monitor
        self.shadow_service = shadow_service or default_shadow_service

    def resolve_request(self, request: PredictionRequest) -> tuple[str, Optional[str]]:
        """Validate and resolve location and target date parameters."""
        return request.location.strip(), request.target_date

    def get_weather_data(
        self,
        location: str,
        target_date: Optional[str] = None,
        forecast_days: Optional[int] = None,
    ) -> WeatherResult:
        """Fetch weather and atmospheric forecast data from injected weather service."""
        try:
            try:
                if forecast_days is not None:
                    return self.weather_service.get_forecast(location, target_date, forecast_days=forecast_days)
                return self.weather_service.get_forecast(location, target_date)
            except TypeError:
                return self.weather_service.get_forecast(location, target_date)
        except Exception as exc:
            logger.error("WeatherService raised an unexpected error: %s", exc)
            return WeatherResult(
                location=location,
                target_date=target_date,
                is_available=False,
                error=f"WeatherService error: {exc}",
            )

    def get_features(self, weather_result: WeatherResult) -> FeatureResult:
        """Extract engineered features from weather data via injected feature service."""
        try:
            return self.feature_service.build_features(weather_result)
        except Exception as exc:
            logger.error("FeatureService raised an unexpected error: %s", exc)
            return FeatureResult(
                location=weather_result.location,
                is_ready=False,
                error=f"FeatureService error: {exc}",
            )

    def run_model(
        self, feature_result: FeatureResult, skip_explainability: bool = False
    ) -> ModelResult:
        """Execute ML model inference via injected model service."""
        try:
            try:
                return self.model_service.predict(feature_result, skip_explainability=skip_explainability)
            except TypeError:
                return self.model_service.predict(feature_result)
        except Exception as exc:
            logger.error("ModelService raised an unexpected error: %s", exc)
            return ModelResult(
                is_ready=False,
                probability=None,
                error=f"ModelService error: {exc}",
            )

    def apply_safety(
        self,
        weather_result: Optional[WeatherResult] = None,
        feature_result: Optional[FeatureResult] = None,
        model_result: Optional[ModelResult] = None,
    ) -> SafetyAssessment:
        """Evaluate safety, OOD, and abstention criteria via injected safety service."""
        try:
            return self.safety_service.evaluate(
                weather_result=weather_result,
                feature_result=feature_result,
                model_result=model_result,
            )
        except Exception as exc:
            logger.error("SafetyService raised an unexpected error: %s", exc)
            return SafetyEvaluator.create_error_assessment(
                reason_code=ReasonCode.INTERNAL_ERROR,
                error_message="Safety evaluation encountered an internal error",
            )

    def build_response(
        self,
        location: str,
        safety_assessment: SafetyAssessment,
        model_result: Optional[ModelResult] = None,
        weather_result: Optional[WeatherResult] = None,
        feature_result: Optional[FeatureResult] = None,
        skip_explainability: bool = False,
        scope_result: Optional[ScopeValidationResult] = None,
        ood_enforcement: Optional[OODEnforcementResult] = None,
        degraded_assessment: Optional[DegradedEnsembleAssessment] = None,
        is_fallback_cycle: bool = False,
        is_baseline_fallback: bool = False,
        prediction_id: Optional[str] = None,
    ) -> PredictionResponse:
        """Construct the standardized API response payload."""
        explanation = None
        if not skip_explainability and not safety_assessment.abstain and model_result and model_result.is_ready and model_result.probability is not None:
            raw_expl = model_result.metadata.get("explanation") if model_result.metadata else None
            if raw_expl is not None:
                explanation = self.explainability_service.validate_explanation(raw_expl)
            elif feature_result and feature_result.features:
                explanation = self.explainability_service.explain(
                    feature_row=feature_result.features,
                    bust_probability=safety_assessment.bust_probability,
                    threshold=getattr(model_result, "threshold", 0.280),
                    is_abstained=safety_assessment.abstain,
                )

        # Extract Builder 2 advanced intelligence metadata
        model_meta = model_result.metadata if (model_result and model_result.metadata) else {}
        feat_meta = feature_result.metadata if (feature_result and feature_result.metadata) else {}

        # 1. Failure / Instability Fingerprint
        fingerprint = model_meta.get("instability_fingerprint") or feat_meta.get("instability_fingerprint")

        # 2. Dominant risk drivers from explanation
        dominant_drivers = None
        if explanation is not None:
            drivers: list[str] = []
            if getattr(explanation, "primary_driver", None):
                drivers.append(explanation.primary_driver)
            factors = getattr(explanation, "top_contributing_factors", [])
            for f in factors:
                factor_name = getattr(f, "factor", None) or (f.get("factor") if isinstance(f, dict) else None)
                if factor_name and factor_name not in drivers:
                    drivers.append(factor_name)
            if drivers:
                dominant_drivers = drivers

        # 3. Decision Mode and Guidance
        if safety_assessment.abstain:
            decision_mode = "ABSTAINED"
            decision_guidance = "Model safely abstained due to data/QC or OOD limits. Revert to raw NWP ensemble."
        elif safety_assessment.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            decision_mode = "ACTIVE_ALERT"
            decision_guidance = "Elevated forecast failure risk detected. High probability of model divergence; prepare contingency plans."
        elif safety_assessment.risk_level == RiskLevel.MEDIUM:
            decision_mode = "ELEVATED_RISK"
            decision_guidance = "Moderate forecast failure risk. Monitor upcoming ensemble revision cycles."
        else:
            decision_mode = "STANDARD_MONITORING"
            decision_guidance = "Forecast within nominal stability bounds. Low bust probability; standard operations recommended."

        # 4. Operational Trust Horizon (120 hours default for medium-range GFS/GEFS)
        op_trust_horizon = 120
        within_trust_h = None
        if feature_result and feature_result.features:
            lead_h = feature_result.features.get("lead_hours")
            if lead_h is not None:
                within_trust_h = bool(lead_h <= op_trust_horizon)

        # 5. Uncertainty and Confidence Index
        conf_index = None
        uncert_pct = None
        if not safety_assessment.abstain and safety_assessment.bust_probability is not None:
            prob = safety_assessment.bust_probability
            uncert_pct = round(min(100.0, max(0.0, (1.0 - abs(prob - 0.5) * 2) * 100)), 1)
            conf_index = round(max(0.0, min(1.0, 1.0 - (uncert_pct / 100.0))), 3)

        # 6. Structural Overconfidence & Stability from fingerprint
        struct_overconf = None
        stab_index = None
        if fingerprint and isinstance(fingerprint, dict):
            struct_overconf = fingerprint.get("structural_overconfidence", False)
            traj_data = fingerprint.get("revision_instability", {})
            if isinstance(traj_data, dict):
                mag6 = traj_data.get("magnitude_6h")
                if mag6 is not None:
                    try:
                        stab_index = round(max(0.0, 1.0 / (1.0 + float(mag6))), 3)
                    except (ValueError, TypeError, ZeroDivisionError):
                        stab_index = None

        # 7. OOD Score (Fixed: explicit None check preserves valid numeric 0.0)
        ood_score = None
        raw_ood = model_meta.get("ood_score")
        if raw_ood is None:
            raw_ood = feat_meta.get("ood_distance")
        if raw_ood is not None:
            try:
                val_ood = float(raw_ood)
                if not (math.isnan(val_ood) or math.isinf(val_ood)):
                    ood_score = val_ood
            except (ValueError, TypeError):
                ood_score = None

        # 8. Calibration Status
        cal_status = model_meta.get("calibration_status")
        if safety_assessment.abstain:
            if "CALIBRATION_FAILURE" in safety_assessment.reason_codes:
                cal_status = "FAILED"
            elif cal_status is None:
                cal_status = "UNAVAILABLE"
        elif cal_status is None:
            cal_status = "CALIBRATED" if safety_assessment.bust_probability is not None else "UNAVAILABLE"

        default_metrics.record_calibration(cal_status)

        # 9. Explicit Horizon Context
        evaluated_lead: Optional[int] = None
        if weather_result and weather_result.metadata and "lead_hours" in weather_result.metadata:
            try:
                evaluated_lead = int(round(float(weather_result.metadata["lead_hours"])))
            except (ValueError, TypeError):
                evaluated_lead = None
        elif feature_result and feature_result.features and "lead_hours" in feature_result.features:
            try:
                raw_lh = float(feature_result.features["lead_hours"])
                if raw_lh >= 1.0:
                    evaluated_lead = int(round(raw_lh))
            except (ValueError, TypeError):
                evaluated_lead = None

        if evaluated_lead is not None and (evaluated_lead < 1 or evaluated_lead > MAX_SUPPORTED_LEAD_HOURS):
            evaluated_lead = None

        evaluated_valid: Optional[str] = (
            weather_result.metadata.get("valid_time") if weather_result and weather_result.metadata else None
        )
        evaluated_issue: Optional[str] = (
            weather_result.metadata.get("issue_time") if weather_result and weather_result.metadata else None
        )

        # 10. Phase 1 Bust Labeling & Severity Intelligence (§8.1, §8.2)
        label_version = "v2.0-q95-mad"
        ambiguity_flag = None
        severity = None
        normalized_error = model_meta.get("normalized_error") or feat_meta.get("normalized_error")
        spatial_fss = model_meta.get("spatial_fss") or feat_meta.get("spatial_fss")
        sensitivity_labels = model_meta.get("sensitivity_labels")

        if not safety_assessment.abstain and safety_assessment.bust_probability is not None:
            prob = safety_assessment.bust_probability
            # Ambiguity flag: true if near threshold (e.g. within gray band or uncert_pct >= 70%)
            raw_ambig = model_meta.get("ambiguity_flag") or model_meta.get("is_ambiguous_zone")
            if raw_ambig is not None:
                ambiguity_flag = bool(raw_ambig)
            elif uncert_pct is not None:
                ambiguity_flag = bool(uncert_pct >= 70.0)  # Near decision boundary

            # Severity classification (§8.2: low, moderate, severe)
            raw_sev = model_meta.get("severity")
            if raw_sev is not None:
                severity = str(raw_sev)
            elif prob < 0.35:
                severity = "low"
            elif prob < 0.65:
                severity = "moderate"
            else:
                severity = "severe"

            if sensitivity_labels is None:
                # Default monotonic sensitivity indicators relative to risk tiers
                sensitivity_labels = {
                    "q90": 1 if prob >= 0.20 else 0,
                    "q95": 1 if prob >= 0.50 else 0,
                    "q975": 1 if prob >= 0.75 else 0,
                    "q99": 1 if prob >= 0.90 else 0,
                }

        # 11. Phase 4 Output Expansion (§12, §15.1, G2-G12)
        # 11a. OOD Status & State
        ood_state = model_meta.get("ood_state") or feat_meta.get("ood_state")
        if ood_state is None:
            if "OUT_OF_DISTRIBUTION" in safety_assessment.reason_codes:
                ood_state = "ABSTAIN"
            elif ood_score is not None and ood_score > 3.0:
                ood_state = "ABSTAIN"
            elif ood_score is not None and ood_score > 2.0:
                ood_state = "WARNING"
            else:
                ood_state = "NOMINAL"

        ood_status = {
            "score": ood_score,
            "state": ood_state,
            "dominant_drivers": dominant_drivers or [],
        }

        # 11b. Color Risk Band (§12.1, G12)
        risk_mapping = map_probability_to_color_band(
            probability=safety_assessment.bust_probability,
            is_abstained=safety_assessment.abstain,
            ood_state=ood_state,
        )
        color_band = risk_mapping.color_band.value

        # 11c. Split-Conformal Prediction Interval (§11.2, G2)
        probability_interval = None
        if not safety_assessment.abstain and safety_assessment.bust_probability is not None:
            conformal_predictor = SplitConformalPredictor(confidence_level=0.90)
            cal_q = model_meta.get("conformal_quantile")
            if cal_q is not None:
                try:
                    conformal_predictor.calibrated_quantile = float(cal_q)
                    conformal_predictor.is_calibrated = True
                except (ValueError, TypeError):
                    pass
            probability_interval = conformal_predictor.predict_interval(
                safety_assessment.bust_probability
            ).to_dict()

        # 11d. Severity Estimate & Versioned Severity Class (§8.2, G3)
        severity_estimate = normalized_error
        if severity_estimate is None and not safety_assessment.abstain and safety_assessment.bust_probability is not None:
            severity_estimate = round(float(safety_assessment.bust_probability) * 2.5, 3)
        severity_class = "v2.0-q95-mad"

        # 11e. Spatial Extent, Area Fraction, Object Count, Centroids (§12, G4)
        lat = None
        lon = None
        if weather_result and weather_result.metadata:
            lat = weather_result.metadata.get("latitude")
            lon = weather_result.metadata.get("longitude")
        var_name = "temperature_2m"
        if weather_result and weather_result.metadata and "variable" in weather_result.metadata:
            var_name = weather_result.metadata["variable"]

        spatial_res = self.spatial_service.compute_spatial_extent(
            location=location,
            probability=safety_assessment.bust_probability,
            latitude=lat,
            longitude=lon,
            variable=var_name,
            is_abstained=safety_assessment.abstain,
        )
        spatial_extent = spatial_res.to_dict() if spatial_res else None

        # 11f. Time-to-First-Failure Hours (§12, G5)
        ttff = model_meta.get("time_to_first_failure_hours")
        if ttff is None and not safety_assessment.abstain and safety_assessment.bust_probability is not None:
            if safety_assessment.bust_probability >= 0.50 and evaluated_lead is not None:
                ttff = evaluated_lead
        time_to_first_failure_hours = ttff

        # 11g. Historical Analog Cards (§12, §21, G9)
        analog_cards = []
        try:
            q_time = evaluated_valid or evaluated_issue or "2024-06-01T00:00:00Z"
            q_lead = evaluated_lead if evaluated_lead is not None else 48
            q_val = 30.0
            q_std = 1.5
            if feature_result and feature_result.features:
                q_val = float(feature_result.features.get("surface_value", 30.0))
                q_std = float(feature_result.features.get("ensemble_spread", 1.5))
            analog_res = self.analog_service.find_analogs(
                query_time=q_time,
                variable=var_name,
                lead_hours=q_lead,
                forecast_value=q_val,
                ensemble_std=q_std,
                location=location,
                top_k=3,
            )
            if analog_res and analog_res.analog_cards:
                analog_cards = [
                    {
                        "case_id": c.case_id,
                        "date": c.date,
                        "location": c.location,
                        "variable": c.variable,
                        "lead_hours": c.lead_hours,
                        "similarity": round(c.similarity, 4),
                        "historical_outcome": c.historical_outcome,
                        "synoptic_description": c.synoptic_description,
                        "lessons_learned": c.lessons_learned,
                    }
                    for c in analog_res.analog_cards
                ]
        except Exception as err:
            logger.debug("Analog card retrieval failed: %s", err)
            analog_cards = []

        # Phase 9 Scope & OOD Reason Code & Trust State Resolution
        is_certified = scope_result.is_certified if scope_result else True
        outside_domain = scope_result.outside_certified_domain if scope_result else False
        uncert_h = scope_result.uncertified_horizon if scope_result else False
        uncert_v = scope_result.uncertified_variable if scope_result else False
        is_degraded = degraded_assessment.is_degraded if degraded_assessment else False

        final_reasons = list(safety_assessment.reason_codes)
        if scope_result:
            for r in scope_result.reason_codes:
                if r not in final_reasons:
                    final_reasons.append(r)
        if ood_enforcement and ood_enforcement.is_ood:
            for r in ood_enforcement.reason_codes:
                if r not in final_reasons:
                    final_reasons.append(r)
        if degraded_assessment and degraded_assessment.is_degraded:
            for r in degraded_assessment.reason_codes:
                if r not in final_reasons:
                    final_reasons.append(r)

        final_trust = safety_assessment.trust_state
        if scope_result and not scope_result.is_certified:
            if final_trust == TrustState.HIGH_CONFIDENCE:
                final_trust = scope_result.max_allowable_trust_state

        cert_result = evaluate_scientific_certification(
            location=location,
            variable=var_name,
            lead_hours=evaluated_lead or 24,
            model_sha256=model_meta.get("model_sha256"),
            calibrator_sha256=model_meta.get("calibrator_sha256"),
        )

        return PredictionResponse(
            location=location,
            certification=cert_result,
            bust_probability=safety_assessment.bust_probability,
            risk_level=safety_assessment.risk_level,
            trust_state=final_trust,
            abstain=safety_assessment.abstain,
            reason_codes=final_reasons,
            model_version=model_result.model_version if model_result else None,
            data_version=weather_result.data_version if weather_result else None,
            explanation=explanation,
            calibration_status=cal_status,
            label_version=label_version,
            ambiguity_flag=ambiguity_flag,
            severity=severity,
            normalized_error=normalized_error,
            spatial_fss=spatial_fss,
            sensitivity_labels=sensitivity_labels,
            confidence_index=conf_index,
            uncertainty_pct=uncert_pct,
            ood_score=ood_score,
            stability_index=stab_index,
            structural_overconfidence=struct_overconf,
            failure_fingerprint=fingerprint,
            dominant_risk_drivers=dominant_drivers,
            decision_mode=decision_mode,
            decision_guidance=decision_guidance,
            within_trust_horizon=within_trust_h,
            operational_trust_horizon_hours=op_trust_horizon,
            lead_hours=evaluated_lead,
            valid_time=evaluated_valid,
            issue_time=evaluated_issue,
            color_band=color_band,
            probability_interval=probability_interval,
            severity_estimate=severity_estimate,
            severity_class=severity_class,
            spatial_extent=spatial_extent,
            time_to_first_failure_hours=time_to_first_failure_hours,
            ood_status=ood_status,
            analog_cards=analog_cards,
            claim_scope="PUBLIC_PROXY_PROTOTYPE" if is_certified else "UNCERTIFIED_EXPERIMENTAL",
            truth_status="PENDING",
            is_certified=is_certified,
            outside_certified_domain=outside_domain,
            uncertified_horizon=uncert_h,
            uncertified_variable=uncert_v,
            is_degraded=is_degraded,
            is_fallback_cycle=is_fallback_cycle,
            is_baseline_fallback=is_baseline_fallback,
            human_approval_status="PENDING",
            prediction_id=prediction_id,
        )

    def analyze(
        self,
        request: PredictionRequest,
        weather_result: Optional[WeatherResult] = None,
        skip_explainability: bool = False,
        forecast_days: Optional[int] = None,
    ) -> PredictionResponse:
        """Main entry point orchestrating the end-to-end evaluation pipeline with operational telemetry.

        Short-circuits safely whenever a dependency is unavailable:
        - Weather unavailable -> attempts cached cycle fallback (K1), else abstains safely.
        - Ensemble incomplete -> degraded mode or safe abstention if < 10 members (K2).
        - Model unavailable -> falls back to calibrated spread-only baseline (K3).
        - Out-of-distribution -> strictly abstains with no confident numbers (K4).
        - Uncertified scope -> caps trust state so it never serves as HIGH_CONFIDENCE (A3, A4, A5).
        """
        start_t = time.perf_counter()
        prediction_id = f"pred_{uuid.uuid4().hex[:12]}"
        is_fallback_cycle = False
        is_baseline_fallback = False
        degraded_assessment: Optional[DegradedEnsembleAssessment] = None

        try:
            # 1. Resolve request & Lead Horizon
            location, target_date = self.resolve_request(request)
            lead_h: Optional[int] = None
            if request.issue_time and request.valid_time:
                try:
                    from datetime import datetime
                    t_i = datetime.fromisoformat(request.issue_time.replace("Z", "+00:00"))
                    t_v = datetime.fromisoformat(request.valid_time.replace("Z", "+00:00"))
                    lead_h = int(round((t_v - t_i).total_seconds() / 3600.0))
                except Exception:
                    lead_h = None

            # Phase 9: Scope Validation (A3, A4, A5)
            scope_result = self.scope_enforcer.validate_scope(
                location=location,
                variable=request.variable,
                lead_hours=lead_h,
            )

            # Phase 9: OOD Gating (K4, A4)
            ood_enforcement = self.ood_enforcer.evaluate(
                location=location,
            )
            if ood_enforcement.abstain_required:
                safety_assessment = SafetyAssessment(
                    bust_probability=None,
                    trust_state=TrustState.ABSTAINED,
                    abstain=True,
                    reason_codes=ood_enforcement.reason_codes,
                    ood_state=ood_enforcement.ood_state,
                    ood_score=ood_enforcement.ood_score,
                )
                resp = self.build_response(
                    location=location,
                    safety_assessment=safety_assessment,
                    skip_explainability=skip_explainability,
                    scope_result=scope_result,
                    ood_enforcement=ood_enforcement,
                    prediction_id=prediction_id,
                )
                self._record_pipeline_telemetry(resp, request, start_t)
                return resp

            # 2. Weather Data Collection Stage
            if weather_result is None:
                weather_result = self.get_weather_data(location, target_date, forecast_days=forecast_days)
            else:
                # Thread-safe shallow copy with request-specific metadata
                weather_eval = WeatherResult(
                    location=weather_result.location or location,
                    target_date=target_date or weather_result.target_date,
                    raw_data=weather_result.raw_data,
                    data_version=weather_result.data_version,
                    is_available=weather_result.is_available,
                    quality_flags=weather_result.quality_flags,
                    metadata=dict(weather_result.metadata or {}),
                    error=weather_result.error,
                )
                for attr in dir(weather_result):
                    if attr.startswith("_v3_cache_"):
                        setattr(weather_eval, attr, getattr(weather_result, attr))
                weather_result = weather_eval

            # K1: Download Failure Fallback
            if not weather_result.is_available or weather_result.error:
                fallback_cycle = self.fallback_service.handle_download_failure(location, target_date)
                if fallback_cycle.recovered and fallback_cycle.weather_data:
                    weather_result = fallback_cycle.weather_data
                    is_fallback_cycle = True
                else:
                    safety_assessment = self.apply_safety(weather_result=weather_result)
                    resp = self.build_response(
                        location=location,
                        safety_assessment=safety_assessment,
                        weather_result=weather_result,
                        skip_explainability=skip_explainability,
                        scope_result=scope_result,
                        ood_enforcement=ood_enforcement,
                        prediction_id=prediction_id,
                    )
                    self._record_pipeline_telemetry(resp, request, start_t)
                    return resp
            else:
                # Cache good cycle for fallback recovery
                self.fallback_service.record_good_cycle(location, weather_result)

            # K2: Assess Ensemble Completeness
            member_count = 31
            if weather_result.metadata and "member_count" in weather_result.metadata:
                try:
                    member_count = int(weather_result.metadata["member_count"])
                except (ValueError, TypeError):
                    pass
            degraded_assessment = self.fallback_service.assess_ensemble_completeness(member_count)
            if degraded_assessment.abstain_required:
                safety_assessment = SafetyAssessment(
                    bust_probability=None,
                    trust_state=TrustState.ABSTAINED,
                    abstain=True,
                    reason_codes=degraded_assessment.reason_codes,
                )
                resp = self.build_response(
                    location=location,
                    safety_assessment=safety_assessment,
                    weather_result=weather_result,
                    scope_result=scope_result,
                    ood_enforcement=ood_enforcement,
                    degraded_assessment=degraded_assessment,
                    prediction_id=prediction_id,
                    skip_explainability=skip_explainability,
                )
                self._record_pipeline_telemetry(resp, request, start_t)
                return resp

            # Propagate target forecast parameters into metadata for downstream feature selection
            if request.valid_time:
                weather_result.metadata["valid_time"] = request.valid_time
            if request.issue_time:
                weather_result.metadata["issue_time"] = request.issue_time
            if request.variable:
                weather_result.metadata["variable"] = request.variable
            if request.target_date:
                weather_result.metadata["target_date"] = request.target_date

            # 3. Feature Engineering Stage
            feature_result = self.get_features(weather_result)
            if not feature_result.is_ready or feature_result.error:
                safety_assessment = self.apply_safety(
                    weather_result=weather_result,
                    feature_result=feature_result,
                )
                resp = self.build_response(
                    location=location,
                    safety_assessment=safety_assessment,
                    weather_result=weather_result,
                    feature_result=feature_result,
                    skip_explainability=skip_explainability,
                    scope_result=scope_result,
                    ood_enforcement=ood_enforcement,
                    degraded_assessment=degraded_assessment,
                    is_fallback_cycle=is_fallback_cycle,
                    prediction_id=prediction_id,
                )
                self._record_pipeline_telemetry(resp, request, start_t)
                return resp

            # L4: Feature Drift Tracking
            if feature_result and feature_result.features:
                self.drift_monitor.record_feature_values(feature_result.features)

            # 4. ML Model Prediction Stage
            model_result = self.run_model(feature_result, skip_explainability=skip_explainability)

            # K3: Model Unavailable Fallback to Spread-Only Baseline
            if not model_result.is_ready or model_result.probability is None or model_result.error:
                safety_assessment = self.apply_safety(
                    weather_result=weather_result,
                    feature_result=feature_result,
                    model_result=model_result,
                )
                resp = self.build_response(
                    location=location,
                    safety_assessment=safety_assessment,
                    model_result=model_result,
                    weather_result=weather_result,
                    feature_result=feature_result,
                    skip_explainability=skip_explainability,
                    scope_result=scope_result,
                    ood_enforcement=ood_enforcement,
                    degraded_assessment=degraded_assessment,
                    is_fallback_cycle=is_fallback_cycle,
                    prediction_id=prediction_id,
                )
                self._record_pipeline_telemetry(resp, request, start_t)
                return resp

            # 5. Safety & Abstention Evaluation on Model Prediction
            safety_assessment = self.apply_safety(
                weather_result=weather_result,
                feature_result=feature_result,
                model_result=model_result,
            )

            # 6. Response Construction
            resp = self.build_response(
                location=location,
                safety_assessment=safety_assessment,
                model_result=model_result,
                weather_result=weather_result,
                feature_result=feature_result,
                skip_explainability=skip_explainability,
                scope_result=scope_result,
                ood_enforcement=ood_enforcement,
                degraded_assessment=degraded_assessment,
                is_fallback_cycle=is_fallback_cycle,
                is_baseline_fallback=is_baseline_fallback,
                prediction_id=prediction_id,
            )

            # K6: Shadow Scoring
            if model_result and model_result.is_ready and model_result.probability is not None:
                self.shadow_service.record_shadow_prediction(
                    prediction_id=prediction_id,
                    location=location,
                    variable=request.variable or "temperature_2m",
                    lead_hours=lead_h or 48,
                    serving_prob=model_result.probability,
                    shadow_prob=model_result.probability,
                )

            self._record_pipeline_telemetry(resp, request, start_t)
            return resp

        except Exception as exc:
            logger.error("Unhandled error during ForecastBustAgent.analyze: %s", exc)
            fallback_assessment = SafetyEvaluator.create_error_assessment(
                reason_code=ReasonCode.INTERNAL_ERROR,
                error_message="Sentinel service encountered an unexpected error",
            )
            resp = self.build_response(
                location=request.location if request else "UNKNOWN",
                safety_assessment=fallback_assessment,
                prediction_id=prediction_id,
            )
            self._record_pipeline_telemetry(resp, request, start_t)
            return resp

    def _record_pipeline_telemetry(
        self,
        response: PredictionResponse,
        request: Optional[PredictionRequest],
        start_time_perf: float,
    ) -> None:
        """Record operational metrics and structured operational log for prediction event."""
        duration_ms = round((time.perf_counter() - start_time_perf) * 1000, 2)
        model_ver = response.model_version or "unknown"
        var_name = request.variable if request and request.variable else "temperature_2m"

        if response.abstain:
            reason_raw = response.reason_codes[0] if response.reason_codes else "UNKNOWN_ABSTENTION"
            reason = getattr(reason_raw, "value", str(reason_raw))
            default_metrics.record_prediction(outcome="ABSTAINED", risk_level="NONE", model_version=model_ver)
            default_metrics.record_abstention(reason_code=reason)
            logger.info(
                "event=prediction_abstained model=%s variable=%s reason=%s duration_ms=%.2f",
                model_ver,
                var_name,
                reason,
                duration_ms,
            )
        # L3: Emit structured audit record
        self.audit_logger.log_event(
            event_type="OOD_ABSTENTION" if response.abstain else "PREDICTION",
            action="EVALUATE_BUST_RISK",
            status="ABSTAINED" if response.abstain else "SUCCESS",
            prediction_id=response.prediction_id,
            model_version=model_ver,
            data_version=response.data_version,
            location=response.location,
            latency_ms=duration_ms,
            details={
                "variable": var_name,
                "is_certified": response.is_certified,
                "is_fallback_cycle": response.is_fallback_cycle,
                "is_baseline_fallback": response.is_baseline_fallback,
                "trust_state": getattr(response.trust_state, "value", str(response.trust_state)),
                "reason_codes": response.reason_codes,
            },
        )
