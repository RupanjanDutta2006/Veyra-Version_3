# Phase 01 — Baseline Truth Snapshot & Audit Evidence

**Audit Timestamp**: `2026-09-22T14:15:00+05:30`  
**Audited SHA**: `c9903fa962179d645eec993c150364e697d98ebe`  
**Repository Branch**: `main`  
**Working Tree Status**: Clean tracked tree  
**Tracked Files**: 630 files  

---

## 1. Executive Baseline Summary

This baseline snapshot independently executes and records the exact starting evidence of `Veyra-Know-When-Forecasts-May-Fail-VERSION-3` prior to roadmap modifications.

| Verification Dimension | Result / Evidence | Status |
|---|---|---|
| Git HEAD Commit | `c9903fa962179d645eec993c150364e697d98ebe` | **VERIFIED** |
| Working Tree Cleanliness | `git status --short` output empty | **CLEAN** |
| V3 ML Model (`lightgbm_v3_challenger.joblib`) | SHA256: `00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660` (1,046,844 bytes) | **PASS** |
| V3 Calibrator (`probability_calibrator_v3.joblib`) | SHA256: `9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531` (2,791 bytes) | **PASS** |
| V3 Feature Schema (`feature_names.json`) | SHA256: `265cffbbd157a2b8b8b46d3702438050980043b5ed3a6a646a7969cdb9853355` (1,114 bytes, 50 features) | **PASS** |
| Artifact Chain Verifier (`scripts/verify_artifacts.py`) | All 3 artifact hashes match manifest, joblib loads successfully | **PASS** |
| Backend Pytest Suite (`pytest backend/tests`) | **891 collected, 891 passed, 0 failed, 53 warnings** (176.65s runtime) | **PASS** |
| Frontend Vitest Suite (`npm test -- --run`) | **9 test files, 111 passed, 0 failed** (16.16s runtime) | **PASS** |
| Frontend Production Build (`npm run build`) | `tsc && vite build` completed successfully (`dist/` generated) | **PASS** |
| ML Smoke Test (`scripts/smoke_test_ml.py`) | Circular import error (`backend.app.ml.artifacts` <-> `backend.app.services`) | **FAIL** (Known) |
| Submission Smoke (`scripts/run_submission_smoke.py`) | Module import error (`ModuleNotFoundError: No module named 'backend'`) | **FAIL** (Known) |
| Master Gates Runner (`scripts/run_all_master_gates.py`) | External workspace path dependency in `gate_test_step1.py` | **FAIL** (Known) |
| Release Gates Runner (`scripts/run_release_gates.py`) | 3 of 5 gates fail: G1/G3 path error, G11 CLI argument error, G15 path error | **FAIL** (Known) |
| Builder-2 Smoke (`scripts/smoke_test_builder2.py`) | Missing parquet file `data/training/training_dataset.parquet` | **FAIL** (Known) |
| Final Smoke (`scripts/smoke_test_final.py`) | Assertion mismatch on TrustState (`MODERATE_CONFIDENCE` vs `HIGH_CONFIDENCE`) | **FAIL** (Known) |

---

## 2. Artifact SHA-256 Inventory (`models/v3/*`)

All 14 model artifacts and manifests located in `models/v3/` have been cryptographically hashed and verified:

```text
9d4d7690a95444324f592e487de4ce32480f537d06f5c5914dfb686e81f1cc60  artifact_manifest.json
a044f4c4187aa2f423ec1509c1e589478a42c2260f4a81464a83fb455242a1d4  CYCLONE_RELIABILITY_V1.json
265cffbbd157a2b8b8b46d3702438050980043b5ed3a6a646a7969cdb9853355  feature_names.json
1d30c15e1f2f210fe547ffc9958b89c27fa5171cf9debd10ab8500a3da0f5c81  HEATWAVE_RELIABILITY_V1.json
00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660  lightgbm_v3_challenger.joblib
8be4f0136be113c7011a6bb1321e6aef739782c4fca413a34d36fe29ee342190  MONSOON_RELIABILITY_V1.json
c5cba5eb0bff1972aa707dc2fe3ff3fcea6444c9c49f5a4ddb4034874986c08c  PRECIP_RELIABILITY_V1.json
9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531  probability_calibrator_v3.joblib
193b44ebd83744b3f458aba60108a239365da365d9e986c7083b42bb8fe8b129  SPATIAL_RELIABILITY_V1.json
b90492a546e03966f8734191545375819fe7ae9aae4bff765733ef0d83d58c11  training_manifest.json
efd14410b2b3d19a10c73bbbf34d49b9b884915e5c7cf02352abf9883dd1ef23  V3_CERTIFIED.json
85e8f87f3b43402381537a048830ae176316e4bda5479590d48b1be1e907b2ac  v3_comprehensive_evaluation.json
542a026533e4d9e6311b7032b2bda796377e7c6573b9582d6bed3b086d82e52d  v3_evaluation_manifest.json
1b8c966205662871f52ea6b1ad099a859e70db220ca94cc97110acdd543e8688  WD_RELIABILITY_V1.json
```

