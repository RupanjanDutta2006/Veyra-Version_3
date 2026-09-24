"""Meteorological Regime & Monsoon Context Feature Extraction for Veyra.

Docs §9, Research Files 061-065:
- Monsoon phase identification (active, break, onset, retreat, pre-monsoon, non-monsoon)
- Atmospheric blocking index (Tibaldi-Molteni gradient reversal proxy)
- Rossby-wave pattern & planetary wave perturbation index
- Jet state (wind velocity / shear anomaly proxy)
- Regime-transition proximity (temporal decay to nearest boundary)
- Cyclonic regime indicator
"""

from datetime import datetime, timezone
from enum import IntEnum
import math
from typing import Any, Dict, Optional, Union
import numpy as np


class MonsoonPhase(IntEnum):
    """Categorical classification of Indian meteorological / seasonal monsoon phase."""
    NON_MONSOON_WINTER = 0   # Dec - Feb
    PRE_MONSOON_SUMMER = 1   # Mar - May
    MONSOON_ONSET = 2        # Late May - June 15
    MONSOON_ACTIVE = 3       # June 16 - Aug 15
    MONSOON_BREAK = 4        # Intra-seasonal dry spell / anomalous ridge
    MONSOON_RETREAT = 5      # Sep - Nov


# Climatological regime transition dates (Month, Day)
REGIME_BOUNDARIES = [
    (3, 1),   # Pre-monsoon start
    (5, 25),  # Monsoon onset window start
    (6, 15),  # Core active monsoon start
    (8, 15),  # Late monsoon / break-prone window start
    (9, 15),  # Monsoon withdrawal / retreat start
    (12, 1),  # Winter start
]


def determine_monsoon_phase(
    valid_dt: datetime,
    surface_pressure_hpa: Optional[float] = None,
    wind_speed_ms: Optional[float] = None,
    latitude: float = 20.0,
) -> MonsoonPhase:
    """Classify the synoptic monsoon phase using calendar date and atmospheric surface proxies."""
    month = valid_dt.month
    day = valid_dt.day

    # 1. Non-monsoon winter (Dec - Feb)
    if month in (12, 1, 2):
        return MonsoonPhase.NON_MONSOON_WINTER

    # 2. Pre-monsoon summer (Mar - May 24)
    if month in (3, 4) or (month == 5 and day < 25):
        return MonsoonPhase.PRE_MONSOON_SUMMER

    # 3. Monsoon onset (May 25 - June 15)
    if (month == 5 and day >= 25) or (month == 6 and day <= 15):
        return MonsoonPhase.MONSOON_ONSET

    # 4. Core Southwest Monsoon (June 16 - August 31)
    if (month == 6 and day > 15) or month in (7, 8):
        # Detect monsoon break: anomalous high surface pressure (+3 hPa over mean) + low wind in core zone
        if (
            surface_pressure_hpa is not None
            and surface_pressure_hpa > 1010.0
            and wind_speed_ms is not None
            and wind_speed_ms < 3.0
            and 15.0 <= latitude <= 28.0
        ):
            return MonsoonPhase.MONSOON_BREAK
        return MonsoonPhase.MONSOON_ACTIVE

    # 5. Monsoon retreat / Post-monsoon (Sep - Nov)
    return MonsoonPhase.MONSOON_RETREAT


def compute_blocking_index(
    surface_pressure_hpa: Optional[float],
    wind_speed_ms: Optional[float] = None,
    latitude: float = 20.0,
    climatological_mean_p_hpa: float = 1013.25,
) -> float:
    """Compute local anticyclonic blocking index proxy.

    Tibaldi-Molteni gradient reversal proxy:
    Persistent elevated pressure accompanied by stagnant low-level wind indicates
    an atmospheric blocking ridge or subtropical high stagnation.
    Normalized into [0.0, 1.0].
    """
    if surface_pressure_hpa is None or not math.isfinite(surface_pressure_hpa):
        return 0.0

    p_anomaly = surface_pressure_hpa - climatological_mean_p_hpa
    if p_anomaly <= 0.0:
        return 0.0

    # Elevated pressure anomaly scaled (e.g. +10 hPa = 1.0)
    p_score = min(1.0, p_anomaly / 10.0)

    # Wind stagnation amplifier (wind < 3 m/s amplifies blocking)
    wind_factor = 1.0
    if wind_speed_ms is not None and math.isfinite(wind_speed_ms):
        if wind_speed_ms < 3.0:
            wind_factor = 1.2
        elif wind_speed_ms > 8.0:
            wind_factor = 0.5

    return round(float(np.clip(p_score * wind_factor, 0.0, 1.0)), 4)


def compute_rossby_wave_index(
    valid_dt: datetime,
    wind_speed_ms: Optional[float] = None,
    latitude: float = 20.0,
) -> float:
    """Compute Rossby planetary wave activity proxy.

    Higher values indicate amplified planetary wave meandering or strong mid-latitude troughs
    interacting with the subtropical jet.
    """
    doy = valid_dt.timetuple().tm_yday
    # Zonal planetary wavenumber-1 to wavenumber-3 harmonic modulation
    wave_phase = 2.0 * math.pi * (doy % 30) / 30.0
    base_activity = 0.5 + 0.3 * math.sin(wave_phase)

    # Latitude scaling: higher Rossby wave amplitude in subtropics/mid-latitudes (> 25°N)
    lat_scale = min(1.5, max(0.5, abs(latitude) / 30.0))

    # Wind perturbation modifier
    wind_mod = 1.0
    if wind_speed_ms is not None and math.isfinite(wind_speed_ms):
        wind_mod = 1.0 + min(0.5, wind_speed_ms / 20.0)

    return round(float(np.clip(base_activity * lat_scale * wind_mod, 0.0, 2.0)), 4)


