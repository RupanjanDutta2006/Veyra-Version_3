"""Authoritative Replay Modes & Provenance Governance Tests (Gate G11 / Phase 5).

Verifies that physical historical ground truth replay and synthetic digital-twin
demonstration scenarios are strictly separated by contract, schema, and CLI behavior.
"""
import subprocess
import sys
from pathlib import Path
import pytest

from backend.app.core.replay_modes import (
    ReplayContract,
    ReplayMode,
    create_historical_replay_record,
    create_synthetic_replay_record,
)
from backend.app.core.replay_harness import ReplayHarness
from backend.app.core.golden_replay_matrix import GOLDEN_REPLAY_MATRIX


def test_replay_mode_separation_contracts():
    """Verify historical and synthetic contract defaults."""
    # 1. Historical mode contract
    hist = create_historical_replay_record(
        provenance="NOAA GEFSv12 2017-2019 Frozen Benchmark",
        scenario_id="HIST-DELHI-001",
    )
    assert hist.mode == ReplayMode.HISTORICAL
    assert hist.is_synthetic is False
    assert hist.is_independent_truth is True
    assert hist.scenario_id == "HIST-DELHI-001"

    # 2. Synthetic digital twin contract
    synth = create_synthetic_replay_record(
        provenance="Digital Twin Scenario Generator (Simulated Progression)",
        scenario_id="TWIN-CYCLONE-001",
    )
    assert synth.mode == ReplayMode.SYNTHETIC
    assert synth.is_synthetic is True
    assert synth.is_independent_truth is False
    assert "[NOTICE]" in synth.disclosure_notice


def test_historical_rejects_synthetic_violation():
    """Negative test: Historical records CANNOT be synthetic."""
    with pytest.raises(ValueError, match="Scientific Conflation Violation"):
        ReplayContract(
            mode=ReplayMode.HISTORICAL,
            provenance="Masquerading Data",
            is_synthetic=True,
            is_independent_truth=True,
        )


def test_historical_requires_independent_truth():
    """Negative test: Historical records MUST have independent truth."""
    with pytest.raises(ValueError, match="Scientific Truth Violation"):
        ReplayContract(
            mode=ReplayMode.HISTORICAL,
            provenance="Fake Historical Without Truth",
            is_synthetic=False,
            is_independent_truth=False,
        )


def test_synthetic_forbids_claiming_independent_truth():
    """Negative test: Synthetic digital twin data CANNOT claim to be independent truth."""
    with pytest.raises(ValueError, match="Scientific Representation Violation"):
        ReplayContract(
            mode=ReplayMode.SYNTHETIC,
            provenance="Simulated Twin Generator",
            is_synthetic=True,
            is_independent_truth=True,
        )


def test_synthetic_requires_synthetic_flag():
    """Negative test: Synthetic mode MUST set is_synthetic=True."""
    with pytest.raises(ValueError, match="Provenance Violation"):
        ReplayContract(
            mode=ReplayMode.SYNTHETIC,
            provenance="Simulation",
            is_synthetic=False,
            is_independent_truth=False,
        )


def test_invalid_replay_mode_rejected():
    """Negative test: Invalid replay mode strings are rejected."""
    with pytest.raises(ValueError, match="Invalid replay mode"):
        ReplayContract(
            mode="quantum_superposition",
            provenance="Unknown",
            is_synthetic=False,
            is_independent_truth=False,
        )


def test_cli_historical_replay_rejects_synthetic_mode():
    """CLI test: scripts/replay_historical.py strictly rejects --mode synthetic."""
    cmd = [sys.executable, "scripts/replay_historical.py", "--mode", "synthetic"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode != 0
    assert "must be 'historical'" in res.stdout or "must be 'historical'" in res.stderr


def test_cli_historical_replay_succeeds_with_historical_mode():
    """CLI test: scripts/replay_historical.py passes with --mode historical."""
    cmd = [sys.executable, "scripts/replay_historical.py", "--mode", "historical"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "[PASS]" in res.stdout


def test_cli_digital_twin_synthetic_mode_disclosure():
    """CLI test: scripts/replay_digital_twin.py outputs explicit synthetic disclosure notice."""
    cmd = [sys.executable, "scripts/replay_digital_twin.py", "--mode", "synthetic"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "[NOTICE]" in res.stdout
    assert "[PASS]" in res.stdout


def test_replay_harness_golden_matrix_reproducibility():
    """Verify offline inference reproducibility across golden replay matrix."""
    harness = ReplayHarness()
    all_passed, results = harness.replay_golden_matrix(GOLDEN_REPLAY_MATRIX[:3])
    assert all_passed is True
    for r in results:
        assert r.is_reproducible is True
        assert len(r.mismatches) == 0
        assert r.contract_checks["artifact_integrity"] is True
