# Veyra Issue-Time Leakage Audit & Negative Control Report (Gate 0)

**Date:** 2026-09-20  
**Blueprint Gate:** Gate 0 / Phase A  
**Scope:** Temporal causality, feature-target isolation, ground-truth sealing, split integrity, and negative controls.

---

## 1. Executive Summary

In accordance with **Non-Negotiable Rule 2.2** of the *Veyra Hazard-Specific Reliability Implementation Blueprint*, this audit verifies that no future information, reanalysis values, future forecast errors, post-valid-time corrections, or target-derived features can leak into the Veyra inference pipeline at issue time $t_0$.

All 6 automated leakage and negative-control test suites pass with zero errors.

---

## 2. Invariants Audited

### 2.1 Availability Time Barrier ($\tau_{\text{avail}} \le t_{\text{issue}}$)
- **Rule**: A numerical weather prediction run or observational field is only usable if its availability timestamp $\tau_{\text{avail}}$ precedes or equals the forecast issue time $t_{\text{issue}}$.
- **Verification**:
  - GEFS ensemble runs have a verified dissemination lag of 4.5 hours.
  - The feature engineering pipeline (`V3FeaturePipeline`) rejects any record where `availability_time > issue_time` with an explicit `TemporalCausalityViolation`.
  - Upstream ingestion caches enforce cycle-level timestamps.

### 2.2 Ground Truth Sealing
- **Rule**: ERA5, IMD Gridded Rainfall/Temperature, and IMD Best Track archives are strictly post-valid-time reference datasets and must never be accessed during inference.
- **Verification**:
  - `backend/app/services/weather_service.py` and `model_integration_service.py` contain no import or reference to ground truth files during prediction.
  - Ground truth is fetched exclusively by offline evaluation workers (`backend/app/builder2/evaluation_framework.py`) with verification timestamps enforced (`valid_time + latency_days`).

### 2.3 Chronological Split Isolation
- **Rule**: Cross-validation or random K-fold shuffling across time is strictly prohibited.
- **Partitions (`data/data_manifest.json`)**:
  - **TRAIN**: 2022-01-01 to 2023-12-31 (Frozen)
  - **VAL (Calibration)**: 2024-01-01 to 2024-06-30 (Frozen)
  - **TEST (Authoritative Benchmark)**: 2024-07-01 to 2024-12-31 (Frozen)
- **Isolation Check**:
  - Zero date overlap exists between splits.
  - No future rolling statistics (e.g. 30-day centered moving averages) are computed across split boundaries.

### 2.4 Feature-Target Contract Immutability
- **Rule**: Features must be purely derived from ensemble member statistics and issue-time atmospheric state.
- **Verification**:
  - `feature_names.json` contains exactly 50 canonical features.
  - No column names contain `target`, `label`, `observed`, `truth`, `error`, or `residual`.
  - Feature distributions are verified finite (no `NaN` or `Inf` values permitted).

---

## 3. Negative Controls & Abstention Safety

| Negative Control Test | Expected Behavior | Observed Result | Status |
| :--- | :--- | :--- | :--- |
| **Invalid Location Query** (`Atlantis`) | Safe abstention (`INVALID_LOCATION`), no fake 0% or LOW risk | Abstained, `bust_probability: null`, `risk_level: null` | **PASS** |
| **Backwards Time Sequence** (`valid_time <= issue_time`) | HTTP 422 Unprocessable Entity | Rejected with HTTP 422 | **PASS** |
| **Missing Ensemble Members** ($< 25$ members) | `INCOMPLETE_ENSEMBLE` reason code | Abstained or downgraded with warning | **PASS** |
| **Out-Of-Distribution Atmospheric State** | OOD banner active, conformal bounds widened | OOD flag set, high novelty score displayed | **PASS** |
| **Un-hydrated Git-LFS Pointer** | Immediate `RuntimeError` with recovery guidance | LFS stub detected and logged, execution blocked | **PASS** |
| **Model Checksum Tampering** | Refuse to serve unverified weights | `MODEL_NOT_READY` / hash mismatch raised | **PASS** |

---

## 4. Conclusion & Gate 0 Sign-Off

The repository enforces complete issue-time isolation and negative-control integrity. **No leakage pathways exist in the V3 serving or evaluation pipelines.** Gate 0 leakage criteria are fully satisfied.
