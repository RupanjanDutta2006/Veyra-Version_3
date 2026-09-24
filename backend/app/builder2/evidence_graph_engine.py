"""Evidence Graph and Self-Critic Consistency Engine for Veyra (Gate 11 / Phase L).

Provides:
- Directed Acyclic Graph (DAG) of physical evidence linking upstream NWP features,
  intermediate physical mechanisms, and downstream failure probabilities.
- Self-Critic Consistency Validator: Detects and flags physical contradictions
  between predicted failure risks and precursor atmospheric evidence.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceNode(BaseModel):
    """Single node in the physical evidence DAG."""
    node_id: str
    node_type: str  # UPSTREAM_NWP, PHYSICAL_MECHANISM, FAILURE_RISK, MOTIF
    description: str
    value: Any
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    signals: List[str] = Field(default_factory=list)


class EvidenceEdge(BaseModel):
    """Directed edge in the evidence graph."""
    source_node: str
    target_node: str
    relation_type: str  # TRIGGERS, AMPLIFIES, CONSTRAINS, EXPLAINS
    weight: float = Field(default=1.0, ge=0.0)


class EvidenceGraph(BaseModel):
    """Structured physical evidence DAG."""
    hazard_family: str
    nodes: List[EvidenceNode]
    edges: List[EvidenceEdge]
    provenance: Dict[str, Any] = Field(default_factory=dict)


class SelfCriticResult(BaseModel):
    """Result of self-critic physical consistency audit."""
    is_consistent: bool
    predicted_bust_prob: float
    adjusted_bust_prob: float
    contradiction_reasons: List[str]
    critic_verdict: str  # CONSISTENT, CORRECTION_APPLIED, CRITICAL_CONTRADICTION
    explanation: str


class EvidenceGraphEngine:
    """Engine for building evidence graphs and auditing self-critic consistency."""

    def build_evidence_graph(
        self,
        hazard_family: str,
        features: Dict[str, Any],
        predicted_bust_prob: float,
        motif_id: Optional[str] = None,
    ) -> EvidenceGraph:
        """Construct physical evidence DAG linking atmospheric state to failure risk."""
        nodes: List[EvidenceNode] = []
        edges: List[EvidenceEdge] = []

        # 1. Upstream NWP nodes
        nodes.append(EvidenceNode(
            node_id="UPSTREAM_STATE",
            node_type="UPSTREAM_NWP",
            description="Upstream ensemble dispersion and thermodynamic state",
            value=features,
            signals=[k for k, v in features.items() if isinstance(v, (int, float)) and v > 0],
        ))

        # 2. Intermediate physical mechanism node
        mechanism_desc = f"Primary atmospheric driver for {hazard_family}"
        nodes.append(EvidenceNode(
            node_id="PHYSICAL_MECHANISM",
            node_type="PHYSICAL_MECHANISM",
            description=mechanism_desc,
            value={"hazard": hazard_family},
        ))
        edges.append(EvidenceEdge(
            source_node="UPSTREAM_STATE",
            target_node="PHYSICAL_MECHANISM",
            relation_type="TRIGGERS",
        ))

        # 3. Downstream failure risk node
        nodes.append(EvidenceNode(
            node_id="FAILURE_RISK",
            node_type="FAILURE_RISK",
            description="Calibrated probability of forecast bust",
            value=predicted_bust_prob,
        ))
        edges.append(EvidenceEdge(
            source_node="PHYSICAL_MECHANISM",
            target_node="FAILURE_RISK",
            relation_type="AMPLIFIES",
        ))

        # 4. Optional motif node
        if motif_id:
            nodes.append(EvidenceNode(
                node_id="FAILURE_MOTIF",
                node_type="MOTIF",
                description="Classified failure motif pattern",
                value=motif_id,
            ))
            edges.append(EvidenceEdge(
                source_node="FAILURE_RISK",
                target_node="FAILURE_MOTIF",
                relation_type="EXPLAINS",
            ))

        return EvidenceGraph(
            hazard_family=hazard_family,
            nodes=nodes,
            edges=edges,
            provenance={"engine": "EvidenceGraphEngine_v1"},
        )

    def validate_self_critic(
        self,
        hazard_family: str,
        predicted_bust_prob: float,
        features: Dict[str, float],
    ) -> SelfCriticResult:
        """Audit predicted failure risk against physical precursor signals to prevent hallucinations."""
        contradictions: List[str] = []
        adjusted_p = predicted_bust_prob

        # Check Precipitation contradiction: high bust risk without moisture or CAPE
        if hazard_family.upper() == "PRECIPITATION" and predicted_bust_prob >= 0.70:
            cape = features.get("cape_proxy_jkg", 1500.0)
            pwat = features.get("precipitable_water_mm", 45.0)
            if cape < 300.0 and pwat < 25.0:
                contradictions.append(
                    f"Predicted 70%+ precipitation bust risk contradicts dry/stable state (CAPE={cape} J/kg, PWAT={pwat} mm)."
                )
                adjusted_p = min(adjusted_p, 0.35)

        # Check Heatwave contradiction: high bust risk with negative temperature anomaly
        if hazard_family.upper() == "HEATWAVE" and predicted_bust_prob >= 0.70:
            temp_anom = features.get("temp_2m_anomaly_k", 2.0)
            if temp_anom < 0.0:
                contradictions.append(
                    f"Predicted heatwave bust risk contradicts below-normal temperature anomaly ({temp_anom:.1f} K)."
                )
                adjusted_p = min(adjusted_p, 0.25)

        # Check Cyclone contradiction: high track bust with minimal track spread and zero shear
        if hazard_family.upper() == "CYCLONE" and predicted_bust_prob >= 0.70:
            track_spread = features.get("ensemble_track_spread_km", 80.0)
            shear = features.get("vertical_wind_shear_ms", 15.0)
            if track_spread < 30.0 and shear < 8.0:
                contradictions.append(
                    f"Predicted cyclone bust contradicts tightly clustered ensemble (spread={track_spread} km, shear={shear} m/s)."
                )
                adjusted_p = min(adjusted_p, 0.30)

        is_consistent = len(contradictions) == 0
        verdict = "CONSISTENT" if is_consistent else "CORRECTION_APPLIED"
        explanation = (
            "Self-critic confirms physical consistency between atmospheric state and failure risk."
            if is_consistent
            else f"Self-critic identified {len(contradictions)} physical contradiction(s): {'; '.join(contradictions)}"
        )

        return SelfCriticResult(
            is_consistent=is_consistent,
            predicted_bust_prob=round(predicted_bust_prob, 4),
            adjusted_bust_prob=round(adjusted_p, 4),
            contradiction_reasons=contradictions,
            critic_verdict=verdict,
            explanation=explanation,
        )
