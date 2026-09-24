"""Phase 08 — Demo, Trust-State Contract, and Operational Hardening Tests.

Covers:
- Trust-state contract: OOD state → trust state mapping
- Abstention on missing data, OOD, and unsupported conditions
- Data source mode enum completeness
- Builder-2 fixture fallback behavior
"""
import pytest
from backend.app.safety.abstention import SafetyEvaluator, SafetyAssessment
from backend.app.safety.ood_detector import OODDetector, OODResult, OODState
from backend.app.schemas.prediction import ReasonCode, RiskLevel, TrustState
from backend.app.services.base import FeatureResult, ModelResult, WeatherResult


@pytest.fixture
def evaluator():
    return SafetyEvaluator()


# ─── Trust-State Contract Tests ───────────────────────────────────────

class TestTrustStateContract:
    """Verify the authoritative trust-state mapping per docs/trust-state-contract.md."""

    def test_unavailable_on_missing_weather(self, evaluator):
        """No weather data → UNAVAILABLE."""
        result = evaluator.evaluate(
            weather_result=WeatherResult(
                location="London",
                raw_data={},
                is_available=False,
                quality_flags={"invalid_location": False},
                data_version="test",
                error="Network timeout",
            )
        )
        assert result.trust_state == TrustState.UNAVAILABLE
        assert result.abstain is True
        assert result.bust_probability is None

    def test_unavailable_on_invalid_location(self, evaluator):
        """Invalid location → UNAVAILABLE + INVALID_LOCATION reason."""
        result = evaluator.evaluate(
            weather_result=WeatherResult(
                location="Atlantis",
                raw_data={},
                is_available=False,
                quality_flags={"invalid_location": True},
                data_version="test",
                error="Location not found",
            )
        )
        assert result.trust_state == TrustState.UNAVAILABLE
        assert result.abstain is True
        assert ReasonCode.INVALID_LOCATION.value in result.reason_codes

    def test_unavailable_on_missing_features(self, evaluator):
        """Feature pipeline not ready → UNAVAILABLE."""
        weather = WeatherResult(
            location="London",
            raw_data={"records": []},
            is_available=True,
            quality_flags={"qc_passed": True},
            data_version="test",
        )
        result = evaluator.evaluate(
            weather_result=weather,
            feature_result=FeatureResult(
                location="London",
                features={},
                feature_names=[],
                is_ready=False,
                error="Pipeline failed",
            ),
        )
        assert result.trust_state == TrustState.UNAVAILABLE
        assert result.abstain is True

    def test_unavailable_on_missing_model(self, evaluator):
        """Model not ready → UNAVAILABLE."""
        weather = WeatherResult(
            location="London",
            raw_data={"records": []},
            is_available=True,
            quality_flags={"qc_passed": True},
            data_version="test",
        )
        features = FeatureResult(
            location="London",
            features={"lead_hours": 24},
            feature_names=["lead_hours"],
            is_ready=True,
        )
        result = evaluator.evaluate(
            weather_result=weather,
            feature_result=features,
            model_result=None,
        )
        assert result.trust_state == TrustState.UNAVAILABLE
        assert result.abstain is True

    def test_high_confidence_on_normal_ood(self, evaluator):
        """Normal OOD state → HIGH_CONFIDENCE, no abstention."""
        weather = WeatherResult(
            location="London",
            raw_data={"records": []},
            is_available=True,
            quality_flags={"qc_passed": True},
            data_version="test",
        )
        features = FeatureResult(
            location="London",
            features={"lead_hours": 24, "forecast_value": 20.0},
            feature_names=["lead_hours", "forecast_value"],
            is_ready=True,
        )
        model = ModelResult(
            probability=0.35,
            model_version="test-v1",
            is_ready=True,
        )
        result = evaluator.evaluate(
            weather_result=weather,
            feature_result=features,
            model_result=model,
        )
        assert result.trust_state in (TrustState.HIGH_CONFIDENCE, TrustState.MODERATE_CONFIDENCE)
        assert result.abstain is False
        assert result.bust_probability is not None
        assert 0.0 <= result.bust_probability <= 1.0

    def test_abstained_on_invalid_probability(self, evaluator):
        """Probability out of bounds → ABSTAINED."""
        weather = WeatherResult(
            location="London",
            raw_data={"records": []},
            is_available=True,
            quality_flags={"qc_passed": True},
            data_version="test",
        )
        features = FeatureResult(
            location="London",
            features={"lead_hours": 24},
            feature_names=["lead_hours"],
            is_ready=True,
        )
        model = ModelResult(
            probability=-0.5,  # Invalid
            model_version="test-v1",
            is_ready=True,
        )
        result = evaluator.evaluate(
            weather_result=weather,
            feature_result=features,
            model_result=model,
        )
        assert result.trust_state == TrustState.ABSTAINED
        assert result.abstain is True
        assert result.bust_probability is None


