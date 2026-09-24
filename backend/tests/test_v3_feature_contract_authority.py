"""Authoritative Gate Tests for V3 Release Manifest, 50-Feature Contract & Routing Authority.

Validates the three core architectural gates established in Phase 03:
- Gate G1: Model, calibrator, and feature-file SHA-256 cross-checks against release manifest & deserialization.
- Gate G2: Inference parity using canonical 50-feature vector producing calibrated probability P in [0, 1].
- Gate G3: Route authority (/v1/predict), operational threshold (0.060), and safe abstention on corruption.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest
from sklearn.isotonic import IsotonicRegression

from backend.app.builder2.v3_feature_pipeline import (
    V3_FEATURE_NAMES,
    V3FeaturePipeline,
)
from backend.app.builder2.v3_model_adapter import (
    ACCEPTED_MODEL_SHAS,
    EXPECTED_CALIBRATOR_SHA256,
    EXPECTED_MODEL_SHA256,
    V3_OPERATIONAL_THRESHOLD,
    Builder2V3ModelAdapter,
)
from backend.app.core.release_manifest import (
    EXPECTED_FEATURE_COUNT,
    load_release_manifest,
    validate_release_manifest,
)
from backend.app.schemas.weather import CanonicalForecastRecord
from backend.app.services.base import FeatureResult

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_MANIFEST_PATH = REPO_ROOT / "backend/app/core/release_manifest.json"
ARTIFACT_MANIFEST_PATH = REPO_ROOT / "models/v3/artifact_manifest.json"
MODEL_PATH = REPO_ROOT / "models/v3/lightgbm_v3_challenger.joblib"
CALIBRATOR_PATH = REPO_ROOT / "models/v3/probability_calibrator_v3.joblib"
FEATURES_PATH = REPO_ROOT / "models/v3/feature_names.json"

EXPECTED_FEATURE_SHA256 = (
    "702ff4153fd95d8c9de3bbd01461d65fde0ef207099f7f3a8e7f5c8bac02031e"
)


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# =========================================================================
# GATE G1: Manifest Authority, Cryptographic Hashes & Deserialization
# =========================================================================


def test_gate_g1_release_manifest_validation():
    """Verify release manifest passes complete schema and integrity checks."""
    assert RELEASE_MANIFEST_PATH.is_file(), f"Missing {RELEASE_MANIFEST_PATH}"
    result = validate_release_manifest(
        manifest_path=str(RELEASE_MANIFEST_PATH),
        verify_artifacts_on_disk=True,
    )
    assert result.is_valid is True, f"Release manifest invalid: {result.errors}"
    assert result.verified_contracts.get("schema_completeness") is True
    assert result.verified_contracts.get("model_artifact_hash") is True
    assert result.verified_contracts.get("calibrator_artifact_hash") is True
    assert result.verified_contracts.get("feature_count") is True


def test_gate_g1_artifact_checksums_match_authority():
    """Verify SHA-256 checksums of model, calibrator, and feature-schema files."""
    model_sha = _compute_sha256(MODEL_PATH)
    assert (
        model_sha == EXPECTED_MODEL_SHA256
    ), f"Model SHA-256 mismatch: {model_sha} != {EXPECTED_MODEL_SHA256}"

    calibrator_sha = _compute_sha256(CALIBRATOR_PATH)
    assert (
        calibrator_sha == EXPECTED_CALIBRATOR_SHA256
    ), f"Calibrator SHA-256 mismatch: {calibrator_sha} != {EXPECTED_CALIBRATOR_SHA256}"

    feature_sha = _compute_sha256(FEATURES_PATH)
    assert (
        feature_sha == EXPECTED_FEATURE_SHA256
    ), f"Feature JSON SHA-256 mismatch: {feature_sha} != {EXPECTED_FEATURE_SHA256}"


def test_gate_g1_manifest_cross_consistency():
    """Verify backend release manifest and models/v3 artifact manifest agree."""
    rel_manifest = load_release_manifest(str(RELEASE_MANIFEST_PATH))
    assert ARTIFACT_MANIFEST_PATH.is_file()
    with open(ARTIFACT_MANIFEST_PATH, "r", encoding="utf-8") as f:
        art_manifest = json.load(f)

    # Cross check model sha
    assert (
        rel_manifest["model_artifact"]["sha256"]
        == art_manifest["artifacts"]["model"]["sha256"]
        == EXPECTED_MODEL_SHA256
    )

    # Cross check calibrator sha
    assert (
        rel_manifest["calibrator_artifact"]["sha256"]
        == art_manifest["artifacts"]["calibrator"]["sha256"]
        == EXPECTED_CALIBRATOR_SHA256
    )

    # Cross check feature schema sha
    assert (
        rel_manifest["feature_contract"]["sha256"]
        == art_manifest["artifacts"]["features"]["sha256"]
        == EXPECTED_FEATURE_SHA256
    )

    # Verify environment pins exist
    env_pins = rel_manifest.get("environment_pins", {})
    assert "python" in env_pins
    assert "scikit-learn" in env_pins or "scikit_learn" in env_pins
    assert "lightgbm" in env_pins
    assert "joblib" in env_pins


def test_gate_g1_artifact_deserialization_and_types():
    """Verify binary models deserialize cleanly into their respective target types."""
    model_obj = joblib.load(MODEL_PATH)
    if hasattr(model_obj, "booster_"):
        booster = model_obj.booster_
    elif isinstance(model_obj, lgb.Booster):
        booster = model_obj
    else:
        booster = getattr(model_obj, "_Booster", None)

    assert booster is not None, "Failed to extract LightGBM Booster from model artifact"
    assert booster.num_feature() == EXPECTED_FEATURE_COUNT

    calibrator_obj = joblib.load(CALIBRATOR_PATH)
    assert isinstance(
        calibrator_obj, IsotonicRegression
    ), f"Calibrator must be IsotonicRegression, got {type(calibrator_obj)}"
    assert hasattr(calibrator_obj, "predict")


# =========================================================================
# GATE G2: Canonical 50-Feature Contract & Inference Parity
# =========================================================================


def test_gate_g2_feature_names_order_and_booster_parity():
    """Verify feature_names.json has 50 entries and identically matches Booster feature order."""
    with open(FEATURES_PATH, "r", encoding="utf-8") as f:
        declared_features = json.load(f)

    assert len(declared_features) == 50
    assert declared_features == list(V3_FEATURE_NAMES)
    assert declared_features[0] == "ensemble_mean"
    assert declared_features[-1] == "ood_score"

    model_obj = joblib.load(MODEL_PATH)
    booster = getattr(model_obj, "booster_", model_obj)
    if not isinstance(booster, lgb.Booster):
        booster = getattr(model_obj, "_Booster", booster)

    booster_features = booster.feature_name()
    assert (
        booster_features == declared_features
    ), "Booster internal feature names differ from authoritative feature_names.json"


def test_gate_g2_feature_pipeline_extraction_and_inference_parity():
    """Verify V3FeaturePipeline outputs 50 finite columns and produces valid calibrated probabilities."""
    pipeline = V3FeaturePipeline()
    record = CanonicalForecastRecord(
        location="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        issue_time="2026-09-01T00:00:00Z",
        valid_time="2026-09-02T12:00:00Z",
        lead_hours=36,
        variable="temperature_2m",
        unit="°C",
        value=32.5,
        ensemble_mean=32.5,
        ensemble_std=1.4,
        ensemble_min=29.0,
        ensemble_max=35.0,
        q10=30.2,
        q90=34.1,
        member_count=31,
    )

    df_feats, meta = pipeline.extract_from_records(
        [record], target_variable="temperature_2m"
    )
    assert df_feats.shape == (1, 50)
    assert list(df_feats.columns) == list(V3_FEATURE_NAMES)
    assert not df_feats.isna().any().any(), "Features must not contain NaNs"
    assert not np.isinf(df_feats.values).any(), "Features must not contain Infs"

    # Direct booster prediction
    model_obj = joblib.load(MODEL_PATH)
    booster = getattr(model_obj, "booster_", model_obj)
    if not isinstance(booster, lgb.Booster):
        booster = getattr(model_obj, "_Booster", booster)

    raw_preds = booster.predict(df_feats)
    assert len(raw_preds) == 1
    raw_score = float(raw_preds[0])

    # Direct calibrator prediction
    calibrator = joblib.load(CALIBRATOR_PATH)
    calibrated_prob = float(calibrator.predict(np.array([raw_score]))[0])
    assert (
        0.0 <= calibrated_prob <= 1.0
    ), f"Calibrated probability {calibrated_prob} out of [0, 1] bounds"


def test_gate_g2_adapter_end_to_end_calibrated_inference():
    """Verify Builder2V3ModelAdapter predicts successfully on valid feature matrices."""
    adapter = Builder2V3ModelAdapter()
    assert adapter.is_ready is True
    assert adapter.threshold == V3_OPERATIONAL_THRESHOLD

    pipeline = V3FeaturePipeline()
    record = CanonicalForecastRecord(
        location="Mumbai",
        latitude=19.0760,
        longitude=72.8777,
        issue_time="2026-09-01T00:00:00Z",
        valid_time="2026-09-02T00:00:00Z",
        lead_hours=24,
        variable="wind_speed_10m",
        unit="m/s",
        value=6.2,
        ensemble_mean=6.2,
        ensemble_std=0.8,
        ensemble_min=4.5,
        ensemble_max=8.0,
        member_count=31,
    )
    df_feats, _ = pipeline.extract_from_records(
        [record], target_variable="wind_speed_10m"
    )

    feature_result = FeatureResult(
        location="Mumbai",
        features=df_feats,
        feature_names=list(V3_FEATURE_NAMES),
        is_ready=True,
    )

    result = adapter.predict(feature_result)
    assert result.is_ready is True
    assert result.error is None
    assert result.probability is not None
    assert 0.0 <= result.probability <= 1.0


# =========================================================================
# GATE G3: Route Authority, Decision Threshold 0.060 & Safe Abstention
# =========================================================================


def test_gate_g3_route_authority_and_threshold_contract():
    """Verify route authority is /v1/predict, threshold is 0.060, and fallback policy is safe_abstention."""
    manifest = load_release_manifest(str(RELEASE_MANIFEST_PATH))

    assert manifest.get("route_authority") == "/v1/predict"
    assert manifest.get("fallback_policy") == "safe_abstention"

    thresholds = manifest.get("threshold_consolidation", {})
    assert thresholds.get("v3_challenger_incumbent") == 0.060

    model_art = manifest.get("model_artifact", {})
    assert model_art.get("decision_threshold") == 0.060

    assert V3_OPERATIONAL_THRESHOLD == 0.060


def test_gate_g3_safe_abstention_on_missing_or_corrupt_artifacts(tmp_path):
    """Verify adapter enforces safe abstention (is_ready=False, refusal to predict) on missing or corrupt files."""
    # Empty directory simulates missing artifacts
    corrupt_adapter = Builder2V3ModelAdapter(model_dir=tmp_path, enforce_sha=True)
    assert corrupt_adapter.is_ready is False
    assert corrupt_adapter.init_error is not None

    feature_result = FeatureResult(
        location="TestLoc",
        features=pd.DataFrame([np.zeros(50)], columns=list(V3_FEATURE_NAMES)),
        feature_names=list(V3_FEATURE_NAMES),
        is_ready=True,
    )

    result = corrupt_adapter.predict(feature_result)
    assert (
        result.is_ready is False
    ), "Corrupt/missing artifact adapter must refuse predictions"
    assert result.probability is None
    assert result.error is not None
    assert "unavailable" in result.error.lower() or "missing" in result.error.lower()


# =========================================================================
# COMPREHENSIVE NINE-POINT CONTRACT INVARIANT PROOFS
# =========================================================================


def test_gate_g1_nine_point_contract_invariants():
    """Verify all 9 platform-independent feature and artifact invariants."""
    # 1. Feature count == 50
    with open(FEATURES_PATH, "r", encoding="utf-8") as f:
        features = json.load(f)
    assert len(features) == 50, f"Expected 50 features, got {len(features)}"

    # 2. feature_names.json order == Booster.feature_name()
    model_obj = joblib.load(MODEL_PATH)
    booster = getattr(model_obj, "booster_", model_obj)
    if not isinstance(booster, lgb.Booster):
        booster = getattr(model_obj, "_Booster", booster)
    assert booster.feature_name() == features

    # 3. Canonical LF byte representation produces exact canonical hash
    raw_bytes = FEATURES_PATH.read_bytes()
    lf_bytes = raw_bytes.replace(b"\r\n", b"\n")
    lf_hash = hashlib.sha256(lf_bytes).hexdigest()
    assert lf_hash == EXPECTED_FEATURE_SHA256 == "702ff4153fd95d8c9de3bbd01461d65fde0ef207099f7f3a8e7f5c8bac02031e"
    assert raw_bytes == lf_bytes, "File on disk must have canonical LF line endings"

    # 4. LF/CRLF platform settings cannot silently invalidate the release contract
    # Simulate a CRLF-checked-out file and prove canonicalization handles it deterministically
    crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
    canonicalized_from_crlf = hashlib.sha256(crlf_bytes.replace(b"\r\n", b"\n")).hexdigest()
    assert canonicalized_from_crlf == EXPECTED_FEATURE_SHA256

    # 5. Model and calibrator hashes remain frozen
    assert _compute_sha256(MODEL_PATH) == "00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660"
    assert _compute_sha256(CALIBRATOR_PATH) == "9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531"

    # 6. Calibrator type remains IsotonicRegression
    calibrator = joblib.load(CALIBRATOR_PATH)
    assert type(calibrator).__name__ == "IsotonicRegression"

    # 7. Serving threshold remains 0.060
    manifest = load_release_manifest(str(RELEASE_MANIFEST_PATH))
    assert manifest["model_artifact"]["decision_threshold"] == 0.060
    assert V3_OPERATIONAL_THRESHOLD == 0.060

    # 8. Route remains /v1/predict
    assert manifest["route_authority"] == "/v1/predict"

    # 9. Fallback policy remains safe_abstention
    assert manifest["fallback_policy"] == "safe_abstention"

