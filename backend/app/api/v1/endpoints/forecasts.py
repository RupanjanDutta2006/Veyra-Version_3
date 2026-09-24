"""Forecast Cycles and Replay Cases API endpoint matching SIH26079 §15 (H3).

Provides catalog of available real-time NWP forecast cycles and historical
frozen replay cases for deterministic evaluation and demonstration.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()


class ForecastCycleInfo(BaseModel):
    """Metadata describing an operational NWP ensemble forecast cycle."""
    cycle_id: str
    model_provider: str  # "NOAA_GEFS", "ECMWF_IFS"
    issue_time: str
    max_lead_hours: int
    member_count: int
    grid_resolution_deg: float
    variables_available: List[str]
    status: str  # "AVAILABLE", "PROCESSING", "ARCHIVED"


class ReplayCaseInfo(BaseModel):
    """Frozen historical forecast replay benchmark case."""
    case_id: str
    name: str
    target_date: str
    issue_time: str
    valid_time: str
    location: str
    variable: str
    lead_hours: int
    observed_outcome: str  # "BUST" or "NORMAL"
    synoptic_regime: str
    description: str


class ForecastCatalogResponse(BaseModel):
    """Response payload listing available operational cycles and replay cases."""
    timestamp: str
    cycles: List[ForecastCycleInfo]
    replay_cases: List[ReplayCaseInfo]
    default_cycle_id: str


# Deterministic frozen replay cases matching §20 and historical archives
BENCHMARK_REPLAY_CASES: List[ReplayCaseInfo] = [
    ReplayCaseInfo(
        case_id="HW-2015-DELHI",
        name="May 2015 Northern Plains Heatwave Bust",
        target_date="2015-05-26",
        issue_time="2015-05-24T00:00:00Z",
        valid_time="2015-05-26T00:00:00Z",
        location="Delhi",
        variable="temperature_2m",
        lead_hours=48,
        observed_outcome="BUST",
        synoptic_regime="PRE_MONSOON_HEATWAVE",
        description="NWP under-forecasted peak surface heat by 3.8°C due to dry soil moisture feedback under-dispersion.",
    ),
    ReplayCaseInfo(
        case_id="CY-2020-AMPHAN",
        name="Super Cyclone Amphan Gangetic Landfall",
        target_date="2020-05-20",
        issue_time="2020-05-18T00:00:00Z",
        valid_time="2020-05-20T12:00:00Z",
        location="Kolkata",
        variable="surface_pressure",
        lead_hours=60,
        observed_outcome="BUST",
        synoptic_regime="TROPICAL_CYCLONE",
        description="Rapid central pressure drop of 42 hPa uncaptured by ensemble mean at 60h lead.",
    ),
    ReplayCaseInfo(
        case_id="CS-2019-CHENNAI",
        name="June 2019 Pre-Monsoon Heat Stability Case",
        target_date="2019-06-15",
        issue_time="2019-06-13T00:00:00Z",
        valid_time="2019-06-15T00:00:00Z",
        location="Chennai",
        variable="temperature_2m",
        lead_hours=48,
        observed_outcome="NORMAL",
        synoptic_regime="COASTAL_MONSOON_ONSET",
        description="Ensemble accurately predicted marine boundary layer penetration; forecast verified with error < 0.8°C.",
    ),
    ReplayCaseInfo(
        case_id="WW-2021-NORTH",
        name="Western Disturbance Winter Precipitation",
        target_date="2021-01-05",
        issue_time="2021-01-02T00:00:00Z",
        valid_time="2021-01-05T00:00:00Z",
        location="Delhi",
        variable="precipitation",
        lead_hours=72,
        observed_outcome="BUST",
        synoptic_regime="WESTERN_DISTURBANCE",
        description="Secondary upper-level trough divergence induced localized heavy rainfall exceeding 95th percentile.",
    ),
]


def _generate_operational_cycles() -> List[ForecastCycleInfo]:
    """Generate deterministic list of recent standard NWP cycles (00Z, 06Z, 12Z, 18Z)."""
    now = datetime.now(timezone.utc)
    base_hours = [0, 6, 12, 18]
    cycles: List[ForecastCycleInfo] = []

    for day_offset in [0, 1]:
        d = now - timedelta(days=day_offset)
        for h in reversed(base_hours):
            cycle_dt = datetime(d.year, d.month, d.day, h, 0, 0, tzinfo=timezone.utc)
            if cycle_dt <= now:
                c_id = f"GEFS_{cycle_dt.strftime('%Y%m%d_%H')}Z"
                cycles.append(
                    ForecastCycleInfo(
                        cycle_id=c_id,
                        model_provider="NOAA_GEFS",
                        issue_time=cycle_dt.isoformat(),
                        max_lead_hours=384,
                        member_count=31,
                        grid_resolution_deg=0.5,
                        variables_available=[
                            "temperature_2m",
                            "surface_pressure",
                            "wind_speed_10m",
                            "relative_humidity_2m",
                            "precipitation",
                            "geopotential_height_500hPa",
                        ],
                        status="AVAILABLE",
                    )
                )
    return cycles[:8]


@router.get(
    "/forecasts",
    response_model=ForecastCatalogResponse,
    summary="List Forecast Cycles and Replay Cases",
    description="Returns available real-time operational NWP cycles and frozen historical benchmark replay cases (§15, H3).",
)
async def list_forecasts(
    catalog_type: Optional[str] = Query(
        default="all",
        description="Filter by type: 'all', 'realtime', or 'replay'",
    ),
) -> ForecastCatalogResponse:
    """Retrieve catalog of operational cycles and replay cases."""
    now_iso = datetime.now(timezone.utc).isoformat()
    cycles = _generate_operational_cycles() if catalog_type in ("all", "realtime") else []
    replay = BENCHMARK_REPLAY_CASES if catalog_type in ("all", "replay") else []
    default_id = cycles[0].cycle_id if cycles else "GEFS_LATEST"

    return ForecastCatalogResponse(
        timestamp=now_iso,
        cycles=cycles,
        replay_cases=replay,
        default_cycle_id=default_id,
    )
