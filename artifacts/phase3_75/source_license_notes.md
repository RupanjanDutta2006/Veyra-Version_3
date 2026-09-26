# Veyra Version-3 Phase 3 — Source License & Data Provenance Notes

## 1. Overview of External Data Sources
For the Phase 3 real-data scientific integrity evaluation, Veyra Version-3 ingests genuine external meteorological payloads from two authoritative data pipelines:

1. **ECMWF Copernicus Climate Change Service (ERA5 Atmospheric Reanalysis)**:
   - **Provider**: European Centre for Medium-Range Weather Forecasts (ECMWF) / Copernicus Programme
   - **Content**: Hourly reanalysis of 2m Temperature, Surface Pressure, and 10m Wind Speed at 0.25° spatial resolution.
   - **Access / API**: Copernicus Climate Data Store (CDS) via Open-Meteo Archive API endpoint (`https://archive-api.open-meteo.com/v1/archive`).
   - **License & Terms of Use**: **Copernicus Open Access License / Creative Commons Attribution 4.0 International (CC-BY 4.0)**.
   - **Usage Permissibility**: Fully open for academic, scientific, governmental, and commercial use with attribution.
   - **Attribution**: *Contains modified Copernicus Climate Change Service information [2024]. Neither the European Commission nor ECMWF is responsible for any use that may be made of the information.*

2. **NOAA NCEP, ECMWF, DWD, ECCC Multi-Model NWP Forecast Archive**:
   - **Provider**: National Oceanic and Atmospheric Administration (NOAA), Deutscher Wetterdienst (DWD), Environment and Climate Change Canada (ECCC), ECMWF.
   - **Models Included**:
     - NOAA Global Forecast System (GFS Seamless 0.25°)
     - ECMWF Integrated Forecasting System (IFS 0.25°)
     - DWD ICON Global Model (ICON Seamless 0.25°)
     - ECCC Global Environmental Multiscale Model (GEM Seamless)
   - **Access / API**: Open-Meteo Historical Forecast API (`https://historical-forecast-api.open-meteo.com/v1/forecast`).
   - **License & Terms of Use**:
     - NOAA GFS: **U.S. Public Domain (17 U.S.C. § 105)** / NOAA Open Data Policy.
     - DWD ICON: **GeoNutzV / Open Data Terms**.
     - Open-Meteo API: **Open Database License (ODbL) / CC-BY 4.0 Attribution**.
   - **Usage Permissibility**: Fully permissible for reproducible benchmark evaluation and scientific validation.

---

## 2. Cryptographic Substantiation & Integrity
- **Total Raw Files Ingested**: 30 files.
- **Total Raw Payload Size**: 8,882,653 bytes (8.47 MB).
- **Average Station Payload**: ~578.3 KB per station.
- **Coverage Period**: 2024-07-01 00:00:00 UTC through 2024-12-31 23:00:00 UTC (4,416 hours per station).
- **Cryptographic Hashes**: Every file's SHA-256 digest is strictly recorded in `artifacts/phase3_75/raw_source_manifest.csv`.
- **Classification**: **`REPRODUCED_REAL_HELD_OUT`**.
