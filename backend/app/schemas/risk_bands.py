"""Risk Band Classification and Decision Guidance Mapping per SIH26079 §12.1.

Implements the 5-tier color risk band taxonomy:
- GREEN (< 0.20): Nominal forecast stability. Standard operational monitoring.
- YELLOW (0.20 - 0.50): Elevated divergence detected. Monitor subsequent NWP cycles.
- ORANGE (0.50 - 0.75): High bust probability. Significant likelihood of forecast error >= 95th percentile.
- RED (>= 0.75): Severe bust risk. High probability of extreme forecast failure.
- GRAY: Sentinel abstains due to data unavailability, OOD, or QC failure.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from backend.app.schemas.prediction import RiskLevel


class ColorRiskBand(str, Enum):
    """5-tier operational color risk band taxonomy matching §12.1."""

    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    GRAY = "GRAY"


@dataclass(frozen=True)
class RiskBandMapping:
    """Structured decision guidance and operational actions per risk band."""

    color_band: ColorRiskBand
    risk_level: Optional[RiskLevel]
    decision_mode: str
    decision_guidance: str
    recommended_action: str
    threshold_range: str


# Static mapping table per §12.1
RISK_BAND_TABLE: dict[ColorRiskBand, RiskBandMapping] = {
    ColorRiskBand.GREEN: RiskBandMapping(
        color_band=ColorRiskBand.GREEN,
        risk_level=RiskLevel.LOW,
        decision_mode="STANDARD_MONITORING",
        decision_guidance="Nominal forecast stability. High confidence in NWP guidance.",
        recommended_action="Proceed with standard forecast dissemination.",
        threshold_range="[0.00, 0.20)",
    ),
    ColorRiskBand.YELLOW: RiskBandMapping(
        color_band=ColorRiskBand.YELLOW,
        risk_level=RiskLevel.MEDIUM,
        decision_mode="ACTIVE_MONITORING",
        decision_guidance="Elevated ensemble divergence detected. Moderate probability of localized forecast failure.",
        recommended_action="Flag for forecaster review in sensitive sectors; track subsequent NWP cycles.",
        threshold_range="[0.20, 0.50)",
    ),
    ColorRiskBand.ORANGE: RiskBandMapping(
        color_band=ColorRiskBand.ORANGE,
        risk_level=RiskLevel.HIGH,
        decision_mode="HEIGHTENED_ALERT",
        decision_guidance="High bust risk. Significant likelihood of forecast error exceeding the 95th percentile threshold.",
        recommended_action="Prepare contingency forecasts; cross-check multi-model ensembles.",
        threshold_range="[0.50, 0.75)",
    ),
    ColorRiskBand.RED: RiskBandMapping(
        color_band=ColorRiskBand.RED,
        risk_level=RiskLevel.CRITICAL,
        decision_mode="EMERGENCY_ALERT",
        decision_guidance="Severe bust risk. High probability of extreme forecast failure and major synoptic breakdown.",
        recommended_action="Issue forecaster alert; delay automated advisory release pending human review.",
        threshold_range="[0.75, 1.00]",
    ),
    ColorRiskBand.GRAY: RiskBandMapping(
        color_band=ColorRiskBand.GRAY,
        risk_level=None,
        decision_mode="ABSTAINED",
        decision_guidance="Sentinel abstains due to data unavailability, out-of-distribution conditions, or QC failure.",
        recommended_action="Rely on raw NWP guidance with manual meteorological assessment.",
        threshold_range="N/A (Abstained)",
    ),
}


def map_probability_to_color_band(
    probability: Optional[float],
    is_abstained: bool = False,
    ood_state: Optional[str] = None,
) -> RiskBandMapping:
    """Map calibrated probability and abstention state to the §12.1 color risk band."""
    if is_abstained or probability is None or ood_state == "ABSTAIN":
        return RISK_BAND_TABLE[ColorRiskBand.GRAY]

    prob = float(probability)
    if prob < 0.20:
        return RISK_BAND_TABLE[ColorRiskBand.GREEN]
    elif prob < 0.50:
        return RISK_BAND_TABLE[ColorRiskBand.YELLOW]
    elif prob < 0.75:
        return RISK_BAND_TABLE[ColorRiskBand.ORANGE]
    else:
        return RISK_BAND_TABLE[ColorRiskBand.RED]
