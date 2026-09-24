# Phase A Report — V3 Certification and Hazard Data Contracts

## Status: COMPLETE

- **Blueprint Gate:** Gate 0
- **Scope:** V3 Certification and Hazard Data Contracts
- **Output:** `V3_CERTIFIED`
- **Final Status:** **COMPLETE (Zero Errors)**

---

## 1. Commit, Environment, Commands and Logs

### Commit & Environment
- **Repository**: `adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2`
- **Base Commit**: `ec17284`
- **Python Runtime**: Python 3.10.11
- **Node Runtime / Tooling**: Node.js, npm, Vite v6.4.3, Vitest v3.2.7
- **Key Installed Packages**:
  - `fastapi`: 0.129.0
  - `pydantic`: 2.12.5
  - `sqlalchemy`: 2.0.52
  - `scikit-learn`: 1.7.2
  - `lightgbm`: 4.7.0
  - `joblib`: 1.5.3
  - `pandas`: 2.2.1
  - `numpy`: 1.26.4
  - `pyarrow`: 25.0.1
  - `httpx`: 0.28.1
  - `pytest`: 9.1.1

### Executed Commands & Verification Logs

1. **Environment & Dependency Verification**
   ```bash
   python scripts/verify_environment.py
   ```
   *Result*: Exit Code 0. All 4 checks PASSED.

2. **V3 Model Artifact Provenance & Git-LFS Guard**
   ```bash
   python scripts/verify_artifacts.py
   ```
   *Result*: Exit Code 0.
   - `models/v3/lightgbm_v3_challenger.joblib`: SHA-256 matched (`00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660`).
   - `models/v3/probability_calibrator_v3.joblib`: SHA-256 matched (`9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531`).
   - `models/v3/feature_names.json`: SHA-256 matched (`265cffbbd157a2b8b8b46d3702438050980043b5ed3a6a646a7969cdb9853355`), 50 canonical features verified.
   - `models/v3/V3_CERTIFIED.json`: Official certification document generated and verified.

3. **Backend Pytest Suite (Artifact Integrity, Parity, Leakage & Hazard Contracts)**
   ```bash
   python -m pytest backend/tests/test_v3_artifact_integrity.py backend/tests/test_v3_reference_parity.py backend/tests/test_leakage_integration.py backend/tests/test_hazard_contracts.py -q
   ```
   *Result*: Exit Code 0. 20 passed, 0 failed.

4. **Backend Pytest Suite (Deployment Readiness & Vercel Entrypoint)**
   ```bash
   python -m pytest backend/tests/test_deployment_readiness.py backend/tests/test_vercel_entrypoint.py -q
   ```
   *Result*: Exit Code 0. 23 passed, 0 failed.

5. **Frontend Vitest Suite**
   ```bash
   cd frontend && npx vitest run
   ```
   *Result*: Exit Code 0.
   - `src/test/Day24ProbabilisticIntelligence.test.tsx`: 4 passed
   - `src/test/ParityVerification.test.tsx`: 3 passed
   - `src/test/RiskTimeline.test.tsx`: 24 passed
   - `src/test/Dashboard.test.tsx`: 27 passed
   - **Total**: 4 test files passed (4), 58 tests passed (58), 0 failed.

6. **Frontend Production Build**
   ```bash
   cd frontend && npm run build
   ```
   *Result*: Exit Code 0. Built successfully in 8.66s.

---

## 2. Test Totals and Failed Test Names

- **Backend Pytest**: 43 passed, 0 failed across test runs
- **Frontend Vitest**: 58 passed, 0 failed
- **Total Test Count**: 101 passed, 0 failed
- **Failed Test Names**: **None (0 failed)**

---

## 3. Metrics and Confidence Intervals

### Authoritative Benchmark (Frozen V3 Incumbent)
- **Evaluation Period**: 2024-07-01 to 2024-12-31 (Out-of-time test split)
- **Rows**: 116,250 rows across 5 synoptic Indian stations
- **Bust Prevalence**: ~6.2%

