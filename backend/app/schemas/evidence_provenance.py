"""Evidence Graph and Provenance Schemas for Veyra (Blueprint Gate 1 / Phase B).

Defines typed schemas for:
- Evidence Graph: Directed causal/attribution graph linking physical atmospheric anomalies to forecast bust probabilities.
- Cryptographic Provenance: End-to-end artifact SHA-256 traceability, data ingestion latency, and runtime environment verification.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class EvidenceNodeType(str, Enum):
    """Categories of physical evidence nodes."""
    ENSEMBLE_SPREAD = "ENSEMBLE_SPREAD"
    RUN_TO_RUN_DRIFT = "RUN_TO_RUN_DRIFT"
    SYNOPTIC_REGIME = "SYNOPTIC_REGIME"
    FAILURE_MEMORY_ANALOG = "FAILURE_MEMORY_ANALOG"
    CLIMATOLOGY_DEPARTURE = "CLIMATOLOGY_DEPARTURE"
    VERTICAL_SHEAR = "VERTICAL_SHEAR"
    SURFACE_ANOMALY = "SURFACE_ANOMALY"


class EvidenceEdgeType(str, Enum):
    """Relationships between evidence nodes and bust outcome."""
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    AMPLIFIES = "AMPLIFIES"
    ATTENUATES = "ATTENUATES"


class EvidenceNode(BaseModel):
    """Physical atmospheric or historical evidence node."""
    node_id: str = Field(..., description="Unique node identifier, e.g. node_ens_spread")
    node_type: EvidenceNodeType
    description: str
    physical_value: Optional[float] = None
    canonical_unit: str
    attribution_weight: float = Field(..., description="Normalized contribution weight or SHAP value")
    signal_code: str = Field(..., description="Standardized code, e.g. HIGH_ENSEMBLE_SPREAD")


class EvidenceEdge(BaseModel):
    """Directed attribution relationship between evidence signals."""
    source_node_id: str
    target_node_id: str
    edge_type: EvidenceEdgeType
    weight: float = Field(..., ge=-1.0, le=1.0, description="Attribution coupling strength in [-1.0, 1.0]")
    narrative: Optional[str] = None


class EvidenceGraph(BaseModel):
    """Complete evidence graph structure explaining forecast reliability."""
    graph_id: str
    nodes: List[EvidenceNode]
    edges: List[EvidenceEdge]
    primary_driver_id: str
    synthesis_narrative: str

    @field_validator("primary_driver_id")
    @classmethod
    def validate_primary_driver_exists(cls, v: str, info) -> str:
        nodes = info.data.get("nodes", [])
        node_ids = {n.node_id for n in nodes}
        if nodes and v not in node_ids:
            raise ValueError(f"primary_driver_id '{v}' must match an existing node_id in nodes")
        return v


class ModelProvenance(BaseModel):
    """Cryptographic model artifact verification."""
    model_version: str
    model_sha256: str = Field(..., min_length=64, max_length=64)
    calibrator_sha256: str = Field(..., min_length=64, max_length=64)
    feature_names_sha256: str = Field(..., min_length=64, max_length=64)
    is_lfs_hydrated: bool = Field(default=True)


class DataProvenance(BaseModel):
    """Telemetry data provenance and latency accounting."""
    provider: str
    issue_cycle: str
    dissemination_latency_hours: float = Field(..., ge=0.0)
    missing_members: int = Field(default=0, ge=0)
    ingestion_timestamp: str


class ReliabilityProvenance(BaseModel):
    """Comprehensive provenance record attached to each ReliabilityState."""
    generation_timestamp: str
    model_provenance: ModelProvenance
    data_provenance: DataProvenance
    runtime_platform: str
    execution_environment: str = Field(default="production")
