# Veyra Sentinel — System Architecture Specification

**Problem Statement:** SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Organization:** Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)  
**Theme:** Disaster Management  
**Architecture Classification:** Modular Monolith with Tiered Reliability, Safety, and Governance Layers  

---

## 1. Executive Architectural Overview

Veyra Sentinel is an **AI-powered reliability layer placed on top of existing numerical weather prediction (NWP) systems**. Rather than attempting to simulate atmospheric physics or replace operational NWP models (e.g. NOAA GEFS, NCMRWF NEPS), Sentinel monitors the operational forecast process itself. At forecast issue time, it evaluates whether the forecast is prone to an unusually large future error (**forecast bust**) across the Indian subcontinent.

The architecture is designed around four strict operational invariants:
1. **Issue-Time Safety**: Zero future information or verifying ground truth (ERA5) may leak into inference features (`availability_time <= issue_time`).
2. **Deterministic Fallbacks**: Graceful degradation under data latency (`DATA_DELAYED`), missing ensemble members, and model corruption (calibrated spread-only baseline).
3. **Conservative Abstention**: The system explicitly withholds numeric probabilities and says *"I don't know — human review required"* when encountering out-of-distribution (OOD) states or uncertified conditions.
4. **Human-in-the-Loop Governance**: Automated AI risk scores must pass operational meteorologist review before dissemination into official district disaster bulletins.

---

## 2. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Data_Sources ["1. Upstream Data Gateway"]
        GEFS["NOAA GEFS Ensembles<br/>(31 Members, 0.5° Grid)"]
        WB2["WeatherBench 2 Benchmark<br/>(Standardized Zarr Fields)"]
        ERA5["Copernicus CDS ERA5<br/>(Verification-Only Reanalysis)"]
    end

    subgraph Data_Pipeline ["2. Ingestion & Quality Control"]
        Ingest["OpenMeteoGEFSWeatherService<br/>(Canonical Coordinate Resolution)"]
        QC["ForecastQualityControl<br/>(Physical Bounds, Monotonicity, Member Count)"]
        ZarrStore["Zarr / Parquet Store<br/>(Gridded Fields & Canonical Records)"]
        Fallback["ForecastFallbackService<br/>(K1 Cached Cycle Recovery & K2 Degraded Mode)"]
    end

    subgraph Feature_ML ["3. ML Intelligence & Calibration"]
        FeatEng["V3 Feature Adapter<br/>(50 Canonical Tabular Features)"]
        Booster["Frozen V3 LightGBM Classifier<br/>(SHA-256 Verified Booster)"]
        SpreadFallback["Spread-Only Logistic Baseline<br/>(K3 Model-Unavailable Fallback)"]
        Calibrator["Isotonic Calibrator<br/>(Reliability ECE <= 0.08)"]
        Conformal["Split Conformal Predictor<br/>(90% Conditional Prediction Intervals)"]
    end

    subgraph Safety_Governance ["4. Safety, OOD & Governance"]
        OOD["OODEnforcer (K4)<br/>(Polar, Oceanic & Mahalanobis Distance)"]
        Scope["ScopeEnforcer (A3/A4/A5)<br/>(India Domain & Lead Horizon Boundaries)"]
        Registry["ModelRegistryService (L1)<br/>(7-Stage Model Promotion Lifecycle)"]
        Shadow["ShadowScoringService (K6)<br/>(Dark Mode Model Evaluation)"]
        Audit["AuditLogger (L3)<br/>(Structured JSON, Correlation IDs)"]
        Drift["DriftMonitoringService (L4)<br/>(PSI & Calibration Decay Tracking)"]
    end

    subgraph Decision_Serving ["5. Decision Support & Serving API"]
        Agent["ForecastBustAgent<br/>(Central Orchestration Monolith)"]
        FastAPI["FastAPI REST Application<br/>(14+ Versioned Endpoints, RBAC, CORS)"]
        Review["HITL Review Engine (A2)<br/>(Forecaster Approval / Modification)"]
    end

    subgraph User_Interface ["6. Operational Frontend"]
        Map["Leaflet Spatial Risk Map<br/>(6 Indian Synoptic Polygons, Centroids)"]
        Gauges["Interactive Risk Gauges<br/>(5-Tier Color Bands: Green/Yellow/Orange/Red/Gray)"]
        Replay["Deterministic Historical Replay<br/>(Cyclone Tauktae 5-Cycle Stepper)"]
        Analogs["Historical Analog Explorer<br/>(Top Synoptic Analogs + 'No Match' Null State)"]
        Metrics["Research Metrics Dashboard<br/>(Reliability Diagrams, Lead Gain Curves)"]
    end

    GEFS --> Ingest
    WB2 --> Ingest
    ERA5 -.->|Post-Forecast Verification Only| ZarrStore

    Ingest --> QC
    QC -->|Valid Run| ZarrStore
    QC -->|Upstream Failure| Fallback
    Fallback -->|Recovered Cycle| FeatEng
    ZarrStore --> FeatEng

    FeatEng --> Booster
    FeatEng --> SpreadFallback
    Booster --> Calibrator
    Calibrator --> Conformal

    Conformal --> Agent
    SpreadFallback --> Agent
    OOD --> Agent
    Scope --> Agent

    Agent --> Audit
    Agent --> Drift
    Agent --> Shadow
    Agent --> FastAPI

    FastAPI --> Review
    Review --> Map
    Review --> Gauges
    Review --> Replay
    Review --> Analogs
    Review --> Metrics
