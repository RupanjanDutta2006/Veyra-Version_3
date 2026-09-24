"""Human-in-the-Loop Review and Approval API Endpoint (A2).

Implements the official Human-in-the-Loop Operational Gate per SIH26079 §1, §2.1, and Research File 076:
- Allows certified human forecasters to review, sign off on, or override automated Sentinel bust alerts.
- Records forecaster ID, approval status (PENDING, APPROVED, REJECTED, OVERRIDDEN), notes, and timestamp.
- Emits structured audit log events for all human decisions.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from backend.app.core.audit_logger import default_audit_logger
from backend.app.core.auth import AuthenticatedUser, UserRole, get_current_user, require_role

router = APIRouter()


class HumanApprovalStatus(str, Enum):
    """Status of human forecaster review for a forecast bust prediction."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"
    MONITORING = "MONITORING"


class HumanReviewSubmission(BaseModel):
    """Request payload for recording a forecaster review decision."""

    status: HumanApprovalStatus = Field(
        ...,
        description="Review decision: APPROVED (confirm alert), REJECTED (false alarm), OVERRIDDEN (manual risk assigned), MONITORING",
    )
    forecaster_id: str = Field(..., min_length=2, max_length=50, description="Forecaster badge or user ID")
    forecaster_notes: str = Field(..., min_length=5, max_length=1000, description="Meteorological rationale for review decision")
    overridden_probability: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional manual probability if status is OVERRIDDEN",
    )


class HumanReviewRecord(BaseModel):
    """Complete recorded review state for a prediction."""

    prediction_id: str
    status: HumanApprovalStatus
    forecaster_id: str
    forecaster_notes: str
    overridden_probability: Optional[float] = None
    reviewed_at: str
    audit_id: str


# In-memory store of human review decisions
_REVIEW_STORE: Dict[str, HumanReviewRecord] = {}


@router.post(
    "/predictions/{prediction_id}/review",
    response_model=HumanReviewRecord,
    summary="Record Human Forecaster Review Decision (A2)",
    description="Allows certified meteorologists to approve, reject, or override an automated Sentinel prediction (§1, §2.1).",
)
async def submit_prediction_review(
    prediction_id: str = Path(..., description="Unique prediction ID"),
    review: HumanReviewSubmission = ...,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> HumanReviewRecord:
    """Submit human review decision for an automated alert."""
    now_str = datetime.now(timezone.utc).isoformat()

    # Log to audit trail
    audit = default_audit_logger.log_event(
        event_type="HUMAN_REVIEW",
        action=f"FORECASTER_{review.status.value}",
        status="SUCCESS",
        prediction_id=prediction_id,
        user_id=review.forecaster_id,
        role=current_user.role.value,
        details={
            "status": review.status.value,
            "notes": review.forecaster_notes,
            "overridden_prob": review.overridden_probability,
        },
    )

    record = HumanReviewRecord(
        prediction_id=prediction_id,
        status=review.status,
        forecaster_id=review.forecaster_id,
        forecaster_notes=review.forecaster_notes,
        overridden_probability=review.overridden_probability,
        reviewed_at=now_str,
        audit_id=audit.audit_id,
    )
    _REVIEW_STORE[prediction_id] = record
    return record


@router.get(
    "/predictions/{prediction_id}/review",
    response_model=HumanReviewRecord,
    summary="Get Human Review State for Prediction (A2)",
    description="Retrieve the current human approval state and forecaster notes for a prediction.",
)
async def get_prediction_review(
    prediction_id: str = Path(..., description="Unique prediction ID"),
) -> HumanReviewRecord:
    """Retrieve human review record if exists."""
    record = _REVIEW_STORE.get(prediction_id)
    if not record:
        # Default pending state
        return HumanReviewRecord(
            prediction_id=prediction_id,
            status=HumanApprovalStatus.PENDING,
            forecaster_id="unassigned",
            forecaster_notes="No forecaster review has been recorded for this prediction yet.",
            reviewed_at=datetime.now(timezone.utc).isoformat(),
            audit_id="none",
        )
    return record
