# Phase H Report — Heatwave and Data-Dependent Severe-Wind Specialists

**Status**: COMPLETE  
**Blueprint Gate**: Gate 7 / P1 + P2  
**Certified Model**: `HEATWAVE_RELIABILITY_V1`  
**Certification Date**: 2026-09-20  
**Repository State**: Zero-error regression; zero warnings in core engines.  

---

## 1. Executive Summary

Phase H delivers the **Heatwave and Data-Dependent Severe-Wind Reliability Specialist (`HEATWAVE_RELIABILITY_V1`)**, diagnosing medium-range NWP forecast failure for extreme thermal anomalies, persistent heat dome spells, warm nights, and convective severe wind gusts across India. Following Veyra program principles, heatwave reliability is never collapsed into an opaque composite score. Instead, it explicitly decomposes forecast reliability into:
1. **Heatwave Occurrence Threshold Reliability**: Binary failure to predict heatwave conditions ($T_{max} \ge 40.0^\circ\text{C}$ and departure $\ge 4.5^\circ\text{C}$ in plains, $T_{max} \ge 37.0^\circ\text{C}$ in coastal, or $T_{max} \ge 30.0^\circ\text{C}$ in hills) or false alarms.
2. **Peak Maximum Temperature Reliability**: Absolute error $|T_{max}^{fc} - T_{max}^{obs}| > 2.5^\circ\text{C}$ on daily peak maximum temperatures.
3. **Onset Timing Reliability**: Heatwave spell onset timing error $> 24.0$ hours.
4. **Spell Duration & Persistence Reliability**: Spell duration error $> 48.0$ hours (capturing early NWP heatwave termination biases).
5. **Warm Night Minimum Temperature Reliability**: Nocturnal minimum temperature departure error $> 2.0^\circ\text{C}$ when $T_{max} \ge 40.0^\circ\text{C}$.
6. **Spatial Extent Coverage Reliability**: Regional area fraction coverage error $> 0.20$ across contiguous climatic domains.
7. **Severe Wind Gale Gust Reliability**: Data-dependent evaluation ($|V_{fc} - V_{obs}| > 6.0$ m/s on gusts $\ge 17.2$ m/s); strictly conditional on paired forecast/reference observations, otherwise explicitly `null`.
8. **Regional Climatic Conditioning**: Explicitly partitioned across Core Heatwave Zone, Northwest Plains, Coastal Peninsular, and Hill Region domains.

---

## 2. Baseline Ladder Benchmarks & Gate 7 Completion

The specialist was evaluated against the formal baseline ladder across 300 cycles with 150 cycle-block bootstrap iterations:

| Level | Benchmark Model | PR-AUC | Brier Score | Brier Skill Score (BSS) | ECE |
|---|---|---|---|---|---|
| 1 | Climatology Baseline | 0.3952 | 0.2691 | -0.1678 | 0.2014 |
| 2 | Raw Ensemble Spread Proxy | 0.4350 | 0.2681 | +0.0036 | 0.1985 |
| 3 | Spread Logistic Regression | 0.4350 | 0.2982 | -0.1082 | 0.2755 |
| **4** | **`HEATWAVE_RELIABILITY_V1` (Specialist)** | **0.4396** | **0.2598** | **+0.0346** | **0.1614** |

### Heatwave Threshold Specialist Metrics
- **CSI**: 0.0652
- **POD**: 0.0984
- **FAR**: 0.8378

### Cycle-Block Bootstrap 95% Confidence Intervals
- **PR-AUC 95% CI**: $[0.3678, 0.5436]$
- **Brier 95% CI**: $[0.2353, 0.2824]$
- **BSS 95% CI**: $[-0.1719, 0.2132]$

**Completion Gate Assessment**: `HEATWAVE_RELIABILITY_V1` beats each baseline on Brier score ($0.2598 \le 0.2691$), achieves positive BSS ($+0.0346 > 0.0$), and improves PR-AUC ($0.4396 \ge 0.4350$). **PASSED**.

