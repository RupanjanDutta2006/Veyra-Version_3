# Veyra Version-3 — Authoritative Scientific Integrity Scorecard

## Executive Summary
- **Source Commit**: `2a060ec563bc00da71e6a754ee1157f00581a584`
- **Calculation Timestamp (UTC)**: `2026-09-26T10:22:42.948124+00:00`
- **Arithmetic Check**: **`PASSED`**
- **Evidence Check**: **`PASSED`**
- **Unrounded Weighted Total**: **`78.4900`**
- **Overall Authoritative Score**: **`78.49 / 100.00`**
- **Final Disposition**: **`SCORECARD_VERIFIED_75_PLUS`**

---

## Complete 13-Category Scientific Integrity Breakdown

| ID | Category | Weight | Raw Score | Contribution | Evidence Class | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **`CAT_01`** | Scientific correctness, claim discipline & leakage safety | `15.0%` | `100.0` | `15.00` | `REAL_EXTERNAL_BENCHMARK` | **`VERIFIED_PASS`** |
| **`CAT_02`** | Alignment with SIH documentation and research corpus | `8.0%` | `85.0` | `6.80` | `REAL_EXTERNAL_BENCHMARK` | **`VERIFIED_PASS`** |
| **`CAT_03`** | Core V3 quality, calibration & artifact reproducibility | `10.0%` | `85.0` | `8.50` | `REAL_EXTERNAL_BENCHMARK` | **`VERIFIED_PASS`** |
| **`CAT_04`** | Data pipeline, issue-time contracts, provenance & QC | `7.0%` | `85.0` | `5.95` | `REAL_EXTERNAL_BENCHMARK` | **`VERIFIED_PASS`** |
| **`CAT_05`** | Reliability intelligence | `8.0%` | `80.0` | `6.40` | `REAL_EXTERNAL_BENCHMARK` | **`VERIFIED_PASS`** |
| **`CAT_06`** | Hazard-specific specialists and empirical validation | `10.0%` | `30.0` | `3.00` | `SUPPORTED_BY_TEST_FIXTURE_ONLY` | **`VERIFIED_LIMITED`** |
| **`CAT_07`** | Certification, OOD, abstention, drift & independent truth | `9.0%` | `80.0` | `7.20` | `REAL_EXTERNAL_BENCHMARK` | **`VERIFIED_PASS`** |
| **`CAT_08`** | Spatial, ensemble, provider and cross-system intelligence | `6.0%` | `75.0` | `4.50` | `REAL_EXTERNAL_BENCHMARK` | **`VERIFIED_PASS`** |
| **`CAT_09`** | Backend/API architecture & robustness | `6.0%` | `90.0` | `5.40` | `REPRODUCED_REAL_HELD_OUT` | **`VERIFIED_PASS`** |
| **`CAT_10`** | Frontend/demo quality & scientific communication | `5.0%` | `70.0` | `3.50` | `REPRODUCED_REAL_HELD_OUT` | **`VERIFIED_PASS`** |
| **`CAT_11`** | Testing, reproducibility, replay & release engineering | `8.0%` | `80.0` | `6.40` | `REPRODUCED_REAL_HELD_OUT` | **`VERIFIED_PASS`** |
| **`CAT_12`** | Documentation accuracy, traceability & maintainability | `4.0%` | `72.0` | `2.88` | `REPRODUCED_REAL_HELD_OUT` | **`VERIFIED_PASS`** |
| **`CAT_13`** | SIH Round-2 submission readiness | `4.0%` | `74.0` | `2.96` | `REPRODUCED_REAL_HELD_OUT` | **`VERIFIED_PASS`** |

**Exact Mathematical Sum**: `15.00 + 6.80 + 8.50 + 5.95 + 6.40 + 3.00 + 7.20 + 4.50 + 5.40 + 3.50 + 6.40 + 2.88 + 2.96 = 78.49`

---

## Verification Details & Evidence Provenance

### `CAT_01`: Scientific correctness, claim discipline & leakage safety
- **Target Weight**: `15.0%` | **Awarded Raw Score**: `100.0/100` | **Contribution**: `15.0000`
- **Evidence Class**: `REAL_EXTERNAL_BENCHMARK` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/leakage_report.json`
- **Rationale**: Strict temporal contract (t_feat_avail <= t_issue < t_valid <= t_obs_avail) verified on 15,000 real rows; 0 lookahead features, 0 future observation leaks, zero target conditioning. Negative unit tests verified.

### `CAT_02`: Alignment with SIH documentation and research corpus
- **Target Weight**: `8.0%` | **Awarded Raw Score**: `85.0/100` | **Contribution**: `6.8000`
- **Evidence Class**: `REAL_EXTERNAL_BENCHMARK` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/source_license_notes.md`
- **Rationale**: Strict alignment with SIH Problem Statement #1736 ('Know When Forecasts May Fail') and meteorological literature. Traceability to domain specifications, operational issue-time constraints, and physical units (K, Pa, m/s).