def compute_jet_state(
    wind_speed_ms: Optional[float],
    surface_pressure_hpa: Optional[float] = None,
) -> float:
    """Compute jet state / atmospheric kinetic energy proxy.

    Measures relative wind speed intensity compared to nominal synoptic scales.
    Normalized into [0.0, 1.0].
    """
    if wind_speed_ms is None or not math.isfinite(wind_speed_ms):
        return 0.2

    # Normalization: 0 m/s -> 0.0, 15 m/s -> 0.6, 25+ m/s -> 1.0
    jet_intensity = min(1.0, max(0.0, wind_speed_ms / 25.0))
    return round(float(jet_intensity), 4)


def compute_regime_transition_proximity(valid_dt: datetime) -> float:
    """Calculate proximity to the nearest seasonal/monsoon regime boundary.

    Returns a value in [0.0, 1.0]:
    - 1.0 when exactly on a regime boundary date (highest uncertainty/transition risk).
    - Decays exponentially with days from boundary: exp(-days / 10.0).
    """
    doy = valid_dt.timetuple().tm_yday
    year = valid_dt.year

    min_days = 365.0
    for m, d in REGIME_BOUNDARIES:
        b_dt = datetime(year, m, d)
        b_doy = b_dt.timetuple().tm_yday
        diff = abs(doy - b_doy)
        diff = min(diff, 365 - diff)  # Circular wrap-around
        if diff < min_days:
            min_days = diff

    # Exponential proximity kernel: 0 days -> 1.0, 7 days -> ~0.50, 14 days -> ~0.25
    proximity = math.exp(-min_days / 10.0)
    return round(float(np.clip(proximity, 0.0, 1.0)), 4)


def compute_cyclonic_regime_flag(
    surface_pressure_hpa: Optional[float],
    wind_speed_ms: Optional[float] = None,
) -> float:
    """Identify whether current state indicates cyclonic disturbance / deep depression.

    Criteria:
    - Surface pressure depressed (< 1004.0 hPa at mean sea level)
    - Concurrently elevated wind speed (> 8.0 m/s)
    """
    if surface_pressure_hpa is None or not math.isfinite(surface_pressure_hpa):
        return 0.0

    is_low_pressure = surface_pressure_hpa < 1004.0
    is_high_wind = (wind_speed_ms is not None and math.isfinite(wind_speed_ms) and wind_speed_ms >= 8.0)

    if is_low_pressure and is_high_wind:
        return 1.0
    elif is_low_pressure:
        return 0.5
    return 0.0


def extract_regime_features(
    valid_dt: datetime,
    surface_pressure_hpa: Optional[float] = None,
    wind_speed_ms: Optional[float] = None,
    latitude: float = 20.0,
    longitude: float = 78.0,
) -> Dict[str, float]:
    """Extract complete dictionary of issue-time regime context features (§9, D3).

    Returns
    -------
    dict of str -> float with keys:
    - monsoon_phase_code (0-5)
    - is_monsoon_active (0/1)
    - is_monsoon_break (0/1)
    - is_pre_monsoon (0/1)
    - blocking_index (0.0 - 1.0)
    - rossby_wave_index (0.0 - 2.0)
    - jet_state (0.0 - 1.0)
    - regime_transition_proximity (0.0 - 1.0)
    - cyclonic_regime_flag (0.0, 0.5, 1.0)
    """
    phase = determine_monsoon_phase(
        valid_dt=valid_dt,
        surface_pressure_hpa=surface_pressure_hpa,
        wind_speed_ms=wind_speed_ms,
        latitude=latitude,
    )

    blocking = compute_blocking_index(
        surface_pressure_hpa=surface_pressure_hpa,
        wind_speed_ms=wind_speed_ms,
        latitude=latitude,
    )

    rossby = compute_rossby_wave_index(
        valid_dt=valid_dt,
        wind_speed_ms=wind_speed_ms,
        latitude=latitude,
    )

    jet = compute_jet_state(
        wind_speed_ms=wind_speed_ms,
        surface_pressure_hpa=surface_pressure_hpa,
    )

    trans_prox = compute_regime_transition_proximity(valid_dt)

    cyclonic = compute_cyclonic_regime_flag(
        surface_pressure_hpa=surface_pressure_hpa,
        wind_speed_ms=wind_speed_ms,
    )

    return {
        "monsoon_phase_code": float(phase.value),
        "is_monsoon_active": 1.0 if phase == MonsoonPhase.MONSOON_ACTIVE else 0.0,
        "is_monsoon_break": 1.0 if phase == MonsoonPhase.MONSOON_BREAK else 0.0,
        "is_pre_monsoon": 1.0 if phase == MonsoonPhase.PRE_MONSOON_SUMMER else 0.0,
        "blocking_index": blocking,
        "rossby_wave_index": rossby,
        "jet_state": jet,
        "regime_transition_proximity": trans_prox,
        "cyclonic_regime_flag": cyclonic,
    }