| Metric | Point Estimate | 95% Confidence Interval | Source |
| :--- | :--- | :--- | :--- |
| **PR-AUC (Overall)** | 0.2110 | [0.198, 0.224] | `models/v3/V3_CERTIFIED.json` |
| **ROC-AUC** | 0.8420 | [0.824, 0.860] | Stratified q95 MAD threshold |
| **Brier Score** | 0.0538 | [0.050, 0.058] | Calibrated Isotonic Output |
| **Brier Skill Score (BSS)** | +0.0770 | [+0.062, +0.091] | Climatology Reference Baseline |
| **Expected Calibration Error (ECE)** | 0.0068 | [0.005, 0.009] | 10-bin Uniform Mass Partition |

### Stratified PR-AUC by Lead Horizon
- **Short Range (24h - 48h)**: 0.284
- **Medium Range (72h - 144h)**: 0.219
- **Extended Range (168h - 240h)**: 0.142

### Operational Hazard Availability Matrix Summary
| Hazard Family | Provider | Variables | Canonical Unit | Dissem. Latency | Status | Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Precipitation** | Open-Meteo GEFS | Precip amount, probability | `mm/24h`, fraction | 4.5h | `OPERATIONAL` | IMD Gridded Rainfall / ERA5 |
| **Tropical Cyclone** | IMD RSMC / GEFS TC | Position, max wind, Pmin | `m/s`, `Pa`, degrees | 3.0h | `PROXY` | IMD Best Track |
| **Monsoon & LPS** | GEFS / NCMRWF | Vorticity 850, shear, PW | `1/s`, `m/s`, `kg/m^2` | 6.0h | `PROXY` | ERA5 Monsoon Analysis |
| **Western Disturbance** | Open-Meteo GEFS | Z500, T-adv 700, precip | `m`, `K/s`, `mm/24h` | 5.0h | `PROXY` | IMD Western Himalayan / ERA5 |
| **Heatwave** | Open-Meteo GEFS | Tmax 2m, Tmax anomaly | `K` | 4.0h | `OPERATIONAL` | IMD Gridded Tmax / ERA5 |
| **Severe Wind** | Open-Meteo GEFS | Wind gust 10m, sustained | `m/s` | 4.5h | `OPERATIONAL` | ERA5 Hourly Gusts / AWS |

---

## 4. Leakage, Ablation, Negative-Control and Independent-Truth Results

- **Leakage Audit (`docs/leakage_report.md`)**:
  - Temporal causality barrier: $ availability\_time \le issue\_time $ enforced.
  - Ground truth sealing: ERA5, IMD rainfall/temperature, and IMD Best Track are strictly post-valid-time and inaccessible during inference.
  - Split isolation: Chronological train (2022–2023), val (2024-H1), test (2024-H2).
- **Negative Controls**:
  - Unresolvable locations (`Atlantis`) safely abstain with `INVALID_LOCATION` without falling back to fake 0% or LOW risk.
  - Invalid time order (`valid_time <= issue_time`) rejected with HTTP 422.
  - Git-LFS pointer stubs immediately detected, execution blocked with `RuntimeError`.

---

## 5. Failure Cases, Status Taxonomy, Rollback Decision and Next-Phase Authorization

- **Failure Cases**: 0 active failures.
- **Status Taxonomy**:
  - `OPERATIONAL`: Precipitation, Heatwave, Severe Wind (GEFS-supported).
  - `PROXY`: Tropical Cyclone, Monsoon/LPS, Western Disturbance (public-proxy / synthetic boundary until NCMRWF/IMD official feeds are connected).
  - `ABSTAINED`: Unresolvable locations, OOD regimes, missing ensemble members ($<25$).
  - `FUTURE`: Direct radar reflectivity assimilation and proprietary NCMRWF NEPS.
- **Rollback Decision**: **NO ROLLBACK NEEDED**. All Gate 0 completion criteria satisfied.
- **Next-Phase Authorization**: **AUTHORIZED TO PROCEED TO PHASE B ("Reliability core and benchmark ladder" - Gate 1)**.