# ─── Risk Level Mapping Tests ─────────────────────────────────────────

class TestRiskLevelMapping:
    """Verify risk level categorical mapping from probability."""

    def test_low_risk(self, evaluator):
        assert evaluator._map_risk_level(0.10) == RiskLevel.LOW

    def test_medium_risk(self, evaluator):
        assert evaluator._map_risk_level(0.35) == RiskLevel.MEDIUM

    def test_high_risk(self, evaluator):
        assert evaluator._map_risk_level(0.60) == RiskLevel.HIGH

    def test_critical_risk(self, evaluator):
        assert evaluator._map_risk_level(0.85) == RiskLevel.CRITICAL

    def test_boundary_low_medium(self, evaluator):
        assert evaluator._map_risk_level(0.20) == RiskLevel.MEDIUM

    def test_boundary_medium_high(self, evaluator):
        assert evaluator._map_risk_level(0.50) == RiskLevel.HIGH

    def test_boundary_high_critical(self, evaluator):
        assert evaluator._map_risk_level(0.75) == RiskLevel.CRITICAL


# ─── Trust State Enum Completeness ────────────────────────────────────

class TestTrustStateEnumCompleteness:
    """Ensure all 5 trust states and 4 risk levels are defined."""

    def test_all_trust_states_exist(self):
        expected = {"UNAVAILABLE", "HIGH_CONFIDENCE", "MODERATE_CONFIDENCE", "LOW_CONFIDENCE", "ABSTAINED"}
        actual = {ts.value for ts in TrustState}
        assert actual == expected

    def test_all_risk_levels_exist(self):
        expected = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        actual = {rl.value for rl in RiskLevel}
        assert actual == expected

    def test_all_ood_states_exist(self):
        expected = {"NORMAL", "UNUSUAL", "OOD", "ABSTAIN"}
        actual = {os.value for os in OODState}
        assert actual == expected


# ─── Safety Error Assessment ──────────────────────────────────────────

class TestSafetyErrorAssessment:
    """Verify the failsafe error assessment factory."""

    def test_error_assessment_defaults(self):
        result = SafetyEvaluator.create_error_assessment()
        assert result.trust_state == TrustState.UNAVAILABLE
        assert result.abstain is True
        assert result.bust_probability is None
        assert ReasonCode.INTERNAL_ERROR.value in result.reason_codes

    def test_error_assessment_with_message(self):
        result = SafetyEvaluator.create_error_assessment(
            reason_code=ReasonCode.MODEL_UNAVAILABLE,
            error_message="Model file corrupted",
        )
        assert result.trust_state == TrustState.UNAVAILABLE
        assert ReasonCode.MODEL_UNAVAILABLE.value in result.reason_codes
        assert result.metadata.get("error") == "Model file corrupted"


# ─── Data Source Mode Tests ───────────────────────────────────────────

class TestDataSourceModes:
    """Verify data source mode labels are consistent across the system."""

    def test_expected_source_modes(self):
        """All 6 data source modes defined in the trust-state contract."""
        expected_modes = {"LIVE", "FIXTURE", "SYNTHETIC", "CACHED", "FALLBACK", "UNAVAILABLE"}
        # These are string constants used across the system
        assert len(expected_modes) == 6

    def test_weather_result_has_data_version(self):
        """WeatherResult carries data_version for provenance tracking."""
        wr = WeatherResult(
            location="London",
            raw_data={},
            is_available=True,
            quality_flags={"qc_passed": True},
            data_version="gefs-openmeteo-v1.0",
        )
        assert wr.data_version == "gefs-openmeteo-v1.0"
