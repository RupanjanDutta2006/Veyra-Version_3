# VEYRA VERSION-3: FRAME 04 EXECUTION & VERIFICATION REGISTER

**Timestamp**: 2026-09-24T15:55:00Z  
**Target**: Project Veyra Version-3 (Authoritative Operational Baseline)  
**Execution Context**: Frame 04 Executor (Phase 07: Calibration & Specialist Containment; Phase 08: Reliability & Spatial Intelligence)  

---

## 1. PHASE PROGRESS LOG

| Phase | Description | Scope | Status | Notes |
|---|---|---|---|---|
| **Phase 07** | Calibration, OOD Diagnostics, Abstention & Specialist Containment | Isotonic calibration verification ($P(\text{BUST}) \in [0.0, 1.0]$), physical OOD Mahalanobis distance checks, safe abstention triggering, and strict containment of the 6 physical hazard specialists under Gate G8. | **100% COMPLETE** | Non-parametric isotonic calibrator verified ($\text{ECE} \le 0.0068$); 6 hazard specialists strictly isolated as `FORMULA_BASELINE`/`EXPERIMENTAL` with zero unvalidated production promotions. |
| **Phase 08** | Reliability Intelligence, Ensemble Dispersion & Spatial Intelligence | GEFS 31-member ensemble variance tracking, multi-provider disagreement metrics, failure motif classification, and spatial orographic boundary validations. | **100% COMPLETE** | Multi-provider resilience operational; terrain features (roughness, elevation, coast distance) verified; 98/98 focused tests passed. |

---

## 2. PHASE 07 AUDIT: CALIBRATION, OOD & SPECIALIST CONTAINMENT

### 1. Probability Calibration & Reliability Metrics
- **Calibrator Binary**: `models/v3/probability_calibrator_v3.joblib` (SHA-256: `9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531`)
- **Algorithm**: `sklearn.isotonic.IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds='clip')`
- **Monotonicity & Support**: Monotonically transforms raw LightGBM log-odds into well-calibrated posterior bust probabilities $P(\text{BUST}) \in [0.0, 1.0]$.
- **Evaluation Benchmarks (Out-Of-Time Test Set — 116,250 rows)**:
  - **Brier Score**: $0.0538$
  - **Brier Skill Score (BSS)**: $0.0770$ (relative to climatological prevalence $0.062$)
  - **Expected Calibration Error (ECE)**: $0.0068$ ($< 0.01$ threshold)
  - **ROC-AUC**: $0.8420$ | **PR-AUC**: $0.2110$

### 2. Physical OOD Diagnostics & Safe Abstention Taxonomy
- **Mahalanobis Distance Guard**: Computes multivariate distance across the 50 canonical physical features against the training covariance matrix.
- **Kinematic & Thermodynamic Bounds**:
  - $T_{2m} \notin [200.0, 340.0]\text{ K}$ $\rightarrow$ `ABSTAIN_OOD_EXTREME_CLIMATE`
  - $\text{CAPE} > 6000\text{ J/kg}$ or $\text{RH} > 100\%$ $\rightarrow$ `ABSTAIN_OOD_THERMODYNAMIC`
  - Elevation / Terrain outside supported orography $\rightarrow$ `ABSTAIN_OOD_UNSUPPORTED_OROGRAPHY`
  - Location outside 25 benchmark stations $\rightarrow$ `ABSTAIN_OUT_OF_SCOPE_LOCATION`
  - Lead time $> 384\text{h}$ $\rightarrow$ `ABSTAIN_OUT_OF_SCOPE_LEAD_TIME`

### 3. Hazard Specialist Containment & Promotion Boundaries (Gate G8)
All 6 domain specialists operate strictly as **deterministic formula baselines and physics heuristics** and are forbidden from overriding the V3 Challenger model in production:

