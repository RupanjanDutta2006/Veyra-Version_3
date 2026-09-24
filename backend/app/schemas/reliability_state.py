"""Common ReliabilityState contract for Veyra (Blueprint Section 4 / Gate 1).

Defines the universal 30+ field operational state emitted by all downstream hazard specialists:
- Forecast identity, temporal anchors, atmospheric regime, and vertical structure
- Probabilistic bust risk, continuous error quantiles, hazard and survival curves
- Multi-horizon time-to-bust and time-to-recovery dynamics
- Failure Memory analogs and Failure Motif attributions
- Operational state machine: STABLE -> WATCHING -> DEGRADING -> FAILURE_PRONE -> ABSTAIN / BUST -> RECOVERING -> STABLE
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class OperationalReliabilityState(str, Enum):
    """Operational reliability lifecycle state machine."""
    STABLE = "STABLE"
    WATCHING = "WATCHING"
    DEGRADING = "DEGRADING"
    FAILURE_PRONE = "FAILURE_PRONE"
    ABSTAIN = "ABSTAIN"
    BUST = "BUST"
    RECOVERING = "RECOVERING"


class DecisionMode(str, Enum):
    """Operational decision mode recommended by Veyra."""
    NOMINAL = "NOMINAL"
    ELEVATED_CAUTION = "ELEVATED_CAUTION"
    CONSERVATIVE_DISPATCH = "CONSERVATIVE_DISPATCH"
    HUMAN_OVERRIDE_REQUIRED = "HUMAN_OVERRIDE_REQUIRED"
    ABSTAIN_UNSUPPORTED = "ABSTAIN_UNSUPPORTED"


class ContinuousErrorDistribution(BaseModel):
    """Continuous forecast error distribution estimates."""
    mean_error: float = Field(..., description="Expected mean signed error (bias)")
    mae: float = Field(..., description="Expected mean absolute error")
    rmse: float = Field(..., description="Expected root mean square error")
    q10: float = Field(..., description="10th percentile forecast error")
    q50: float = Field(..., description="Median (50th percentile) forecast error")
    q90: float = Field(..., description="90th percentile forecast error")
    crps: Optional[float] = Field(None, description="Continuous Ranked Probability Score")


class EnsembleSummary(BaseModel):
    """Statistical summary of ensemble members."""
    member_count: int = Field(..., ge=1)
    mean: float
    std: float = Field(..., ge=0.0)
    min_val: float
    max_val: float
    spread_to_error_ratio: Optional[float] = None
    ensemble_cv: Optional[float] = None


class EnsembleGeometry(BaseModel):
    """Ensemble phase-space dispersion and clustering geometry."""
    dispersion_metric: float = Field(..., ge=0.0)
    bimodality_coefficient: Optional[float] = None
    cluster_count: int = Field(default=1, ge=1)
    outlier_member_count: int = Field(default=0, ge=0)


class HazardPoint(BaseModel):
    """Probability of hazard occurrence at a specific lead time."""
    lead_hours: int = Field(..., ge=0)
    hazard_prob: float = Field(..., ge=0.0, le=1.0)
    bust_prob: float = Field(..., ge=0.0, le=1.0)


class FailureMemorySummary(BaseModel):
    """Retrieved historical failure memory signals."""
    analog_count: int = Field(default=0, ge=0)
    analog_bust_frequency: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_analog_episode_id: Optional[str] = None
    mean_historical_error: Optional[float] = None


class ReliabilityState(BaseModel):
    """Universal reliability contract emitted across all hazard specialists (Blueprint §4)."""

    # 1. Identity & Cadence
    forecast_identity: str = Field(..., description="Unique deterministic forecast run ID")
    issue_time: str = Field(..., description="UTC ISO-8601 forecast issue time (t0)")
    location: str = Field(..., description="Location name or coordinates")
    variable: str = Field(..., description="Target meteorological variable")
    lead_hours: int = Field(..., ge=0, description="Forecast lead horizon in hours")
    model_version: str = Field(..., description="Active reliability model version")

    # 2. Forecast State & Geometry
    forecast_values: Dict[str, Any] = Field(..., description="Raw and transformed forecast values")
    ensemble_summary: EnsembleSummary = Field(..., description="Statistical ensemble moments")
    ensemble_geometry: EnsembleGeometry = Field(..., description="Ensemble dispersion geometry")

    # 3. Probabilistic & Continuous Failure Risk
    bust_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Calibrated probability of exceeding error threshold (null if abstained)"
    )
    continuous_error_distribution: Optional[ContinuousErrorDistribution] = Field(
        None, description="Continuous error distribution estimates"
    )

    # 4. Hazard & Survival Curves
    hazard_type: Optional[str] = Field(None, description="Dominant active hazard family (e.g. PRECIPITATION)")
    hazard_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="P(hazard condition present)")
    hazard_curve: List[HazardPoint] = Field(default_factory=list, description="Multi-horizon hazard curve")
    survival_curve: List[float] = Field(default_factory=list, description="P(forecast survives without bust up to lead t)")

    # 5. Temporal Dynamics
    expected_time_to_bust: Optional[float] = Field(None, description="Estimated hours until forecast failure")
    expected_time_to_recovery: Optional[float] = Field(None, description="Estimated hours until forecast recovers")

    # 6. Memory & Motifs
    failure_memory: Optional[FailureMemorySummary] = Field(None, description="Historical failure memory analogs")
    failure_motif: Optional[str] = Field(None, description="Identified failure motif pattern code")

    # 7. Regimes & Spatial Propagation
    atmospheric_regime: Optional[str] = Field(None, description="Classified synoptic/macro regime")
    vertical_regime: Optional[str] = Field(None, description="Tropospheric vertical stability regime")
    spatial_risk: Optional[float] = Field(None, ge=0.0, le=1.0, description="Spatial neighborhood bust risk")
    propagation_score: Optional[float] = Field(None, description="Directional error propagation velocity/score")

    # 8. Novelty, Health & Governance
    ood_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Out-of-distribution novelty score")
    drift_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Inter-cycle forecast revision drift")
    missingness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Fraction of missing inputs")
    calibration_health: str = Field(default="NOMINAL", description="Calibration health status")
    reference_health: str = Field(default="VERIFIED", description="Reference source health status")

    # 9. Operational Lifecycle State & Decision
    reliability_state: OperationalReliabilityState = Field(
        ..., description="Current state in reliability lifecycle"
    )
    abstention_state: bool = Field(default=False, description="True if automated scoring is safely withheld")
    decision_mode: DecisionMode = Field(..., description="Operational decision recommendation")

    # 10. Evidence & Provenance
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Structured evidence graph attributions")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Cryptographic provenance and hashes")

    @model_validator(mode="after")
    def check_abstention_invariant(self) -> "ReliabilityState":
        if self.abstention_state and self.bust_probability is not None:
            raise ValueError("bust_probability must be null when abstention_state is True")
        return self
