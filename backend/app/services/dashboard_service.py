"""Dashboard Intelligence Service for Veyra Phase 3 Day 25.

Orchestrates unified, multi-horizon forecast bust intelligence for dashboard consumption.
Reuses existing ForecastBustAgent, DynamicLocationService, and caching pipelines
without modifying frozen model weights or duplicating prediction logic.

Performance-optimized: fetches weather data ONCE and evaluates all horizons in parallel
via ThreadPoolExecutor, eliminating redundant upstream requests and sequential bottlenecks.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.core.metrics import default_metrics
from backend.app.schemas.dashboard import (
    DashboardIntelligenceResponse,
    DashboardLocationContext,
    DashboardMode,
    DashboardRequest,
    DashboardScientificContext,
    DashboardStatus,
    DashboardSummary,
    DashboardTimelinePoint,
    DecisionMode,
)
from backend.app.schemas.prediction import (
    CalibrationStatus,
    PredictionRequest,
    PredictionResponse,
    ReasonCode,
    RiskLevel,
    TrustState,
)
from backend.app.services.location_service import BaseLocationService, DynamicLocationService

logger = logging.getLogger(__name__)


class DashboardIntelligenceService:
    """Production service orchestrating dashboard-ready probabilistic intelligence.

    Performance Architecture:
    - Weather data is fetched ONCE and shared across all horizon evaluations.
    - All horizon evaluations (feature engineering + ML inference + safety) run
      in parallel via a bounded ThreadPoolExecutor.
    - Location resolution happens once at the orchestration level, not per-horizon.
    - Issue timestamp is extracted from the shared weather data, eliminating
      the separate pre-fetch round-trip.
    """

    def __init__(
        self,
        location_service: Optional[BaseLocationService] = None,
        agent_factory: Optional[Callable[[], Any]] = None,
        max_workers: Optional[int] = None,
    ):
        self.location_service = location_service or DynamicLocationService()
        self.agent_factory = agent_factory
        self.max_workers = max_workers or settings.DASHBOARD_MAX_WORKERS

    @staticmethod
    def get_horizons_for_mode(mode: DashboardMode) -> List[int]:
        """Return canonical ordered lead hour list for requested evaluation mode."""
        if mode == DashboardMode.SINGLE:
            return [24]
        if mode == DashboardMode.STANDARD_7D:
            return [24, 48, 72, 96, 120, 144, 168]
        if mode == DashboardMode.FULL_16D:
            return [24 * i for i in range(1, 17)]  # 24 through 384 every 24h
        return [24, 48, 72, 96, 120, 144, 168]

    def _get_agent(self) -> Any:
        """Retrieve or construct the ForecastBustAgent."""
        if self.agent_factory:
            return self.agent_factory()
        from backend.app.api.v1.endpoints.predict import get_forecast_bust_agent

        return get_forecast_bust_agent()

    def _evaluate_single_horizon(
        self,
        agent: Any,
        location: str,
        variable: str,
        issue_iso: str,
        h: int,
        weather_res: Optional[Any] = None,
    ) -> Tuple[int, DashboardTimelinePoint, Optional[PredictionResponse]]:
        """Evaluate a single horizon point using the shared agent (thread-safe).

        Returns (lead_hours, timeline_point, selected_prediction_or_None).
        """
        lead_days = round(h / 24.0, 1)
        valid_dt = datetime.fromisoformat(issue_iso.replace("Z", "+00:00")) + timedelta(hours=h)
        valid_iso = valid_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        pred_req = PredictionRequest(
            location=location,
            variable=variable,
            issue_time=issue_iso,
            valid_time=valid_iso,
        )
        skip_expl = (h != 24)
        try:
            pred_resp = agent.analyze(
                pred_req,
                weather_result=weather_res,
                skip_explainability=skip_expl,
            )
        except TypeError:
            try:
                pred_resp = agent.analyze(pred_req, weather_result=weather_res)
            except TypeError:
                pred_resp = agent.analyze(pred_req)

        is_certified = h <= 240
        within_h = pred_resp.within_trust_horizon if pred_resp.within_trust_horizon is not None else (h <= 168)
        op_trust_h = pred_resp.operational_trust_horizon_hours if pred_resp.operational_trust_horizon_hours is not None else 168
        dec_mode = pred_resp.decision_mode or DecisionMode.ABSTAINED.value

        point = DashboardTimelinePoint(
            lead_hours=h,
            lead_days=lead_days,
            valid_time=valid_iso,
            bust_probability=pred_resp.bust_probability,
            risk_level=pred_resp.risk_level,
            trust_state=pred_resp.trust_state,
            abstain=pred_resp.abstain,
            reason_codes=pred_resp.reason_codes,
            calibration_status=pred_resp.calibration_status,
            decision_mode=dec_mode,
            within_trust_horizon=within_h,
            operational_trust_horizon_hours=op_trust_h,
            is_certified_horizon=is_certified,
        )

        # Mark the canonical 24h prediction for selected_prediction
        selected = pred_resp if h == 24 else None
        return h, point, selected

    def orchestrate(
        self, request: DashboardRequest, request_id: Optional[str] = None
    ) -> DashboardIntelligenceResponse:
        """Synthesize unified multi-horizon intelligence for a single dashboard request.

        Optimized pipeline:
        1. Parse issue timestamp (if explicit)
        2. Resolve location ONCE
        3. Fetch weather data ONCE to prime cache and extract issue_time
        4. Evaluate ALL horizons IN PARALLEL (weather cache ensures instant hits)
        5. Assemble deterministic summary
        """
        horizons = self.get_horizons_for_mode(request.mode)
        total_points = len(horizons)

        # 1. Parse base issue timestamp if explicitly requested
        base_issue_dt: Optional[datetime] = None
        if request.issue_time:
            try:
                raw = request.issue_time.strip().replace("Z", "+00:00")
                parsed = datetime.fromisoformat(raw)
                base_issue_dt = parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except Exception as err:
                logger.warning("Failed to parse requested issue_time '%s': %s", request.issue_time, err)

        # 2. Resolve geographic location ONCE (not per-horizon)
        resolved = self.location_service.resolve(request.location)
        if resolved is None or resolved.latitude is None or resolved.longitude is None:
            # Short-circuit on invalid location without triggering upstream weather requests
            default_metrics.record_abstention(ReasonCode.INVALID_LOCATION.value)
            default_metrics.record_dashboard_request("ABSTAINED", total_points, 0, total_points)

            if base_issue_dt is None:
                now = datetime.now(timezone.utc)
                base_issue_dt = now.replace(hour=(now.hour // 6) * 6, minute=0, second=0, microsecond=0)

            issue_iso = base_issue_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            location_ctx = DashboardLocationContext(
                query=request.location,
                resolved_name=None,
                latitude=None,
                longitude=None,
                region_id=None,
            )
            abstained_pred = PredictionResponse(
                location=request.location,
                bust_probability=None,
                risk_level=None,
                trust_state=TrustState.UNAVAILABLE,
                abstain=True,
                reason_codes=[ReasonCode.INVALID_LOCATION],
                calibration_status=CalibrationStatus.UNAVAILABLE,
                decision_mode=DecisionMode.ABSTAINED,
            )
            timeline_points = [
                DashboardTimelinePoint(
                    lead_hours=h,
                    lead_days=round(h / 24.0, 1),
                    valid_time=(base_issue_dt + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    bust_probability=None,
                    risk_level=None,
                    trust_state=TrustState.UNAVAILABLE,
                    abstain=True,
                    reason_codes=[ReasonCode.INVALID_LOCATION],
                    calibration_status=CalibrationStatus.UNAVAILABLE,
                    decision_mode=DecisionMode.ABSTAINED,
                    within_trust_horizon=h <= 168,
                    operational_trust_horizon_hours=168,
                    is_certified_horizon=h <= 240,
                )
                for h in horizons
            ]
            summary = DashboardSummary(
                available_points=0,
                abstained_points=total_points,
                total_points=total_points,
                max_bust_probability=None,
                max_risk_level=None,
                max_risk_lead_hours=None,
                mean_bust_probability=None,
                elevated_risk_points=0,
                first_elevated_risk_lead_hours=None,
                overall_decision_mode=DecisionMode.ABSTAINED,
            )
            return DashboardIntelligenceResponse(
                status=DashboardStatus.ABSTAINED,
                location=location_ctx,
                variable=request.variable or "temperature_2m",
                issue_time=issue_iso,
                mode=request.mode,
                selected_prediction=abstained_pred,
                timeline=timeline_points,
                summary=summary,
                scientific_context=DashboardScientificContext(),
                request_id=request_id,
            )

        region_id_val = getattr(resolved, "region_id", None)
        if not region_id_val and resolved.country == "India":
            region_id_val = f"IN_{resolved.name.upper().replace(' ', '_')}"

        location_ctx = DashboardLocationContext(
            query=request.location,
            resolved_name=resolved.name,
            latitude=resolved.latitude,
            longitude=resolved.longitude,
            region_id=region_id_val,
        )

        agent = self._get_agent()
        if hasattr(agent, "fallback_service") and hasattr(agent.fallback_service, "enable_fallback_cache"):
            agent.fallback_service.enable_fallback_cache = getattr(settings, "WEATHER_FALLBACK_CACHE_ENABLED", True)

        # 3. Fetch weather data ONCE upfront
        #    WeatherResult is shared across all horizon workers, eliminating
        #    redundant upstream network calls, geocoding lookups, and JSON parsing.
        #    Tailor forecast_days to requested mode to avoid fetching unused days:
        #    - single (24h lead): 3 days buffer (72h)
        #    - standard_7d (168h lead): 8 days buffer (192h)
        #    - full_16d (384h lead): 16 days (384h)
        max_h = max(horizons) if horizons else 24
        needed_days = min(16, max(3, (max_h + 23) // 24 + 1))

        weather_res: Optional[Any] = None
        if hasattr(agent, "get_weather_data"):
            try:
                try:
                    weather_res = agent.get_weather_data(request.location, None, forecast_days=needed_days)
                except TypeError:
                    weather_res = agent.get_weather_data(request.location, None)

                if (weather_res is None or not weather_res.is_available or weather_res.error) and hasattr(agent, "fallback_service"):
                    fb = agent.fallback_service.handle_download_failure(request.location)
                    if fb.recovered and fb.weather_data:
                        weather_res = fb.weather_data

                if weather_res and weather_res.is_available and weather_res.raw_data:
                    raw_records = weather_res.raw_data.get("records", [])
                    if raw_records and base_issue_dt is None:
                        first_issue = raw_records[0].get("issue_time")
                        if first_issue:
                            try:
                                parsed_first = datetime.fromisoformat(first_issue.replace("Z", "+00:00"))
                                base_issue_dt = parsed_first.astimezone(timezone.utc) if parsed_first.tzinfo else parsed_first.replace(tzinfo=timezone.utc)
                            except Exception:
                                pass
            except Exception as exc:
                logger.debug("Could not pre-fetch weather: %s", exc)

        if base_issue_dt is None:
            now = datetime.now(timezone.utc)
            base_issue_dt = now.replace(hour=(now.hour // 6) * 6, minute=0, second=0, microsecond=0)

        issue_iso = base_issue_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 4. Evaluate ALL horizons IN PARALLEL with shared weather_res
        #    Feature engineering + ML inference + safety run concurrently across threads.
        timeline_results: Dict[int, Tuple[DashboardTimelinePoint, Optional[PredictionResponse]]] = {}
        variable = request.variable or "temperature_2m"

        effective_workers = min(self.max_workers, len(horizons))

        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            future_to_h = {
                executor.submit(
                    self._evaluate_single_horizon,
                    agent,
                    request.location,
                    variable,
                    issue_iso,
                    h,
                    weather_res,
                ): h
                for h in horizons
            }

            for future in as_completed(future_to_h):
                h = future_to_h[future]
                try:
                    lead_hours, point, selected = future.result()
                    timeline_results[lead_hours] = (point, selected)
                except Exception as exc:
                    logger.error("Horizon h=%d evaluation failed: %s", h, exc)
                    # Produce an abstained point for this failed horizon
                    lead_days = round(h / 24.0, 1)
                    valid_dt = base_issue_dt + timedelta(hours=h)
                    valid_iso = valid_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    fallback_point = DashboardTimelinePoint(
                        lead_hours=h,
                        lead_days=lead_days,
                        valid_time=valid_iso,
                        bust_probability=None,
                        risk_level=None,
                        trust_state=TrustState.UNAVAILABLE,
                        abstain=True,
                        reason_codes=[ReasonCode.INTERNAL_ERROR],
                        calibration_status=CalibrationStatus.UNAVAILABLE,
                        decision_mode=DecisionMode.ABSTAINED,
                        within_trust_horizon=h <= 168,
                        operational_trust_horizon_hours=168,
                        is_certified_horizon=h <= 240,
                    )
                    timeline_results[h] = (fallback_point, None)

        # Reassemble timeline in canonical lead-hour order (deterministic)
        timeline_points: List[DashboardTimelinePoint] = []
        selected_pred: Optional[PredictionResponse] = None
        for h in horizons:
            point, selected = timeline_results.get(h, (None, None))
            if point is not None:
                timeline_points.append(point)
            if selected is not None:
                selected_pred = selected

        if selected_pred is None:
            fallback_req = PredictionRequest(
                location=request.location,
                variable=variable,
            )
            try:
                selected_pred = agent.analyze(fallback_req, weather_result=weather_res)
            except TypeError:
                selected_pred = agent.analyze(fallback_req)

        # 5. Compute deterministic summary intelligence
        valid_points = [p for p in timeline_points if p.bust_probability is not None]
        available_cnt = len(valid_points)
        abstained_cnt = total_points - available_cnt

        if available_cnt == 0:
            summary = DashboardSummary(
                available_points=0,
                abstained_points=total_points,
                total_points=total_points,
                max_bust_probability=None,
                max_risk_level=None,
                max_risk_lead_hours=None,
                mean_bust_probability=None,
                elevated_risk_points=0,
                first_elevated_risk_lead_hours=None,
                overall_decision_mode=DecisionMode.ABSTAINED,
            )
            status = DashboardStatus.ABSTAINED
        else:
            valid_probs = [p.bust_probability for p in valid_points if p.bust_probability is not None]
            max_pt = max(valid_points, key=lambda p: (p.bust_probability if p.bust_probability is not None else -1.0))
            max_prob = max_pt.bust_probability
            max_risk = max_pt.risk_level
            max_lead = max_pt.lead_hours
            mean_prob = round(sum(valid_probs) / len(valid_probs), 4)

            elevated = [
                p for p in valid_points
                if p.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)
            ]
            elevated_cnt = len(elevated)
            first_elevated_lead = elevated[0].lead_hours if elevated else None

            # Peak operational decision mode across valid points
            modes = {p.decision_mode for p in valid_points}
            if DecisionMode.CRITICAL_INTERVENTION in modes:
                overall_mode = DecisionMode.CRITICAL_INTERVENTION
            elif DecisionMode.HIGH_UNCERTAINTY in modes:
                overall_mode = DecisionMode.HIGH_UNCERTAINTY
            elif DecisionMode.ELEVATED_AWARENESS in modes:
                overall_mode = DecisionMode.ELEVATED_AWARENESS
            elif DecisionMode.STANDARD_MONITORING in modes:
                overall_mode = DecisionMode.STANDARD_MONITORING
            else:
                overall_mode = DecisionMode.ABSTAINED

            summary = DashboardSummary(
                available_points=available_cnt,
                abstained_points=abstained_cnt,
                total_points=total_points,
                max_bust_probability=max_prob,
                max_risk_level=max_risk,
                max_risk_lead_hours=max_lead,
                mean_bust_probability=mean_prob,
                elevated_risk_points=elevated_cnt,
                first_elevated_risk_lead_hours=first_elevated_lead,
                overall_decision_mode=overall_mode,
            )

            status = DashboardStatus.SUCCESS if abstained_cnt == 0 else DashboardStatus.PARTIAL

        # 6. Record telemetry
        default_metrics.record_dashboard_request(
            outcome=status.value,
            total_points=total_points,
            valid_points=available_cnt,
            abstained_points=abstained_cnt,
        )

        return DashboardIntelligenceResponse(
            status=status,
            location=location_ctx,
            variable=variable,
            issue_time=issue_iso,
            mode=request.mode,
            selected_prediction=selected_pred,
            timeline=timeline_points,
            summary=summary,
            scientific_context=DashboardScientificContext(),
            request_id=request_id,
        )