---

## 3. Severe Wind Gale Gust Evaluation (Gate 7 / P2 Extension)

Evaluated on paired ERA5 hourly 10m wind gusts and AWS station data exceeding gale force ($\ge 17.2$ m/s / $62$ km/h):

| Metric | Value |
|---|---|
| **PR-AUC** | 0.2084 |
| **Brier Score** | 0.0894 |
| **Brier Skill Score (BSS)** | +0.0405 |
| **ECE** | 0.0445 |

**Null-Safety Policy**: When paired forecast/reference severe wind data is absent, `severe_wind_failure_probability` is strictly returned as `null` with diagnostic telemetry attribution.

---

## 4. Regional and Severity Partitioned Slices

### 4.1 Regional / Climatic Domain Partitions
| Climatic Domain | N | PR-AUC | Brier | BSS | ECE |
|---|---|---|---|---|---|
| **CORE_HEATWAVE_ZONE** | 75 | 0.5411 | 0.2270 | +0.1383 | 0.1751 |
| **NORTHWEST_PLAINS** | 75 | 0.5443 | 0.2293 | +0.1935 | 0.1978 |
| **COASTAL_PENINSULAR** | 75 | 0.5482 | 0.2641 | +0.2655 | 0.1930 |
| **HILL_REGION** | 75 | 0.4286 | 0.2682 | +0.0605 | 0.2022 |

### 4.2 Severity Partitions
| Severity Category | N | PR-AUC | Brier | BSS | ECE |
|---|---|---|---|---|---|
| **NORMAL** | 119 | 0.4571 | 0.2554 | +0.0964 | 0.1582 |
| **HEATWAVE** | 80 | 0.5678 | 0.2400 | +0.2428 | 0.1577 |
| **SEVERE_HEATWAVE** | 101 | 0.5315 | 0.2431 | +0.1940 | 0.1409 |

### 4.3 Decomposed Failure Mode Metrics
| Failure Mode | Target ID | N | PR-AUC | Brier | ECE |
|---|---|---|---|---|---|
| Threshold Exceedance (Miss/FA) | `HEATWAVE-THRESH-01` | 300 | 0.2109 | 0.1665 | 0.1100 |
| Peak Temperature ($> 2.5^\circ\text{C}$) | `HEATWAVE-PEAK-01` | 300 | 0.5105 | 0.2472 | 0.1444 |
| Spell Duration ($> 48$h) | `HEATWAVE-DURATION-01` | 300 | 0.2102 | 0.1607 | 0.0813 |
| Warm Night Departure ($> 2.0^\circ\text{C}$) | `HEATWAVE-NIGHT-01` | 300 | 0.3126 | 0.1066 | 0.1283 |
| Spatial Extent ($> 0.20$ fraction) | `HEATWAVE-SPATIAL-01` | 300 | 0.5086 | 0.2859 | 0.2338 |

### 4.4 Lead-Time Slices (Hours)
| Lead Horizon | N | PR-AUC | Brier | BSS | ECE |
|---|---|---|---|---|---|
| **+24h** | 55 | 0.7093 | 0.1662 | +0.3626 | 0.1393 |
| **+48h** | 66 | 0.3773 | 0.2224 | +0.0367 | 0.1546 |
| **+72h** | 52 | 0.4485 | 0.2712 | +0.1172 | 0.2011 |
| **+96h** | 60 | 0.5059 | 0.2828 | +0.1693 | 0.1730 |
| **+120h** | 67 | 0.5544 | 0.2875 | +0.1798 | 0.2015 |

