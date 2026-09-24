"""Open-Meteo GEFS Provider Adapter for Veyra Phase 3 Day 37 (Gate C7).

Wraps the production OpenMeteoGEFSWeatherService behind the standardized BaseProviderAdapter interface,
preserving 100% backward compatibility, live 31-member GEFS ensemble ingestion, quality control,
and short-lived in-memory caching.
"""
import logging
from typing import Optional

from backend.app.adapters.provider_adapter import (
    BaseProviderAdapter,
    NormalizedProviderForecast,
    ProviderResponseStatus,
    ProviderSourceMode,
    normalize_unit_value,
)
from backend.app.services.openmeteo_service import OpenMeteoGEFSWeatherService

logger = logging.getLogger(__name__)


class OpenMeteoProviderAdapter(BaseProviderAdapter):
    """Adapter wrapping the primary production Open-Meteo GEFS weather service."""

    def __init__(self, service: Optional[OpenMeteoGEFSWeatherService] = None):
        self._service = service or OpenMeteoGEFSWeatherService()

    @property
    def provider_id(self) -> str:
        return "openmeteo_gefs"

    @property
    def provider_name(self) -> str:
        return "Open-Meteo GEFS Ensemble"

    @property
    def provider_source_mode(self) -> ProviderSourceMode:
        return ProviderSourceMode.LIVE

    def fetch_forecast(
        self,
        location: str,
        variable: str,
        lead_hours: int = 24,
        issue_time: Optional[str] = None,
        valid_time: Optional[str] = None,
    ) -> NormalizedProviderForecast:
        """Fetch forecast from Open-Meteo GEFS and convert into NormalizedProviderForecast."""
        try:
            res = self._service.get_forecast(location=location)

            if not res or not res.is_available or not res.raw_data:
                return NormalizedProviderForecast(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    provider_source_mode=self.provider_source_mode,
                    canonical_location=location,
                    latitude=0.0,
                    longitude=0.0,
                    issue_time=issue_time or "",
                    valid_time=valid_time or "",
                    lead_hours=lead_hours,
                    variable=variable,
                    forecast_value=None,
                    unit="",
                    is_available=False,
                    status=ProviderResponseStatus.UNAVAILABLE,
                    error_detail=res.error if res else "Open-Meteo returned empty result",
                )

            records = res.raw_data.get("records", [])
            matching_var = [r for r in records if r.get("variable") == variable]
            if not matching_var:
                matching_var = records

            target_rec = None
            if valid_time:
                for r in matching_var:
                    if r.get("valid_time") == valid_time:
                        target_rec = r
                        break
            if target_rec is None and matching_var:
                target_rec = min(matching_var, key=lambda r: abs(r.get("lead_hours", 0) - lead_hours))

            if not target_rec:
                return NormalizedProviderForecast(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    provider_source_mode=self.provider_source_mode,
                    canonical_location=location,
                    latitude=res.raw_data.get("latitude", 0.0),
                    longitude=res.raw_data.get("longitude", 0.0),
                    issue_time=res.raw_data.get("issue_time", issue_time or ""),
                    valid_time=valid_time or "",
                    lead_hours=lead_hours,
                    variable=variable,
                    forecast_value=None,
                    unit="",
                    is_available=False,
                    status=ProviderResponseStatus.UNAVAILABLE,
                    error_detail=f"No record found for variable '{variable}'",
                )

            val = target_rec.get("value")
            norm_val, norm_unit = normalize_unit_value(
                value=val,
                source_unit=target_rec.get("unit", ""),
                target_variable=variable,
            )

            return NormalizedProviderForecast(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                provider_source_mode=self.provider_source_mode,
                canonical_location=target_rec.get("location", location),
                latitude=target_rec.get("latitude", 0.0),
                longitude=target_rec.get("longitude", 0.0),
                issue_time=target_rec.get("issue_time", ""),
                valid_time=target_rec.get("valid_time", ""),
                lead_hours=target_rec.get("lead_hours", lead_hours),
                variable=target_rec.get("variable", variable),
                forecast_value=round(norm_val, 4) if norm_val is not None else None,
                unit=norm_unit,
                ensemble_mean=target_rec.get("ensemble_mean"),
                ensemble_std=target_rec.get("ensemble_std"),
                member_values=target_rec.get("member_values"),
                is_available=True,
                status=ProviderResponseStatus.SUCCESS,
                metadata={
                    "data_version": res.data_version,
                    "quality_flags": res.quality_flags,
                },
            )

        except Exception as exc:
            logger.warning("OpenMeteoProviderAdapter fetch error: %s", exc)
            return NormalizedProviderForecast(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                provider_source_mode=self.provider_source_mode,
                canonical_location=location,
                latitude=0.0,
                longitude=0.0,
                issue_time=issue_time or "",
                valid_time=valid_time or "",
                lead_hours=lead_hours,
                variable=variable,
                forecast_value=None,
                unit="",
                is_available=False,
                status=ProviderResponseStatus.UNAVAILABLE,
                error_detail=f"OpenMeteo fetch exception: {str(exc)}",
            )