| Specialist Module | Status / Nature | Active in Production | PR-AUC Claim Policy |
|---|---|---|---|
| **Precipitation Specialist** | `FORMULA_BASELINE` (Deterministic) | **FALSE** | Pilot Evidence Package archived in `docs/science-evidence/` |
| **Cyclone Specialist** | `FORMULA_BASELINE` (Deterministic) | **FALSE** | Physics-rule heuristic; empirical artifact pending |
| **Monsoon LPS Specialist** | `FORMULA_BASELINE` (Deterministic) | **FALSE** | Physics-rule heuristic; empirical artifact pending |
| **Western Disturbance** | `FORMULA_BASELINE` (Deterministic) | **FALSE** | Physics-rule heuristic; empirical artifact pending |
| **Heatwave Specialist** | `FORMULA_BASELINE` (Deterministic) | **FALSE** | Physics-rule heuristic; empirical artifact pending |
| **Severe Wind Specialist** | `QUARANTINED` (No Artifact) | **FALSE** | Requires Doppler radar training dataset |
| **Spatial Reliability Engine** | `EXPERIMENTAL` (Deterministic) | **FALSE** | Graph neighbor propagation prototype |
| **Cross-System Transfer** | `EXPERIMENTAL` (Deterministic) | **FALSE** | Upstream NWP shift prototype |

*Verification*: `scripts/check_production_specialists.py` and `scripts/validate_specialist_evidence.py` confirm **0 uncertified specialists in the production inference pipeline**.

---

## 3. PHASE 08 AUDIT: RELIABILITY, MULTI-PROVIDER & SPATIAL INTELLIGENCE

### 1. Ensemble Dispersion & Spread Calculations
- **Source**: 31-member NOAA GEFS ensemble via Open-Meteo API.
- **Spread Metrics**: Computes ensemble mean, standard deviation, spread variance, p10, p90, and skewness across all core atmospheric variables (temperature, precipitation, wind speed, relative humidity, CAPE, CIN, geopotential height).
- **Lead-Time Monotonicity**: Verifies that ensemble dispersion widens realistically with increasing forecast horizon ($24\text{h} \rightarrow 384\text{h}$).

### 2. Multi-Provider Disagreement & Resilience
- **Cross-Provider Contract**: Evaluates normalized divergence between GEFS, ECMWF IFS proxies, and regional NWP feeds.
- **Graceful Degradation**: If secondary provider telemetry fails or is unavailable, the system transparently degrades to single-provider GEFS mode with explicit metadata disclosure (`trust_state: CAUTION_DEGRADED_ENSEMBLE`) rather than failing or hallucinating.

### 3. Spatial Intelligence & Topographical Invariants
- **Geographic Feature Extraction**: Validated continuous static features:
  - `surface_roughness` ($z_0 \ge 0$)
  - `elevation` (meters above sea level)
  - `distance_to_coast` ($\text{km} \ge 0$)
  - `urban_fraction` ($\in [0.0, 1.0]$)
- **Topographical Consistency**: Preserves exact coordinate-to-grid mapping across all 25 benchmark stations.

---

## 4. TEST METRICS & GATE VERIFICATION

| Verification Layer | Target Scope | Result | Status |
|---|---|---|---|
| **Phase 6 Gate** (`scripts/gate_test_phase6.py`) | Gate G8 (Specialist Containment & Promotion Boundaries) | **24 passed in 2.28s** | **PASS (100%)** |
| **Specialist Boundary Audit** (`check_production_specialists.py`) | 10 specialists in registry | **10/10 compliant (0 uncertified in prod)** | **PASS (100%)** |
| **Specialist Evidence Audit** (`validate_specialist_evidence.py`) | Ledger & Precipitation pilot package | **10 entries verified** | **PASS (100%)** |
| **Focused Phase 7 & 8 Tests** (`pytest`) | 7 test modules (98 tests) | **98 passed / 98 total (15.50s)** | **PASS (100%)** |
| **Release Gates** (`run_release_gates.py --require-all`) | 6 Mandatory Release Gates | **6/6 Passed (Exit Code 0, 6.64s)** | **PASS (100%)** |
| **Full Backend Test Suite** (`pytest`) | All backend tests | **954 passed / 954 total** | **PASS (100%)** |
| **Frontend Test Suite** (`vitest`) | All frontend tests | **111 passed / 111 total** | **PASS (100%)** |

---

## 5. CHANGE LOG

1. `brain/frame_04.md`: Created Frame 04 execution & verification register detailing Phase 07 (Calibration, OOD, Gate G8 Specialist Containment) and Phase 08 (Reliability Intelligence, Multi-Provider & Spatial features).
