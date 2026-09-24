"""Authoritative Prediction Envelope Schema matching SIH26079 §15.1.

Wraps single-horizon and multi-horizon predictions with complete audit provenance:
- Formal conformal probability intervals (§11.2, G2).
- Severity estimates & versioned classes (§8.2, G3).
- Spatial extent, area fraction, and centroids (§12, G4).
- Time-to-first-failure horizon tracking (§12, G5).
- Auditable reason codes and rich attribution (§12, G7).
- Real multi-signal OOD status (§11.3, G8).
- Historical analog cards with event exclusion (§12, G9).
- Explicit claim scope & verification status (§12, §15, G10, G11).
- Green/Yellow/Orange/Red/Gray color risk bands (§12.1, G12).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.schemas.explainability import ExplanationItem
from backend.app.schemas.prediction import ReasonCode, RiskLevel, TrustState
from backend.app.schemas.risk_bands import ColorRiskBand


class PredictionEnvelope(BaseModel):
    """Full prediction envelope with certified metadata and scientific provenance (§15.1)."""

    prediction_id: str = Field(
        default_factory=lambda: f"pred_{uuid.uuid4().hex[:12]}",
        description="Unique cryptographic identifier for this prediction instance",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Evaluation timestamp in ISO 8601 UTC format",
    )
    claim_scope: str = Field(
        default="PUBLIC_PROXY_PROTOTYPE",
        description="Declared operational scope and validation boundary (§2.1, G10)",
    )
    truth_status: str = Field(
        default="PENDING",
        description="Verification ground truth status: PENDING, VERIFIED, or UNVERIFIED (§12, G11)",
    )
    location: str = Field(
        ...,
        description="Target geographical location, city name, or coordinate pair",
    )
    variable: str = Field(
        default="temperature_2m",
        description="Evaluated meteorological variable",
    )
    issue_time: Optional[str] = Field(
        default=None,
        description="Forecast issuance timestamp in ISO 8601 UTC format",
    )
    valid_time: Optional[str] = Field(
        default=None,
        description="Forecast target valid timestamp in ISO 8601 UTC format",
    )
    lead_hours: Optional[int] = Field(
        default=None,
        description="Forecast lead time in hours (valid_time - issue_time)",
    )
    bust_probability: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Calibrated probability that forecast error exceeds bust threshold. null when abstained.",
    )
    probability_interval: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Split-conformal prediction interval: lower_bound, upper_bound, confidence_level, method (§11.2, G2)",
    )
    risk_level: Optional[RiskLevel] = Field(
        default=None,
        description="Categorical risk tier: LOW, MEDIUM, HIGH, CRITICAL",
    )
    color_band: ColorRiskBand = Field(
        default=ColorRiskBand.GRAY,
        description="5-tier operational risk band: GREEN, YELLOW, ORANGE, RED, GRAY (§12.1, G12)",
    )
    trust_state: TrustState = Field(
        default=TrustState.UNAVAILABLE,
        description="Model trust assessment: HIGH_CONFIDENCE, MODERATE_CONFIDENCE, LOW_CONFIDENCE, UNAVAILABLE, ABSTAINED",
    )
    abstain: bool = Field(
        default=True,
        description="Whether the sentinel safely abstains from automated prediction",
    )
    reason_codes: List[str] = Field(
        default_factory=list,
        description="Standardized machine-readable reason codes explaining prediction or abstention",
    )
    time_to_first_failure_hours: Optional[int] = Field(
        default=None,
        description="Earliest forecast lead time (hours) crossing bust alert threshold (§12, G5)",
    )
    severity_estimate: Optional[float] = Field(
        default=None,
        description="Continuous normalized error magnitude estimate relative to training MAD (§8.2, G3)",
    )
    severity_class: Optional[str] = Field(
        default="v2.0-q95-mad",
        description="Versioned bust severity class: low, moderate, or severe (§8.2, G3)",
    )
    spatial_extent: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Spatial risk distribution: area_fraction, object_count, centroids, risk_field (§12, G4)",
    )
    ood_status: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Multi-signal out-of-distribution evaluation: score, state, dominant_drivers (§11.3, G8)",
    )
    analog_cards: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical similar forecast failure and success cases (§12, §21, G9)",
    )
    explanation: Optional[ExplanationItem] = Field(
        default=None,
        description="Deterministic physical feature attribution and primary drivers",
    )
    model_version: Optional[str] = Field(
        default=None,
        description="Identifier of serving model artifact",
    )
    data_version: Optional[str] = Field(
        default=None,
        description="Identifier of ingested weather pipeline version",
    )
    decision_mode: Optional[str] = Field(
        default=None,
        description="Operational guidance mode (e.g. STANDARD_MONITORING, HEIGHTENED_ALERT, ABSTAINED)",
    )
    decision_guidance: Optional[str] = Field(
        default=None,
        description="Human-in-the-loop operational advisory text",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supplementary audit and pipeline execution telemetry",
    )
