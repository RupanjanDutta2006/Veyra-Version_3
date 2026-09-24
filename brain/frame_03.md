# VEYRA VERSION-3: FRAME 03 EXECUTION & VERIFICATION REGISTER

**Timestamp**: 2026-09-24T15:50:00Z  
**Target**: Project Veyra Version-3 (Authoritative Operational Baseline)  
**Execution Context**: Frame 03 Executor (Phase 05: Data Lineage & Anti-Leakage Safety; Phase 06: Historical Replay & Mode Separation)  

---

## 1. PHASE PROGRESS LOG

| Phase | Description | Scope | Status | Notes |
|---|---|---|---|---|
| **Phase 05** | Data Lineage, Issue-Time Metadata, QC & Zero-Data-Leakage | Strict UTC time contract (`backend/app/core/time_contract.py`), temporal invariant validation (`lead_hours = valid_time - issue_time`), quality control, and truth-sealing anti-leakage barriers. | **100% COMPLETE** | All timestamps normalized to ISO 8601 UTC; zero future data leakage; 61/61 focused tests passed. |
| **Phase 06** | Independent Historical Replay Engine & Mode Separation | Durable revision store (`backend/app/core/revision_store.py`), independent offline replay harness (`backend/app/core/replay_harness.py`), strict mode separation between Historical Atmospheric Replay and Synthetic Digital Twin simulations. | **100% COMPLETE** | Gate P5 (Gates G9 & G11) passed; CLI tools `replay_historical.py` and `replay_digital_twin.py` verified with explicit disclosure labels. |

---

## 2. PHASE 05 VALIDATION: DATA LINEAGE & ZERO-LEAKAGE GUARDS

### 1. Authoritative Time Contract & Temporal Invariants
- **Core Module**: `backend/app/core/time_contract.py`
- **Invariant Law**: $\text{lead\_hours} = (\text{valid\_time} - \text{issue\_time})\text{ in hours}$, with $\text{lead\_hours} \ge 1$.
- **UTC Timezone Governance**: All incoming ISO 8601 strings are normalized to timezone-aware UTC datetime instances.
- **Horizon Scope Separation**:
  - $\le 240\text{h}$: Certified benchmark lead scope (eligible for scientific evaluation).
  - $264\text{h} - 384\text{h}$: Extended operational forecast horizon.
  - $> 384\text{h}$: Rejected as out-of-scope lead time (`ABSTAIN_OUT_OF_SCOPE_LEAD_TIME`).

### 2. Truth-Sealing & Anti-Leakage Architecture
- **Verification Barrier**: Ground truth observations (ERA5 reanalysis / IMD AWS network) are strictly sealed from the feature extraction pipeline at forecast issue time $t_0$.
- **Spatial Separation**: Station-level coordinates and geographic properties are decoupled from verification observations to prevent spatial information bleed.

---

## 3. PHASE 06 VALIDATION: REPLAY HARNESS & REPLAY MODE SEPARATION

### 1. Replay Mode Separation Law (Gate G11)
The system enforces strict architectural separation between historical records and synthetic scenario simulations:
1. **Historical Atmospheric Replay (`--mode historical`)**:
   - Runs against immutable ground-truth verified weather events.
   - Evaluates forecast error against sealed reference observations.
   - Forbids synthetic parameter perturbation or synthetic labeling.
2. **Synthetic Digital Twin Counterfactuals (`--mode synthetic`)**:
   - Generates controlled perturbation scenarios (e.g. spread widening, moisture injection).
   - Carries mandatory `SYNTHETIC` disclosure badges in all API responses and CLI outputs.
   - Forbidden from masquerading as historical truth.

### 2. Durable SQLite-WAL Revision Store (`backend/app/core/revision_store.py`)
- **Target Identity**: Unique compound key `(canonical_location, variable, valid_time, issue_time, provider_source)`.
- **Idempotency**: Repeated ingest of identical forecast issue runs creates exactly 1 persistent record.
- **Chronological Ordering**: Queries previous cycles strictly by issue-time order (`issue_time < current_issue_time ORDER BY issue_time DESC LIMIT 1`).
- **Delta Computation**: Revisions calculate $\Delta = \text{CURRENT} - \text{PREVIOUS}$ across probability and ensemble metrics.

### 3. Independent Offline Replay Engine (`backend/app/core/replay_harness.py`)
- Reconstructs low-level feature extraction, cryptographic artifact verification, isotonic calibration, and OOD diagnostics independently of production REST endpoints.
- Enforces strict floating-point numerical tolerance ($< 10^{-5}$) across golden replay vectors.

---

## 4. TEST METRICS & GATE VERIFICATION

| Verification Layer | Test Target | Result | Status |
|---|---|---|---|
| **Phase 5 Gate** (`scripts/gate_test_phase5.py`) | Gates G9 & G11 (Revision Store & Replay Mode Separation) | **All checks passed (4.29s)** | **PASS (100%)** |
| **Historical Smoke Test** (`scripts/smoke_test_historical.py`) | ERA5 alignment, unit conversion, bust labeling, anti-leakage | **6/6 Verification Steps Passed** | **PASS (100%)** |
| **Focused Phase 5 & 6 Tests** (`pytest`) | 10 specialized test modules (61 tests) | **61 passed / 61 total (4.97s)** | **PASS (100%)** |
| **Full Backend Test Suite** (`pytest`) | Full backend suite | **954 passed / 954 total** | **PASS (100%)** |
| **Frontend Test Suite** (`vitest`) | Full frontend suite | **111 passed / 111 total** | **PASS (100%)** |

---

## 5. CHANGE LOG

1. `brain/frame_03.md`: Created Frame 03 tracking register detailing Phase 05 and Phase 06 validations, time contracts, replay mode separation, and test verification metrics.
