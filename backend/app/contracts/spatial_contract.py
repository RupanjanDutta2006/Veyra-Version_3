"""Operational Spatial, Compound and Common-Mode Reliability Contract (Gate 8 / Phase I).

Defines strongly-typed Pydantic contracts for:
- 25-station spatial network topology and adjacency
- Lagged empirical error covariance propagation (strictly non-causal)
- Regional cluster aggregation and continuous 2D spatial risk surfaces
- Compound hazard sets with copula dependence bounds (no probability averaging)
- Strict decoupling: rainfall reliability is strictly distinct from flood probability
- Common-mode failure indicators and synoptic phase lock detection
- Out-of-Distribution (OOD) novelty flags and provenance metadata
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class MacroRegion(str, Enum):
    """The 7 macro-meteorological geographic clusters of India."""
    NORTHERN_PLAINS = "Northern Plains"
    WESTERN_ARID = "Western Arid"
    CENTRAL_HIGHLANDS = "Central Highlands"
    EASTERN_COASTAL = "Eastern Coastal"
    WESTERN_GHATS = "Western Ghats"
    SOUTHERN_PENINSULA = "Southern Peninsula"
    HIMALAYAN_NORTHEASTERN = "Himalayan/Northeastern"


class StationNode(BaseModel):
    """Canonical meteorological station in the 25-station network."""
    id: str = Field(..., description="Unique station uppercase identifier, e.g. DELHI")
    name: str = Field(..., description="Full station display name")
    latitude: float = Field(..., ge=6.0, le=38.0, description="Station latitude in degrees N")
    longitude: float = Field(..., ge=68.0, le=98.0, description="Station longitude in degrees E")
    elevation_m: float = Field(..., ge=0.0, le=9000.0, description="Elevation above mean sea level in meters")
    region: MacroRegion = Field(..., description="Assigned macro-meteorological region")
    state: str = Field(..., description="Administrative State or Union Territory")
    synoptic_corridor: str = Field(..., description="Dominant atmospheric synoptic corridor")


class SpatialEdge(BaseModel):
    """Directed or undirected graph edge linking two network stations."""
    source: str = Field(..., description="Source station ID")
    target: str = Field(..., description="Target station ID")
    distance_km: float = Field(..., ge=0.0, description="Great-circle Haversine distance in kilometers")
    synoptic_coupling: float = Field(..., ge=0.0, le=1.0, description="Empirical synoptic error correlation weight [0, 1]")


class SpatialIssueFeatures(BaseModel):
    """Issue-time features for network-wide spatial reliability evaluation at t0."""
    lead_hours: int = Field(..., ge=0, le=240, description="Forecast lead time in hours")
    variable: str = Field(..., description="Target atmospheric variable (e.g. precipitation, temperature_2m, wind_speed_10m)")
    station_forecasts: Dict[str, float] = Field(..., description="Station-wise deterministic/ensemble-mean forecast values")
    station_spreads: Dict[str, float] = Field(..., description="Station-wise ensemble standard deviation spreads")
    synoptic_flow_u_ms: Optional[float] = Field(default=5.0, description="Synoptic zonal 850hPa wind component in m/s")
    synoptic_flow_v_ms: Optional[float] = Field(default=2.0, description="Synoptic meridional 850hPa wind component in m/s")

    @field_validator("station_spreads")
    @classmethod
    def validate_positive_spreads(cls, v: Dict[str, float]) -> Dict[str, float]:
        for stn, spr in v.items():
            if spr < 0.0:
                raise ValueError(f"Ensemble spread for station {stn} cannot be negative, got {spr}")
        return v


class SpatialReliabilityOutput(BaseModel):
    """Blueprint Gate 8 certified Spatial Reliability output."""
    hazard: str = Field(default="SPATIAL_NETWORK", description="Hazard identifier")
    station_reliabilities: Dict[str, float] = Field(..., description="Individual station forecast reliability indices [0, 1]")
    station_bust_probabilities: Dict[str, float] = Field(..., description="Individual station bust probabilities [0, 1]")
    cluster_reliabilities: Dict[str, float] = Field(..., description="Aggregated regional macro-cluster reliability indices")
    spatial_risk_surface: Dict[str, Any] = Field(default_factory=dict, description="Continuous 2D interpolated spatial risk surface grid")
    propagation_correlations: Dict[str, float] = Field(default_factory=dict, description="Lagged empirical error covariance between corridor nodes")
    adversarial_robustness_score: float = Field(..., ge=0.0, le=1.0, description="Robustness against spatial dropout / perturbation [0, 1]")
    evidence: List[str] = Field(default_factory=list, description="Spatial diagnostics and evidence")
    ood: bool = Field(default=False, description="Out-of-distribution network novelty flag")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Execution and model provenance")

    @model_validator(mode="after")
    def validate_spatial_hazard(self) -> "SpatialReliabilityOutput":
        if self.hazard != "SPATIAL_NETWORK":
            raise ValueError(f"hazard must be 'SPATIAL_NETWORK', got: {self.hazard}")
        return self


class CompoundHazardType(str, Enum):
    """Supported compound multi-hazard combinations."""
    HEAT_WIND = "HEAT_WIND"         # Extreme heatwave + severe dry convective wind
    RAIN_WIND = "RAIN_WIND"         # Heavy precipitation + gale gust (cyclonic/monsoon)
    RAIN_SNOW = "RAIN_SNOW"         # Mixed-phase heavy precipitation + freezing level shift


class CompoundHazardRequest(BaseModel):
    """Request for evaluating joint multi-hazard forecast reliability."""
    hazard_type: CompoundHazardType = Field(..., description="Type of compound hazard combination")
    hazard_a_probability: float = Field(..., ge=0.0, le=1.0, description="P(Failure on Hazard A)")
    hazard_b_probability: float = Field(..., ge=0.0, le=1.0, description="P(Failure on Hazard B)")
    copula_dependence: float = Field(default=0.5, ge=0.0, le=1.0, description="Dependence parameter chi in [0, 1]")
    location: str = Field(default="ALL_INDIA", description="Geographic location or station ID")
    lead_hours: int = Field(default=48, ge=0, le=240, description="Forecast lead hours")


class CompoundHazardOutput(BaseModel):
    """Certified Compound Multi-Hazard Reliability Output.
    
    Enforces strict mathematical copula bounds and the non-negotiable invariant:
    rainfall reliability is strictly distinct from flood probability.
    """
    hazard_type: CompoundHazardType = Field(..., description="Type of compound hazard")
    joint_failure_probability: float = Field(..., ge=0.0, le=1.0, description="P(Hazard A Fail AND Hazard B Fail)")
    upper_bound: float = Field(..., ge=0.0, le=1.0, description="Fréchet-Hoeffding upper copula bound: min(P_A, P_B)")
    lower_bound: float = Field(..., ge=0.0, le=1.0, description="Fréchet-Hoeffding lower copula bound: max(0, P_A + P_B - 1)")
    independence_probability: float = Field(..., ge=0.0, le=1.0, description="Independence product: P_A * P_B")
    
    # Non-negotiable Veyra invariant
    hydrological_flood_claim: bool = Field(
        default=False,
        description="Strictly False. Rainfall forecast reliability must NEVER claim flood probability."
    )
    rainfall_reliability_distinct_from_flood: bool = Field(
        default=True,
        description="Explicitly certifies that precipitation forecast failure is distinct from catchment flood risk."
    )
    evidence: List[str] = Field(default_factory=list, description="Diagnostic compound attributions")

    @model_validator(mode="after")
    def validate_copula_bounds_and_flood_invariant(self) -> "CompoundHazardOutput":
        # Strict copula bound check
        if self.joint_failure_probability > self.upper_bound + 1e-5:
            raise ValueError(
                f"Joint probability ({self.joint_failure_probability}) exceeds Fréchet-Hoeffding upper bound ({self.upper_bound})"
            )
        if self.joint_failure_probability < self.lower_bound - 1e-5:
            raise ValueError(
                f"Joint probability ({self.joint_failure_probability}) violates Fréchet-Hoeffding lower bound ({self.lower_bound})"
            )
        # Strict flood claim invariant
        if self.hydrological_flood_claim is True:
            raise ValueError("hydrological_flood_claim must strictly be False in atmospheric reliability contract")
        if self.rainfall_reliability_distinct_from_flood is not True:
            raise ValueError("rainfall_reliability_distinct_from_flood must strictly be True")
        return self


class CommonModeIndicatorType(str, Enum):
    """Systemic failure mechanisms spanning multiple stations."""
    SYNOPTIC_PHASE_LOCK = "SYNOPTIC_PHASE_LOCK"           # Misplaced Rossby wave / trough axis
    CONVECTIVE_BREAKDOWN = "CONVECTIVE_BREAKDOWN"         # Diurnal convective parameterization failure
    HEAT_DOME_BIAS = "HEAT_DOME_BIAS"                     # Widespread anticyclonic thermal over/underestimation
    PHYSICS_TRANSITION_SHOCK = "PHYSICS_TRANSITION_SHOCK" # Model cycle discontinuity across domains


class CommonModeOutput(BaseModel):
    """Common-mode failure detection diagnostics."""
    common_mode_detected: bool = Field(..., description="Flag indicating systemic multi-station failure")
    severity_index: float = Field(..., ge=0.0, le=1.0, description="Common-Mode Severity Index (CMSI) [0, 1]")
    participating_stations: List[str] = Field(default_factory=list, description="Station IDs exhibiting coherent failure")
    indicator_type: Optional[CommonModeIndicatorType] = Field(None, description="Identified failure mechanism")
    evidence: List[str] = Field(default_factory=list, description="Common-mode diagnostic evidence")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Detection metadata")


_DEFAULT_TOPOLOGY_PATH = Path(__file__).resolve().parents[3] / "data" / "spatial_network_topology.json"
_DEFAULT_SPATIAL_MANIFEST_PATH = Path(__file__).resolve().parents[3] / "data" / "spatial_target_manifest.json"


def load_spatial_network_topology(topology_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the 25-station network topology from disk."""
    path = topology_path or _DEFAULT_TOPOLOGY_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Spatial network topology not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_spatial_target_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load spatial target manifest from disk."""
    path = manifest_path or _DEFAULT_SPATIAL_MANIFEST_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Spatial target manifest not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
