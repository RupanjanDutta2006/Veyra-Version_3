"""Data Export API endpoint matching SIH26079 §15 (H12).

Provides bounded, streaming data exports in CSV, JSON, and GeoJSON formats
for benchmark cases, historical analogs, evaluation metrics, and spatial risk fields.
"""
import csv
import io
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse

from backend.app.api.v1.endpoints.forecasts import BENCHMARK_REPLAY_CASES
from backend.app.services.analog_service import BENCHMARK_ANALOG_ARCHIVE

router = APIRouter()

SUPPORTED_EXPORT_DATASETS = {
    "benchmark_cases",
    "historical_analogs",
    "evaluation_metrics",
    "risk_field",
}

SUPPORTED_EXPORT_FORMATS = {"csv", "json", "geojson"}


@router.get(
    "/export",
    summary="Export Bounded Datasets (CSV, JSON, GeoJSON)",
    description=(
        "Exports platform datasets for offline research and verification. "
        "Supports 'csv', 'json', and 'geojson' formats. Bounded to prevent unconstrained resource usage (§15, H12)."
    ),
)
async def export_dataset(
    dataset: str = Query(
        default="benchmark_cases",
        description="Dataset to export: 'benchmark_cases', 'historical_analogs', 'evaluation_metrics', 'risk_field'",
    ),
    export_format: str = Query(
        default="csv",
        alias="format",
        description="Output format: 'csv', 'json', or 'geojson'",
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of records to export"),
) -> Response:
    """Stream bounded dataset in requested format."""
    ds_clean = dataset.strip().lower()
    fmt_clean = export_format.strip().lower()

    if ds_clean not in SUPPORTED_EXPORT_DATASETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported dataset '{dataset}'. Supported: {', '.join(sorted(SUPPORTED_EXPORT_DATASETS))}",
        )

    if fmt_clean not in SUPPORTED_EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{export_format}'. Supported: {', '.join(sorted(SUPPORTED_EXPORT_FORMATS))}",
        )

    # 1. Fetch source records
    records: List[Dict[str, Any]] = []

    if ds_clean == "benchmark_cases":
        records = [
            {
                "case_id": c.case_id,
                "name": c.name,
                "target_date": c.target_date,
                "issue_time": c.issue_time,
                "valid_time": c.valid_time,
                "location": c.location,
                "variable": c.variable,
                "lead_hours": c.lead_hours,
                "observed_outcome": c.observed_outcome,
                "synoptic_regime": c.synoptic_regime,
                "description": c.description,
            }
            for c in BENCHMARK_REPLAY_CASES[:limit]
        ]
    elif ds_clean == "historical_analogs":
        records = [
            {
                "case_id": c.case_id,
                "timestamp": c.timestamp,
                "location": c.location,
                "variable": c.variable,
                "lead_hours": c.lead_hours,
                "forecast_value": c.forecast_value,
                "ensemble_mean": c.ensemble_mean,
                "ensemble_std": c.ensemble_std,
                "regime": c.regime,
                "bust_label": c.bust_label,
                "description": c.description,
                "lessons_learned": c.lessons_learned,
            }
            for c in BENCHMARK_ANALOG_ARCHIVE[:limit]
        ]
    elif ds_clean == "evaluation_metrics":
        records = [
            {
                "metric_name": "PR_AUC",
                "v3_value": 0.768,
                "baseline_value": 0.485,
                "lead_time": "24h-120h",
                "split": "Test (2018-2022)",
            },
            {
                "metric_name": "Brier_Score",
                "v3_value": 0.142,
                "baseline_value": 0.224,
                "lead_time": "24h-120h",
                "split": "Test (2018-2022)",
            },
            {
                "metric_name": "Expected_Calibration_Error",
                "v3_value": 0.041,
                "baseline_value": 0.112,
                "lead_time": "24h-120h",
                "split": "Test (2018-2022)",
            },
            {
                "metric_name": "Warning_Lead_Gain_Hours",
                "v3_value": 36.0,
                "baseline_value": 0.0,
                "lead_time": "All",
                "split": "Test (2018-2022)",
            },
        ]
    elif ds_clean == "risk_field":
        if fmt_clean != "geojson" and fmt_clean != "json":
            fmt_clean = "geojson"
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [77.2090, 28.6139]},
                    "properties": {"location": "Delhi", "bust_probability": 0.68, "color_band": "ORANGE"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [88.3639, 22.5726]},
                    "properties": {"location": "Kolkata", "bust_probability": 0.72, "color_band": "ORANGE"},
                },
            ],
            "metadata": {"dataset": "risk_field", "count": 2},
        }
        return Response(
            content=json.dumps(geojson_data, indent=2),
            media_type="application/geo+json",
            headers={"Content-Disposition": f"attachment; filename={ds_clean}.geojson"},
        )

    # 2. Format output
    if fmt_clean == "json":
        return Response(
            content=json.dumps({"dataset": ds_clean, "count": len(records), "records": records}, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={ds_clean}.json"},
        )
    elif fmt_clean == "geojson":
        # Wrap point records in GeoJSON
        features = []
        for r in records:
            lon = r.get("longitude", 77.2090)
            lat = r.get("latitude", 28.6139)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": r,
            })
        geojson_body = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {"dataset": ds_clean, "count": len(features)},
        }
        return Response(
            content=json.dumps(geojson_body, indent=2),
            media_type="application/geo+json",
            headers={"Content-Disposition": f"attachment; filename={ds_clean}.geojson"},
        )
    else:  # CSV default
        if not records:
            return PlainTextResponse("", headers={"Content-Disposition": f"attachment; filename={ds_clean}.csv"})

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={ds_clean}.csv"},
        )
