"""License and Terms of Use Registry for Veyra Datasets (SIH26079 §7.4, §16, C11).

Maintains authoritative metadata, terms of use, license URIs, and attribution
requirements for all ingested NWP, reanalysis, benchmark, and proxy datasets.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class DatasetRole(str, Enum):
    """Operational role of the dataset in Veyra pipeline."""
    PREDICTOR_INPUT = "PREDICTOR_INPUT"
    VERIFICATION_ONLY = "VERIFICATION_ONLY"
    BENCHMARK_EVALUATION = "BENCHMARK_EVALUATION"


@dataclass(frozen=True)
class DatasetLicenseInfo:
    """Legal and operational license terms for a dataset snapshot (§7.4, C11)."""
    dataset_id: str
    dataset_name: str
    version: str
    provider: str
    role: DatasetRole
    license_name: str
    license_uri: str
    terms_summary: str
    attribution_text: str
    commercial_use_permitted: bool
    requires_attribution: bool
    strict_anti_leakage_role: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "version": self.version,
            "provider": self.provider,
            "role": self.role.value,
            "license_name": self.license_name,
            "license_uri": self.license_uri,
            "terms_summary": self.terms_summary,
            "attribution_text": self.attribution_text,
            "commercial_use_permitted": self.commercial_use_permitted,
            "requires_attribution": self.requires_attribution,
            "strict_anti_leakage_role": self.strict_anti_leakage_role,
        }


# Authoritative Dataset License Registry
DATASET_LICENSE_REGISTRY: Dict[str, DatasetLicenseInfo] = {
    "NOAA_GEFS": DatasetLicenseInfo(
        dataset_id="NOAA_GEFS",
        dataset_name="NOAA Global Ensemble Forecast System (GEFS) Reforecast & Real-time",
        version="v12.0",
        provider="National Oceanic and Atmospheric Administration (NOAA / NCEP)",
        role=DatasetRole.PREDICTOR_INPUT,
        license_name="U.S. Government Work / Public Domain",
        license_uri="https://www.weather.gov/disclaimer",
        terms_summary="Public domain data available for global redistribution and forecast model evaluation.",
        attribution_text="Data provided by NOAA/NWS National Centers for Environmental Prediction (NCEP).",
        commercial_use_permitted=True,
        requires_attribution=True,
        strict_anti_leakage_role=False,
    ),
    "ECMWF_ERA5": DatasetLicenseInfo(
        dataset_id="ECMWF_ERA5",
        dataset_name="ECMWF ERA5 Reanalysis",
        version="ERA5-single-levels-hourly",
        provider="European Centre for Medium-Range Weather Forecasts (ECMWF) / Copernicus Climate Change Service",
        role=DatasetRole.VERIFICATION_ONLY,
        license_name="Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        license_uri="https://creativecommons.org/licenses/by/4.0/",
        terms_summary=(
            "Generated using Copernicus Climate Change Service information [2020-2026]. "
            "STRICT INVARIANT: Used exclusively for post-event ground truth verification and bust labeling. "
            "Never used as a predictor feature input."
        ),
        attribution_text="Contains modified Copernicus Climate Change Service information [2026].",
        commercial_use_permitted=True,
        requires_attribution=True,
        strict_anti_leakage_role=True,
    ),
    "WEATHERBENCH_2": DatasetLicenseInfo(
        dataset_id="WEATHERBENCH_2",
        dataset_name="WeatherBench 2 Benchmark Dataset",
        version="v2.0-standard",
        provider="Google Research / ECMWF / WeatherBench Community",
        role=DatasetRole.BENCHMARK_EVALUATION,
        license_name="Apache 2.0 / CC-BY 4.0",
        license_uri="https://github.com/google-research/weatherbench2/blob/main/LICENSE",
        terms_summary="Standardized atmospheric benchmark evaluation data for data-driven and NWP models.",
        attribution_text="WeatherBench 2: A benchmark for the next generation of data-driven global weather models.",
        commercial_use_permitted=True,
        requires_attribution=True,
        strict_anti_leakage_role=False,
    ),
    "OPEN_METEO_PROXY": DatasetLicenseInfo(
        dataset_id="OPEN_METEO_PROXY",
        dataset_name="Open-Meteo Weather API Data Feed",
        version="v1",
        provider="Open-Meteo GmbH",
        role=DatasetRole.PREDICTOR_INPUT,
        license_name="Open Database License (ODbL) / CC-BY 4.0",
        license_uri="https://open-meteo.com/en/terms",
        terms_summary="Real-time and archived weather forecast API proxy providing GEFS ensemble members.",
        attribution_text="Weather data by Open-Meteo.com (CC-BY 4.0).",
        commercial_use_permitted=True,
        requires_attribution=True,
        strict_anti_leakage_role=False,
    ),
}


class LicenseRegistry:
    """Query interface for dataset licensing and usage terms."""

    def __init__(self, registry: Optional[Dict[str, DatasetLicenseInfo]] = None):
        self._registry = registry or DATASET_LICENSE_REGISTRY

    def get_license(self, dataset_id: str) -> Optional[DatasetLicenseInfo]:
        """Retrieve license information by dataset identifier."""
        return self._registry.get(dataset_id.strip().upper())

    def list_licenses(self) -> List[Dict[str, Any]]:
        """List all registered dataset licenses."""
        return [info.to_dict() for info in self._registry.values()]

    def verify_role_invariant(self, dataset_id: str, intended_usage: str) -> bool:
        """Verify that a dataset is not used contrary to its strict role (e.g. ERA5 as predictor)."""
        info = self.get_license(dataset_id)
        if not info:
            return True
        if info.strict_anti_leakage_role and intended_usage.upper() == "PREDICTOR":
            return False
        return True
