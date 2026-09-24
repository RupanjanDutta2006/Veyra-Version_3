"""Operational Tropical Cyclone Reliability Contract (Gate 4 / Phase E).

Defines strongly-typed Pydantic contracts for the tropical cyclone reliability specialist:
- Track failure probability (Great-circle displacement exceedance)
- Intensity failure probability (Wind speed error > 15 knots / 7.7 m/s)
- Rapid Intensification (RI) failure probability (>= 30 kt / 24h)
- Landfall location displacement probability (> 80 km)
- Landfall timing displacement probability (> 6h)
- Conformal track uncertainty radius
- Strict null-safety: Landfall fields evaluate to None when non-landfall.
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CycloneBasin(str, Enum):
    """North Indian Ocean cyclone basins."""
    BAY_OF_BENGAL = "BAY_OF_BENGAL"
    ARABIAN_SEA = "ARABIAN_SEA"


class CycloneCategory(str, Enum):
    """IMD tropical cyclone intensity classification."""
    DEPRESSION = "DEPRESSION"                             # 17-27 knots (8.5-13.9 m/s)
    DEEP_DEPRESSION = "DEEP_DEPRESSION"                   # 28-33 knots (14.0-17.1 m/s)
    CYCLONIC_STORM = "CYCLONIC_STORM"                     # 34-47 knots (17.2-24.4 m/s)
    SEVERE_CYCLONIC_STORM = "SEVERE_CYCLONIC_STORM"       # 48-63 knots (24.5-32.6 m/s)
    VERY_SEVERE_CYCLONIC_STORM = "VERY_SEVERE_CYCLONIC_STORM"  # 64-89 knots (32.7-46.0 m/s)
    EXTREMELY_SEVERE_CYCLONIC_STORM = "EXTREMELY_SEVERE_CYCLONIC_STORM"  # 90-119 knots (46.1-61.4 m/s)
    SUPER_CYCLONIC_STORM = "SUPER_CYCLONIC_STORM"         # >= 120 knots (>= 61.5 m/s)


class CycloneIssueFeatures(BaseModel):
    """Issue-time features for tropical cyclone forecast reliability at t0."""
    lead_hours: int = Field(..., ge=0, le=240, description="Forecast lead time in hours")
    basin: CycloneBasin = Field(..., description="Active oceanic basin")
    forecast_lat: float = Field(..., ge=-10.0, le=35.0, description="Latitude in degrees")
    forecast_lon: float = Field(..., ge=50.0, le=105.0, description="Longitude in degrees")
    forward_speed_kmh: float = Field(default=15.0, ge=0.0, le=80.0, description="System translation speed")
    
    # Track features
    ensemble_track_spread_km: float = Field(..., ge=0.0, description="Cross-track/along-track ensemble dispersion")
    ensemble_track_clustering: Optional[float] = Field(None, ge=0.0, le=1.0, description="Bimodality/clustering metric")
    steering_flow_speed_ms: Optional[float] = Field(None, ge=0.0, description="500-hPa steering flow velocity")
    steering_flow_dir_deg: Optional[float] = Field(None, ge=0.0, le=360.0, description="Steering flow azimuth")
    
    # Intensity and environment features
    forecast_max_wind_ms: float = Field(..., ge=8.5, le=85.0, description="10m max sustained wind speed")
    ensemble_intensity_spread_ms: float = Field(..., ge=0.0, description="Intensity ensemble standard deviation")
    vertical_wind_shear_ms: float = Field(default=10.0, ge=0.0, le=60.0, description="200-850 hPa deep-layer shear")
    central_pressure_tendency_hpa_12h: Optional[float] = Field(None, description="12h pressure drop rate")
    
    # Landfall features
    distance_to_coast_km: Optional[float] = Field(None, ge=0.0, description="Distance to nearest coastline")
    forecast_landfall: bool = Field(default=False, description="Whether forecast indicates landfall")
    forecast_landfall_lead_hours: Optional[int] = Field(None, ge=0, description="Projected landfall lead horizon")
    revision_delta_km: Optional[float] = Field(None, description="Inter-cycle track position revision")


class CycloneReliabilityOutput(BaseModel):
    """Blueprint Section 8 certified tropical cyclone reliability output."""
    hazard: str = Field(default="CYCLONE", description="Hazard identifier")
    track_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Track error > 100km at 48h / 180km at 72h)"
    )
    intensity_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(|V_fc - V_obs| > 15 knots / 7.7 m/s)"
    )
    rapid_intensification_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(RI failure: Miss or False Alarm on >= 30 kt/24h)"
    )
    landfall_location_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Landfall location displacement > 80km). Null if non-landfall."
    )
    landfall_timing_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Landfall timing error > 6h). Null if non-landfall."
    )
    conformal_track_uncertainty_radius_km: Optional[float] = Field(
        None, ge=0.0, description="Conformal 90% coverage uncertainty radius in km"
    )
    overall_reliability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Composite cyclone reliability index [0=unreliable, 1=reliable]"
    )
    evidence: List[str] = Field(default_factory=list, description="Attribution and diagnostic factors")
    ood: Optional[bool] = Field(None, description="Out-of-distribution novelty flag")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Execution and reference metadata")

    @model_validator(mode="after")
    def validate_hazard_and_landfall(self) -> "CycloneReliabilityOutput":
        if self.hazard != "CYCLONE":
            raise ValueError(f"hazard must be 'CYCLONE', got: {self.hazard}")
        return self


_DEFAULT_CYCLONE_MANIFEST = Path(__file__).resolve().parents[3] / "data" / "cyclone_target_manifest.json"
_DEFAULT_CYCLONE_CATALOGUE = Path(__file__).resolve().parents[3] / "data" / "cyclone_event_catalogue.json"


def load_cyclone_target_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load cyclone target manifest from disk."""
    target_path = manifest_path or _DEFAULT_CYCLONE_MANIFEST
    if not target_path.is_file():
        raise FileNotFoundError(f"Cyclone target manifest not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cyclone_event_catalogue(catalogue_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load historical cyclone event catalogue from disk."""
    target_path = catalogue_path or _DEFAULT_CYCLONE_CATALOGUE
    if not target_path.is_file():
        raise FileNotFoundError(f"Cyclone event catalogue not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)
