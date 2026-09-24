"""Unit tests for Compound Multi-Hazard Reliability (Gate 8 / Phase I)."""

import pytest
from pydantic import ValidationError

from backend.app.contracts.spatial_contract import (
    CompoundHazardOutput,
    CompoundHazardRequest,
    CompoundHazardType,
)
from backend.app.builder2.compound_hazard_engine import CompoundHazardEngine


@pytest.fixture
def compound_engine():
    return CompoundHazardEngine()


def test_compound_hazard_copula_bounds(compound_engine):
    """Verify joint failure probability satisfies Fréchet-Hoeffding copula bounds."""
    req = CompoundHazardRequest(
        hazard_type=CompoundHazardType.HEAT_WIND,
        hazard_a_probability=0.40,
        hazard_b_probability=0.30,
        copula_dependence=0.50,
        location="DELHI",
        lead_hours=48,
    )
    out = compound_engine.evaluate_compound_hazard(req)

    assert out.upper_bound == 0.30  # min(0.40, 0.30)
    assert out.lower_bound == 0.00  # max(0, 0.40 + 0.30 - 1)
    assert out.lower_bound <= out.joint_failure_probability <= out.upper_bound
    assert out.joint_failure_probability > out.independence_probability  # Positive dependence


def test_compound_hazard_no_probability_averaging(compound_engine):
    """Verify joint failure probability is not a flat arithmetic mean."""
    req = CompoundHazardRequest(
        hazard_type=CompoundHazardType.RAIN_WIND,
        hazard_a_probability=0.60,
        hazard_b_probability=0.20,
        copula_dependence=0.40,
        location="MUMBAI",
        lead_hours=24,
    )
    out = compound_engine.evaluate_compound_hazard(req)

    arithmetic_mean = 0.5 * (req.hazard_a_probability + req.hazard_b_probability)
    assert abs(out.joint_failure_probability - arithmetic_mean) > 0.05
    assert out.joint_failure_probability <= 0.20


def test_compound_hazard_flood_decoupling_invariant(compound_engine):
    """Verify rainfall reliability is strictly distinct from flood probability."""
    req = CompoundHazardRequest(
        hazard_type=CompoundHazardType.RAIN_WIND,
        hazard_a_probability=0.50,
        hazard_b_probability=0.40,
        copula_dependence=0.60,
        location="KOLKATA",
        lead_hours=48,
    )
    out = compound_engine.evaluate_compound_hazard(req)

    # Invariants enforced on output
    assert out.hydrological_flood_claim is False
    assert out.rainfall_reliability_distinct_from_flood is True


def test_compound_hazard_flood_claim_rejection():
    """Verify schema rejects any attempt to claim hydrological flood probability."""
    with pytest.raises(ValidationError):
        CompoundHazardOutput(
            hazard_type=CompoundHazardType.RAIN_WIND,
            joint_failure_probability=0.20,
            upper_bound=0.30,
            lower_bound=0.00,
            independence_probability=0.15,
            hydrological_flood_claim=True,  # Forbidden!
            rainfall_reliability_distinct_from_flood=True,
        )

    with pytest.raises(ValidationError):
        CompoundHazardOutput(
            hazard_type=CompoundHazardType.RAIN_WIND,
            joint_failure_probability=0.20,
            upper_bound=0.30,
            lower_bound=0.00,
            independence_probability=0.15,
            hydrological_flood_claim=False,
            rainfall_reliability_distinct_from_flood=False,  # Forbidden!
        )
