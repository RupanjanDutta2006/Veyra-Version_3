"""Tests for Phase 6: Data Pipeline & Storage Architecture (SIH26079 §7.1-§7.4, §16).

Validates:
- C2: WeatherBench 2 benchmark adapter (latitude-weighted RMSE, ACC, CRPS, Bias)
- C3: ERA5 verification-only role invariant and anti-leakage guarantee
- C6: Zarr/chunked gridded field storage engine, checksums, and spatial slice queries
- C8: PostgreSQL/SQLAlchemy metadata store, audit trails, and truth status updates
- C9: Ingested payload SHA-256 checksum calculation and API exposure
- C10: Gray-band state handling for near-threshold data quality gates
- C11: Dataset license registry, terms of use, and license URIs
"""
import numpy as np
import pytest

from backend.app.data.license_registry import (
    DATASET_LICENSE_REGISTRY,
    DatasetRole,
    LicenseRegistry,
)
from backend.app.data.provenance_db import (
    DatasetSnapshotRecord,
    ForecastCycleRecord,
    PredictionAuditRecord,
    ProvenanceDatabase,
)
from backend.app.data.weatherbench_adapter import (
    WeatherBench2Adapter,
    WB2EvaluationResult,
)
from backend.app.data.zarr_store import ZarrGriddedStore, GriddedFieldMetadata
from backend.app.safety.abstention import SafetyAssessment, SafetyEvaluator
from backend.app.schemas.prediction import ReasonCode, TrustState
from backend.app.services.base import FeatureResult, ModelResult, WeatherResult


class TestPhase6WeatherBench2C2:
    """Test C2: WeatherBench 2 benchmark adapter and standardized metrics."""

    def test_latitude_weights_computation(self):
        adapter = WeatherBench2Adapter()
        lats = np.array([-90.0, -45.0, 0.0, 45.0, 90.0])
        weights = adapter.compute_latitude_weights(lats)

        # Equator (0 deg) should have maximum weight; poles (90 deg) should have minimum weight ~0
        assert weights[2] > weights[1] > weights[0]
        assert weights[2] > weights[3] > weights[4]
        assert np.isclose(weights[0], 0.0, atol=1e-5)
        assert np.isclose(weights[4], 0.0, atol=1e-5)

    def test_evaluate_grid_metrics(self):
        adapter = WeatherBench2Adapter(default_resolution_deg=2.5)
        f, t, lats, clim = adapter.create_synthetic_benchmark_grid(variable="temperature_2m", n_lat=19, n_lon=36)

        # Add 3 ensemble members
        ens = np.stack([f - 0.5, f, f + 0.5], axis=0)

        result = adapter.evaluate_grid(
            forecast=f,
            ground_truth=t,
            latitudes=lats,
            climatology=clim,
            variable="temperature_2m",
            lead_hours=48,
            ensemble_members=ens,
        )

        assert isinstance(result, WB2EvaluationResult)
        assert result.variable == "temperature_2m"
        assert result.lead_hours == 48
        assert result.latitude_weighted_rmse > 0.0
        assert -1.0 <= result.anomaly_correlation_coefficient <= 1.0
        assert result.crps_ensemble is not None
        assert result.crps_ensemble > 0.0
        assert result.verification_source == "ECMWF_ERA5"
        assert result.benchmark_standard == "WeatherBench-2-Protocol"


class TestPhase6LicenseAndAntiLeakageC3C11:
    """Test C3 & C11: License registry and strict ERA5 verification-only invariant."""

    def test_license_registry_contents(self):
        registry = LicenseRegistry()
        licenses = registry.list_licenses()
        assert len(licenses) >= 4

        era5 = registry.get_license("ECMWF_ERA5")
        assert era5 is not None
        assert era5.role == DatasetRole.VERIFICATION_ONLY
        assert "CC-BY 4.0" in era5.license_name
        assert era5.strict_anti_leakage_role is True

        gefs = registry.get_license("NOAA_GEFS")
        assert gefs is not None
        assert gefs.role == DatasetRole.PREDICTOR_INPUT

    def test_era5_anti_leakage_role_invariant(self):
        registry = LicenseRegistry()
        # ERA5 cannot be used as a predictor input
        assert registry.verify_role_invariant("ECMWF_ERA5", "PREDICTOR") is False
        # ERA5 can be used for verification
        assert registry.verify_role_invariant("ECMWF_ERA5", "VERIFICATION") is True