---

## 3. Test Suites Exact Counts

### Backend (Python / Pytest)
- **Command**: `python -m pytest backend/tests -q`
- **Collected**: 891 items
- **Passed**: 891
- **Failed**: 0
- **Errors**: 0
- **Warnings**: 53 (primarily library deprecation warnings from sklearn unpickling and pydantic index interpretation)
- **Execution Duration**: 176.65s (~2m 56s)

### Frontend (TypeScript / React / Vitest)
- **Command**: `npm test --prefix frontend -- --run`
- **Test Files**: 9 passed (9)
- **Tests**: 111 passed (111)
- **Failed**: 0
- **Execution Duration**: 16.16s

### Frontend Compilation
- **Command**: `npm run build --prefix frontend`
- **Output**: `dist/index.html` (1.21 kB), `dist/assets/index-ThlVVUh7.css` (35.24 kB), `dist/assets/index-BtMrqfHs.js` (768.63 kB)
- **Status**: Zero compiler errors, production bundle generated.

---

## 4. Itemized Known Failures & Root Causes

The following 6 defects prevent automated release gates from passing out-of-the-box and are explicitly documented for attributable repair in subsequent roadmap phases:

### Failure 1: ML Smoke Circular Import
- **Command**: `python scripts/smoke_test_ml.py`
- **Exception**: `ImportError: cannot import name 'ModelArtifactManager' from partially initialized module 'backend.app.ml.artifacts' (most likely due to a circular import)`
- **Cycle**: `artifacts.py` -> `features.py` -> `services/__init__.py` -> `evaluation_service.py` -> `model_integration_service.py` -> `model_service.py` -> `artifacts.py`
- **Target Resolution Phase**: Phase 04

### Failure 2: Submission Smoke Module Resolution
- **Command**: `python scripts/run_submission_smoke.py`
- **Exception**: `ModuleNotFoundError: No module named 'backend'`
- **Root Cause**: `sys.path` does not anchor repo root before importing `backend.app.core.time_contract`.
- **Target Resolution Phase**: Phase 04

### Failure 3: Master Gates Workspace Path Coupling
- **Command**: `python scripts/run_all_master_gates.py`
- **Failure**: Fails at Step 1 (`gate_test_step1.py`) expecting non-existent multi-repo directory structures (`repos/repo_a`, `repos/repo_b`) and a hardcoded historical SHA.
- **Target Resolution Phase**: Phase 04 / Phase 05

### Failure 4: Release Gates Argument and Path Errors
- **Command**: `python scripts/run_release_gates.py --require-all`
- **Failure**:
  - G1/G3: `[WinError 267] The directory name is invalid`
  - G11: `replay_digital_twin.py: error: unrecognized arguments: --mode synthetic`
  - G15: `[WinError 267] The directory name is invalid`
- **Target Resolution Phase**: Phase 05

### Failure 5: Builder-2 Missing Training Parquet
- **Command**: `python scripts/smoke_test_builder2.py`
- **Exception**: `AssertionError: Parquet dataset not found at data\training\training_dataset.parquet`
- **Root Cause**: Training fixture file not checked into repo.
- **Target Resolution Phase**: Phase 08

### Failure 6: Final Smoke Trust State Coercion
- **Command**: `python scripts/smoke_test_final.py`
- **Exception**: `AssertionError: assert safety_res.trust_state == TrustState.HIGH_CONFIDENCE`
- **Root Cause**: Smoke test expects `HIGH_CONFIDENCE`, but the defensive safety layer correctly evaluates the sample inputs as `MODERATE_CONFIDENCE`.
- **Target Resolution Phase**: Phase 08

---

## 5. Certification & Baseline Freeze Conclusion

The baseline evidence is now frozen. All test counts and artifact hashes are verified by automated execution. No claim is accepted on documentation authority alone.
