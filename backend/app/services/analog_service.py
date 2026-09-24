"""Historical Analog Retrieval and Similarity Service for Veyra.

Docs §9, §12, §21, Research File 067:
- Historical analog retrieval with similarity scoring (Euclidean distance on normalized state)
- Strict event-exclusion (cases within ±14 days excluded to prevent same-event leakage)
- Temporal anti-leakage (future cases t_case >= t_query strictly excluded)
- Outputs: analog_similarity_score, analog_bust_frequency, analog_distance_nearest, analog_hit_rate
- Generates structured AnalogCard objects for explanation panels and /v1/analogs endpoint
- Handles 'No eligible analog found' gracefully as a valid operational state.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


@dataclass
class AnalogCard:
    """Structured human-readable historical analog card (§12, §21)."""
    case_id: str
    date: str
    location: str
    variable: str
    lead_hours: int
    similarity: float
    historical_outcome: str  # "BUST" or "NORMAL"
    synoptic_description: str
    lessons_learned: str


@dataclass
class AnalogResult:
    """Complete analog search result and summary features."""
    status: str  # "SUCCESS" or "NO_ELIGIBLE_ANALOG"
    similarity_score: float  # Top-K average similarity in [0.0, 1.0]
    bust_frequency: Optional[float]  # Fraction of top-K analogs that busted
    distance_nearest: float
    hit_rate: float  # Fraction of candidates matching regime
    top_k_count: int
    analog_cards: List[AnalogCard] = field(default_factory=list)


@dataclass
class HistoricalAnalogCase:
    """Stored historical forecast event in the analog archive."""
    case_id: str
    timestamp: str  # ISO 8601 UTC
    location: str
    variable: str
    lead_hours: int
    forecast_value: float
    ensemble_mean: float
    ensemble_std: float
    regime: str
    bust_label: int  # 1 = bust, 0 = normal
    description: str
    lessons_learned: str


# Benchmark historical cases covering diverse atmospheric regimes across India
BENCHMARK_ANALOG_ARCHIVE: List[HistoricalAnalogCase] = [
    # Extreme heatwaves / pre-monsoon
    HistoricalAnalogCase(
        case_id="HW-2015-DELHI",
        timestamp="2015-05-24T00:00:00Z",
        location="Delhi",
        variable="temperature_2m",
        lead_hours=48,
        forecast_value=44.5,
        ensemble_mean=44.0,
        ensemble_std=1.2,
        regime="PRE_MONSOON_HEATWAVE",
        bust_label=1,
        description="Severe pre-monsoon heatwave over NW India; NWP underpredicted peak surface heating by 3.8°C.",
        lessons_learned="Under-dispersion during dry soil moisture anomalies leads to rapid temperature busts.",
    ),
    HistoricalAnalogCase(
        case_id="HW-2019-KOLKATA",
        timestamp="2019-06-02T00:00:00Z",
        location="Kolkata",
        variable="temperature_2m",
        lead_hours=72,
        forecast_value=39.0,
        ensemble_mean=38.8,
        ensemble_std=0.9,
        regime="PRE_MONSOON_HEATWAVE",
        bust_label=0,
        description="Moderate pre-monsoon heat conditions before thunderstorm onset; forecast verified accurately.",
        lessons_learned="Ensemble mean was well-centered with adequate spread.",
    ),
    # Cyclonic disturbances / monsoon onset
    HistoricalAnalogCase(
        case_id="CY-2020-AMPHAN",
        timestamp="2020-05-18T00:00:00Z",
        location="Kolkata",
        variable="surface_pressure",
        lead_hours=48,
        forecast_value=988.0,
        ensemble_mean=992.0,
        ensemble_std=5.4,
        regime="SUPER_CYCLONE",
        bust_label=1,
        description="Super Cyclone Amphan landfall; rapid central pressure deepening was missed by 4 hPa.",
        lessons_learned="High ensemble spread in pressure gradients signals elevated bust potential.",
    ),
    HistoricalAnalogCase(
        case_id="CY-2021-TAUKTAE",
        timestamp="2021-05-16T00:00:00Z",
        location="Mumbai",
        variable="wind_speed_10m",
        lead_hours=48,
        forecast_value=22.0,
        ensemble_mean=20.5,
        ensemble_std=4.8,
        regime="EXTREME_CYCLONIC_WIND",
        bust_label=1,
        description="Extremely Severe Cyclonic Storm Tauktae; coastal gale winds exceeded forecast by 8 m/s.",
        lessons_learned="Coastal boundary friction uncertainties cause wind-speed forecast underestimation.",
    ),
    # Monsoon active & break events
    HistoricalAnalogCase(
        case_id="MN-2018-KERALA",
        timestamp="2018-08-14T00:00:00Z",
        location="Chennai",
        variable="wind_speed_10m",
        lead_hours=72,
        forecast_value=12.0,
        ensemble_mean=11.2,
        ensemble_std=2.1,
        regime="MONSOON_ACTIVE_DEPRESSION",
        bust_label=1,
        description="Active monsoon low-pressure system producing persistent orographic rainfall and winds.",
        lessons_learned="Orographic moisture convergence frequently produces localized wind/rain busts.",
    ),
    HistoricalAnalogCase(
        case_id="MN-2021-BREAK",
        timestamp="2021-07-20T00:00:00Z",
        location="Delhi",
        variable="temperature_2m",
        lead_hours=96,
        forecast_value=36.0,
        ensemble_mean=35.5,
        ensemble_std=1.5,
        regime="MONSOON_BREAK",
        bust_label=0,
        description="Prolonged monsoon break over northern plains; clear sky temperature accurately tracked.",
        lessons_learned="Anticyclonic blocking during break phases provides high forecast predictability.",
    ),
    # Winter fog / temperature inversions
    HistoricalAnalogCase(
        case_id="WN-2022-FOG-DELHI",
        timestamp="2022-01-12T00:00:00Z",
        location="Delhi",
        variable="temperature_2m",
        lead_hours=24,
        forecast_value=14.0,
        ensemble_mean=14.5,
        ensemble_std=0.8,
        regime="WINTER_INVERSION_FOG",
        bust_label=1,
        description="Dense radiation fog and cold day condition; maximum temperature bust of -4.5°C.",
        lessons_learned="NWP models struggle with low boundary-layer stratus dissipation timing.",
    ),
    HistoricalAnalogCase(
        case_id="WN-2023-MUMBAI",
        timestamp="2023-01-22T00:00:00Z",
        location="Mumbai",
        variable="temperature_2m",
        lead_hours=48,
        forecast_value=27.0,
        ensemble_mean=26.8,
        ensemble_std=0.6,
        regime="WINTER_NORMAL",
        bust_label=0,
        description="Stable coastal winter weather with typical sea breeze cycle; verified accurately.",
        lessons_learned="Low spread with maritime moderation yields reliable forecasts.",
    ),
]


class HistoricalAnalogService:
    """Service for finding issue-time-safe historical forecast analogs."""

    def __init__(
        self,
        archive: Optional[List[HistoricalAnalogCase]] = None,
        event_exclusion_days: int = 14,
        min_similarity_threshold: float = 0.35,
    ):
        self.archive = archive if archive is not None else list(BENCHMARK_ANALOG_ARCHIVE)
        self.event_exclusion_days = event_exclusion_days
        self.min_similarity_threshold = min_similarity_threshold

    def find_analogs(
        self,
        query_time: Union[str, datetime],
        variable: str,
        lead_hours: int,
        forecast_value: float,
        ensemble_std: float,
        location: Optional[str] = None,
        top_k: int = 3,
    ) -> AnalogResult:
        """Find historical analogs strictly obeying temporal and event-exclusion invariants.

        Invariants:
        1. Temporal ordering: t_case < t_query (no future knowledge).
        2. Event-exclusion: |t_case - t_query| >= event_exclusion_days (prevents same-event leakage).
        3. Feature distance: normalized state vector distance.
        """
        if isinstance(query_time, str):
            dt_query = datetime.fromisoformat(query_time.strip().replace("Z", "+00:00"))
        else:
            dt_query = query_time
            if dt_query.tzinfo is None:
                dt_query = dt_query.replace(tzinfo=timezone.utc)

        exclusion_window = timedelta(days=self.event_exclusion_days)

        candidates: List[Tuple[float, HistoricalAnalogCase]] = []

        for case in self.archive:
            case_dt = datetime.fromisoformat(case.timestamp.strip().replace("Z", "+00:00"))

            # Invariant 1: Strictly earlier than query time
            if case_dt >= dt_query:
                continue

            # Invariant 2: Exclude same-event window
            if abs(dt_query - case_dt) < exclusion_window:
                continue

            # Variable compatibility
            if case.variable.lower() != variable.lower():
                continue

            # Compute normalized distance
            # 1. Normalized value difference
            scale_val = 30.0 if variable == "temperature_2m" else (100.0 if variable == "surface_pressure" else 15.0)
            d_val = (case.forecast_value - forecast_value) / scale_val

            # 2. Spread difference
            scale_std = 3.0 if variable == "temperature_2m" else (10.0 if variable == "surface_pressure" else 2.5)
            d_std = (case.ensemble_std - ensemble_std) / scale_std

            # 3. Lead hours difference
            d_lead = (case.lead_hours - lead_hours) / 240.0

            # 4. Seasonal cycle distance (sin/cos of month)
            q_month = dt_query.month
            c_month = case_dt.month
            d_season_sin = math.sin(2.0 * math.pi * q_month / 12.0) - math.sin(2.0 * math.pi * c_month / 12.0)
            d_season_cos = math.cos(2.0 * math.pi * q_month / 12.0) - math.cos(2.0 * math.pi * c_month / 12.0)
            d_season = math.sqrt(d_season_sin**2 + d_season_cos**2)

            # 5. Location matching bonus (weight reduction if same location)
            loc_penalty = 0.0 if (location and case.location.lower() == location.lower()) else 0.2

            # Weighted Euclidean distance
            total_dist = math.sqrt(
                1.5 * (d_val ** 2)
                + 1.0 * (d_std ** 2)
                + 0.8 * (d_lead ** 2)
                + 0.7 * (d_season ** 2)
                + loc_penalty
            )

            similarity = 1.0 / (1.0 + total_dist)
            candidates.append((similarity, case))

        if not candidates:
            return AnalogResult(
                status="NO_ELIGIBLE_ANALOG",
                similarity_score=0.0,
                bust_frequency=None,
                distance_nearest=999.0,
                hit_rate=0.0,
                top_k_count=0,
                analog_cards=[],
            )

        # Sort descending by similarity
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = candidates[:top_k]

        # Check if nearest candidate meets threshold
        nearest_sim = top_candidates[0][0]
        if nearest_sim < self.min_similarity_threshold:
            return AnalogResult(
                status="NO_ELIGIBLE_ANALOG",
                similarity_score=round(nearest_sim, 4),
                bust_frequency=None,
                distance_nearest=round((1.0 / nearest_sim) - 1.0, 4),
                hit_rate=0.0,
                top_k_count=0,
                analog_cards=[],
            )

        # Compute summary metrics
        sim_scores = [c[0] for c in top_candidates]
        avg_sim = float(np.mean(sim_scores))
        bust_count = sum(1 for c in top_candidates if c[1].bust_label == 1)
        bust_freq = round(bust_count / len(top_candidates), 4)
        nearest_dist = round((1.0 / top_candidates[0][0]) - 1.0, 4)

        # Build cards
        cards: List[AnalogCard] = []
        for sim, case in top_candidates:
            cards.append(
                AnalogCard(
                    case_id=case.case_id,
                    date=case.timestamp[:10],
                    location=case.location,
                    variable=case.variable,
                    lead_hours=case.lead_hours,
                    similarity=round(sim, 4),
                    historical_outcome="BUST" if case.bust_label == 1 else "NORMAL",
                    synoptic_description=case.description,
                    lessons_learned=case.lessons_learned,
                )
            )

        return AnalogResult(
            status="SUCCESS",
            similarity_score=round(avg_sim, 4),
            bust_frequency=bust_freq,
            distance_nearest=nearest_dist,
            hit_rate=1.0,
            top_k_count=len(cards),
            analog_cards=cards,
        )

    def extract_analog_features(
        self,
        query_time: Union[str, datetime],
        variable: str,
        lead_hours: int,
        forecast_value: float,
        ensemble_std: float,
        location: Optional[str] = None,
    ) -> Dict[str, float]:
        """Extract issue-time-safe analog similarity features for the ML feature matrix (§9, D4)."""
        result = self.find_analogs(
            query_time=query_time,
            variable=variable,
            lead_hours=lead_hours,
            forecast_value=forecast_value,
            ensemble_std=ensemble_std,
            location=location,
        )

        return {
            "analog_similarity_score": result.similarity_score,
            "analog_bust_frequency": result.bust_frequency if result.bust_frequency is not None else 0.0,
            "analog_distance_nearest": min(10.0, result.distance_nearest),
            "analog_hit_rate": result.hit_rate,
            "has_eligible_analog": 1.0 if result.status == "SUCCESS" else 0.0,
        }
