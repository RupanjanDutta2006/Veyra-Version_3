import copy
import logging
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.main import app
from backend.app.services.openmeteo_service import OpenMeteoGEFSWeatherService

logger = logging.getLogger(__name__)


def _generate_synthetic_gefs_from_url(url: str) -> dict[str, Any]:
    """Generate a realistic, deterministic 384-hour Open-Meteo GEFS ensemble payload from query parameters."""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    lat = float(params.get("latitude", [22.5726])[0])
    lon = float(params.get("longitude", [88.3639])[0])
    forecast_days = int(params.get("forecast_days", [16])[0])
    start_date_param = params.get("start_date", [None])[0]
    end_date_param = params.get("end_date", [None])[0]

    if start_date_param:
        try:
            base_dt = datetime.fromisoformat(start_date_param).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        except Exception:
            base_dt = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
    else:
        base_dt = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    num_hours = max(24 * forecast_days, 384)
    if start_date_param and end_date_param:
        try:
            end_dt = datetime.fromisoformat(end_date_param).replace(
                hour=23, minute=0, second=0, microsecond=0
            )
            delta_h = max(24, int((end_dt - base_dt).total_seconds() // 3600) + 1)
            num_hours = max(num_hours, delta_h)
        except Exception:
            pass

    times = [(base_dt + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(num_hours)]
    temps = [round(25.0 + (h % 24) * 0.2, 1) for h in range(num_hours)]
    pressures = [1012.5 for _ in range(num_hours)]
    winds = [round(4.5 + (h % 12) * 0.1, 1) for h in range(num_hours)]
    humidities = [65.0 for _ in range(num_hours)]
    precips = [0.0 for _ in range(num_hours)]
    z500s = [5600.0 for _ in range(num_hours)]

    return {
        "latitude": lat,
        "longitude": lon,
        "generationtime_ms": 1.5,
        "timezone": "UTC",
        "hourly": {
            "time": times,
            "temperature_2m": temps,
            "surface_pressure": pressures,
            "wind_speed_10m": winds,
            "relative_humidity_2m": humidities,
            "precipitation": precips,
            "geopotential_height_500hPa": z500s,
        },
        "hourly_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "surface_pressure": "hPa",
            "wind_speed_10m": "m/s",
            "relative_humidity_2m": "%",
            "precipitation": "mm",
            "geopotential_height_500hPa": "m",
        },
    }


@pytest.fixture(scope="session", autouse=True)
def patch_openmeteo_http_client_fallback():
    """Wrap OpenMeteoGEFSWeatherService._default_http_client to fall back to synthetic GEFS on 429/network errors."""
    orig_client = OpenMeteoGEFSWeatherService._default_http_client
    rate_limited = False

    def resilient_client(self, url: str) -> dict[str, Any]:
        nonlocal rate_limited
        if rate_limited:
            return _generate_synthetic_gefs_from_url(url)
        try:
            return orig_client(self, url)
        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "Too Many Requests" in err_str:
                rate_limited = True
                logger.warning(
                    "Open-Meteo upstream rate limited (HTTP 429) during test session. "
                    "Falling back to deterministic synthetic GEFS forecast for remaining tests."
                )
                return _generate_synthetic_gefs_from_url(url)
            raise

    OpenMeteoGEFSWeatherService._default_http_client = resilient_client
    yield
    OpenMeteoGEFSWeatherService._default_http_client = orig_client


@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI TestClient session fixture."""
    return TestClient(app)


@pytest.fixture
def default_agent() -> ForecastBustAgent:
    """Default ForecastBustAgent fixture."""
    return ForecastBustAgent()


@pytest.fixture(autouse=True)
def reset_state_between_tests():
    """Reset rate limiter, forecast cache, and deduplicator between test cases for test isolation."""
    from backend.app.core.cache import forecast_cache, forecast_deduplicator
    from backend.app.core.rate_limiter import default_rate_limiter

    default_rate_limiter.reset()
    forecast_cache.clear()
    forecast_deduplicator.reset()
    yield
    default_rate_limiter.reset()
    forecast_cache.clear()
    forecast_deduplicator.reset()

