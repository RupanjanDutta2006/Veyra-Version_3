"""Operational Watchlist and Promotion Status Contract for Veyra (Gate 10 / Phase K).

Defines strongly-typed Pydantic contracts for:
- Operational alert tiers (INFO, ADVISORY, WATCH, WARNING, CRITICAL)
- Promotion status taxonomy (FROZEN, CERTIFIED, OPERATIONAL_ONLY, EXPERIMENTAL, DIAGNOSTIC, ABSTAINED, REJECTED, FUTURE)
- Watchlist items with conformal intervals and spatial propagation risk
- Invariant: No experimental model output may appear as certified.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AlertTier(str, Enum):
    """Operational alert tiers based on forecast bust probability."""
    INFO = "INFO"
    ADVISORY = "ADVISORY"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class PromotionStatus(str, Enum):
    """Certified operational promotion status taxonomy."""
    FROZEN = "FROZEN"
    CERTIFIED = "CERTIFIED"
    OPERATIONAL_ONLY = "OPERATIONAL_ONLY"
    EXPERIMENTAL = "EXPERIMENTAL"
    DIAGNOSTIC = "DIAGNOSTIC"
    ABSTAINED = "ABSTAINED"
    REJECTED = "REJECTED"
    FUTURE = "FUTURE"


class WatchlistStatus(str, Enum):
    """Status of an item in the operational watchlist."""
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


class ConformalBounds(BaseModel):
    """Conformal prediction uncertainty bounds."""
    lower_bound: float = Field(..., ge=0.0, le=1.0)
    upper_bound: float = Field(..., ge=0.0, le=1.0)
    target_coverage: float = Field(default=0.90, ge=0.50, le=1.0)


class WatchlistItem(BaseModel):
    """Single item tracked on the operational hazard watchlist."""
    watchlist_id: str
    station_id: str
    station_name: str
    hazard_family: str
    lead_hours: int
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    conformal_interval: ConformalBounds
    alert_level: AlertTier
    created_at: datetime
    status: WatchlistStatus
    spatial_propagation_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class OperationalHazardDescriptor(BaseModel):
    """Registry descriptor for an operational hazard model."""
    hazard_family: str
    model_id: str
    model_version: str
    status: PromotionStatus
    endpoint_route: Optional[str] = None
    lead_hours_min: int = Field(default=0, ge=0)
    lead_hours_max: int = Field(default=120, ge=1)
    cadence_hours: int = Field(default=6, ge=1)
    primary_reference: str
    verification_latency_days: int
    calibrated_brier: float
    ece: float
    conformal_target_coverage: float = 0.90


def compute_alert_tier(failure_prob: float) -> AlertTier:
    """Classify failure probability into operational alert tier."""
    if failure_prob >= 0.75:
        return AlertTier.CRITICAL
    elif failure_prob >= 0.50:
        return AlertTier.WARNING
    elif failure_prob >= 0.30:
        return AlertTier.WATCH
    elif failure_prob >= 0.15:
        return AlertTier.ADVISORY
    else:
        return AlertTier.INFO
