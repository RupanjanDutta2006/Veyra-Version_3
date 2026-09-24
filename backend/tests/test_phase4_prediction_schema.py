"""Unit and integration tests for Phase 4 prediction schema expansion (SIH26079 §12, §15.1).

Covers:
- G2: Split-conformal prediction intervals (§11.2)
- G3: Severity estimates and versioned severity class v2.0-q95-mad (§8.2)
- G4: Spatial extent, area fraction, object count, centroids, GeoJSON risk fields (§12, §17)
- G5: Time-to-first-failure horizon tracking (§12)
- G7: Auditable reason codes and physical driver attribution (§12)
- G8: Multi-signal out-of-distribution evaluation (§11.3)
- G9: Historical analog cards with event exclusion (§12, §21)
- G10: Per-prediction claim scope declaration (§2.1)
- G11: Ground truth verification lifecycle status (§12)
- G12: 5-tier color risk band taxonomy (§12.1)
- A6: Z500 geopotential height 500hPa meteorological variable support
- PredictionEnvelope authoritative contract serialization
"""
import pytest
from unittest.mock import MagicMock

from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.ml.conformal import SplitConformalPredictor, METHOD_DECLARATION
from backend.app.safety.abstention import SafetyAssessment, SafetyEvaluator
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    ReasonCode,
    RiskLevel,
    TrustState,
    SUPPORTED_VARIABLES,
)
from backend.app.schemas.prediction_envelope import PredictionEnvelope
from backend.app.schemas.risk_bands import (
    ColorRiskBand,
    RISK_BAND_TABLE,
    map_probability_to_color_band,
)
from backend.app.services.analog_service import (
    BENCHMARK_ANALOG_ARCHIVE,
    HistoricalAnalogCase,
    HistoricalAnalogService,
)
from backend.app.services.base import FeatureResult, ModelResult, WeatherResult
from backend.app.services.spatial_service import SpatialRiskService


class TestPhase4RiskBandsG12:
    """Test G12: 5-tier color risk band mapping per §12.1."""

    def test_color_risk_band_mapping_thresholds(self):
        # Green (< 0.20)
        green_res = map_probability_to_color_band(0.12)
        assert green_res.color_band == ColorRiskBand.GREEN
        assert green_res.risk_level == RiskLevel.LOW
        assert green_res.decision_mode == "STANDARD_MONITORING"

        # Yellow (0.20 - 0.50)
        yellow_res = map_probability_to_color_band(0.35)
        assert yellow_res.color_band == ColorRiskBand.YELLOW
        assert yellow_res.risk_level == RiskLevel.MEDIUM
        assert yellow_res.decision_mode == "ACTIVE_MONITORING"

        # Orange (0.50 - 0.75)
        orange_res = map_probability_to_color_band(0.62)
        assert orange_res.color_band == ColorRiskBand.ORANGE
        assert orange_res.risk_level == RiskLevel.HIGH
        assert orange_res.decision_mode == "HEIGHTENED_ALERT"

        # Red (>= 0.75)
        red_res = map_probability_to_color_band(0.88)
        assert red_res.color_band == ColorRiskBand.RED
        assert red_res.risk_level == RiskLevel.CRITICAL
        assert red_res.decision_mode == "EMERGENCY_ALERT"

    def test_gray_band_on_abstain_or_ood(self):
        gray_abstained = map_probability_to_color_band(0.65, is_abstained=True)
        assert gray_abstained.color_band == ColorRiskBand.GRAY
        assert gray_abstained.risk_level is None
        assert gray_abstained.decision_mode == "ABSTAINED"

        gray_ood = map_probability_to_color_band(0.65, is_abstained=False, ood_state="ABSTAIN")
        assert gray_ood.color_band == ColorRiskBand.GRAY

        gray_none = map_probability_to_color_band(None)
        assert gray_none.color_band == ColorRiskBand.GRAY


