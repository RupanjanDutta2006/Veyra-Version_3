"""Operational Heatwave and Severe-Wind Reliability Contract (Gate 7 / Phase H).

Defines strongly-typed Pydantic contracts for the heatwave and severe-wind reliability specialist:
- Heatwave occurrence threshold failure probability (missed heatwave or false alarm)
- Peak maximum temperature failure probability (|Tmax_fc - Tmax_obs| > 2.5°C)
- Heatwave onset timing failure probability (onset timing error > 24.0h)
- Spell duration and persistence failure probability (|D_fc - D_obs| > 48.0h)
- Warm night minimum temperature failure probability (|Tmin_fc - Tmin_obs| > 2.0°C)
- Spatial extent area coverage failure probability (fraction error > 0.20)
- Severe wind gale gust failure probability (|V_fc - V_obs| > 6.0 m/s; data-dependent)
- Overall composite reliability
- Out-of-distribution (OOD) novelty flag and selective abstention
- Provenance and evidence metadata
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class HeatwaveRegime(str, Enum):
    """Climatic and geographic domains for heatwave evaluation."""
    CORE_HEATWAVE_ZONE = "CORE_HEATWAVE_ZONE"       # Central, North, and Eastern India (Punjab to AP/Telangana, Bengal)
    NORTHWEST_PLAINS = "NORTHWEST_PLAINS"           # Rajasthan, Haryana, Delhi, Western UP (arid / semi-arid)
    COASTAL_PENINSULAR = "COASTAL_PENINSULAR"       # Coastal Andhra, Odisha, Tamil Nadu, Maharashtra (humid heat)
    HILL_REGION = "HILL_REGION"                     # Western/Eastern Himalayas (lower threshold >= 30°C)


class HeatwaveSeverity(str, Enum):
    """IMD heatwave severity classification."""
    NORMAL = "NORMAL"                               # Below heatwave criteria
    HEATWAVE = "HEATWAVE"                           # Tmax >= 40°C & dep >= 4.5°C (or >= 45°C)
    SEVERE_HEATWAVE = "SEVERE_HEATWAVE"             # Tmax >= 40°C & dep >= 6.5°C (or >= 47°C)


class HeatwaveIssueFeatures(BaseModel):
    """Issue-time features for Heatwave and Severe-Wind forecast reliability at t0."""
    lead_hours: int = Field(..., ge=0, le=240, description="Forecast lead time in hours")
    regime: HeatwaveRegime = Field(..., description="Geographic climatic domain")
    severity: HeatwaveSeverity = Field(..., description="Forecast heatwave severity category")

    # Spatial coordinates
    forecast_lat: float = Field(..., ge=8.0, le=38.0, description="Forecast point latitude")
    forecast_lon: float = Field(..., ge=68.0, le=98.0, description="Forecast point longitude")

    # Thermal and ensemble spread features
    forecast_tmax_celsius: float = Field(..., ge=15.0, le=58.0, description="Forecast daily peak 2m maximum temperature")
    forecast_tmin_celsius: float = Field(..., ge=0.0, le=42.0, description="Forecast daily minimum 2m temperature")
    climatological_normal_tmax_celsius: float = Field(default=38.0, ge=15.0, le=48.0, description="30-year normal maximum temperature")
    departure_tmax_celsius: float = Field(default=0.0, ge=-15.0, le=20.0, description="Forecast departure from climatological normal")
    ensemble_tmax_spread_celsius: float = Field(..., ge=0.0, le=15.0, description="Ensemble maximum temperature standard deviation")
    ensemble_tmin_spread_celsius: float = Field(default=1.5, ge=0.0, le=12.0, description="Ensemble minimum temperature standard deviation")

    # Thermodynamic and surface environment
    soil_moisture_fraction: float = Field(default=0.15, ge=0.0, le=1.0, description="Volumetric surface soil moisture fraction [0-1]")
    temp_advection_850hpa_k_s: float = Field(default=1.0e-5, ge=-1e-3, le=1e-3, description="850-hPa horizontal thermal advection")
    forecast_duration_days: float = Field(default=3.0, ge=1.0, le=60.0, description="Forecast contiguous spell duration in days")

    # Paired severe wind features (Gate 0 data-dependent)
    wind_gust_10m_ms: Optional[float] = Field(None, ge=0.0, le=80.0, description="Peak 10m wind gust speed")
    ensemble_gust_spread_ms: Optional[float] = Field(None, ge=0.0, le=30.0, description="Ensemble wind gust spread")
    has_paired_wind_data: bool = Field(default=False, description="Flag indicating paired forecast/reference severe wind data availability")


class HeatwaveReliabilityOutput(BaseModel):
    """Blueprint Section 8 certified Heatwave and Severe-Wind reliability output."""
    hazard: str = Field(default="HEATWAVE", description="Hazard identifier")

    # Decomposed failure modes
    threshold_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Heatwave occurrence threshold miss or false alarm)"
    )
    peak_temperature_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Peak maximum temperature error |Tmax_fc - Tmax_obs| > 2.5°C)"
    )
    onset_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Heatwave onset timing error > 24.0 hours)"
    )
    duration_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Heatwave spell duration error > 48.0 hours / 2 days)"
    )
    warm_night_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Warm night minimum temperature departure error > 2.0°C)"
    )
    spatial_extent_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Heatwave spatial extent area coverage fraction error > 0.20)"
    )
    severe_wind_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Gale gust error > 6.0 m/s; strictly null when paired wind data unsupported)"
    )

    # Composite reliability and diagnostics
    overall_reliability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Composite heatwave reliability index [0=unreliable, 1=reliable]"
    )
    evidence: List[str] = Field(default_factory=list, description="Diagnostic factor attributions")
    ood: Optional[bool] = Field(None, description="Out-of-distribution novelty flag")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Model and execution provenance")

    @model_validator(mode="after")
    def validate_hazard_and_wind_policy(self) -> "HeatwaveReliabilityOutput":
        if self.hazard != "HEATWAVE":
            raise ValueError(f"hazard must be 'HEATWAVE', got: {self.hazard}")
        return self


_DEFAULT_HEATWAVE_MANIFEST = Path(__file__).resolve().parents[3] / "data" / "heatwave_target_manifest.json"
_DEFAULT_HEATWAVE_CATALOGUE = Path(__file__).resolve().parents[3] / "data" / "heatwave_event_catalogue.json"


def load_heatwave_target_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load heatwave target manifest from disk."""
    target_path = manifest_path or _DEFAULT_HEATWAVE_MANIFEST
    if not target_path.is_file():
        raise FileNotFoundError(f"Heatwave target manifest not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_heatwave_event_catalogue(catalogue_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load historical heatwave event catalogue from disk."""
    target_path = catalogue_path or _DEFAULT_HEATWAVE_CATALOGUE
    if not target_path.is_file():
        raise FileNotFoundError(f"Heatwave event catalogue not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)