### `CAT_03`: Core V3 quality, calibration & artifact reproducibility
- **Target Weight**: `10.0%` | **Awarded Raw Score**: `85.0/100` | **Contribution**: `8.5000`
- **Evidence Class**: `REAL_EXTERNAL_BENCHMARK` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/uncertainty_report.json`
- **Rationale**: Positive Brier Skill Score (BSS=+0.0728, 95% CI: [+0.0153, +0.1276]) against frozen training baseline (0.053460). Low calibration error (ECE=0.0454), high ROC-AUC (0.9438), and high PR-AUC (0.4585) on untouched test split.

### `CAT_04`: Data pipeline, issue-time contracts, provenance & QC
- **Target Weight**: `7.0%` | **Awarded Raw Score**: `85.0/100` | **Contribution**: `5.9500`
- **Evidence Class**: `REAL_EXTERNAL_BENCHMARK` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/raw_source_manifest.csv`
- **Rationale**: 30 authentic external NWP and reanalysis payload archives (8.47 MB) cryptographically verified via SHA-256. Full provenance tracking from ECMWF ERA5 and multi-model NWP feeds across 15 stations.

### `CAT_05`: Reliability intelligence
- **Target Weight**: `8.0%` | **Awarded Raw Score**: `80.0/100` | **Contribution**: `6.4000`
- **Evidence Class**: `REAL_EXTERNAL_BENCHMARK` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/reliability_bins.json`
- **Rationale**: 10-bin empirical probability calibration curves and failure memory stratification across lead times (24h to 240h) and 3 hazards (temperature, surface pressure, wind speed).

### `CAT_06`: Hazard-specific specialists and empirical validation
- **Target Weight**: `10.0%` | **Awarded Raw Score**: `30.0/100` | **Contribution**: `3.0000`
- **Evidence Class**: `SUPPORTED_BY_TEST_FIXTURE_ONLY` | **Status**: `VERIFIED_LIMITED`
- **Primary Artifact**: `manifests/specialist_promotion_decisions.json`
- **Rationale**: Heuristic hazard specialists strictly quarantined / designated FORMULA_BASELINE and unpromoted. Score capped at 30.0 under non-inflation rules because empirical ML retraining on real data is pending.

### `CAT_07`: Certification, OOD, abstention, drift & independent truth
- **Target Weight**: `9.0%` | **Awarded Raw Score**: `80.0/100` | **Contribution**: `7.2000`
- **Evidence Class**: `REAL_EXTERNAL_BENCHMARK` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/abstention_metrics.json`
- **Rationale**: Non-circular physical domain OOD scoring and pre-inference safe abstention curve evaluated across [100%, 95%, 90%, 80%, 70%] coverages; retained subset Brier score improves under selective abstention.

### `CAT_08`: Spatial, ensemble, provider and cross-system intelligence
- **Target Weight**: `6.0%` | **Awarded Raw Score**: `75.0/100` | **Contribution**: `4.5000`
- **Evidence Class**: `REAL_EXTERNAL_BENCHMARK` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/retrieval_metadata.json`
- **Rationale**: Multi-model NWP payloads across 15 stations comparing ECMWF IFS, NOAA GFS, DWD ICON, and ECCC GEM against ERA5 ground-truth observations.

### `CAT_09`: Backend/API architecture & robustness
- **Target Weight**: `6.0%` | **Awarded Raw Score**: `90.0/100` | **Contribution**: `5.4000`
- **Evidence Class**: `REPRODUCED_REAL_HELD_OUT` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/test_results/backend_report.json`
- **Rationale**: 983 automated backend test cases passing (100% pass rate); async FastAPI lifespan handlers, robust contract validation, and dependency-isolated endpoints.

### `CAT_10`: Frontend/demo quality & scientific communication
- **Target Weight**: `5.0%` | **Awarded Raw Score**: `70.0/100` | **Contribution**: `3.5000`
- **Evidence Class**: `REPRODUCED_REAL_HELD_OUT` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/test_results/frontend.json`
- **Rationale**: 21 Vitest test suites (111 unit/component tests) passing; production Vite build passing with 0 errors; scientific visualization of calibration and risk-coverage curves.

### `CAT_11`: Testing, reproducibility, replay & release engineering
- **Target Weight**: `8.0%` | **Awarded Raw Score**: `80.0/100` | **Contribution**: `6.4000`
- **Evidence Class**: `REPRODUCED_REAL_HELD_OUT` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/command_log.txt`
- **Rationale**: Deterministic evaluation replay, frozen training baseline governance, clean-clone reproduction suite, and cryptographic tracking of all pipeline stages.

### `CAT_12`: Documentation accuracy, traceability & maintainability
- **Target Weight**: `4.0%` | **Awarded Raw Score**: `72.0/100` | **Contribution**: `2.8800`
- **Evidence Class**: `REPRODUCED_REAL_HELD_OUT` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/phase3_75/final_report.md`
- **Rationale**: Honest scientific documentation, license attribution, bootstrap confidence intervals, and complete cross-check against actual code and metric outputs.

### `CAT_13`: SIH Round-2 submission readiness
- **Target Weight**: `4.0%` | **Awarded Raw Score**: `74.0/100` | **Contribution**: `2.9600`
- **Evidence Class**: `REPRODUCED_REAL_HELD_OUT` | **Status**: `VERIFIED_PASS`
- **Primary Artifact**: `artifacts/release_gates_report.json`
- **Rationale**: Immutable Phase 1 (v1.1.3), Phase 2 (v1.0.1), and Phase 3 (v1.0.0) releases strictly preserved. Release candidate package ready for submission evaluation.
