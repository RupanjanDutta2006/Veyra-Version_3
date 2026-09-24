"""System, Model, Data and Licensing Metadata API endpoint matching SIH26079 §15, §16 (H10).

Exposes system architecture, active model provenance, data sources, license URIs,
operational scope boundaries, and verification invariants.
"""
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class DataSourceMetadata(BaseModel):
    name: str
    role: str  # "PREDICTOR_INPUT" or "VERIFICATION_ONLY"
    provider: str
    update_frequency: str
    license_name: str
    license_uri: str
    terms_summary: str


class OperationalScopeMetadata(BaseModel):
    claim_scope: str = "PUBLIC_PROXY_PROTOTYPE"
    certified_domain: str
    bounding_box: Dict[str, float]
    certified_variables: List[str]
    certified_lead_horizons_hours: List[int]
    experimental_lead_horizons_hours: List[int]
    unsupported_regions_warning: str


class VeyraMetadataResponse(BaseModel):
    system_name: str
    system_version: str
    build_date: str
    governing_spec: str
    claim_scope: str
    active_model_id: str
    active_model_version: str
    active_features_count: int
    data_sources: List[DataSourceMetadata]
    operational_scope: OperationalScopeMetadata
    reproducibility_manifest_uri: str


@router.get(
    "/metadata",
    response_model=VeyraMetadataResponse,
    summary="Get System, Model & Dataset Metadata",
    description="Returns comprehensive system, model, data provenance, license, and claim scope metadata (§15, §16, H10).",
)
async def get_metadata() -> VeyraMetadataResponse:
    """Retrieve full platform metadata and governance specifications."""
    return VeyraMetadataResponse(
        system_name="Veyra: Know When Forecasts May Fail",
        system_version="v2.0-championship",
        build_date="2026-09-19",
        governing_spec="SIH26079 Master Specification v2.0",
        claim_scope="PUBLIC_PROXY_PROTOTYPE",
        active_model_id="builder2_v3",
        active_model_version="v3.0.0",
        active_features_count=50,
        data_sources=[
            DataSourceMetadata(
                name="NOAA GEFS (Global Ensemble Forecast System)",
                role="PREDICTOR_INPUT",
                provider="National Oceanic and Atmospheric Administration (NOAA)",
                update_frequency="4 cycles/day (00Z, 06Z, 12Z, 18Z)",
                license_name="U.S. Public Domain",
                license_uri="https://www.weather.gov/disclaimer",
                terms_summary="Open public meteorological data for global forecast evaluation.",
            ),
            DataSourceMetadata(
                name="ECMWF ERA5 Reanalysis",
                role="VERIFICATION_ONLY",
                provider="European Centre for Medium-Range Weather Forecasts (ECMWF)",
                update_frequency="Monthly / Delayed 5 days",
                license_name="Creative Commons Attribution 4.0 International (CC-BY 4.0)",
                license_uri="https://creativecommons.org/licenses/by/4.0/",
                terms_summary="Strictly restricted to post-event ground truth verification and bust labeling. NEVER used as a predictor feature.",
            ),
            DataSourceMetadata(
                name="Open-Meteo Weather API",
                role="PREDICTOR_INPUT",
                provider="Open-Meteo GmbH",
                update_frequency="Hourly real-time proxy",
                license_name="Open Database License (ODbL) / CC-BY 4.0",
                license_uri="https://open-meteo.com/en/terms",
                terms_summary="Provides standardized GEFS ensemble member ingestion endpoints.",
            ),
        ],
        operational_scope=OperationalScopeMetadata(
            claim_scope="PUBLIC_PROXY_PROTOTYPE",
            certified_domain="Indian Subcontinent and Maritime Littoral Zones",
            bounding_box={
                "min_latitude": 6.0,
                "max_latitude": 38.0,
                "min_longitude": 68.0,
                "max_longitude": 98.0,
            },
            certified_variables=[
                "temperature_2m",
                "surface_pressure",
                "wind_speed_10m",
                "relative_humidity_2m",
                "precipitation",
                "geopotential_height_500hPa",
            ],
            certified_lead_horizons_hours=[24, 48, 72, 96, 120, 144, 168, 192, 216, 240],
            experimental_lead_horizons_hours=[264, 288, 312, 336, 360, 384],
            unsupported_regions_warning=(
                "Coordinates outside the Indian domain (e.g. oceanic poles, North America, Europe) "
                "are out-of-distribution (OOD) and will trigger safe model abstention."
            ),
        ),
        reproducibility_manifest_uri="/v1/data-provenance",
    )
