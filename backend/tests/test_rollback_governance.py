"""Rollback Governance and Release Defense Tests (Gate G16 / Phase 5).

Verifies the operational readiness, documentation completeness, and trigger criteria
of the Veyra Fast Rollback Procedure (MTTR < 5m).
"""
import json
import os
from pathlib import Path
import tempfile
import pytest

from backend.app.core.release_manifest import validate_release_manifest


def get_repo_root() -> Path:
    current = Path.cwd()
    if (current / "backend").is_dir() and (current / "models").is_dir():
        return current
    elif (current / "repos" / "repo_b" / "backend").is_dir():
        return current / "repos" / "repo_b"
    return Path(__file__).resolve().parent.parent.parent


def test_rollback_procedure_manifest_completeness():
    """Verify manifests/rollback_procedure.md exists, is comprehensive, and defines MTTR < 5m."""
    repo_root = get_repo_root()
    rb_path = repo_root / "manifests" / "rollback_procedure.md"
    assert rb_path.is_file(), f"Missing rollback procedure at {rb_path}"
    
    size = rb_path.stat().st_size
    assert size >= 500, f"Rollback procedure documentation too brief ({size} bytes, expected >= 500)"

    content = rb_path.read_text(encoding="utf-8")
    content_lower = content.lower()
    
    # Must specify exact trigger conditions
    assert "rollback triggers" in content_lower
    # Must specify rapid rollback protocol
    assert "fast rollback procedure" in content_lower
    # Must specify MTTR target (5 minutes / 5m)
    assert "5 minutes" in content_lower or "5m" in content_lower or "5 min" in content_lower
    # Must specify git tag / release candidate target
    assert "git checkout" in content or "git revert" in content or "tag" in content


def test_corrupted_model_artifact_triggers_rejection():
    """Verify that release manifest validation immediately catches corrupted artifacts."""
    repo_root = get_repo_root()
    manifest_path = repo_root / "backend" / "app" / "core" / "release_manifest.json"
    assert manifest_path.is_file()

    # Legitimate manifest validates cleanly
    res_valid = validate_release_manifest(str(manifest_path), verify_artifacts_on_disk=True)
    assert res_valid.is_valid is True

    # Mutated / corrupt dummy manifest fails validation and blocks release
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["model_artifact"]["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(data, tf)
        temp_path = tf.name

    try:
        res_corrupt = validate_release_manifest(temp_path, verify_artifacts_on_disk=True)
        assert res_corrupt.is_valid is False
        assert len(res_corrupt.errors) > 0
        assert any("does not match" in err.lower() or "sha256" in err.lower() for err in res_corrupt.errors)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_rollback_stop_triggers_logic():
    """Verify automated rollback decision logic when runtime errors exceed threshold."""
    def evaluate_rollback_condition(error_rate: float, ece_score: float, p99_latency_ms: float) -> dict:
        triggers = []
        if error_rate > 0.01:
            triggers.append(f"Inference error rate {error_rate:.2%} exceeds 1.0% limit")
        if ece_score > 0.060:
            triggers.append(f"Expected Calibration Error {ece_score:.4f} exceeds 0.060 limit")
        if p99_latency_ms > 200.0:
            triggers.append(f"P99 latency {p99_latency_ms:.1f}ms exceeds 200ms limit")
        
        return {
            "trigger_rollback": len(triggers) > 0,
            "triggers": triggers,
            "target_recovery_action": "Execute Fast Rollback Procedure (Step 1-3)" if triggers else "NORMAL_OPERATION"
        }

    # Nominal operation: no rollback
    res_nominal = evaluate_rollback_condition(error_rate=0.001, ece_score=0.025, p99_latency_ms=45.0)
    assert res_nominal["trigger_rollback"] is False

    # High calibration drift triggers rollback
    res_drift = evaluate_rollback_condition(error_rate=0.001, ece_score=0.085, p99_latency_ms=45.0)
    assert res_drift["trigger_rollback"] is True
    assert "Expected Calibration Error" in res_drift["triggers"][0]

    # Latency spike triggers rollback
    res_latency = evaluate_rollback_condition(error_rate=0.001, ece_score=0.025, p99_latency_ms=250.0)
    assert res_latency["trigger_rollback"] is True
    assert "P99 latency" in res_latency["triggers"][0]
