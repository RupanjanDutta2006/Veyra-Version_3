"""Unit tests for Frontier Challengers and Generative Simulation Engine (Gate 11 / Phase L)."""

import numpy as np
import pytest

from backend.app.builder2.frontier_engine import (
    FrontierChallengerEngine,
    InformationGainMetrics,
    GenerativeFieldSimulation,
)
from backend.app.contracts.operational_watchlist_contract import PromotionStatus


@pytest.fixture
def frontier_engine():
    return FrontierChallengerEngine(max_allowed_latency_overhead=5.0)


def test_frontier_evaluation_rejects_excessive_latency(frontier_engine):
    """Ensure challenger with high latency overhead is rejected for production and certified model is retained."""
    np.random.seed(42)
    y_true = np.array([0, 1, 0, 1, 1, 0, 1, 0, 0, 1])
    p_inc = np.array([0.2, 0.8, 0.3, 0.7, 0.9, 0.1, 0.85, 0.15, 0.25, 0.75])
    # Challenger is slightly sharper
    p_ch = np.array([0.1, 0.9, 0.2, 0.8, 0.95, 0.05, 0.9, 0.1, 0.2, 0.8])

    # 15x latency overhead (150ms vs 10ms)
    metrics = frontier_engine.evaluate_information_gain(
        challenger_id="FRONTIER_GRAPH_DIFFUSION_V0",
        incumbent_id="CERTIFIED_PRECIPITATION_V1",
        p_challenger=p_ch,
        p_incumbent=p_inc,
        y_true=y_true,
        challenger_latency_ms=150.0,
        incumbent_latency_ms=10.0,
    )

    assert isinstance(metrics, InformationGainMetrics)
    assert metrics.gate_decision == "REJECTED_FOR_PRODUCTION_RETAIN_CERTIFIED"
    assert "latency penalty" in metrics.explanation
    assert metrics.delta_brier > 0  # It was better on Brier, but failed on latency
    assert metrics.information_gain_kl_bits >= 0


def test_frontier_evaluation_rejects_worse_brier(frontier_engine):
    """Ensure challenger with worse Brier score is rejected."""
    y_true = np.array([0, 1, 0, 1])
    p_inc = np.array([0.1, 0.9, 0.1, 0.9])
    p_ch = np.array([0.4, 0.6, 0.4, 0.6])  # Worse accuracy/calibration

    metrics = frontier_engine.evaluate_information_gain(
        challenger_id="FRONTIER_TRANSFORMER_V0",
        incumbent_id="CERTIFIED_CYCLONE_V1",
        p_challenger=p_ch,
        p_incumbent=p_inc,
        y_true=y_true,
        challenger_latency_ms=20.0,
        incumbent_latency_ms=15.0,
    )

    assert metrics.gate_decision == "REJECTED_FOR_PRODUCTION_RETAIN_CERTIFIED"
    assert metrics.delta_brier <= 0
    assert "worse Brier score" in metrics.explanation


def test_generative_spatial_simulation_marked_as_simulation(frontier_engine):
    """Ensure generative field outputs are explicitly tagged is_simulation: true with EXPERIMENTAL status."""
    station_ids = ["STN_DELHI", "STN_JAIPUR", "STN_LUCKNOW"]
    base_probs = [0.45, 0.60, 0.30]

    sim = frontier_engine.generate_spatial_simulation(
        hazard_family="HEATWAVE",
        station_ids=station_ids,
        base_probs=base_probs,
        diffusion_steps=30,
        random_seed=123,
    )

    assert isinstance(sim, GenerativeFieldSimulation)
    assert sim.is_simulation is True
    assert sim.status == PromotionStatus.EXPERIMENTAL
    assert len(sim.simulated_failure_field) == 3
    assert sim.provenance["is_simulation"] is True
    for val in sim.simulated_failure_field:
        assert 0.0 <= val <= 1.0