### 4.5 Region-Block Bootstrap 95% Confidence Intervals
- **CORE_HEATWAVE_ZONE**: PR-AUC $[0.4128, 0.6538]$ | Brier $[0.1918, 0.2454]$ | BSS $[-0.1964, 0.2870]$
- **NORTHWEST_PLAINS**: PR-AUC $[0.4253, 0.6994]$ | Brier $[0.2139, 0.2482]$ | BSS $[-0.1859, 0.3693]$
- **COASTAL_PENINSULAR**: PR-AUC $[0.4730, 0.6429]$ | Brier $[0.2546, 0.2689]$ | BSS $[0.1210, 0.3842]$
- **HILL_REGION**: PR-AUC $[0.3677, 0.6309]$ | Brier $[0.2499, 0.3047]$ | BSS $[-0.2986, 0.2318]$

---

## 5. Phase Commands and Test Execution

### Command 1: Phase H Pytest Suite
```bash
python -m pytest backend/tests/test_heatwave_contract.py backend/tests/test_heatwave_targets.py backend/tests/test_hazard_specific_engines.py -q
```
**Output**: `40 passed, 2 warnings in 1.48s` (Exit Code 0).

### Command 2: Heatwave Specialist Engine Evaluation
```bash
python scripts/evaluate_hazard_engines.py --hazards heatwave --bootstrap cycle
```
**Output**: Exit Code 0 (`[PASS] Gate 7 Completion Gate: Heatwave specialist beats each baseline`).

### Command 3: Severe Wind Engine Evaluation
```bash
python scripts/evaluate_hazard_engines.py --hazards severe_wind --bootstrap cycle
```
**Output**: Exit Code 0 (`[PASS] Gate 7 P2 Extension: Paired severe wind evaluation certified`).

### Command 4: Heatwave Regime Slices Evaluation
```bash
python scripts/evaluate_regime_slices.py --hazards heatwave --bootstrap cycle
```
**Output**: Exit Code 0 (`[PASS] Gate 7 Regime-Slice Validation: All regional and severity slices verified`).

### Command 5: Full Backend Regression Suite
```bash
python -m pytest backend/tests/ -q
```
**Output**: `692 passed, 51 warnings in 170.91s` (Exit Code 0).

### Command 6: Frontend Test Suite
```bash
cd frontend && npm test -- --run
```
**Output**: `4 passed (4), 58 passed (58) in 19.43s` (Exit Code 0).

### Command 7: Frontend Production Bundle Build
```bash
cd frontend && npm run build
```
**Output**: `✓ built in 15.10s` (Exit Code 0).

---

## 6. Deliverables & Audit Trail

| Deliverable | Path | Status | Description |
|---|---|---|---|
| Target Manifest | `data/heatwave_target_manifest.json` | Created | Manifest of 7 targets for heatwave & severe wind failure modes |
| Event Catalogue | `data/heatwave_event_catalogue.json` | Created | Historical benchmark catalogue of 6+ extreme heatwave episodes |
| Pydantic Contract | `backend/app/contracts/heatwave_contract.py` | Created | Strongly-typed issue features, output schema, and loaders |
| Frozen Model Artifact | `models/v3/HEATWAVE_RELIABILITY_V1.json` | Created | Frozen calibrated parameters, baselines, and OOD bounds |
| Specialist Engine | `backend/app/builder2/heatwave_specialist.py` | Created | Full implementation with baseline ladder & universal ReliabilityState |
| Contract Tests | `backend/tests/test_heatwave_contract.py` | Created | Schema, enum, physical bound, and loader verification |
| Target Tests | `backend/tests/test_heatwave_targets.py` | Created | Manifest structure, threshold, and catalogue integrity tests |
| Specialist Tests | `backend/tests/test_hazard_specific_engines.py` | Updated | Added Level 1-4 baselines, decomposed modes, null-safety, and OOD tests |
| Evaluation Scripts | `scripts/evaluate_hazard_engines.py` | Updated | Heatwave and Severe Wind bootstrap evaluation routines |
| Regime Slice Scripts | `scripts/evaluate_regime_slices.py` | Updated | Regional, severity, decomposed, and lead-time slice routines |
| Report | `docs/phase-h-report.md` | Created | Certified Gate 7 completion report |
| Plan Archive | `.round2-roadmap/imple-plan/implementation_plan-H` | Created | Archived execution plan for Phase H |
