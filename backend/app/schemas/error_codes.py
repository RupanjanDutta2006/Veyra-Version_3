"""Standardized Error Code Taxonomy and Error Envelope for Veyra API (SIH26079 §15, H13).

Provides stable, machine-readable error codes covering all operational failure modes:
- Upstream data delays, corruption, and unavailability.
- Out-of-distribution (OOD) abstentions.
- Historical analog misses ("NO_ELIGIBLE_ANALOG").
- Spatial risk map readiness.
- Validation, QC, calibration, and internal service errors.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field


class VeyraErrorCode(str, Enum):
    """Authoritative API error code taxonomy (§15, H13)."""

    # Data & Upstream Providers
    DATA_DELAYED = "DATA_DELAYED"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    DATA_CORRUPTED = "DATA_CORRUPTED"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_RATE_LIMITED = "UPSTREAM_RATE_LIMITED"

    # Safety, QC & Abstention
    QC_FAILED = "QC_FAILED"
    OOD_ABSTAIN = "OOD_ABSTAIN"
    OOD_DETECTED = "OOD_DETECTED"
    CALIBRATION_FAILURE = "CALIBRATION_FAILURE"
    EXTREME_VOLATILITY = "EXTREME_VOLATILITY"

    # Historical Analogs
    NO_ANALOG = "NO_ANALOG"
    NO_ELIGIBLE_ANALOG = "NO_ELIGIBLE_ANALOG"

    # Spatial & Mapping
    MAP_NOT_READY = "MAP_NOT_READY"
    SPATIAL_INDEX_UNAVAILABLE = "SPATIAL_INDEX_UNAVAILABLE"

    # Validation & Scope
    INVALID_LOCATION = "INVALID_LOCATION"
    INVALID_REGION = "INVALID_REGION"
    INVALID_VARIABLE = "INVALID_VARIABLE"
    INVALID_HORIZON = "INVALID_HORIZON"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    SCOPE_UNSUPPORTED = "SCOPE_UNSUPPORTED"

    # Model & Serving
    MODEL_NOT_READY = "MODEL_NOT_READY"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_FAILED = "MODEL_FAILED"

    # System & Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error explanation and operational remediation guidance."""

    error_code: VeyraErrorCode = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable summary of the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Diagnostic context or telemetry")
    resolution_guidance: Optional[str] = Field(
        default=None,
        description="Recommended action for the operator, forecaster, or client API",
    )


class ErrorResponseEnvelope(BaseModel):
    """Standardized top-level error response envelope matching §15.1."""

    error: ErrorDetail
    request_id: str = Field(
        default_factory=lambda: f"err_{uuid.uuid4().hex[:12]}",
        description="Unique request tracking identifier",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Error occurrence timestamp in ISO 8601 UTC",
    )
    status_code: int = Field(default=400, description="HTTP status code")
