"""Tests for Evidence Graph and Provenance contracts (Blueprint Gate 1 / Phase B)."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.evidence_provenance import (
    DataProvenance,
    EvidenceEdge,
    EvidenceEdgeType,
    EvidenceGraph,
    EvidenceNode,
    EvidenceNodeType,
    ModelProvenance,
    ReliabilityProvenance,
)


@pytest.fixture
def sample_evidence_graph() -> EvidenceGraph:
    """Fixture providing a valid 3-node EvidenceGraph."""
    nodes = [
        EvidenceNode(
            node_id="node_spread",
            node_type=EvidenceNodeType.ENSEMBLE_SPREAD,
            description="Normalized ensemble standard deviation",
            physical_value=2.45,
            canonical_unit="K",
            attribution_weight=0.34,
            signal_code="ELEVATED_ENSEMBLE_SPREAD",
        ),
        EvidenceNode(
            node_id="node_drift",
            node_type=EvidenceNodeType.RUN_TO_RUN_DRIFT,
            description="24-hour inter-cycle forecast delta",
            physical_value=1.85,
            canonical_unit="K",
            attribution_weight=0.28,
            signal_code="HIGH_REVISION_DRIFT",
        ),
        EvidenceNode(
            node_id="node_regime",
            node_type=EvidenceNodeType.SYNOPTIC_REGIME,
            description="Active monsoon low-pressure regime index",
            physical_value=0.72,
            canonical_unit="dimensionless",
            attribution_weight=0.15,
            signal_code="MONSOON_TROUGH_PROXIMITY",
        ),
    ]

    edges = [
        EvidenceEdge(
            source_node_id="node_spread",
            target_node_id="node_drift",
            edge_type=EvidenceEdgeType.AMPLIFIES,
            weight=0.65,
            narrative="High spread compounds inter-cycle revision instability",
        ),
        EvidenceEdge(
            source_node_id="node_regime",
            target_node_id="node_spread",
            edge_type=EvidenceEdgeType.SUPPORTS,
            weight=0.45,
            narrative="Monsoon trough proximity supports elevated ensemble dispersion",
        ),
    ]

    return EvidenceGraph(
        graph_id="graph_delhi_t2m_48h",
        nodes=nodes,
        edges=edges,
        primary_driver_id="node_spread",
        synthesis_narrative="Elevated ensemble spread amplified by 24h run-to-run drift indicates heightened risk.",
    )


def test_evidence_graph_validation(sample_evidence_graph: EvidenceGraph):
    """Verify evidence graph structure and edge weights."""
    graph = sample_evidence_graph
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.primary_driver_id == "node_spread"

    for edge in graph.edges:
        assert -1.0 <= edge.weight <= 1.0


def test_primary_driver_id_must_exist_in_nodes(sample_evidence_graph: EvidenceGraph):
    """Verify primary_driver_id validation catches non-existent node references."""
    graph_dict = sample_evidence_graph.model_dump()
    graph_dict["primary_driver_id"] = "non_existent_node"

    with pytest.raises(ValidationError) as exc:
        EvidenceGraph.model_validate(graph_dict)
    assert "primary_driver_id 'non_existent_node' must match an existing node_id in nodes" in str(exc.value)


def test_model_provenance_requires_valid_sha256():
    """Verify ModelProvenance enforces 64-character SHA-256 strings."""
    valid_sha = "00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660"
    model_prov = ModelProvenance(
        model_version="veyra-v3-challenger",
        model_sha256=valid_sha,
        calibrator_sha256="9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531",
        feature_names_sha256="702ff4153fd95d8c9de3bbd01461d65fde0ef207099f7f3a8e7f5c8bac02031e",
        is_lfs_hydrated=True,
    )
    assert model_prov.model_sha256 == valid_sha

    # Test rejection of invalid short hash
    with pytest.raises(ValidationError):
        ModelProvenance(
            model_version="veyra-v3",
            model_sha256="short_hash",
            calibrator_sha256=valid_sha,
            feature_names_sha256=valid_sha,
        )


def test_reliability_provenance_full_record():
    """Verify composition of complete ReliabilityProvenance record."""
    valid_sha = "00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660"
    prov = ReliabilityProvenance(
        generation_timestamp="2026-09-20T11:45:00Z",
        model_provenance=ModelProvenance(
            model_version="veyra-v3-challenger",
            model_sha256=valid_sha,
            calibrator_sha256=valid_sha,
            feature_names_sha256=valid_sha,
            is_lfs_hydrated=True,
        ),
        data_provenance=DataProvenance(
            provider="Open-Meteo GEFS",
            issue_cycle="2026-09-20T00:00:00Z",
            dissemination_latency_hours=4.5,
            missing_members=0,
            ingestion_timestamp="2026-09-20T04:30:00Z",
        ),
        runtime_platform="Windows / x86_64",
        execution_environment="production",
    )

    assert prov.data_provenance.dissemination_latency_hours == 4.5
    assert prov.model_provenance.is_lfs_hydrated is True