```

---

## 3. End-to-End Pipeline & Request Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Forecaster / Client
    participant API as FastAPI REST Gateway (/v1/predict)
    participant Auth as Auth & RBAC Guard
    participant Agent as ForecastBustAgent
    participant Scope as ScopeEnforcer
    participant OOD as OODEnforcer
    participant Weather as OpenMeteoGEFSWeatherService
    participant Fallback as ForecastFallbackService
    participant Features as Builder2V3FeatureAdapter
    participant Model as ModelIntegrationService (V3 LightGBM)
    participant Safety as SafetyEvaluator & Conformal
    participant Audit as AuditLogger

    User->>API: POST /v1/predict (location="Delhi", variable="temperature_2m")
    API->>Auth: Verify API Key & Scopes (predict:read)
    Auth-->>API: Authorized
    API->>Agent: analyze(request)
    
    Agent->>Scope: validate_scope(location, variable, lead_hours)
    Scope-->>Agent: ScopeResult (is_certified=True, outside_domain=False)
    
    Agent->>OOD: evaluate(location, lat, lon)
    OOD-->>Agent: OODResult (is_ood=False, state=NORMAL)

    Agent->>Weather: get_forecast(location)
    alt Upstream Download Success
        Weather-->>Agent: WeatherResult (is_available=True, 31 members)
        Agent->>Fallback: record_good_cycle(location, weather)
    else Upstream Download Failure
        Weather-->>Agent: WeatherResult (is_available=False)
        Agent->>Fallback: handle_download_failure(location)
        Fallback-->>Agent: FallbackCycleResult (recovered=True, is_fallback=True, status="DATA_DELAYED")
    end

    Agent->>Features: build_features(weather_result)
    Features-->>Agent: FeatureResult (50 canonical features, availability_time verified)

    Agent->>Model: predict(feature_result)
    alt Model Online
        Model-->>Agent: ModelResult (calibrated_prob=0.32, SHAP explanation)
    else Model Offline / Corrupted
        Agent->>Fallback: compute_spread_only_fallback(spread, lead)
        Fallback-->>Agent: BaselineFallbackResult (spread_only_prob=0.28)
    end

    Agent->>Safety: evaluate(model_result, conformal)
    Safety-->>Agent: SafetyAssessment (trust_state=HIGH_CONFIDENCE, band=YELLOW, interval=[0.24, 0.40])

    Agent->>Audit: log_event(PREDICTION, prediction_id, latency, versions)
    Agent-->>API: PredictionResponse envelope
    API-->>User: HTTP 200 JSON Response
```

---

## 4. Failure Handling & Degradation Topology (§21)

Veyra Sentinel implements an exhaustive, non-silent failure matrix ensuring no error condition is ever hidden from human decision-makers:

```mermaid
flowchart TD
    Start([Inference Request]) --> CheckGeo{Location Check}
    
    CheckGeo -->|Polar / Deep Ocean| AbstainOOD[ABSTAIN: OUT_OF_DISTRIBUTION<br/>Suppress Probabilities<br/>Human Review Required]
    CheckGeo -->|Foreign City| WarnGeo[Serve with UNSUPPORTED_GEOGRAPHIC_REGION<br/>outside_certified_domain=True]
    CheckGeo -->|Certified Indian Domain| CheckWeather{Weather Data Fetch}

    WarnGeo --> CheckWeather

    CheckWeather -->|Failure / Timeout| CheckCache{Cached Cycle Exists?}
    CheckCache -->|Yes| FallbackK1[Recover Cached Previous Cycle<br/>Flag status='DATA_DELAYED'<br/>is_fallback_cycle=True]
    CheckCache -->|No| AbstainWeather[ABSTAIN: DATA_UNAVAILABLE<br/>bust_probability=null<br/>trust_state=UNAVAILABLE]

    CheckWeather -->|Success| CheckMembers{Ensemble Completeness}
    FallbackK1 --> CheckMembers

    CheckMembers -->|< 10 Members| AbstainEnsemble[ABSTAIN: INSUFFICIENT_MEMBERS<br/>bust_probability=null<br/>Critical Data Degradation]
    CheckMembers -->|10–30 Members| DegradeK2[DEGRADED MODE: Incomplete Ensemble<br/>Inflate Uncertainty by sqrt(31/N)<br/>Flag is_degraded=True]
    CheckMembers -->|31/31 Members| CheckModel{Primary ML Model}
    DegradeK2 --> CheckModel

    CheckModel -->|Model Offline / Missing| FallbackK3[CALIBRATED SPREAD-ONLY BASELINE<br/>Logistic Regression Baseline<br/>Flag is_baseline_fallback=True]
    CheckModel -->|Model Operational| RunGBM[V3 LightGBM Inference<br/>Isotonic Calibration<br/>Conformal Prediction Interval]

    FallbackK3 --> AssembleResponse[Assemble Standardized Prediction Envelope]
    RunGBM --> AssembleResponse
    
    AssembleResponse --> End([Dispatch HTTP Response])
    AbstainOOD --> End
    AbstainWeather --> End
    AbstainEnsemble --> End
```

---

## 5. Model Lifecycle & Promotion State Machine (§22, L1)

Model versions must navigate a strict 7-stage promotion lifecycle before serving live predictions:

```mermaid
stateDiagram-v2
    [*] --> CANDIDATE: Model Trained & Checksum Logged
    
    CANDIDATE --> VALIDATED: Gate 1 Passed (PR-AUC >= 0.60, Brier <= 0.20)
    CANDIDATE --> RETIRED: Gate 1 Failed
    
    VALIDATED --> CALIBRATED: Gate 2 Passed (ECE <= 0.08, Platt Slope in [0.8, 1.2])
    VALIDATED --> RETIRED: Gate 2 Failed
    
    CALIBRATED --> STRESS_TESTED: Gate 3 Passed (Perturbation Stability >= 0.80)
    CALIBRATED --> RETIRED: Gate 3 Failed
    
    STRESS_TESTED --> APPROVED: Gate 4 Passed (Human Forecaster Sign-off & Notes)
    STRESS_TESTED --> RETIRED: Rejection
    
    APPROVED --> SERVING: Gate 5 Passed (Promotion to Active Production)
    
    SERVING --> RETIRED: Superseded by New Version
    RETIRED --> [*]
```

---

## 6. Component Responsibilities & Package Structure

