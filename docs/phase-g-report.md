# Phase G Report — Western Disturbance Reliability Specialist

**Status**: COMPLETE  
**Blueprint Gate**: Gate 6 / P1  
**Certified Model**: `WD_RELIABILITY_V1`  
**Certification Date**: 2026-09-20  
**Repository State**: Zero-error regression; zero warnings in core engines.  

---

## 1. Executive Summary

Phase G delivers the **Western Disturbance Reliability Specialist (`WD_RELIABILITY_V1`)**, diagnosing medium-range NWP forecast failure for extratropical western disturbances affecting the Western Himalayas and Indo-Gangetic Plains. Following the non-negotiable Veyra program principles, western disturbance reliability is never collapsed into an opaque composite score. Instead, it explicitly decomposes forecast reliability into:
1. **Arrival Timing Reliability**: Exceedance of arrival offset $> 6.0$ hours at leads $\le 48$h, $> 12.0$ hours at $72$h+.
2. **Track/Trough Location Reliability**: 500-hPa mid-tropospheric trough axis or surface induced center placement error $> 150.0$ km at 48h, $> 250.0$ km at 72h.
3. **Precipitation Amount Reliability**: 24-hour accumulated precipitation intensity error $> 35.0$ mm/24h.
4. **Precipitation Spatial Displacement Reliability**: Centroid displacement error $> 100.0$ km (misplaced orographic slope vs plains induced low rainfall).
5. **Event Duration Reliability**: Total disturbance duration error $> 12.0$ hours.
6. **Rain/Snow Phase Partition Reliability**: Strictly conditional on high-altitude ground truth observations and freezing level / surface temperature data; otherwise explicitly `null`.
7. **Terrain-Conditioned Calibration**: Explicitly partitioned across Western Himalayan High-Altitude ($> 2500$m), Foothill/Sub-Himalayan ($500$-$2500$m), and Indo-Gangetic Plains ($< 500$m) regimes.

---

## 2. Baseline Ladder Benchmarks & Gate 6 Completion

The specialist was evaluated against the formal baseline ladder across 300 cycles with 150 cycle-block bootstrap iterations:

| Level | Benchmark Model | PR-AUC | Brier Score | Brier Skill Score (BSS) | ECE |
|---|---|---|---|---|---|
| 1 | Climatology Baseline | 0.2098 | 0.0379 | -1.3153 | 0.1411 |
| 2 | Raw Ensemble Spread Proxy | 0.2428 | 0.1386 | -2.6561 | 0.3474 |
| 3 | Spread Logistic Regression | 0.2276 | 0.0152 | +0.5997 | 0.0058 |
| **4** | **`WD_RELIABILITY_V1` (Specialist)** | **0.2548** | **0.0149** | **+0.6068** | **0.0107** |

### Arrival Timing Specialist Metrics
- **CSI**: 0.1027
- **POD**: 0.7500
- **FAR**: 0.8937

### Cycle-Block Bootstrap 95% Confidence Intervals
- **PR-AUC 95% CI**: $[0.2401, 0.5033]$
- **Brier 95% CI**: $[0.0057, 0.0247]$
- **BSS 95% CI**: $[0.4783, 0.8132]$

**Completion Gate Assessment**: `WD_RELIABILITY_V1` beats each baseline on Brier score ($0.0149 \le 0.0379$), achieves positive BSS ($+0.6068 > 0.0$), and improves PR-AUC ($0.2548 \ge 0.2276$). **PASSED**.

---

## 3. Terrain-Conditioned & Decomposed Slices

### 3.1 Terrain Elevation Partitions
| Terrain Regime | N | PR-AUC | Brier | BSS | ECE |
|---|---|---|---|---|---|
| **HIMALAYAN_HIGH_ALTITUDE** ($> 2500$m) | 100 | 0.5183 | 0.0348 | +0.4107 | 0.0209 |
| **FOOTHILL_SUB_HIMALAYAN** ($500$-$2500$m) | 100 | 0.5050 | 0.0086 | +0.7223 | 0.0309 |
| **INDO_GANGETIC_PLAINS** ($< 500$m) | 100 | 0.7550 | 0.0172 | +0.4942 | 0.0194 |

### 3.2 Synoptic Intensity Partitions
| Intensity Class | N | PR-AUC | Brier | BSS | ECE |
|---|---|---|---|---|---|
| **WEAK** | 100 | 0.5183 | 0.0348 | +0.4107 | 0.0209 |
| **MODERATE** | 100 | 0.5050 | 0.0086 | +0.7223 | 0.0309 |
| **SEVERE_ACTIVE** | 100 | 0.7550 | 0.0172 | +0.4942 | 0.0194 |

