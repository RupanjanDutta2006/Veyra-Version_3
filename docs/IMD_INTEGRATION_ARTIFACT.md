# India Meteorological Department (IMD) Operational Integration Artifact

**Document Reference:** VEYRA-IMD-SOP-2026-V1  
**Target Invariant:** §1.0, §2.1, §3.1, §22 (Audit Item A8)  
**Classification:** Operational Technical Specification / Dissemination Standard Operating Procedure  
**Authors:** Veyra Architecture Team & IMD Operational Integration Working Group  

---

## 1. Operational Overview & Mission Alignment

Veyra Sentinel operates as an **AI-powered Decision Support System (DSS)** designed to complement existing Numerical Weather Prediction (NWP) infrastructure at the India Meteorological Department (IMD) and National Centre for Medium Range Weather Forecasting (NCMRWF).

### Core Principle
> **"Sentinel advises, meteorologists decide."**  
> Veyra Sentinel does **not** replace the official IMD forecaster. It acts as an early-warning watchdog on already-issued medium-range forecasts (24h to 240h), identifying synoptic regimes where standard NWP guidance exhibits an elevated probability of severe failure (forecast bust).

---

## 2. IMD 4-Stage Warning Color Code Mapping

Veyra's risk levels and 5-tier color bands map directly to IMD's standard meteorological warning matrix:

| Veyra Risk Tier | IMD Color Code | P(Bust) Threshold | Synoptic Meaning | Operational IMD Action |
|---|---|---|---|---|
| **GREEN** | **Green (No Warning)** | $p < 0.30$ | Forecast in nominal stability bounds | Standard monitoring. No special bulletin required. |
| **YELLOW** | **Yellow (Be Updated)** | $0.30 \le p < 0.50$ | Elevated uncertainty; ensemble spread widening | Issue internal advisory to regional meteorological centres (RMCs). Monitor upcoming 06Z/18Z cycle updates. |
| **ORANGE** | **Orange (Be Prepared)** | $0.50 \le p < 0.70$ | High failure probability; regime transition or revision acceleration | Alert disaster management authorities (NDRF/SDMA). Prepare contingency forecasts and ensemble reruns. |
| **RED** | **Red (Take Action)** | $p \ge 0.70$ | Critical forecast bust imminent; high-impact divergence | Issue red-tier special weather bulletin. Initiate emergency forecaster review; update public advisories. |
| **GRAY** | **Gray (Abstain)** | N/A (Abstained) | Out-of-distribution or degraded observation | Sentinel withholds automated guidance. Forecaster manual synoptic chart analysis mandatory. |

---

## 3. Common Alerting Protocol (CAP) Schema Mapping

Veyra Sentinel outputs conform to the WMO / ITU-T **Common Alerting Protocol (CAP-CP v1.0 / NDMA Schema)**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>VEYRA-IMD-20260919-001</identifier>
  <sender>sentinel@imd.gov.in</sender>
  <sent>2026-09-19T12:00:00+05:30</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <info>
    <category>Met</category>
    <event>Medium-Range Forecast Bust Alert</event>
    <urgency>Expected</urgency>
    <severity>Severe</severity>
    <certainty>Likely</certainty>
    <eventCode>
      <valueName>IMD_COLOR_CODE</valueName>
      <value>ORANGE</value>
    </eventCode>
    <headline>Potential GEFS Forecast Bust Detected for Coastal Gujarat (Lead: 48h)</headline>
    <description>
      Veyra Sentinel V3 has detected a 74.2% probability of severe forecast bust for 24-hour rainfall and 10m wind speed.
      Primary drivers: Revision acceleration (delta_k_6h = 1.42), Rapidly collapsing ensemble spread (spread-to-error divergence).
      Dominant regime: Arabian Sea Pre-Monsoon Tropical Cyclogenesis.
    </description>
    <area>
      <areaDesc>IN_WEST (Saurashtra and Kutch, Coastal Gujarat)</areaDesc>
      <polygon>20.5,69.0 24.5,68.0 24.5,73.0 20.5,73.0 20.5,69.0</polygon>
    </area>
  </info>
</alert>
```

---

## 4. Operational Ingestion & Latency Budget

Veyra Sentinel synchronizes with IMD / NCMRWF operational NWP cycles:

```
00Z Cycle Ingestion:
+00:00 - Global NWP execution begins (NCMRWF / NOAA GEFS)
+03:30 - Raw GRIB2/NetCDF field dissemination available
+03:35 - Veyra Sentinel automated ingestion triggered via open data pipe
+03:38 - Feature extraction & cycle-revision dynamics computed (Δk_6h, Δk_12h)
+03:40 - Inference, OOD evaluation, and calibration layer executed
+03:42 - Sentinel Alert Bulletin published to IMD Forecaster Workstation
```

**Total Veyra Processing Latency:** $\le 7\text{ minutes}$ from raw field availability to forecaster screen.

---

## 5. Forecaster-in-the-Loop Standard Operating Procedure (SOP)

When Veyra flags an **Orange** or **Red** tier alert:

1. **Automated Triage**: Alert appears on the IMD Forecaster Dashboard with audio/visual notification.
2. **Review Step (A2)**:
   - Duty meteorologist reviews the **Explainability Panel** (SHAP drivers and reason codes).
   - Forecaster checks the **Analog Explorer** to inspect similar historical cyclones/monsoon busts.
   - Forecaster verifies that `availability_time <= issue_time` (zero future data leakage).
3. **Action Decision**:
   - `APPROVE`: Forecaster agrees with bust risk; Sentinel alert is merged into the National Weather Bulletin.
   - `REJECT`: Forecaster determines local radar/nowcast contradicts bust signal; logged as false alarm.
   - `OVERRIDE`: Forecaster adjusts probability or risk tier based on proprietary radar/satellite feeds.
4. **Audit Logging (L3)**:
   - Forecaster badge ID, decision timestamp, and rationale are immutably logged to the Veyra audit trail.

---

## 6. Certified Geographic Domain & Fallback Invariants

- **Certified Domain**: Indian Landmass + Exclusive Economic Zone (EEZ) [6.0°N to 37.5°N, 68.0°E to 98.0°E].
- **Certified Variables**: 2m Temperature, 10m Wind Speed, Surface Pressure, 500hPa Geopotential Height (Z500), 24h Accumulated Precipitation.
- **Certified Horizons**: 24h to 240h (Days 1 to 10).
- **Fallback Invariants (K1–K4)**:
  - Upstream data delayed $\rightarrow$ Automatic fallback to previous valid cycle with `DATA_DELAYED` banner.
  - Incomplete ensemble ($< 10$ members) $\rightarrow$ Mandatory safe abstention.
  - Model engine failure $\rightarrow$ Seamless fallback to calibrated ensemble spread-only baseline.
  - Extreme polar / foreign queries $\rightarrow$ Immediate abstention with out-of-scope guidance.