class TestPhase6ZarrStoreC6:
    """Test C6: Zarr / chunked gridded field storage engine."""

    def test_write_and_read_field(self, tmp_path):
        store = ZarrGriddedStore(root_dir=tmp_path / "zarr")
        lats = np.linspace(8.0, 37.0, 30)
        lons = np.linspace(68.0, 97.0, 30)
        data = np.random.randn(30, 30).astype(np.float32)

        meta = store.write_field(
            field_id="gefs_20260919_t2m_48h",
            data=data,
            variable="temperature_2m",
            units="K",
            cycle_id="GEFS_20260919_00Z",
            latitudes=lats,
            longitudes=lons,
        )

        assert meta.field_id == "gefs_20260919_t2m_48h"
        assert len(meta.sha256_checksum) == 64
        assert meta.shape == (30, 30)

        # Read back
        read_arr, read_meta = store.read_field("gefs_20260919_t2m_48h")
        assert np.allclose(data, read_arr)
        assert read_meta.sha256_checksum == meta.sha256_checksum

    def test_spatial_slice_query(self, tmp_path):
        store = ZarrGriddedStore(root_dir=tmp_path / "zarr")
        lats = np.linspace(10.0, 35.0, 26)
        lons = np.linspace(70.0, 95.0, 26)
        data = np.arange(26 * 26, dtype=np.float32).reshape(26, 26)

        store.write_field(
            field_id="india_t2m_test",
            data=data,
            variable="temperature_2m",
            units="K",
            cycle_id="TEST_CYCLE",
            latitudes=lats,
            longitudes=lons,
        )

        # Slice Northern India (25-32 N, 75-85 E)
        sub_grid = store.get_spatial_slice(
            field_id="india_t2m_test",
            min_lat=25.0,
            max_lat=32.0,
            min_lon=75.0,
            max_lon=85.0,
            latitudes=lats,
            longitudes=lons,
        )
        assert sub_grid.ndim == 2
        assert sub_grid.shape[0] > 0
        assert sub_grid.shape[1] > 0


class TestPhase6ProvenanceDatabaseC8:
    """Test C8: PostgreSQL/SQLAlchemy metadata and audit database."""

    def test_db_tables_and_crud(self):
        # In-memory SQLite for deterministic test isolation
        db = ProvenanceDatabase(db_url="sqlite:///:memory:")

        # 1. Record forecast cycle
        cycle = db.record_forecast_cycle(
            cycle_id="GEFS_20260919_12Z",
            model_provider="NOAA_GEFS",
            max_lead_hours=384,
            member_count=31,
            sha256_checksum="abc123sha256fakechecksum4567890abcdef1234567890abcdef1234567890abcdef",
        )
        assert cycle.cycle_id == "GEFS_20260919_12Z"
        assert cycle.member_count == 31

        # 2. Record prediction audit
        pred = db.record_prediction_audit(
            prediction_id="pred_test123",
            location="Delhi",
            bust_probability=0.72,
            color_band="ORANGE",
            variable="temperature_2m",
            lead_hours=48,
            risk_level="HIGH",
            ood_score=0.25,
            claim_scope="PUBLIC_PROXY_PROTOTYPE",
            truth_status="PENDING",
            reason_codes=["REVISION_ACCELERATION"],
        )
        assert pred.prediction_id == "pred_test123"
        assert pred.truth_status == "PENDING"

        # 3. Update truth status upon verification
        updated = db.update_truth_status("pred_test123", "BUST")
        assert updated is not None
        assert updated.truth_status == "VERIFIED"
        assert updated.verified_outcome == "BUST"

        # 4. Record dataset snapshot
        snap = db.record_dataset_snapshot(
            snapshot_id="snap_era5_202609",
            dataset_name="ECMWF ERA5",
            version="v1.0",
            storage_uri="s3://veyra-data/era5/202609.zarr",
            sha256_checksum="fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
            license_uri="https://creativecommons.org/licenses/by/4.0/",
            role="VERIFICATION_ONLY",
        )
        assert snap.snapshot_id == "snap_era5_202609"
        assert snap.role == "VERIFICATION_ONLY"


class TestPhase6GrayBandDataQualityC10:
    """Test C10: Gray-band state handling for near-threshold data quality issues."""

    def test_near_threshold_data_quality_triggers_gray_band(self):
        evaluator = SafetyEvaluator()

        # Weather result with near_threshold_qc flag
        weather_res = WeatherResult(
            location="Delhi",
            is_available=True,
            quality_flags={"qc_passed": True, "near_threshold_qc": True},
        )

        assessment = evaluator.evaluate(weather_result=weather_res)
        assert assessment.abstain is True
        assert assessment.trust_state == TrustState.UNAVAILABLE
        assert assessment.is_gray_band is True
        assert assessment.metadata.get("color_band") == "GRAY"
        assert "NEAR_THRESHOLD_DATA_QUALITY" in assessment.reason_codes
