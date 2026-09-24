"""Unit tests for Evidence Graph and Self-Critic Consistency Engine (Gate 11 / Phase L)."""

import pytest

from backend.app.builder2.evidence_graph_engine import (
    EvidenceGraphEngine,
    EvidenceGraph,
    SelfCriticResult,
)


@pytest.fixture
def evidence_engine():
    return EvidenceGraphEngine()


def test_build_evidence_graph_structure(evidence_engine):
    """Verify DAG structure with upstream NWP, physical mechanisms, and failure risk nodes."""
    features = {
        "cape_proxy_jkg": 2400.0,
        "precipitable_water_mm": 55.0,
        "vertical_wind_shear_ms": 18.5,
    }
    graph = evidence_engine.build_evidence_graph(
        hazard_family="PRECIPITATION",
        features=features,
        predicted_bust_prob=0.68,
        motif_id="CONVECTIVE_UNDERPREDICTION",
    )

    assert isinstance(graph, EvidenceGraph)
    assert graph.hazard_family == "PRECIPITATION"

    node_ids = [n.node_id for n in graph.nodes]
    assert "UPSTREAM_STATE" in node_ids
    assert "PHYSICAL_MECHANISM" in node_ids
    assert "FAILURE_RISK" in node_ids
    assert "FAILURE_MOTIF" in node_ids

    # Check edges
    edge_pairs = [(e.source_node, e.target_node) for e in graph.edges]
    assert ("UPSTREAM_STATE", "PHYSICAL_MECHANISM") in edge_pairs
    assert ("PHYSICAL_MECHANISM", "FAILURE_RISK") in edge_pairs
    assert ("FAILURE_RISK", "FAILURE_MOTIF") in edge_pairs


def test_self_critic_detects_precipitation_contradiction(evidence_engine):
    """Detect contradiction when 70%+ precipitation bust risk is predicted under dry/stable conditions."""
    dry_features = {
        "cape_proxy_jkg": 100.0,   # Very low instability
        "precipitable_water_mm": 15.0,  # Very dry
    }

    result = evidence_engine.validate_self_critic(
        hazard_family="PRECIPITATION",
        predicted_bust_prob=0.85,
        features=dry_features,
    )

    assert isinstance(result, SelfCriticResult)
    assert result.is_consistent is False
    assert result.critic_verdict == "CORRECTION_APPLIED"
    assert len(result.contradiction_reasons) > 0
    assert result.adjusted_bust_prob <= 0.35  # Damped to physically plausible level


def test_self_critic_detects_heatwave_contradiction(evidence_engine):
    """Detect contradiction when high heatwave bust risk is predicted with negative temperature anomaly."""
    cold_features = {
        "temp_2m_anomaly_k": -2.5,  # Below normal
    }

    result = evidence_engine.validate_self_critic(
        hazard_family="HEATWAVE",
        predicted_bust_prob=0.75,
        features=cold_features,
    )

    assert result.is_consistent is False
    assert result.critic_verdict == "CORRECTION_APPLIED"
    assert result.adjusted_bust_prob <= 0.25


def test_self_critic_confirms_consistent_state(evidence_engine):
    """Verify consistent physical state is validated without correction."""
    convective_features = {
        "cape_proxy_jkg": 2800.0,
        "precipitable_water_mm": 58.0,
    }

    result = evidence_engine.validate_self_critic(
        hazard_family="PRECIPITATION",
        predicted_bust_prob=0.72,
        features=convective_features,
    )

    assert result.is_consistent is True
    assert result.critic_verdict == "CONSISTENT"
    assert len(result.contradiction_reasons) == 0
    assert result.adjusted_bust_prob == 0.72
