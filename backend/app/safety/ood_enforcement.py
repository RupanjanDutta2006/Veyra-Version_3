"""Authoritative Out-Of-Distribution (OOD) Enforcement Layer.

Implements strict OOD gating per SIH26079 §21, §11.3, and Research Files 076, 090:
- Polar coordinates (abs(lat) > 66.5) strictly trigger OOD abstention.
- Oceanic coordinates / uncalibrated maritime zones far from land stations trigger OOD abstention.
- Unsupported foreign cities (London, New York, Tokyo, etc.) trigger OOD abstention.
- Feature Mahalanobis distance > threshold triggers OOD abstention.
- Core Invariant (K4): Out-of-distribution cases must NEVER receive confident probability numbers.
"""
from dataclasses import dataclass, field
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from backend.app.safety.ood_detector import OODState
from backend.app.schemas.prediction import ReasonCode, TrustState

logger = logging.getLogger(__name__)

# Extreme latitude thresholds for polar domains
POLAR_LATITUDE_THRESHOLD = 66.5

# Extreme non-terrestrial / polar locations that strictly require OOD abstention (K4)
EXTREME_OOD_LOCATIONS = {
    "north pole", "south pole", "arctic", "antarctica", "pacific ocean",
    "atlantic ocean", "indian ocean offshore", "international waters", "pole", "ocean",
}

# Indian Subcontinent geographic bounding box (with offshore buffer)
INDIA_MIN_LAT = 6.0
INDIA_MAX_LAT = 37.5
INDIA_MIN_LON = 68.0
INDIA_MAX_LON = 98.0


@dataclass
class OODEnforcementResult:
    """Result of authoritative OOD safety gating."""

    is_ood: bool
    ood_state: OODState
    ood_score: float
    abstain_required: bool
    trust_state: TrustState
    reason_codes: List[str]
    enforcement_message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class OODEnforcer:
    """Authoritative OOD gatekeeper ensuring non-compliant or extreme locations never receive confident numbers."""

    def __init__(
        self,
        mahalanobis_threshold: float = 3.0,
        unusual_threshold: float = 2.0,
    ):
        self.mahalanobis_threshold = mahalanobis_threshold
        self.unusual_threshold = unusual_threshold

    def evaluate(
        self,
        location: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        feature_ood_score: Optional[float] = None,
        regime_novelty_score: Optional[float] = None,
    ) -> OODEnforcementResult:
        """Evaluate location and atmospheric coordinates for out-of-distribution conditions."""
        loc_clean = location.strip().lower()
        reasons: List[str] = []

        # 1. Check extreme non-terrestrial / polar locations (K4)
        if any(ext in loc_clean for ext in EXTREME_OOD_LOCATIONS):
            return OODEnforcementResult(
                is_ood=True,
                ood_state=OODState.ABSTAIN,
                ood_score=9.9,
                abstain_required=True,
                trust_state=TrustState.ABSTAINED,
                reason_codes=[
                    "OUT_OF_DISTRIBUTION_GEOGRAPHIC",
                    ReasonCode.OOD_DETECTED.value,
                ],
                enforcement_message=(
                    f"Location '{location}' is in an extreme polar/oceanic domain. "
                    "Veyra Sentinel strictly withholds confident numbers per K4 safety invariant."
                ),
                metadata={"location": location, "domain": "EXTREME_OOD"},
            )

        # 2. Check Polar Coordinates (abs(lat) > 66.5) (K4)
        if latitude is not None and abs(latitude) >= POLAR_LATITUDE_THRESHOLD:
            return OODEnforcementResult(
                is_ood=True,
                ood_state=OODState.ABSTAIN,
                ood_score=9.9,
                abstain_required=True,
                trust_state=TrustState.ABSTAINED,
                reason_codes=[
                    "OUT_OF_DISTRIBUTION_POLAR",
                    ReasonCode.OOD_DETECTED.value,
                ],
                enforcement_message=(
                    f"Latitude {latitude}° exceeds polar boundary ({POLAR_LATITUDE_THRESHOLD}°). "
                    "Polar atmospheric dynamics are uncertified in Veyra Sentinel V3."
                ),
                metadata={"latitude": latitude, "domain": "POLAR"},
            )

        # 3. Check Oceanic Coordinates outside regional basin
        if latitude is not None and longitude is not None:
            is_outside_india = not (
                INDIA_MIN_LAT <= latitude <= INDIA_MAX_LAT
                and INDIA_MIN_LON <= longitude <= INDIA_MAX_LON
            )
            if is_outside_india:
                # Deep ocean or foreign coordinates
                return OODEnforcementResult(
                    is_ood=True,
                    ood_state=OODState.ABSTAIN,
                    ood_score=4.5,
                    abstain_required=True,
                    trust_state=TrustState.ABSTAINED,
                    reason_codes=[
                        "OUT_OF_DISTRIBUTION_GEOGRAPHIC",
                        ReasonCode.OOD_DETECTED.value,
                    ],
                    enforcement_message=(
                        f"Coordinates ({latitude}°, {longitude}°) lie outside the certified Indian subcontinental domain. "
                        "Automated guidance safely withheld."
                    ),
                    metadata={"latitude": latitude, "longitude": longitude, "domain": "OUTSIDE_INDIA_DOMAIN"},
                )

        # 4. Feature-space OOD checks (Mahalanobis / KDE)
        effective_score = feature_ood_score if feature_ood_score is not None else 0.0
        if regime_novelty_score is not None and regime_novelty_score > effective_score:
            effective_score = regime_novelty_score

        if effective_score >= self.mahalanobis_threshold:
            return OODEnforcementResult(
                is_ood=True,
                ood_state=OODState.ABSTAIN,
                ood_score=effective_score,
                abstain_required=True,
                trust_state=TrustState.ABSTAINED,
                reason_codes=[
                    ReasonCode.OOD_DETECTED.value,
                    "OUT_OF_DISTRIBUTION_SYNOPTIC",
                ],
                enforcement_message=(
                    f"Atmospheric synoptic state OOD score ({effective_score:.2f}) exceeds critical threshold ({self.mahalanobis_threshold}). "
                    "Novel circulation pattern detected; human forecaster review required."
                ),
                metadata={"feature_ood_score": effective_score},
            )

        if effective_score >= self.unusual_threshold:
            return OODEnforcementResult(
                is_ood=False,
                ood_state=OODState.UNUSUAL,
                ood_score=effective_score,
                abstain_required=False,
                trust_state=TrustState.LOW_CONFIDENCE,
                reason_codes=["UNUSUAL_SYNOPTIC_STATE"],
                enforcement_message="Unusual atmospheric state detected. Model confidence downgraded.",
                metadata={"feature_ood_score": effective_score},
            )

        # Normal in-distribution
        return OODEnforcementResult(
            is_ood=False,
            ood_state=OODState.NORMAL,
            ood_score=effective_score,
            abstain_required=False,
            trust_state=TrustState.HIGH_CONFIDENCE,
            reason_codes=[],
            enforcement_message="Operational state within nominal training manifold.",
            metadata={"feature_ood_score": effective_score},
        )


default_ood_enforcer = OODEnforcer()