class TestPhase4ConformalIntervalsG2:
    """Test G2: Split-conformal prediction intervals (§11.2)."""

    def test_conformal_interval_generation_and_contract(self):
        predictor = SplitConformalPredictor(confidence_level=0.90)
        interval = predictor.predict_interval(0.45)
        data = interval.to_dict()

        assert "lower_bound" in data
        assert "upper_bound" in data
        assert "bandwidth" in data
        assert "confidence_level" in data
        assert "method" in data
        assert data["lower_bound"] <= 0.45 <= data["upper_bound"]
        assert 0.0 <= data["lower_bound"] <= 1.0
        assert 0.0 <= data["upper_bound"] <= 1.0
        assert round(data["bandwidth"], 4) == round(data["upper_bound"] - data["lower_bound"], 4)
        assert METHOD_DECLARATION in data["method"]

    def test_conformal_calibration_quantile(self):
        predictor = SplitConformalPredictor(confidence_level=0.90)
        y_true = [0, 0, 1, 1, 0, 1, 0, 1, 0, 0]
        y_prob = [0.1, 0.2, 0.8, 0.9, 0.15, 0.85, 0.05, 0.95, 0.2, 0.3]
        predictor.calibrate(y_true, y_prob)

        assert predictor.is_calibrated
        assert predictor.calibrated_quantile is not None
        interval = predictor.predict_interval(0.50)
        assert interval.lower_bound < 0.50 < interval.upper_bound


class TestPhase4SpatialExtentG4:
    """Test G4: Spatial extent, area fraction, object count, and centroids (§12)."""

    def test_spatial_extent_scaling(self):
        service = SpatialRiskService()

        # Low risk: 0 objects, minimal area fraction
        low_res = service.compute_spatial_extent("Kolkata", 0.10)
        assert low_res is not None
        assert low_res.object_count == 0
        assert low_res.area_fraction < 0.05
        assert len(low_res.centroids) == 0

        # Moderate risk: 1 object
        med_res = service.compute_spatial_extent("Kolkata", 0.35)
        assert med_res is not None
        assert med_res.object_count == 1
        assert len(med_res.centroids) == 1
        assert med_res.centroids[0]["cluster_id"] == 1

        # High risk: 2 objects
        high_res = service.compute_spatial_extent("Kolkata", 0.65)
        assert high_res is not None
        assert high_res.object_count == 2
        assert len(high_res.centroids) == 2

        # Severe risk: 3 objects, large area fraction
        sev_res = service.compute_spatial_extent("Kolkata", 0.85)
        assert sev_res is not None
        assert sev_res.object_count == 3
        assert len(sev_res.centroids) == 3
        assert sev_res.area_fraction > 0.60
        assert sev_res.risk_field is not None
        assert sev_res.risk_field["type"] == "FeatureCollection"
        assert len(sev_res.risk_field["features"]) == 3

    def test_spatial_extent_abstained(self):
        service = SpatialRiskService()
        res = service.compute_spatial_extent("Kolkata", None, is_abstained=True)
        assert res is None


class TestPhase4HistoricalAnalogsG9:
    """Test G9: Historical analog retrieval with strict event exclusion."""

    def test_analog_service_event_exclusion(self):
        service = HistoricalAnalogService(event_exclusion_days=14)
        # Query near HW-2015-DELHI (2015-05-24) within 14 days -> should exclude it
        res = service.find_analogs(
            query_time="2015-05-28T00:00:00Z",
            variable="temperature_2m",
            lead_hours=48,
            forecast_value=44.0,
            ensemble_std=1.2,
            location="Delhi",
        )
        # Case from 2015-05-24 must be excluded
        case_ids = [c.case_id for c in res.analog_cards]
        assert "HW-2015-DELHI" not in case_ids

    def test_analog_service_temporal_leakage_prevention(self):
        service = HistoricalAnalogService()
        # Query before 2015 -> no cases in 2015 or later should be returned
        res = service.find_analogs(
            query_time="2014-01-01T00:00:00Z",
            variable="temperature_2m",
            lead_hours=48,
            forecast_value=30.0,
            ensemble_std=1.0,
        )
        # All benchmark cases are 2015+, so status should be NO_ELIGIBLE_ANALOG
        assert res.status == "NO_ELIGIBLE_ANALOG"
        assert len(res.analog_cards) == 0


