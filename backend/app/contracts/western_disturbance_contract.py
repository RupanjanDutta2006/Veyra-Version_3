"""Operational Western Disturbance Reliability Contract (Gate 6 / Phase G).

Defines strongly-typed Pydantic contracts for the western disturbance reliability specialist:
- Arrival timing failure probability (arrival timing error > 6.0h / 12.0h)
- Track/trough location failure probability (trough axis placement error > 150 km / 250 km)
- Precipitation intensity failure probability (24h precipitation error > 35 mm/24h)
- Precipitation spatial displacement failure probability (centroid displacement > 100 km)
- Event duration failure probability (duration error > 12.0h)
- Rain/snow phase partition failure probability (conditional on observations; strictly null when unsupported)
- Overall composite reliability
- Out-of-distribution (OOD) novelty flag and selective abstention
- Provenance and evidence metadata
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class WDIntensityClass(str, Enum):
    """Western disturbance synoptic intensity classification."""
    WEAK = "WEAK"                       # Shallow 500-hPa trough, precip < 25 mm, no induced low
    MODERATE = "MODERATE"               # Noticeable trough, jet speed 60-80 m/s, light-to-moderate rain/snow
    SEVERE_ACTIVE = "SEVERE_ACTIVE"     # Deep trough, negative tilt, induced low over Rajasthan/plains, heavy snow/rain


class WDTerrainRegime(str, Enum):
    """Terrain and elevation domain for Western Disturbance conditioning."""
    HIMALAYAN_HIGH_ALTITUDE = "HIMALAYAN_HIGH_ALTITUDE"     # > 2500m elevation (J&K, Ladakh, HP, Uttarakhand peaks)
    FOOTHILL_SUB_HIMALAYAN = "FOOTHILL_SUB_HIMALAYAN"       # 500m - 2500m elevation (valleys, foothills)
    INDO_GANGETIC_PLAINS = "INDO_GANGETIC_PLAINS"           # < 500m elevation (Punjab, Haryana, Delhi, Rajasthan, West UP)


class WDTroughTilt(str, Enum):
    """Orientation and tilt of 500-hPa mid-tropospheric trough axis."""
    POSITIVE = "POSITIVE"   # Northeast to southwest (less favorable for plains development)
    NEUTRAL = "NEUTRAL"     # North-south aligned
    NEGATIVE = "NEGATIVE"   # Northwest to southeast (strongly diffluent, severe weather triggering)


class WDIssueFeatures(BaseModel):
    """Issue-time features for Western Disturbance forecast reliability at t0."""
    lead_hours: int = Field(..., ge=0, le=240, description="Forecast lead time in hours")
    intensity_class: WDIntensityClass = Field(..., description="Synoptic intensity classification")
    terrain_regime: WDTerrainRegime = Field(..., description="Elevation/terrain classification")

    # Spatial coordinates
    forecast_lat: float = Field(..., ge=24.0, le=38.0, description="Disturbance / trough center latitude (North India)")
    forecast_lon: float = Field(..., ge=68.0, le=86.0, description="Disturbance / trough center longitude")

    # Jet stream and upper-air dynamics
    subtropical_jet_speed_ms: float = Field(default=65.0, ge=20.0, le=120.0, description="200-hPa Subtropical Westerly Jet core wind speed")
    jet_core_lat_displacement_deg: float = Field(default=0.0, ge=-10.0, le=10.0, description="Meridional displacement of jet axis relative to climatology (negative = south)")
    trough_depth_500hpa_gpm: float = Field(default=5580.0, ge=5100.0, le=5950.0, description="Geopotential height at 500-hPa trough minimum")
    trough_tilt: WDTroughTilt = Field(default=WDTroughTilt.NEUTRAL, description="Tilt of mid-tropospheric trough axis")
    induced_low_present: bool = Field(default=False, description="Presence of induced cyclonic circulation in northern plains")
    ensemble_trough_spread_km: float = Field(..., ge=0.0, description="Ensemble dispersion of 500-hPa trough axis position")

    # Precipitation and duration features
    forecast_precip_max_24h_mm: float = Field(..., ge=0.0, description="Forecast peak 24h accumulated precipitation")
    ensemble_precip_spread_mm: float = Field(..., ge=0.0, description="Ensemble precipitation spread (std dev)")
    forecast_duration_hours: float = Field(default=36.0, ge=1.0, le=168.0, description="Forecast disturbance duration in hours")

    # Thermal and observation support (for rain/snow partition)
    freezing_level_m: Optional[float] = Field(None, ge=0.0, le=6000.0, description="0°C isotherm altitude in meters above sea level")
    surface_temp_celsius: Optional[float] = Field(None, ge=-40.0, le=45.0, description="Surface ambient temperature")
    has_high_altitude_obs: bool = Field(default=False, description="Flag indicating presence of high-altitude ground truth observation stations")


class WDReliabilityOutput(BaseModel):
    """Blueprint Section 8 certified Western Disturbance reliability output."""
    hazard: str = Field(default="WESTERN_DISTURBANCE", description="Hazard identifier")

    # Decomposed failure modes
    arrival_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Arrival timing error > 6.0h at <=48h or > 12.0h at 72h+)"
    )
    track_location_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Trough axis or center position placement error > 150 km at 48h or > 250 km at 72h)"
    )
    precipitation_amount_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(24h precipitation intensity error > 35 mm/24h)"
    )
    precipitation_displacement_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Precipitation centroid spatial displacement > 100 km)"
    )
    duration_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Event duration error > 12.0 hours)"
    )
    rain_snow_partition_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Rain vs snow phase misclassification; strictly null when observations unsupported)"
    )

    # Composite reliability and diagnostics
    overall_reliability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Composite WD reliability index [0=unreliable, 1=reliable]"
    )
    evidence: List[str] = Field(default_factory=list, description="Diagnostic factor attributions")
    ood: Optional[bool] = Field(None, description="Out-of-distribution novelty flag")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Model and execution provenance")

    @model_validator(mode="after")
    def validate_hazard_and_null_safety(self) -> "WDReliabilityOutput":
        if self.hazard != "WESTERN_DISTURBANCE":
            raise ValueError(f"hazard must be 'WESTERN_DISTURBANCE', got: {self.hazard}")
        return self


_DEFAULT_WD_MANIFEST = Path(__file__).resolve().parents[3] / "data" / "western_disturbance_target_manifest.json"
_DEFAULT_WD_CATALOGUE = Path(__file__).resolve().parents[3] / "data" / "western_disturbance_event_catalogue.json"


def load_wd_target_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load western disturbance target manifest from disk."""
    target_path = manifest_path or _DEFAULT_WD_MANIFEST
    if not target_path.is_file():
        raise FileNotFoundError(f"Western disturbance target manifest not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_wd_event_catalogue(catalogue_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load historical western disturbance event catalogue from disk."""
    target_path = catalogue_path or _DEFAULT_WD_CATALOGUE
    if not target_path.is_file():
        raise FileNotFoundError(f"Western disturbance event catalogue not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)
