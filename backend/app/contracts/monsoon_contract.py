"""Operational Monsoon and Low-Pressure-System (LPS) Reliability Contract (Gate 5 / Phase F).

Defines strongly-typed Pydantic contracts for the monsoon reliability specialist:
- System Dynamics:
  - System location failure probability (Center placement error > 200 km)
  - Propagation speed failure probability (Speed error > 5 km/h or arrival error > 12h)
  - Deepening failure probability (24h central pressure deepening error > 4 hPa)
- Precipitation Dynamics:
  - Rainfall centroid placement failure probability (> 100 km)
  - Heavy rainfall intensity failure probability (> 50 mm/24h)
- Regime Transition:
  - Active <-> Break regime transition failure probability (> 24h error or false transition)
- Overall composite reliability
- Out-of-distribution (OOD) novelty flag and selective abstention
- Provenance and evidence metadata
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class MonsoonSystemType(str, Enum):
    """Monsoon synoptic system classification."""
    LOW_PRESSURE_AREA = "LOW_PRESSURE_AREA"         # Central pressure drop ~2-3 hPa, winds < 17 kt
    DEPRESSION = "DEPRESSION"                       # Central pressure drop 3-5 hPa, winds 17-27 kt
    DEEP_DEPRESSION = "DEEP_DEPRESSION"             # Central pressure drop 6-8 hPa, winds 28-33 kt
    MONSOON_DEPRESSION = "MONSOON_DEPRESSION"       # Synoptic depression embedded in the monsoon trough


class MonsoonRegimeState(str, Enum):
    """Large-scale South Asian monsoon regime state."""
    ACTIVE_MONSOON = "ACTIVE_MONSOON"               # Trough south of normal, enhanced core-zone rain
    BREAK_MONSOON = "BREAK_MONSOON"                 # Trough at Himalayan foothills, rain subdued in plains
    NORMAL = "NORMAL"                               # Trough in near-normal climatological position
    TRANSITION_TO_ACTIVE = "TRANSITION_TO_ACTIVE"   # Revival phase from break to active
    TRANSITION_TO_BREAK = "TRANSITION_TO_BREAK"     # Weakening phase toward break conditions


class MonsoonIssueFeatures(BaseModel):
    """Issue-time features for monsoon and LPS forecast reliability at t0."""
    lead_hours: int = Field(..., ge=0, le=240, description="Forecast lead time in hours")
    system_type: MonsoonSystemType = Field(..., description="Classification of synoptic low-pressure system")
    regime_state: MonsoonRegimeState = Field(..., description="Active, break, normal, or transitional regime")
    
    # Position and dynamics
    forecast_lat: float = Field(..., ge=5.0, le=38.0, description="System center latitude in degrees")
    forecast_lon: float = Field(..., ge=60.0, le=102.0, description="System center longitude in degrees")
    central_pressure_hpa: float = Field(default=996.0, ge=960.0, le=1025.0, description="Central sea level pressure")
    pressure_tendency_hpa_24h: Optional[float] = Field(None, description="24h central pressure change (negative = deepening)")
    forward_speed_kmh: float = Field(default=15.0, ge=0.0, le=70.0, description="System propagation velocity")
    ensemble_track_spread_km: float = Field(..., ge=0.0, description="Ensemble dispersion of system center position")
    
    # Dynamic and thermodynamic environment
    vorticity_850hpa_s: float = Field(default=1.2e-4, ge=0.0, le=1e-3, description="Low-level relative vorticity at 850 hPa")
    vertical_wind_shear_ms: float = Field(default=12.0, ge=0.0, le=65.0, description="Deep-layer 200-850 hPa shear")
    moisture_flux_transport_kg_ms: float = Field(default=450.0, ge=20.0, le=2000.0, description="Integrated zonal/meridional moisture transport")
    
    # Precipitation features
    forecast_rainfall_max_24h_mm: float = Field(..., ge=0.0, description="Forecast peak 24h accumulated rainfall")
    ensemble_rainfall_spread_mm: float = Field(..., ge=0.0, description="Ensemble precipitation spread (std dev)")
    
    # Large-scale synoptic indices
    monsoon_trough_displacement_km: Optional[float] = Field(
        None, description="Meridional displacement of the monsoon trough axis relative to normal position (positive = north)"
    )
    offshore_trough_present: bool = Field(default=False, description="Presence of Arabian Sea offshore trough along west coast")
    revision_delta_km: Optional[float] = Field(None, description="Inter-cycle system position revision")


class MonsoonReliabilityOutput(BaseModel):
    """Blueprint Section 8 certified monsoon and LPS reliability output."""
    hazard: str = Field(default="MONSOON_LPS", description="Hazard identifier")
    
    # Three-pillar decomposed outputs
    # Pillar 1: System Dynamics Reliability
    system_location_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(LPS center position placement error > 200 km)"
    )
    propagation_speed_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Translation speed error > 5 km/h or arrival error > 12h)"
    )
    deepening_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(24h central pressure deepening error > 4 hPa)"
    )
    
    # Pillar 2: Precipitation Reliability
    rainfall_placement_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Monsoon rainfall centroid placement error > 100 km)"
    )
    rainfall_intensity_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(24h rainfall intensity error > 50 mm/24h)"
    )
    
    # Pillar 3: Regime Transition Reliability
    regime_transition_failure_probability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="P(Active <-> Break regime transition timing error > 24h or false transition)"
    )
    
    # Overall and diagnostic outputs
    overall_reliability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Composite monsoon reliability index [0=unreliable, 1=reliable]"
    )
    evidence: List[str] = Field(default_factory=list, description="Diagnostic factor attributions")
    ood: Optional[bool] = Field(None, description="Out-of-distribution novelty flag")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Model and execution provenance")

    @model_validator(mode="after")
    def validate_hazard(self) -> "MonsoonReliabilityOutput":
        if self.hazard != "MONSOON_LPS":
            raise ValueError(f"hazard must be 'MONSOON_LPS', got: {self.hazard}")
        return self


_DEFAULT_MONSOON_MANIFEST = Path(__file__).resolve().parents[3] / "data" / "monsoon_target_manifest.json"
_DEFAULT_MONSOON_CATALOGUE = Path(__file__).resolve().parents[3] / "data" / "monsoon_event_catalogue.json"


def load_monsoon_target_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load monsoon target manifest from disk."""
    target_path = manifest_path or _DEFAULT_MONSOON_MANIFEST
    if not target_path.is_file():
        raise FileNotFoundError(f"Monsoon target manifest not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_monsoon_event_catalogue(catalogue_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load historical monsoon event catalogue from disk."""
    target_path = catalogue_path or _DEFAULT_MONSOON_CATALOGUE
    if not target_path.is_file():
        raise FileNotFoundError(f"Monsoon event catalogue not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)