class TestPhase4Z500SupportA6:
    """Test A6: Support for geopotential_height_500hPa (Z500)."""

    def test_z500_in_supported_variables(self):
        assert "geopotential_height_500hPa" in SUPPORTED_VARIABLES
        assert "z500" in SUPPORTED_VARIABLES

    def test_prediction_request_accepts_z500(self):
        req1 = PredictionRequest(location="Delhi", variable="geopotential_height_500hPa")
        assert req1.variable == "geopotential_height_500hPa"

        req2 = PredictionRequest(location="Delhi", variable="z500")
        assert req2.variable == "z500"


class TestPhase4ForecastBustAgentPipeline:
    """Integration test of ForecastBustAgent producing all Phase 4 fields."""

    def test_agent_produces_full_phase4_fields(self):
        weather_res = WeatherResult(
            location="Delhi",
            is_available=True,
            metadata={
                "lead_hours": 48,
                "valid_time": "2026-06-15T00:00:00Z",
                "issue_time": "2026-06-13T00:00:00Z",
                "variable": "temperature_2m",
                "latitude": 28.6139,
                "longitude": 77.2090,
            },
        )
        feat_res = FeatureResult(
            location="Delhi",
            is_ready=True,
            features={
                "lead_hours": 48.0,
                "surface_value": 43.5,
                "ensemble_spread": 2.8,
                "revision_accel_6h": 1.4,
                "ensemble_spread_to_iqr_ratio": 1.8,
            },
            metadata={"ood_distance": 1.2},
        )
        model_res = ModelResult(
            is_ready=True,
            probability=0.68,
            model_version="builder2-v3-lightgbm",
            metadata={
                "ood_score": 1.2,
                "ood_state": "NOMINAL",
                "normalized_error": 1.65,
                "spatial_fss": 0.42,
            },
        )
        safety_eval = MagicMock()
        safety_eval.evaluate.return_value = SafetyAssessment(
            bust_probability=0.68,
            risk_level=RiskLevel.HIGH,
            trust_state=TrustState.MODERATE_CONFIDENCE,
            abstain=False,
            reason_codes=[ReasonCode.HIGH_ENSEMBLE_SPREAD.value],
        )

        agent = ForecastBustAgent(safety_service=safety_eval)
        resp = agent.build_response(
            location="Delhi",
            safety_assessment=safety_eval.evaluate(),
            model_result=model_res,
            weather_result=weather_res,
            feature_result=feat_res,
        )

        # G12: Color risk band
        assert resp.color_band == "ORANGE"

        # G2: Probability interval
        assert resp.probability_interval is not None
        assert "lower_bound" in resp.probability_interval
        assert "upper_bound" in resp.probability_interval
        assert "bandwidth" in resp.probability_interval
        assert resp.probability_interval["confidence_level"] == 0.90

        # G3: Severity estimate & versioned class
        assert resp.severity_estimate == 1.65
        assert resp.severity_class == "v2.0-q95-mad"

        # G4: Spatial extent
        assert resp.spatial_extent is not None
        assert resp.spatial_extent["area_fraction"] > 0.0
        assert resp.spatial_extent["object_count"] == 2
        assert len(resp.spatial_extent["centroids"]) == 2

        # G5: Time to first failure
        assert resp.time_to_first_failure_hours == 48

        # G8: OOD status
        assert resp.ood_status is not None
        assert resp.ood_status["state"] == "NOMINAL"
        assert resp.ood_status["score"] == 1.2

        # G9: Historical analogs
        assert resp.analog_cards is not None
        assert isinstance(resp.analog_cards, list)

        # G10: Claim scope
        assert resp.claim_scope == "PUBLIC_PROXY_PROTOTYPE"

        # G11: Truth status
        assert resp.truth_status == "PENDING"

        # Envelope conversion
        envelope = resp.to_envelope()
        assert isinstance(envelope, PredictionEnvelope)
        assert envelope.color_band == ColorRiskBand.ORANGE
        assert envelope.claim_scope == "PUBLIC_PROXY_PROTOTYPE"
        assert envelope.truth_status == "PENDING"
        assert envelope.lead_hours == 48
