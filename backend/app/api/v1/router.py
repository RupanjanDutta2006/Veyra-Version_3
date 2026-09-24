"""V1 API Router combining all v1 endpoints."""
from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    analogs,
    dashboard,
    evaluation,
    export,
    forecasts,
    health,
    metadata,
    metrics,
    models,
    multi_location,
    predict,
    provenance,
    risk_map,
    explanation,
    hazard,
    review,
    certification,
    ood,
    revision,
    spatial,
    disagreement,
    provider_disagreement,
)

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    metrics.router,
    tags=["Observability"],
)

api_router.include_router(
    predict.router,
    tags=["Prediction"],
)

api_router.include_router(
    multi_location.router,
    tags=["Multi-Location"],
)

api_router.include_router(
    evaluation.router,
    tags=["Model Evaluation"],
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard Intelligence"],
)

# Phase 5 Endpoints (§15, §15.2)
api_router.include_router(
    models.router,
    tags=["Model Registry"],
)

api_router.include_router(
    forecasts.router,
    tags=["Forecast Cycles & Replay"],
)

api_router.include_router(
    risk_map.router,
    tags=["Risk Mapping"],
)

api_router.include_router(
    analogs.router,
    tags=["Historical Analogs"],
)

api_router.include_router(
    explanation.router,
    tags=["Physical Attribution"],
)

api_router.include_router(
    metadata.router,
    tags=["System Metadata"],
)

api_router.include_router(
    provenance.router,
    tags=["Data Provenance"],
)

api_router.include_router(
    export.router,
    tags=["Data Export"],
)

api_router.include_router(
    review.router,
    tags=["Human-in-the-Loop Review"],
)

api_router.include_router(
    hazard.router,
    tags=["Hazard Dynamics & Motifs"],
)

api_router.include_router(
    certification.router,
    tags=["Scientific Certification"],
)

api_router.include_router(
    ood.router,
    tags=["OOD Diagnostic Policy"],
)

api_router.include_router(
    revision.router,
    prefix="/revision",
    tags=["Forecast Revision Intelligence"],
)

api_router.include_router(
    spatial.router,
    prefix="/spatial",
    tags=["Spatial Forecast Reliability"],
)

api_router.include_router(
    disagreement.router,
    prefix="/disagreement",
    tags=["Forecast Disagreement & Ensemble Dispersion"],
)

api_router.include_router(
    provider_disagreement.router,
    prefix="/disagreement",
    tags=["Cross-Provider Disagreement"],
)

