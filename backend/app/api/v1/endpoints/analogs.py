"""Historical Analog Search API endpoint matching SIH26079 §12, §15, §21 (H7).

Retrieves similar historical NWP forecast failure and success cases using
normalized Euclidean state distance, strict ±14-day event exclusion, and
temporal anti-leakage invariants. Handles 'No eligible analog found' gracefully.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from backend.app.services.analog_service import (
    AnalogCard,
    AnalogResult,
    HistoricalAnalogService,
)

router = APIRouter()
_analog_service = HistoricalAnalogService(event_exclusion_days=14)


class AnalogCardResponse(BaseModel):
    """Structured human-readable historical analog card."""
    case_id: str
    date: str
    location: str
    variable: str
    lead_hours: int
    similarity: float
    historical_outcome: str  # "BUST" or "NORMAL"
    synoptic_description: str
    lessons_learned: str


class AnalogSearchResponse(BaseModel):
    """Complete analog search response payload."""
    status: str  # "SUCCESS" or "NO_ELIGIBLE_ANALOG"
    similarity_score: float
    bust_frequency: Optional[float]
    distance_nearest: float
    hit_rate: float
    top_k_count: int
    event_exclusion_window_days: int = 14
    analog_cards: List[AnalogCardResponse]
    claim_scope: str = "PUBLIC_PROXY_PROTOTYPE"


@router.get(
    "/analogs",
    response_model=AnalogSearchResponse,
    summary="Search Historical Atmospheric Analogs",
    description=(
        "Retrieves historical forecast cases matching the current synoptic state. "
        "Strictly enforces temporal anti-leakage (t_case < t_query) and event-exclusion "
        "(|t_case - t_query| >= 14 days). Gracefully returns 'NO_ELIGIBLE_ANALOG' if no match is found (§15, H7)."
    ),
)
async def search_analogs(
    location: str = Query(default="Delhi", description="Target location name"),
    variable: str = Query(default="temperature_2m", description="Evaluated meteorological variable"),
    lead_hours: int = Query(default=48, ge=1, le=384, description="Forecast lead horizon in hours"),
    forecast_value: float = Query(default=32.0, description="Forecasted point value (e.g. °C, hPa, m/s)"),
    ensemble_std: float = Query(default=1.5, description="Ensemble standard deviation / spread"),
    query_time: Optional[str] = Query(default=None, description="ISO 8601 query timestamp (defaults to now)"),
    top_k: int = Query(default=3, ge=1, le=10, description="Number of top analogs to retrieve"),
) -> AnalogSearchResponse:
    """Execute analog search across frozen historical cases."""
    q_time = query_time or datetime.now(timezone.utc).isoformat()

    result: AnalogResult = _analog_service.find_analogs(
        query_time=q_time,
        variable=variable,
        lead_hours=lead_hours,
        forecast_value=forecast_value,
        ensemble_std=ensemble_std,
        location=location,
        top_k=top_k,
    )

    cards = [
        AnalogCardResponse(
            case_id=c.case_id,
            date=c.date,
            location=c.location,
            variable=c.variable,
            lead_hours=c.lead_hours,
            similarity=round(c.similarity, 4),
            historical_outcome=c.historical_outcome,
            synoptic_description=c.synoptic_description,
            lessons_learned=c.lessons_learned,
        )
        for c in result.analog_cards
    ]

    return AnalogSearchResponse(
        status=result.status,
        similarity_score=round(result.similarity_score, 4),
        bust_frequency=round(result.bust_frequency, 4) if result.bust_frequency is not None else None,
        distance_nearest=round(result.distance_nearest, 4),
        hit_rate=round(result.hit_rate, 4),
        top_k_count=len(cards),
        event_exclusion_window_days=_analog_service.event_exclusion_days,
        analog_cards=cards,
        claim_scope="PUBLIC_PROXY_PROTOTYPE",
    )
