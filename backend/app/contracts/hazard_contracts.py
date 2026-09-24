"""Operational Hazard Data Contracts and Availability Matrix for Veyra (Gate 0 / Phase A).

Defines strongly-typed Pydantic contracts for 6 meteorological hazard families:
- PRECIPITATION
- CYCLONE
- MONSOON_LPS
- WESTERN_DISTURBANCE
- HEATWAVE
- SEVERE_WIND

Enforces temporal causality, unit transformations, dissemination latency, and reference truth-sealing.
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class HazardFamily(str, Enum):
    """Supported meteorological hazard families."""
    PRECIPITATION = "PRECIPITATION"
    CYCLONE = "CYCLONE"
    MONSOON_LPS = "MONSOON_LPS"
    WESTERN_DISTURBANCE = "WESTERN_DISTURBANCE"
    HEATWAVE = "HEATWAVE"
    SEVERE_WIND = "SEVERE_WIND"


class OperationalStatus(str, Enum):
    """Operational deployment status of hazard reliability specialist."""
    OPERATIONAL = "OPERATIONAL"
    PROXY = "PROXY"
    ABSTAINED = "ABSTAINED"
    FUTURE = "FUTURE"


class HazardVariableContract(BaseModel):
    """Contract for an input or derived variable within a hazard family."""
    name: str = Field(..., description="Canonical variable identifier")
    raw_unit: str = Field(..., description="Raw upstream provider unit")
    canonical_unit: str = Field(..., description="Transformed canonical SI/meteorological unit")
    description: str = Field(..., description="Physical definition and description")


class GridContract(BaseModel):
    """Spatial resolution and domain boundary specification."""
    spatial_resolution_deg: float = Field(..., ge=0.01, le=2.5)
    domain: str = Field(..., description="Geographical coverage description")
    coordinate_system: str = Field(default="WGS84")


class CadenceContract(BaseModel):
    """Temporal issuance cycle and lead horizon bounds."""
    issue_cycle_hours: List[int] = Field(..., description="UTC issue cycle hours, e.g. [0, 6, 12, 18]")
    lead_hours_min: int = Field(..., ge=0)
    lead_hours_max: int = Field(..., le=360)
    cadence_hours: int = Field(..., ge=1)


class EnsembleContract(BaseModel):
    """Ensemble size, missingness tolerance, and member criteria."""
    member_count: int = Field(..., ge=1)
    minimum_required_members: int = Field(..., ge=1)
    missingness_tolerance_pct: float = Field(..., ge=0.0, le=50.0)

    @field_validator("minimum_required_members")
    @classmethod
    def check_min_members(cls, v: int, info: Any) -> int:
        member_count = info.data.get("member_count")
        if member_count is not None and v > member_count:
            raise ValueError("minimum_required_members cannot exceed member_count")
        return v


class ReferenceContract(BaseModel):
    """Authoritative ground truth reference and verification latency."""
    primary: str = Field(..., description="Primary reference source identifier")
    fallback: Optional[str] = Field(None, description="Secondary reference source")
    resolution_deg: float = Field(..., ge=0.01)
    verification_latency_days: int = Field(..., ge=0, description="Sealed truth delay in days")


class LabelContract(BaseModel):
    """Bust threshold and label definition contract."""
    label_name: str
    threshold_type: str
    description: str
    threshold_fixed_mm: Optional[float] = None
    threshold_quantile: Optional[float] = None
    threshold_track_error_km: Optional[float] = None
    threshold_intensity_error_ms: Optional[float] = None
    threshold_genesis_timing_hours: Optional[float] = None
    threshold_center_placement_km: Optional[float] = None
    threshold_arrival_hours: Optional[float] = None
    threshold_precip_error_mm: Optional[float] = None
    threshold_plains_celsius: Optional[float] = None
    threshold_anomaly_celsius: Optional[float] = None
    threshold_speed_ms: Optional[float] = None


class HazardContract(BaseModel):
    """Complete operational contract for a single hazard family."""
    hazard_id: str
    hazard_family: HazardFamily
    hazard_name: str
    provider: str
    variables: List[HazardVariableContract]
    grid: GridContract
    cadence: CadenceContract
    ensemble: EnsembleContract
    dissemination_latency_hours: float = Field(..., ge=0.0)
    reference: ReferenceContract
    label_contract: LabelContract
    operational_status: OperationalStatus


class HazardAvailabilityMatrix(BaseModel):
    """Top-level matrix container for all hazard operational contracts."""
    version: str
    last_updated: str
    gate: str
    description: str
    invariants: Dict[str, str]
    hazards: List[HazardContract]


_DEFAULT_MATRIX_PATH = Path(__file__).resolve().parents[3] / "data" / "hazard_availability_matrix.json"


def load_hazard_availability_matrix(matrix_path: Optional[Path] = None) -> HazardAvailabilityMatrix:
    """Load and validate the hazard availability matrix from JSON disk artifact."""
    target_path = matrix_path or _DEFAULT_MATRIX_PATH
    if not target_path.is_file():
        raise FileNotFoundError(f"Hazard availability matrix artifact not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return HazardAvailabilityMatrix.model_validate(data)


def get_hazard_contract(
    hazard_family: HazardFamily | str,
    matrix: Optional[HazardAvailabilityMatrix] = None,
) -> Optional[HazardContract]:
    """Retrieve the operational hazard contract for a given hazard family."""
    mat = matrix or load_hazard_availability_matrix()
    family_str = hazard_family.value if isinstance(hazard_family, HazardFamily) else str(hazard_family).upper()
    for h in mat.hazards:
        if h.hazard_family.value == family_str:
            return h
    return None
