"""Operational Precipitation Reliability Contract (Gate 3 / Phase D).

Defines strongly-typed Pydantic contracts for the precipitation reliability specialist:
- Occurrence failure (False Alarm vs Miss)
- Amount failure (continuous and thresholded errors)
- Heavy rainfall failure (>= 64.5 mm/24h)
- Extreme rainfall failure (>= 204.5 mm/24h)
- Timing displacement
- Spatial displacement
- Accumulation intervals (6h, 12h, 24h, 48h, 72h)
- Strict null-safety: unsupported quantities evaluate to None, never invented values.
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class PrecipitationIntensityThreshold(str, Enum):
    """Standard IMD 24h rainfall intensity categories."""
    NONE = "NONE"                     # < 2.5 mm
    LIGHT = "LIGHT"                   # 2.5 - 15.5 mm
    MODERATE = "MODERATE"             # 15.6 - 64.4 mm
    HEAVY = "HEAVY"                   # 64.5 - 115.5 mm
    VERY_HEAVY = "VERY_HEAVY"         # 115.6 - 204.4 mm
    EXTREMELY_HEAVY = "EXTREMELY_HEAVY" # >= 204.5 mm


class PrecipitationAccumulationWindow(str, Enum):
    """Supported precipitation accumulation windows."""
    H6 = "6h"
    H12 = "12h"
    H24 = "24h"
    H48 = "48h"
    H72 = "72h"


class PrecipitationOccurrenceFailureType(str, Enum):
    """Categorical occurrence failure modes."""
    NONE = "NONE"
    FALSE_ALARM = "FALSE_ALARM"  # Forecast >= 2.5mm, Obs < 2.5mm
    MISS = "MISS"                # Forecast < 2.5mm, Obs >= 2.5mm


class PrecipitationIssueFeatures(BaseModel):
    """Issue-time features available at t0 without future leakage."""
    lead_hours: int = Field(..., ge=0, le=384)
    ensemble_mean_precip_mm: float = Field(..., ge=0.0)
    ensemble_median_precip_mm: float = Field(..., ge=0.0)
    ensemble_spread_precip_mm: float = Field(..., ge=0.0)
    ensemble_p90_precip_mm: float = Field(..., ge=0.0)
    wet_member_fraction: float = Field(..., ge=0.0, le=1.0)
    dry_member_fraction: float = Field(..., ge=0.0, le=1.0)
    heavy_exceedance_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Thermodynamic and kinematic proxies at t0
    cape_proxy_jkg: Optional[float] = Field(None, ge=0.0)
    precipitable_water_mm: Optional[float] = Field(None, ge=0.0)
    low_level_moisture_convergence: Optional[float] = None
    orographic_lift_proxy: Optional[float] = None
    revision_delta_mm: Optional[float] = None
    terrain_class: str = Field(default="inland")


class PrecipitationReliabilityOutput(BaseModel):
    """Blueprint Section 7.6 certified precipitation reliability output."""
    hazard: str = Field(default="PRECIPITATION", description="Hazard identifier")
    occurrence_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Forecast wet/dry disagreement at >= 2.5mm)"
    )
    amount_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(|Forecast - Observed| > 25mm or Q95)"
    )
    heavy_rain_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Missed or false alarm for heavy rain >= 64.5mm)"
    )
    extreme_rain_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Failure on extreme rain >= 204.5mm)"
    )
    timing_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(|T_peak_fc - T_peak_obs| > 6h)"
    )
    spatial_displacement_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Centroid displacement > 75km)"
    )
    overall_reliability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Composite precipitation forecast reliability score [0=unreliable, 1=reliable]"
    )
    evidence: List[str] = Field(default_factory=list, description="Audit and feature attribution items")
    ood: Optional[bool] = Field(None, description="Out-of-distribution flag")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Model and reference tracking metadata")

    @model_validator(mode="after")
    def validate_hazard_name(self) -> "PrecipitationReliabilityOutput":
        if self.hazard != "PRECIPITATION":
            raise ValueError(f"hazard must be 'PRECIPITATION', got: {self.hazard}")
        return self


_DEFAULT_PRECIP_MANIFEST = Path(__file__).resolve().parents[3] / "data" / "precipitation_target_manifest.json"


def load_precipitation_target_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load precipitation target manifest from disk."""
    target_path = manifest_path or _DEFAULT_PRECIP_MANIFEST
    if not target_path.is_file():
        raise FileNotFoundError(f"Precipitation target manifest not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)
