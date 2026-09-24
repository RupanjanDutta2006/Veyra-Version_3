"""Tests for Upstream NWP Model Version Shift and Drift Safety (Gate 10 / Phase K)."""

import numpy as np
import pytest

from backend.app.builder2.cross_system_transfer_engine import CrossSystemTransferEngine


def test_no_shift_detection():
    """Verify engine detects stable distribution with NO_SHIFT."""
    engine = CrossSystemTransferEngine()
    rng = np.random.RandomState(42)
    n = 1000

    baseline = rng.normal(10.0, 2.0, size=(n, 2))
    current = rng.normal(10.0, 2.0, size=(n, 2))

    res = engine.detect_version_shift(baseline, current, ["cape", "pwat"])
    assert res.status == "NO_SHIFT"
    assert not res.should_abstain
    assert res.overall_psi < 0.10
    assert res.recommended_margin_pct == 0.0


def test_moderate_shift_detection():
    """Verify engine detects moderate shift and applies conservative margin without abstaining."""
    engine = CrossSystemTransferEngine()
    rng = np.random.RandomState(42)
    n = 1000

    baseline = rng.normal(10.0, 2.0, size=(n, 2))
    # Slight shift in mean (+0.8 units)
    current = rng.normal(10.8, 2.1, size=(n, 2))

    res = engine.detect_version_shift(baseline, current, ["cape", "pwat"])
    assert res.status in ["MODERATE_SHIFT", "NO_SHIFT"]
    assert not res.should_abstain
    if res.status == "MODERATE_SHIFT":
        assert res.recommended_margin_pct > 0.0


def test_severe_shift_triggers_abstention():
    """Verify severe upstream model version shift triggers automated abstention."""
    engine = CrossSystemTransferEngine()
    rng = np.random.RandomState(42)
    n = 1000

    baseline = rng.normal(10.0, 2.0, size=(n, 2))
    # Severe shift (mean jumps by 4.0 units / 2 standard deviations)
    current = rng.normal(14.0, 3.5, size=(n, 2))

    res = engine.detect_version_shift(baseline, current, ["cape", "pwat"])
    assert res.status == "SEVERE_SHIFT_ABSTAIN"
    assert res.should_abstain is True
    assert res.overall_psi >= 0.25
    assert "abstention" in res.explanation.lower()
