"""Hazard, Trajectory, Failure Motifs, and Failure Memory API endpoints (Gate 2 / Phase C)."""

from typing import List, Optional
from fastapi import APIRouter, Query

from backend.app.builder2.failure_memory import FailureMemoryStore
from backend.app.builder2.failure_motifs import (
    CANONICAL_FAILURE_MOTIFS,
    FailureMotif,
    MotifClassifier,
    MotifMatchResult,
)
from backend.app.builder2.hazard_engine import HazardTrajectoryEngine
from backend.app.contracts.hazard_contracts import HazardFamily
from backend.app.schemas.reliability_state import ReliabilityState

router = APIRouter()

_trajectory_engine = HazardTrajectoryEngine()
_motif_classifier = MotifClassifier()
_memory_store = FailureMemoryStore()


@router.get("/hazard/trajectory", response_model=ReliabilityState)
async def get_hazard_trajectory(
    location: str = Query(..., description="Location name or station"),
    variable: str = Query(default="temperature_2m", description="Meteorological variable"),
    issue_time: str = Query(default="2026-09-20T00:00:00Z", description="UTC issue time"),
    lead_hours: int = Query(default=48, ge=0, le=360),
    base_bust_prob: float = Query(default=0.0569, ge=0.0, le=1.0),
    hazard_family: Optional[HazardFamily] = Query(default=None),
) -> ReliabilityState:
    """Retrieve full multi-horizon hazard curve, survival curve, and recovery dynamics."""
    return _trajectory_engine.build_reliability_state(
        forecast_identity=f"FC_{location}_{variable}_{lead_hours}h",
        issue_time=issue_time,
        location=location,
        variable=variable,
        lead_hours=lead_hours,
        model_version="veyra-v3-challenger",
        base_bust_prob=base_bust_prob,
        ensemble_mean=300.0,
        ensemble_std=1.5,
        hazard_family=hazard_family,
    )


@router.get("/hazard/motifs", response_model=List[FailureMotif])
async def get_motif_catalog(
    hazard_family: Optional[HazardFamily] = Query(default=None),
) -> List[FailureMotif]:
    """Retrieve canonical Failure Motifs filtered by hazard family."""
    if hazard_family:
        return [m for m in CANONICAL_FAILURE_MOTIFS if m.hazard_family == hazard_family]
    return CANONICAL_FAILURE_MOTIFS


@router.get("/hazard/motifs/match", response_model=List[MotifMatchResult])
async def match_failure_motif(
    precursor_signals: str = Query(
        default="HIGH_Z500_ANOMALY,SUBSIDENCE_WARMING",
        description="Comma-separated physical precursor signals",
    ),
    hazard_family: Optional[HazardFamily] = Query(default=None),
) -> List[MotifMatchResult]:
    """Classify current atmospheric signals against canonical Failure Motifs."""
    signals = [s.strip() for s in precursor_signals.split(",") if s.strip()]
    sample_trajectory = [0.1, 0.3, 0.6, 0.8, 0.9]
    return _motif_classifier.classify(
        trajectory=sample_trajectory,
        precursor_signals=signals,
        hazard_family=hazard_family,
    )


@router.get("/hazard/episodes")
async def get_failure_episodes(
    hazard_family: Optional[HazardFamily] = Query(default=None),
    lead_hours: Optional[int] = Query(default=48),
    top_k: int = Query(default=5, ge=1, le=50),
):
    """Retrieve historical Failure Memory analogs with sample support and uncertainty."""
    query_vector = [0.5, 0.5, 0.5, 0.5]
    result = _memory_store.retrieve_analogs(
        query_vector=query_vector,
        hazard=hazard_family,
        lead_hours=lead_hours,
        top_k=top_k,
    )
    return result.model_dump()