| Package / Module | Responsibility | Key Invariants Enforced |
|---|---|---|
| `backend/app/agents/` | Central orchestration monolith (`ForecastBustAgent`). | Coordinates all downstream services; never mutates feature vectors; applies zero lookahead. |
| `backend/app/services/openmeteo_service.py` | Upstream weather ingestion for NOAA GEFS ensembles. | Harmonizes units (Kelvin, Pa, m/s); enforces 31-member ensemble structure; validates coordinate bounds. |
| `backend/app/safety/ood_enforcement.py` | Authoritative Out-Of-Distribution gating. | Polar $|\text{lat}| \ge 66.5^\circ$, oceanic domains, and Mahalanobis distance $> 3.0$ strictly withhold confident probabilities. |
| `backend/app/safety/scope_enforcer.py` | Certified operational scope enforcement. | Indian subcontinental domain bounds; 24h–240h lead horizon limits; core variable certification. |
| `backend/app/services/fallback_service.py` | Operational fallbacks for download dropouts, missing members, and model downtime. | Last good cycle retrieval (`DATA_DELAYED`); uncertainty inflation for 10–30 members; calibrated spread-only fallback. |
| `backend/app/services/model_registry.py` | Enterprise model governance and lifecycle transitions. | 7-stage promotion gates (`CANDIDATE` to `SERVING`); prevents unauthorized model activation. |
| `backend/app/services/shadow_scoring.py` | Shadow/dark mode model evaluation. | Compares candidate vs serving model divergence and bias over empirical sample budgets. |
| `backend/app/core/auth.py` | Security, authentication, and defensive engineering. | 4-tier RBAC (`ADMIN`, `FORECASTER`, `RESEARCHER`, `VIEWER`); API key guards; input bounds sanitization. |
| `backend/app/core/audit_logger.py` | Structured audit event logging. | Structured JSON emission with `audit_id`, `prediction_id`, latency, and circular buffer querying. |
| `backend/app/services/drift_monitor.py` | Online feature drift and calibration decay monitoring. | Feature Population Stability Index (PSI); verification Brier score deterioration; automated retraining proposals. |
| `backend/app/api/v1/endpoints/review.py` | Human-in-the-Loop approval gate. | Forecaster review states (`APPROVED`, `MODIFIED`, `REJECTED`) for bulletin dissemination. |
| `backend/app/services/analog_service.py` | Historical weather analog discovery. | Temporal causality enforcement; B6 event exclusion; clean `"No eligible analog found"` null state. |
| `backend/app/services/spatial_service.py` | Spatial extent, object detection, and risk zones. | 6 Indian synoptic risk polygons; 42.5 km centroid error circles; Fractions Skill Score (FSS). |

---

## 7. Complete API Route Map (All 14+ Endpoints)

| Method | Path | Summary | Auth Role | Description |
|---|---|---|---|---|
| `GET` | `/v1/health` | Liveness & Readiness Probe | Public | Returns service status, version, and dependency health. |
| `POST` | `/v1/predict` | Single-Horizon Bust Risk Evaluation | Public / Key | Standard prediction endpoint returning full prediction envelope. |
| `POST` | `/v1/predict/batch` | Multi-Location Batch Prediction | Public / Key | Concurrent evaluation across up to 50 locations with failure isolation. |
| `POST` | `/v1/dashboard/intelligence` | Multi-Horizon Trajectory Intelligence | Public / Key | 16-day and 7-day risk trajectories, summary statistics, and scientific context. |
| `GET` | `/v1/models` | Model Registry Catalog | Viewer | Lists all registered models, lifecycle statuses, and performance metrics. |
| `GET` | `/v1/models/{id}` | Model Version Details | Viewer | Returns model architecture, training window, SHA-256 hash, and status. |
| `POST` | `/v1/models/{id}/promote` | Model Lifecycle Promotion | Admin | Promotes model to next lifecycle stage if gate criteria are satisfied. |
| `GET` | `/v1/models/{id}/gates` | Promotion Gate Assessment | Researcher | Evaluates candidate model against promotion acceptance criteria. |
| `GET` | `/v1/forecasts` | Available Forecast Cycles | Viewer | Lists cached and historical forecast cycles available for evaluation. |
| `GET` | `/v1/risk-map` | GeoJSON Spatial Risk Overlays | Viewer | Returns 6 synoptic Indian risk polygons and centroid coordinates. |
| `GET` | `/v1/analogs` | Historical Analog Search | Viewer | Returns top similar historical weather cases or authoritative null state. |
| `GET` | `/v1/explanation` | Explainability & SHAP Attribution | Viewer | Returns signed SHAP bars, timestamps, and auditable reason codes. |
| `GET` | `/v1/metrics` | Operational & Evaluation Metrics | Researcher | Returns PR-AUC, Brier score, ECE, reliability diagrams, and ops counters. |
| `GET` | `/v1/metadata` | System & License Metadata | Public | System versions, open data licenses, and claim scope statements. |
| `GET` | `/v1/data-provenance` | Data Provenance & Lineage | Viewer | Artifact SHA-256 hashes, source URLs, and verification invariants. |
| `GET` | `/v1/export` | Multi-Format Data Export | Researcher | Bounded export in CSV, JSON, GeoJSON, and NetCDF formats. |
| `POST` | `/v1/predictions/{id}/review` | Submit Forecaster Review | Forecaster | Records meteorologist approval, modification, or rejection. |
| `GET` | `/v1/predictions/{id}/review` | Retrieve Prediction Review | Viewer | Retrieves HITL review status and forecaster notes. |
