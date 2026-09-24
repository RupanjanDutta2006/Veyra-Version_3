"""Tests for Phase 5: Full API Contract (12 Specified Endpoints) per SIH26079 §15.

Validates:
- H2: GET /v1/models (listing, model cards, checksums, lifecycle status)
- H3: GET /v1/forecasts (operational cycles, replay benchmark cases)
- H5: GET /v1/risk-map (GeoJSON FeatureCollection, coordinates, properties)
- H7: GET /v1/analogs (historical analog search, event exclusion, graceful no-analog)
- H8: GET /v1/explanation (reason codes, physical attribution, SHAP factors)
- H9: GET /v1/metrics (operational counters + scientific evaluation metrics)
- H10: GET /v1/metadata (system, data sources, license URIs, operational scope)
- H11: GET /v1/data-provenance (checksums, transformation pipeline, anti-leakage policy)
- H12: GET /v1/export (CSV, JSON, GeoJSON exports, bounds, MIME types)
- H13: Full error code vocabulary and envelope
- A7: Region-based units (India core zones, admin boundaries, grid-patches)
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.error_codes import VeyraErrorCode, ErrorDetail, ErrorResponseEnvelope
from backend.app.services.region_service import RegionService, INDIA_REGIONS


@pytest.fixture
def client():
    return TestClient(app)


class TestPhase5ModelsH2:
    """Test H2: GET /v1/models endpoint."""

    def test_list_models(self, client):
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3

        model_ids = [m["model_id"] for m in data]
        assert "builder2_v3" in model_ids
        assert "prototype-gbm-v1" in model_ids
        assert "baseline-logistic-v1.0" in model_ids

        v3 = next(m for m in data if m["model_id"] == "builder2_v3")
        assert v3["status"] == "SERVING"
        assert v3["is_active"] is True
        assert v3["feature_count"] == 50
        assert "d8664fd3736ddc1fc438bf22818aa40adcb371c695c02b37016b8b9cb07aa99b" in v3["artifacts"]["model_sha256"]
        assert v3["metrics"]["pr_auc"] > 0.70

    def test_get_specific_model(self, client):
        resp = client.get("/v1/models/builder2_v3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_id"] == "builder2_v3"
        assert data["architecture"].startswith("LightGBM")

    def test_get_unknown_model_returns_404(self, client):
        resp = client.get("/v1/models/nonexistent_model")
        assert resp.status_code == 404


class TestPhase5ForecastsH3:
    """Test H3: GET /v1/forecasts endpoint."""

    def test_list_forecasts(self, client):
        resp = client.get("/v1/forecasts")
        assert resp.status_code == 200
        data = resp.json()
        assert "cycles" in data
        assert "replay_cases" in data
        assert len(data["cycles"]) > 0
        assert len(data["replay_cases"]) >= 4

        # Verify replay case contents
        replay_ids = [r["case_id"] for r in data["replay_cases"]]
        assert "HW-2015-DELHI" in replay_ids
        assert "CY-2020-AMPHAN" in replay_ids


class TestPhase5RiskMapH5:
    """Test H5: GET /v1/risk-map endpoint."""

    def test_get_risk_map_geojson(self, client):
        resp = client.get("/v1/risk-map?variable=temperature_2m&lead_hours=48")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) > 0

        first_f = data["features"][0]
        assert first_f["type"] == "Feature"
        assert "geometry" in first_f
        assert first_f["geometry"]["type"] == "Point"
        assert "properties" in first_f
        assert "bust_probability" in first_f["properties"]
        assert "color_band" in first_f["properties"]
        assert "area_fraction" in first_f["properties"]

    def test_get_risk_map_with_region_filter(self, client):
        resp = client.get("/v1/risk-map?region_id=IN_NORTH")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["features"]) > 0


class TestPhase5AnalogsH7:
    """Test H7: GET /v1/analogs endpoint."""

    def test_search_analogs(self, client):
        resp = client.get("/v1/analogs?location=Delhi&variable=temperature_2m&lead_hours=48&forecast_value=42.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "analog_cards" in data
        assert data["claim_scope"] == "PUBLIC_PROXY_PROTOTYPE"

    def test_search_analogs_no_match_returns_gracefully(self, client):
        # Far past timestamp before any archive case
        resp = client.get("/v1/analogs?query_time=2000-01-01T00:00:00Z")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_ELIGIBLE_ANALOG"
        assert len(data["analog_cards"]) == 0


class TestPhase5ExplanationH8:
    """Test H8: GET /v1/explanation endpoint."""

    def test_get_explanation(self, client):
        resp = client.get("/v1/explanation?location=Delhi&variable=temperature_2m&lead_hours=48&bust_probability=0.72")
        assert resp.status_code == 200
        data = resp.json()
        assert "primary_driver" in data
        assert "top_contributing_factors" in data
        assert len(data["top_contributing_factors"]) > 0
        assert "auditable_reason_codes" in data
        assert "analog_evidence" in data
        assert data["decision_mode"] == "HEIGHTENED_ALERT"
        assert data["claim_scope"] == "PUBLIC_PROXY_PROTOTYPE"


class TestPhase5MetricsH9:
    """Test H9: GET /v1/metrics endpoint."""

    def test_metrics_default_returns_both_ops_and_eval(self, client):
        resp = client.get("/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        # Operations snapshot
        assert "predictions_total" in data
        # Evaluation snapshot
        assert "evaluation" in data
        eval_meta = data["evaluation"]
        assert eval_meta["metrics"]["pr_auc"] == 0.768
        assert "pr_auc_95ci" in eval_meta["metrics"]
        assert "reliability_diagram" in eval_meta

    def test_metrics_evaluation_view(self, client):
        resp = client.get("/v1/metrics?view=evaluation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_id"] == "builder2_v3"
        assert data["metrics"]["brier_score"] == 0.142


class TestPhase5MetadataH10:
    """Test H10: GET /v1/metadata endpoint."""

    def test_get_metadata(self, client):
        resp = client.get("/v1/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert "system_name" in data
        assert "active_model_id" in data
        assert data["active_model_id"] == "builder2_v3"
        assert len(data["data_sources"]) >= 3

        era5 = next(d for d in data["data_sources"] if "ERA5" in d["name"])
        assert era5["role"] == "VERIFICATION_ONLY"
        assert "CC-BY 4.0" in era5["license_name"]


class TestPhase5DataProvenanceH11:
    """Test H11: GET /v1/data-provenance endpoint."""

    def test_get_data_provenance(self, client):
        resp = client.get("/v1/data-provenance")
        assert resp.status_code == 200
        data = resp.json()
        assert "anti_leakage_policy" in data
        assert "STRICTLY used for post-event verification" in data["anti_leakage_policy"]
        assert "checksums" in data
        assert len(data["checksums"]) >= 3
        assert "transformation_pipeline" in data
        assert len(data["transformation_pipeline"]) >= 5


class TestPhase5ExportH12:
    """Test H12: GET /v1/export endpoint."""

    def test_export_csv(self, client):
        resp = client.get("/v1/export?dataset=benchmark_cases&format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment; filename=benchmark_cases.csv" in resp.headers["content-disposition"]
        assert "case_id" in resp.text

    def test_export_json(self, client):
        resp = client.get("/v1/export?dataset=historical_analogs&format=json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        data = resp.json()
        assert data["dataset"] == "historical_analogs"
        assert len(data["records"]) > 0

    def test_export_geojson(self, client):
        resp = client.get("/v1/export?dataset=risk_field&format=geojson")
        assert resp.status_code == 200
        assert "application/geo+json" in resp.headers["content-type"]
        data = resp.json()
        assert data["type"] == "FeatureCollection"

    def test_export_invalid_dataset_raises_400(self, client):
        resp = client.get("/v1/export?dataset=invalid_ds")
        assert resp.status_code == 400


class TestPhase5ErrorCodesH13:
    """Test H13: Error codes and ErrorResponseEnvelope."""

    def test_error_code_enumeration(self):
        assert VeyraErrorCode.DATA_DELAYED == "DATA_DELAYED"
        assert VeyraErrorCode.OOD_ABSTAIN == "OOD_ABSTAIN"
        assert VeyraErrorCode.NO_ELIGIBLE_ANALOG == "NO_ELIGIBLE_ANALOG"
        assert VeyraErrorCode.MAP_NOT_READY == "MAP_NOT_READY"

    def test_error_envelope_serialization(self):
        envelope = ErrorResponseEnvelope(
            error=ErrorDetail(
                error_code=VeyraErrorCode.OOD_ABSTAIN,
                message="Atmospheric state exceeds operational envelope",
                details={"ood_score": 0.88},
                resolution_guidance="Revert to human forecaster evaluation.",
            ),
            status_code=422,
        )
        data = envelope.model_dump()
        assert data["error"]["error_code"] == "OOD_ABSTAIN"
        assert data["status_code"] == 422
        assert data["request_id"].startswith("err_")


class TestPhase5RegionServiceA7:
    """Test A7: Region-based units (India core zones, admin, grid patches)."""

    def test_region_listing_and_queries(self):
        service = RegionService()
        regions = service.list_regions()
        assert len(regions) >= 7

        north = service.get_region("IN_NORTH")
        assert north is not None
        assert north.region_type == "METEOROLOGICAL_ZONE"
        assert "Delhi" in north.representative_stations

    def test_coordinate_resolution(self):
        service = RegionService()
        # Delhi coords
        reg = service.find_region_by_coordinates(28.6139, 77.2090)
        assert reg is not None
        assert reg.region_id in ("DELHI_NCR", "IN_NORTH")

    def test_grid_patch_tiling(self):
        service = RegionService()
        patches = service.generate_grid_patches("DELHI_NCR", resolution_deg=0.25)
        assert len(patches) > 0
        p0 = patches[0]
        assert p0.patch_id.startswith("DELHI_NCR_")
        assert p0.area_sq_km > 0
