"""Real Weather Ingestion Service using Open-Meteo GEFS / GFS public ensemble API."""
import copy
import gzip
import hashlib
import json
import logging
import time
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from typing import Any, Callable, Optional
import numpy as np
from backend.app.core.cache import (
    BoundedTTLCache,
    SingleFlight,
    forecast_cache,
    forecast_deduplicator,
)
from backend.app.core.config import settings
from backend.app.core.http_retry import execute_with_retry
from backend.app.core.metrics import default_metrics
from backend.app.data.qc import ForecastQualityControl, QualityControlResult
from backend.app.schemas.location import ResolvedLocation
from backend.app.schemas.prediction import ReasonCode
from backend.app.schemas.weather import (
    CanonicalForecastDataset,
    CanonicalForecastRecord,
)
from backend.app.services.base import BaseWeatherService, WeatherResult
from backend.app.services.location_service import (
    BaseLocationService,
    DynamicLocationService,
    KNOWN_BENCHMARK_LOCATIONS,
)

logger = logging.getLogger(__name__)

# Backward-compatible alias for legacy references
KNOWN_LOCATIONS: dict[str, tuple[float, float]] = {
    k: (v["latitude"], v["longitude"]) for k, v in KNOWN_BENCHMARK_LOCATIONS.items()
}

DEFAULT_ENSEMBLE_API_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"


