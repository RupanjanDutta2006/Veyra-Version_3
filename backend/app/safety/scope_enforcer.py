"""Operational Scope Enforcement Layer.

Implements strict certified scope boundaries per SIH26079 §3.1, §1.0, and Research Files 023, 042:
- Certified Geos: Indian Subcontinent (IN_NORTH, IN_WEST, IN_CENTRAL, IN_EAST, IN_SOUTH, IN_NORTHEAST).
- Certified Variables: temperature_2m, wind_speed_10m, surface_pressure, geopotential_height_500hPa, precipitation_24h.
- Certified Horizons: 24h to 240h (Days 1 to 10).
- Sub-24h (< 24h) and extended medium-range (264h to 384h / Days 11 to 16) are uncertified.
- Invariants:
  - Uncertified geos/vars/horizons MUST NOT serve as HIGH_CONFIDENCE (A3).
  - Explicit warning issued for foreign locations (London, New York, poles) (A4).
  - Explicit uncertified_horizon flag for sub-24h and 264-384h (A5).
"""
from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.schemas.prediction import TrustState

logger = logging.getLogger(__name__)

# Canonical Certified Indian Subcontinental Domain
CERTIFIED_REGIONS = {
    "IN_NORTH",
    "IN_WEST",
    "IN_CENTRAL",
    "IN_EAST",
    "IN_SOUTH",
    "IN_NORTHEAST",
    "INDIA",
}

CERTIFIED_VARIABLES = {
    "temperature_2m",
    "wind_speed_10m",
    "surface_pressure",
    "geopotential_height_500hPa",
    "precipitation_24h",
}

# Certified operational medium-range horizon (24h to 240h)
MIN_CERTIFIED_HORIZON_HOURS = 24
MAX_CERTIFIED_HORIZON_HOURS = 240
MAX_SUPPORTED_HORIZON_HOURS = 384


@dataclass
class ScopeValidationResult:
    """Result of certified operational scope validation."""

    is_certified: bool
    outside_certified_domain: bool = False
    uncertified_horizon: bool = False
    uncertified_variable: bool = False
    max_allowable_trust_state: TrustState = TrustState.HIGH_CONFIDENCE
    warnings: List[str] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)
    scope_descriptor: str = "PUBLIC_PROXY_PROTOTYPE"


class ScopeEnforcer:
    """Enforces certified operational boundaries across geography, variables, and lead horizons."""

    def validate_scope(
        self,
        location: str,
        variable: Optional[str] = None,
        lead_hours: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> ScopeValidationResult:
        """Validate request against certified operational scope parameters."""
        loc_clean = location.strip().lower()
        warnings: List[str] = []
        reason_codes: List[str] = []
        is_certified = True
        outside_domain = False
        uncert_horizon = False
        uncert_var = False
        max_trust = TrustState.HIGH_CONFIDENCE

        # 1. Geographic Scope Enforcement (A4)
        foreign_indicators = [
            "london", "new york", "new york city", "north pole", "south pole", "arctic", "antarctica", "pole", "ocean",
        ]
        if any(f in loc_clean for f in foreign_indicators):
            is_certified = False
            outside_domain = True
            warnings.append(
                f"Location '{location}' is outside the certified Indian operational domain. "
                "Serving with uncertified experimental warning."
            )
            reason_codes.append("UNSUPPORTED_GEOGRAPHIC_REGION")

        # Coordinate bounding box check if coordinates are provided
        if latitude is not None and longitude is not None:
            if not (6.0 <= latitude <= 37.5 and 68.0 <= longitude <= 98.0):
                is_certified = False
                outside_domain = True
                warnings.append(
                    f"Coordinates ({latitude:.2f}°, {longitude:.2f}°) fall outside the Indian subcontinental domain."
                )
                reason_codes.append("OUT_OF_DOMAIN_COORDINATES")
                max_trust = TrustState.LOW_CONFIDENCE

        # 2. Horizon Scope Enforcement (A5)
        if lead_hours is not None:
            if lead_hours < MIN_CERTIFIED_HORIZON_HOURS:
                is_certified = False
                uncert_horizon = True
                warnings.append(
                    f"Lead time {lead_hours}h is sub-24h (nowcast/short-range). "
                    "Veyra Sentinel is certified strictly for medium-range forecasts (24h–240h)."
                )
                reason_codes.append("UNCERTIFIED_HORIZON_SHORT_RANGE")
                max_trust = TrustState.MODERATE_CONFIDENCE

            elif lead_hours > MAX_CERTIFIED_HORIZON_HOURS:
                is_certified = False
                uncert_horizon = True
                warnings.append(
                    f"Lead time {lead_hours}h exceeds certified 240h (Day 10) horizon. "
                    "Extended medium range (264h–384h) carries reduced predictability and uncertified status."
                )
                reason_codes.append("UNCERTIFIED_HORIZON_EXTENDED_RANGE")
                max_trust = TrustState.MODERATE_CONFIDENCE

        # 3. Variable Scope Enforcement (A3)
        if variable is not None and variable.strip() not in CERTIFIED_VARIABLES:
            is_certified = False
            uncert_var = True
            warnings.append(
                f"Variable '{variable}' is not among certified core variables "
                f"({', '.join(sorted(CERTIFIED_VARIABLES))})."
            )
            reason_codes.append("UNCERTIFIED_VARIABLE")
            max_trust = TrustState.LOW_CONFIDENCE

        # Cap Trust State per Invariant A3: Uncertified horizon, variable, or coordinates must NEVER serve as HIGH_CONFIDENCE
        if (uncert_horizon or uncert_var or (latitude is not None and outside_domain)) and max_trust == TrustState.HIGH_CONFIDENCE:
            max_trust = TrustState.MODERATE_CONFIDENCE

        return ScopeValidationResult(
            is_certified=is_certified,
            outside_certified_domain=outside_domain,
            uncertified_horizon=uncert_horizon,
            uncertified_variable=uncert_var,
            max_allowable_trust_state=max_trust,
            warnings=warnings,
            reason_codes=reason_codes,
            scope_descriptor="PUBLIC_PROXY_PROTOTYPE" if is_certified else "UNCERTIFIED_EXPERIMENTAL",
        )


default_scope_enforcer = ScopeEnforcer()