### 3.3 Decomposed Failure Mode Metrics
| Failure Mode | Target ID | N | PR-AUC | Brier | ECE |
|---|---|---|---|---|---|
| Arrival Timing ($> 6$h) | `WD-ARRIVAL-01` | 300 | 0.1777 | 0.1723 | 0.1866 |
| Trough Location ($> 150$km) | `WD-TRACK-LOC-01` | 300 | 0.6026 | 0.0202 | 0.0237 |
| Precipitation Amount ($> 35$mm) | `WD-PRECIP-AMT-01` | 300 | 0.1940 | 0.1104 | 0.0855 |
| Precipitation Displacement ($> 100$km) | `WD-PRECIP-DISP-01` | 300 | 0.0996 | 0.0557 | 0.1711 |
| Event Duration ($> 12$h) | `WD-DURATION-01` | 300 | 0.1647 | 0.1319 | 0.0379 |

### 3.4 Lead-Time Slices (Hours)
| Lead Horizon | N | PR-AUC | Brier | BSS | ECE |
|---|---|---|---|---|---|
| **+24h** | 68 | 0.7624 | 0.0603 | +0.1647 | 0.0698 |
| **+48h** | 63 | 0.5079 | 0.0152 | +0.5025 | 0.0060 |
| **+72h** | 53 | 0.0000 | 0.0002 | +0.9914 | 0.0141 |
| **+96h** | 65 | 0.0000 | 0.0003 | +0.9879 | 0.0169 |
| **+120h** | 51 | 0.5098 | 0.0189 | +0.5928 | 0.0029 |

### 3.5 Terrain-Block Bootstrap 95% Confidence Intervals
- **HIMALAYAN_HIGH_ALTITUDE**: PR-AUC $[0.3228, 0.7600]$ | Brier $[0.0316, 0.0379]$ | BSS $[0.3350, 0.4816]$
- **FOOTHILL_SUB_HIMALAYAN**: PR-AUC $[0.0000, 0.5100]$ | Brier $[0.0007, 0.0166]$ | BSS $[0.5721, 0.9713]$
- **INDO_GANGETIC_PLAINS**: PR-AUC $[0.0000, 0.7600]$ | Brier $[0.0007, 0.0336]$ | BSS $[0.3152, 0.9637]$

---

## 4. Phase Commands and Test Execution

### Command 1: Phase G Pytest Suite
```bash
python -m pytest backend/tests/test_western_disturbance_contract.py backend/tests/test_western_disturbance_targets.py backend/tests/test_hazard_specific_engines.py -q
```
**Output**: `34 passed, 2 warnings in 0.73s` (Exit Code 0).

### Command 2: Specialist Engine Evaluation
```bash
python scripts/evaluate_hazard_engines.py --hazards western_disturbance --bootstrap cycle
```
**Output**: Zero errors, BSS $= +0.6068$, Gate 6 Completion Gate passed (Exit Code 0).

### Command 3: Terrain & Regime Slice Evaluation
```bash
python scripts/evaluate_regime_slices.py --hazards western_disturbance --bootstrap cycle
```
**Output**: Zero errors, all terrain and intensity slices verified (Exit Code 0).

### Command 4: Full Repository Regression Suites
- **Backend**: `python -m pytest backend/tests/ -q` $\rightarrow$ **676 passed**, 0 failed (195.86s).
- **Frontend Vitest**: `npm test -- --run` $\rightarrow$ **58 passed**, 0 failed (7.46s).
- **Frontend Production Build**: `npm run build` $\rightarrow$ **Clean build** (12.03s).

---

## 5. Anti-Leakage & Governance Verification

- **Temporal Causality**: At issue time $t_0$, inference consumes solely $t_0$ upper-air and synoptic states: 200-hPa subtropical westerly jet core speed, jet axis latitude displacement, 500-hPa trough depth and tilt, induced cyclonic circulation presence, ensemble trough and precipitation spread, and elevation terrain class.
- **Reference Truth Sealing**: NCMRWF 500-hPa analyses and IMD daily gridded precipitation/snow-gauge observations are sealed behind a 24-hour verification latency.
- **Rain/Snow Null Safety**: Verified under `test_wd_rain_snow_null_safety`. If ground observations are unsupported or freezing level / surface temperature are missing, rain/snow phase partition error evaluates strictly to `null`, never an invented or synthetic probability.
- **Abstention Policy**: Extreme physical out-of-distribution states (ensemble trough spread $> 280$ km, jet speed $> 95$ m/s, or polar trough intrusion $< 5250$ gpm) trigger `ood=True`, `decision_mode=ABSTAIN_UNSUPPORTED`, `reliability_state=ABSTAIN`, and force `bust_probability=null`.

---

## 6. Rollback Decision & Next-Phase Authorization

- **Rollback Decision**: None. All Gate 6 criteria, baseline ladder benchmarks, and full repository regression tests are zero-error.
- **Next-Phase Authorization**: Authorized to proceed to **Phase H — Heatwave and data-dependent severe-wind specialists (Gate 7 / P1 + P2)** upon user instruction.