class OpenMeteoGEFSWeatherService(BaseWeatherService):
    """Production-grade weather ingestion service querying public GFS/GEFS ensemble data.

    Implements BaseWeatherService. Strictly converts raw vendor responses
    into CanonicalForecastRecord structures and runs rigorous Quality Control.
    Features bounded short-lived in-memory caching and concurrent in-flight request deduplication.
    """

    def __init__(
        self,
        api_url: str = DEFAULT_ENSEMBLE_API_URL,
        qc_validator: Optional[ForecastQualityControl] = None,
        http_client: Optional[Callable[[str], dict[str, Any]]] = None,
        data_version: str = "gefs-openmeteo-v1.0",
        timeout_seconds: Optional[int] = None,
        location_service: Optional[BaseLocationService] = None,
        max_retries: Optional[int] = None,
        retry_backoff_factor: Optional[float] = None,
        cache: Optional[BoundedTTLCache] = None,
        enable_cache: Optional[bool] = None,
        cache_ttl: Optional[int] = None,
        deduplicator: Optional[SingleFlight] = None,
        enable_dedup: Optional[bool] = None,
    ):
        self.api_url = api_url
        self.qc = qc_validator or ForecastQualityControl()
        self.http_client = http_client
        self.data_version = data_version
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.WEATHER_TIMEOUT_SECONDS
        )
        self.location_service = location_service or DynamicLocationService()
        self.max_retries = (
            max_retries
            if max_retries is not None
            else settings.MAX_HTTP_RETRIES
        )
        self.retry_backoff_factor = (
            retry_backoff_factor
            if retry_backoff_factor is not None
            else settings.RETRY_BACKOFF_FACTOR
        )
        self.enable_cache = (
            enable_cache
            if enable_cache is not None
            else settings.WEATHER_CACHE_ENABLED
        )
        self.cache_ttl = (
            cache_ttl
            if cache_ttl is not None
            else settings.WEATHER_CACHE_TTL_SECONDS
        )
        self.cache = cache if cache is not None else forecast_cache
        self.enable_dedup = (
            enable_dedup
            if enable_dedup is not None
            else settings.WEATHER_DEDUP_ENABLED
        )
        self.deduplicator = deduplicator if deduplicator is not None else forecast_deduplicator


    def _default_http_client(self, url: str) -> dict[str, Any]:
        """Perform HTTP GET request using standard library urllib with bounded retry, backoff, and gzip decompression."""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Veyra-Forecast-Bust-Sentinel/0.1.0",
                "Accept-Encoding": "gzip, deflate",
            },
        )

        def _do_fetch() -> dict[str, Any]:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP error {response.status} fetching forecast data")
                raw_bytes = response.read()
                encoding = response.headers.get("Content-Encoding", "").lower()
                if "gzip" in encoding:
                    payload = gzip.decompress(raw_bytes).decode("utf-8")
                elif "deflate" in encoding:
                    payload = zlib.decompress(raw_bytes).decode("utf-8")
                else:
                    payload = raw_bytes.decode("utf-8")
                return json.loads(payload)

        return execute_with_retry(
            _do_fetch,
            max_retries=self.max_retries,
            backoff_factor=self.retry_backoff_factor,
            operation_name="OpenMeteo GEFS weather fetch",
        )

    def resolve_location(self, location: str) -> Optional[ResolvedLocation]:
        """Resolve location name or coordinate string to a structured ResolvedLocation object."""
        return self.location_service.resolve(location)

    def resolve_coordinates(self, location: str) -> Optional[tuple[float, float]]:
        """Resolve location name or coordinate string to (latitude, longitude)."""
        return self.location_service.resolve_coordinates(location)

    def build_query_url(
        self,
        latitude: float,
        longitude: float,
        target_date: Optional[str] = None,
        forecast_days: int = 16,
    ) -> str:
        """Construct the Open-Meteo GEFS ensemble query URL with normalized parameters.

        Lat/lon are rounded to 4 decimal places (~11m precision) to maximize
        cache hit rates when the same location is queried with slightly different precision.
        """
        # Normalize coordinates for consistent cache keys
        norm_lat = round(latitude, 4)
        norm_lon = round(longitude, 4)

        params: dict[str, str] = {
            "latitude": str(norm_lat),
            "longitude": str(norm_lon),
            "hourly": "temperature_2m,surface_pressure,wind_speed_10m,relative_humidity_2m,precipitation,geopotential_height_500hPa",
            "models": "gfs_seamless",
            "timezone": "UTC",
            "wind_speed_unit": "ms",
        }
        if target_date:
            params["start_date"] = target_date
            params["end_date"] = target_date
        else:
            params["forecast_days"] = str(forecast_days)

        # Sort parameters for deterministic URL (maximizes cache hit rate)
        sorted_params = sorted(params.items())
        return f"{self.api_url}?{urllib.parse.urlencode(sorted_params)}"

    def parse_canonical_records(
        self,
        raw_response: dict[str, Any],
        location: str,
        latitude: float,
        longitude: float,
    ) -> list[CanonicalForecastRecord]:
        """Parse vendor JSON payload into standardized CanonicalForecastRecords."""
        records: list[CanonicalForecastRecord] = []
        hourly = raw_response.get("hourly", {})
        hourly_units = raw_response.get("hourly_units", {})
        times = hourly.get("time", [])
        elevation = raw_response.get("elevation")
        if elevation is not None:
            try:
                elevation = float(elevation)
            except (ValueError, TypeError):
                elevation = None

        if not times:
            return []

        # Determine model issue time (first timestamp truncated to day cycle or current cycle)
        # In Open-Meteo, issue cycle is standard 00Z / 06Z / 12Z / 18Z run
        first_time = times[0]
        try:
            first_dt = datetime.fromisoformat(first_time)
            issue_dt = first_dt.replace(hour=(first_dt.hour // 6) * 6, minute=0, second=0)
            issue_time_iso = issue_dt.isoformat() + "Z"
        except Exception:
            issue_time_iso = datetime.now(timezone.utc).isoformat()

        # Variable mapping: Open-Meteo key -> (canonical name, canonical unit)
        var_mapping = {
            "temperature_2m": ("temperature_2m", "celsius"),
            "surface_pressure": ("surface_pressure", "hPa"),
            "wind_speed_10m": ("wind_speed_10m", "m/s"),
            "relative_humidity_2m": ("relative_humidity_2m", "%"),
            "precipitation": ("precipitation", "mm"),
            "geopotential_height_500hPa": ("geopotential_height_500hPa", "m"),
            "z500": ("geopotential_height_500hPa", "m"),
        }

        # Pre-compute issue datetime once outside the loop
        try:
            dt_issue = datetime.fromisoformat(issue_time_iso.replace("Z", "+00:00"))
        except Exception:
            dt_issue = datetime.now(timezone.utc)

        # Pre-parse valid timestamps and lead hours
        valid_time_isos: list[str] = []
        lead_hours_list: list[int] = []
        for i, valid_time_str in enumerate(times):
            try:
                valid_dt = datetime.fromisoformat(valid_time_str)
                valid_time_iso = valid_dt.isoformat() + "Z"
                if valid_dt.tzinfo is None:
                    valid_dt = valid_dt.replace(tzinfo=timezone.utc)
                lead_h = max(0, int((valid_dt - dt_issue).total_seconds() // 3600))
            except Exception:
                valid_time_iso = valid_time_str
                lead_h = i
            valid_time_isos.append(valid_time_iso)
            lead_hours_list.append(lead_h)

        # Pre-compute vectorized statistics across all timesteps for each variable
        n_times = len(times)
        var_stats: dict[str, dict[str, Any]] = {}
        for src_var, (canon_var, canon_unit) in var_mapping.items():
            if src_var not in hourly:
                continue
            vals = hourly[src_var]
            val_floats = [float(v) if v is not None else None for v in vals]
            m_keys = sorted([k for k in hourly.keys() if k.startswith(f"{src_var}_member")])

            if m_keys:
                all_series = []
                all_series.append([float(v) if v is not None else np.nan for v in vals])
                for mk in m_keys:
                    ms = hourly.get(mk, [])
                    all_series.append([float(v) if v is not None else np.nan for v in ms])

                arr = np.array(all_series, dtype=float)
                member_counts = np.sum(~np.isnan(arr), axis=0)
                means = np.nanmean(arr, axis=0)
                stds = np.where(member_counts > 1, np.nanstd(arr, axis=0, ddof=1), 0.0)
                mins = np.nanmin(arr, axis=0)
                maxs = np.nanmax(arr, axis=0)
                q10s = np.nanpercentile(arr, 10, axis=0)
                q90s = np.nanpercentile(arr, 90, axis=0)

                var_stats[src_var] = {
                    "vals": val_floats,
                    "member_count": member_counts,
                    "means": means,
                    "stds": stds,
                    "mins": mins,
                    "maxs": maxs,
                    "q10s": q10s,
                    "q90s": q90s,
                    "has_members": True,
                }
            else:
                var_stats[src_var] = {
                    "vals": val_floats,
                    "member_count": [31] * n_times,
                    "means": val_floats,
                    "stds": [None] * n_times,
                    "mins": val_floats,
                    "maxs": val_floats,
                    "q10s": val_floats,
                    "q90s": val_floats,
                    "has_members": False,
                }

        for i in range(n_times):
            vt_iso = valid_time_isos[i]
            lh = lead_hours_list[i]
            for src_var, (canon_var, canon_unit) in var_mapping.items():
                if src_var not in var_stats:
                    continue
                st = var_stats[src_var]
                if i >= len(st["vals"]):
                    continue
                vf = st["vals"][i]
                if st["has_members"]:
                    raw_nm = int(st["member_count"][i])
                    nm = raw_nm if raw_nm >= 1 else None
                    em = float(st["means"][i]) if not np.isnan(st["means"][i]) else None
                    es = float(st["stds"][i]) if not np.isnan(st["stds"][i]) else None
                    emin = float(st["mins"][i]) if not np.isnan(st["mins"][i]) else None
                    emax = float(st["maxs"][i]) if not np.isnan(st["maxs"][i]) else None
                    eq10 = float(st["q10s"][i]) if not np.isnan(st["q10s"][i]) else None
                    eq90 = float(st["q90s"][i]) if not np.isnan(st["q90s"][i]) else None
                else:
                    nm = 31
                    em = vf
                    es = None
                    emin = vf
                    emax = vf
                    eq10 = vf
                    eq90 = vf

                record = CanonicalForecastRecord(
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    elevation=elevation,
                    issue_time=issue_time_iso,
                    valid_time=vt_iso,
                    lead_hours=lh,
                    variable=canon_var,
                    unit=canon_unit,
                    value=vf,
                    source="NOAA_GEFS_OPENMETEO",
                    member_count=nm,
                    ensemble_mean=em,
                    ensemble_std=es,
                    ensemble_min=emin,
                    ensemble_max=emax,
                    q10=eq10,
                    q90=eq90,
                )
                records.append(record)

        return records

    @staticmethod
    def _classify_upstream_error(exc: Exception) -> str:
        """Categorize upstream exceptions into standardized operational telemetry outcomes."""
        err_str = str(exc).lower()
        if "429" in err_str:
            return "HTTP_429"
        if any(code in err_str for code in ("500", "502", "503", "504")):
            return "HTTP_5XX"
        if "timeout" in err_str or isinstance(exc, TimeoutError):
            return "TIMEOUT"
        if isinstance(exc, (json.JSONDecodeError, ValueError)):
            return "MALFORMED_RESPONSE"
        return "NETWORK_ERROR"

    def _fetch_raw_forecast(self, query_url: str) -> dict[str, Any]:
        """Fetch raw JSON payload with bounded TTL caching, deduplication, and operational telemetry."""
        # 1. Fast-path cache lookup
        if self.enable_cache and self.cache is not None:
            cached = self.cache.get(query_url)
            if cached is not None:
                logger.debug("event=cache_hit component=openmeteo_service query_url=%s", query_url)
                return dict(cached)
            else:
                logger.debug("event=cache_miss component=openmeteo_service query_url=%s", query_url)
        elif not self.enable_cache:
            logger.debug("event=cache_disabled component=openmeteo_service")

        # 2. Worker action executed under deduplication leader
        def _do_fetch() -> dict[str, Any]:
            # Double-check cache inside leader in case another flight populated it
            if self.enable_cache and self.cache is not None:
                cached = self.cache.get(query_url)
                if cached is not None:
                    return dict(cached)

            start_t = time.perf_counter()
            try:
                fetch_fn = self.http_client if self.http_client is not None else self._default_http_client
                raw = fetch_fn(query_url)
                duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
                default_metrics.record_upstream_request("openmeteo", "SUCCESS", duration_ms)
                logger.info(
                    "event=upstream_fetch_complete provider=openmeteo outcome=SUCCESS duration_ms=%.2f",
                    duration_ms,
                )
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
                outcome = self._classify_upstream_error(exc)
                default_metrics.record_upstream_request("openmeteo", outcome, duration_ms)
                logger.warning(
                    "event=upstream_fetch_failed provider=openmeteo outcome=%s duration_ms=%.2f error=%s",
                    outcome,
                    duration_ms,
                    exc,
                )
                raise exc

            # Store in cache only on successful, non-empty response
            if self.enable_cache and self.cache is not None and raw:
                self.cache.set(query_url, raw, ttl=self.cache_ttl)
            return raw

        # 3. Deduplicate in-flight concurrent requests for identical query_url
        if self.enable_dedup and self.deduplicator is not None:
            result = self.deduplicator.do(query_url, _do_fetch)
        else:
            result = _do_fetch()

        return result

    def get_forecast(
        self,
        location: str,
        target_date: Optional[str] = None,
        forecast_days: Optional[int] = None,
    ) -> WeatherResult:
        """Fetch live or mocked forecast data, validate QC, and return standardized WeatherResult."""
        coords = self.resolve_coordinates(location)
        if coords is None:
            default_metrics.record_abstention(ReasonCode.INVALID_LOCATION.value)
            logger.info("event=location_resolution_failed location=%s", location)
            return WeatherResult(
                location=location,
                target_date=target_date,
                is_available=False,
                quality_flags={"qc_passed": False, "invalid_location": True},
                metadata={"status": ReasonCode.INVALID_LOCATION.value},
                error=f"Location '{location}' could not be resolved to coordinates",
            )

        latitude, longitude = coords
        f_days = forecast_days if forecast_days is not None else 16
        query_url = self.build_query_url(latitude, longitude, target_date, forecast_days=f_days)

        try:
            raw_data = self._fetch_raw_forecast(query_url)
        except Exception as exc:
            default_metrics.record_abstention(ReasonCode.DATA_UNAVAILABLE.value)
            logger.error("Failed to query weather API for location '%s': %s", location, exc)
            return WeatherResult(
                location=location,
                target_date=target_date,
                is_available=False,
                quality_flags={"qc_passed": False, "network_error": True},
                metadata={"status": ReasonCode.DATA_UNAVAILABLE.value},
                error=f"Weather ingestion failed: {exc}",
            )

        # Parse canonical records
        records = self.parse_canonical_records(raw_data, location, latitude, longitude)
        if not records:
            default_metrics.record_abstention(ReasonCode.DATA_NOT_READY.value)
            return WeatherResult(
                location=location,
                target_date=target_date,
                is_available=False,
                quality_flags={"qc_passed": False, "empty_records": True},
                metadata={"status": ReasonCode.DATA_NOT_READY.value},
                error="Vendor API returned zero parseable time-step records",
            )

        # Execute Quality Control checks
        qc_result = self.qc.validate_records(records)
        if not qc_result.passed:
            reason = qc_result.reason_code.value if qc_result.reason_code else ReasonCode.QC_FAILED.value
            default_metrics.record_abstention(reason)
            logger.warning("Quality control failed for location '%s': %s", location, qc_result.violations)
            return WeatherResult(
                location=location,
                target_date=target_date,
                raw_data={"record_count": len(records), "sample_records": [r.model_dump() for r in records[:3]]},
                data_version=self.data_version,
                is_available=False,
                quality_flags=qc_result.flags,
                metadata={
                    "status": reason,
                    "violations": qc_result.violations,
                },
                error=f"Quality control checks failed: {'; '.join(qc_result.violations[:3])}",
            )

        # QC Succeeded
        payload_sha256 = hashlib.sha256(json.dumps(raw_data, sort_keys=True).encode("utf-8")).hexdigest()

        dataset = CanonicalForecastDataset(
            location=location,
            latitude=latitude,
            longitude=longitude,
            issue_time=records[0].issue_time,
            source="NOAA_GEFS_OPENMETEO",
            records=records,
            metadata={"record_count": len(records), "data_version": self.data_version, "payload_sha256": payload_sha256},
        )

        return WeatherResult(
            location=location,
            target_date=target_date,
            raw_data=dataset.model_dump(),
            data_version=self.data_version,
            is_available=True,
            quality_flags=qc_result.flags,
            metadata={
                "status": ReasonCode.SUCCESS.value,
                "record_count": len(records),
                "issue_time": records[0].issue_time,
                "lead_hours_range": [records[0].lead_hours, records[-1].lead_hours],
                "payload_sha256": payload_sha256,
                "dataset_license": "Open-Meteo (ODbL / CC-BY 4.0)",
                "license_uri": "https://open-meteo.com/en/terms",
                "provider": "NOAA_GEFS",
                "dataset_role": "PREDICTOR_INPUT",
            },
        )
