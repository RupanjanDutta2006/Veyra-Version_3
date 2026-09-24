# Trust-State Contract — Veyra Sentinel

## Overview

This document defines the authoritative mapping from pipeline conditions to trust states.
The `SafetyEvaluator` in `backend/app/safety/abstention.py` implements these rules.

## Trust State Vocabulary

| Trust State | Meaning | Probability Returned | User Action |
|---|---|---|---|
| `HIGH_CONFIDENCE` | All pipeline stages nominal; OOD state = NORMAL | Yes (calibrated) | Actionable forecast reliability assessment |
| `MODERATE_CONFIDENCE` | OOD state = UNUSUAL; elevated atmospheric variance | Yes (calibrated, widened intervals) | Interpret with caution; review recommended |
| `LOW_CONFIDENCE` | OOD state = OOD; outside training distribution | Yes (uncalibrated) | Do not rely on probability; human review required |
| `ABSTAINED` | OOD state = ABSTAIN; probability boundary violation | No (None) | System refuses to score; human forecaster decides |
| `UNAVAILABLE` | Upstream failure (data, features, model, or location) | No (None) | System cannot operate; check infrastructure |

## Decision Rules

### 1. Weather Data Stage
| Condition | Trust State | Reason Code |
|---|---|---|
| `is_available = False` + `invalid_location` | `UNAVAILABLE` | `INVALID_LOCATION` |
| `is_available = False` + `network_error` | `UNAVAILABLE` | `DATA_UNAVAILABLE` |
| `qc_passed = False` | `UNAVAILABLE` | `QC_FAILED` |
| `near_threshold_qc = True` | `UNAVAILABLE` | `NEAR_THRESHOLD_DATA_QUALITY` |

### 2. Feature Pipeline Stage
| Condition | Trust State | Reason Code |
|---|---|---|
| `is_ready = False` | `UNAVAILABLE` | `FEATURES_NOT_READY` |

### 3. Model Inference Stage
| Condition | Trust State | Reason Code |
|---|---|---|
| `model_result = None` or `is_ready = False` | `UNAVAILABLE` | `MODEL_NOT_READY` |
| `probability < 0 or > 1` | `ABSTAINED` | `QC_FAILED` |

### 4. OOD Evaluation (§11.3)
| OOD State | Trust State | Abstain | Reason Code |
|---|---|---|---|
| `NORMAL` | `HIGH_CONFIDENCE` | No | `SUCCESS` |
| `UNUSUAL` | `MODERATE_CONFIDENCE` | No | `SUCCESS` |
| `OOD` | `LOW_CONFIDENCE` | No | `OOD_DETECTED` |
| `ABSTAIN` | `ABSTAINED` | Yes | `OOD_ABSTAIN` |

### 5. Certified Scope Rules
| Dimension | Certified Scope | Outside Scope |
|---|---|---|
| Variables | `temperature_2m`, `surface_pressure`, `wind_speed_10m`, `relative_humidity_2m`, `precipitation` | Any other → `EXPERIMENTAL` label |
| Horizons | 24h – 168h (Day 1 – Day 7) | > 168h → capped at `MODERATE_CONFIDENCE` |
| Locations | Registered in `LocationRegistry` | Unknown → `UNAVAILABLE` + `INVALID_LOCATION` |
| Model types | `baseline-logistic-v1.0`, `prototype-gbm-v1` | Unknown → `MODEL_NOT_READY` |

## Data Source Mode Labels

Every prediction response carries an implicit data source provenance:

| Source Mode | Meaning | Frontend Label |
|---|---|---|
| `LIVE` | Real-time API weather data from Open-Meteo | 🟢 Live |
| `FIXTURE` | Deterministic test fixture (offline/secondary provider) | 🔵 Fixture |
| `SYNTHETIC` | Digital twin / simulation scenario | 🟣 Synthetic |
| `CACHED` | In-memory cached weather query result | 🟡 Cached |
| `FALLBACK` | Offline fallback weather fixture (network failure) | 🟠 Fallback |
| `UNAVAILABLE` | No data source available | ⚫ Unavailable |

## Risk Level Mapping

| Probability Range | Risk Level |
|---|---|
| `p < 0.20` | `LOW` |
| `0.20 ≤ p < 0.50` | `MEDIUM` |
| `0.50 ≤ p < 0.75` | `HIGH` |
| `p ≥ 0.75` | `CRITICAL` |

## Implementation Reference

- Safety evaluator: [`abstention.py`](../backend/app/safety/abstention.py)
- OOD detector: [`ood_detector.py`](../backend/app/safety/ood_detector.py)
- Trust state enum: [`prediction.py`](../backend/app/schemas/prediction.py)
- Frontend trust banners: [`PredictionResult.tsx`](../frontend/src/components/PredictionResult.tsx)
