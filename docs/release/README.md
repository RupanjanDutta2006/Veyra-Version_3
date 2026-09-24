# Veyra Sentinel — SIH Round-2 Master Release Package

## Executive Release Metadata

- **Product Name**: Veyra Sentinel — Know When Forecasts May Fail (VERSION-3)
- **Problem Statement**: PS 26079 (SIH 2026) — Ministry of Earth Sciences (MoES) & NCMRWF
- **Team**: HEXARK
- **Release Candidate ID**: `veyra-v3.0.0-release-candidate`
- **Release Tag**: `sih-round2-submission-v1.0.0` / `sih-round2-candidate-v1`
- **Candidate Commit SHA**: `6c1e8453d0f2fc12fc1b12f813858430cf5ebda4`
- **Base Audited SHA**: `82eded8194151e37fb9b3eecf273010dc62d7b29`
- **Candidate Head Branch**: `main`
- **Target Repository**: `adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-3`

---

## 1. Release Invariant & Integrity Ledger

Every core artifact in this submission is cryptographically locked, validated on disk, and audited:

| Component | File Path | Algorithm | SHA-256 Hash / State | Verification Tool |
|---|---|:---:|---|---|
| **V3 Model Booster** | `models/v3/lightgbm_v3_challenger.joblib` | SHA-256 | `00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660` | `scripts/verify_artifacts.py` |
| **Probability Calibrator** | `models/v3/probability_calibrator_v3.joblib` | SHA-256 | `9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531` | `scripts/verify_artifacts.py` |
| **50-Feature Schema** | `models/v3/feature_names.json` | SHA-256 | `265cffbbd157a2b8b8b46d3702438050980043b5ed3a6a646a7969cdb9853355` | `scripts/verify_artifacts.py` |
| **Master Claim Register** | `manifests/claim_register.csv` | SHA-256 | 19 Claims across 7 Evidence Classes | `scripts/validate_claim_register.py` |
| **500-Test Ledger** | `manifests/test_500_ledger.csv` | CSV | 500 named specifications (376 passed, 124 N/A) | `scripts/verify_test_ledger.py` |
| **Specialist Evidence Ledger** | `docs/science-evidence/specialist_evidence_ledger.csv` | CSV | 6 Hazard Specialists Contained as Baselines | `scripts/validate_specialist_evidence.py` |
| **Rollback Procedure** | `manifests/rollback_procedure.md` | Doc | 4 Fast Rollback Procedures & Decision Trees | `scripts/run_release_gates.py` |

---

## 2. Master Verification & Test Summary

| Metric | Measured Value | Standard / Requirement | Compliance Status |
|---|:---:|:---:|:---:|
| **Backend Tests (Pytest)** | **952 Passed** | ≥ 900 tests; 0 failures | **100% COMPLIANT** |
| **Frontend Tests (Vitest)** | **111 Passed** | ≥ 100 tests; 0 failures | **100% COMPLIANT** |
| **Total Automated Tests** | **1,063 Passed** | > 1,000 automated tests | **100% COMPLIANT** |
| **500-Test Specification Ledger** | **376 Passed, 124 N/A** | 20 domains × 25 IDs = 500 specs | **100% COMPLIANT** (0 fabricated) |
| **Master Acceptance Gates** | **10 / 10 Passed** | 100% compulsory gate pass rate | **100% COMPLIANT** |
| **Mandatory Release Gates** | **6 / 6 Passed** | Gates G1/G3, G8, G11, G15, G16, G17 | **100% COMPLIANT** |
| **Clean-Clone Reproduction** | **PASSED** | Isolated directory reproduction | **100% COMPLIANT** |
| **Smoke Suite Coverage** | **6 / 6 Suites Passed** | Builder-2, Final, Serving, Weather, Hist, Submission | **100% COMPLIANT** |

---

## 3. Seven Evidence Classes & Architectural Truth

1. **Class 1 — Artifact Authority**: Single canonical V3 model artifact (`veyra-v3-benchmark-lightgbm`, decision threshold 0.060) and Isotonic Calibrator loaded via authoritative `/v1/predict` endpoint.
2. **Class 2 — Temporal Contract**: Strict UTC issue-time invariant (`backend/app/core/time_contract.py`). Zero data leakage between forecast issuance and verification observations.
3. **Class 3 — Certified Scope**: Explicitly bounded to 25 benchmark stations, 3 core variables (`temperature_2m`, `wind_speed_10m`, `surface_pressure`), and 24h–240h lead horizons. Extended horizons (264h–384h) are conservatively capped at `MODERATE_CONFIDENCE` with `UNCERTIFIED_EXTENDED_HORIZON` reason codes.
4. **Class 4 — Defensive Abstention**: Safe abstention enforced across Mahalanobis/Isolation Forest OOD scores, epistemic variance, missing weather feeds, and invalid coordinates.
5. **Class 5 — Durable History & Replay Separation**: Replay modes strictly separated into Historical Truth (`--mode historical`, immutable forecast/truth fixtures) and Synthetic Digital Twin (`--mode synthetic`, simulation scenarios carrying mandatory disclosure flags).
6. **Class 6 — Specialist Containment**: All 6 hazard specialists (`PRECIPITATION`, `CYCLONE`, `MONSOON_LPS`, `WESTERN_DISTURBANCE`, `HEATWAVE`, `SEVERE_WIND`) contained as `FORMULA_BASELINE` and `EXPERIMENTAL` pending held-out empirical training artifacts.
7. **Class 7 — Test Ledger Discipline**: Strict separation between the 500 named architectural specifications (20 domains × 25 IDs) and discovered automated software tests (1,063). Uncovered domains (Domain 13: VERT) are honestly marked `N/A — uncovered/missing`.

---

## 4. Replay Separation Matrix

| Feature | Historical Replay Mode (`--mode historical`) | Synthetic Digital Twin (`--mode synthetic`) |
|---|---|---|
| **Data Source** | Immutable verified forecast & observation fixtures (`data/historical/`) | Parametric counterfactual generators (`data/digital_twin_scenarios.json`) |
| **Truth Grounding** | Reanalysis & Ground truth observations (ERA5, IMD AWS) | Synthetic perturbation physics & stress trajectories |
| **UI Provenance Badge** | 🟢 `LIVE` / 🔵 `FIXTURE` | 🟣 `SYNTHETIC` |
| **CLI Verification** | `python scripts/replay_historical.py --mode historical` | `python scripts/replay_digital_twin.py --mode synthetic` |
| **Safety Invariant** | Rejects synthetic scenarios; asserts immutable timestamps | Explicit `is_synthetic = True` flag on all output records |

---

## 5. Rollback Governance & Fast Reversion Runbook

Authoritative document: [`manifests/rollback_procedure.md`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RIII/repos/repo_b/manifests/rollback_procedure.md)

### Automated Reversion Triggers:
1. Any P0 Master Acceptance Gate failure (`code != 0`).
2. Calibration drift ($ECE > 0.080$ on reference holdout).
3. Live inference $p_{99}$ latency exceeding $500\text{ ms}$.
4. Upstream NWP schema corruption or unhandled feature dimensionality mismatch.

### Reversion Execution:
```bash
# 1. Stop operational daemon
# 2. Reset worktree to base audited commit
git checkout -f 82eded8194151e37fb9b3eecf273010dc62d7b29
# 3. Verify base artifact hashes
python scripts/verify_artifacts.py
# 4. Restart services under safe fallback mode
```
Mean Time to Recovery (MTTR) is audited at $< 60$ seconds.

---

## 6. Launch & Verification Quick-Commands

```bash
# Run all 10 Master Acceptance Gates
python scripts/run_all_master_gates.py

# Run Compulsory Release Gates with JSON audit report
python scripts/run_release_gates.py --require-all --output-json artifacts/release_gates_report.json

# Run 500-test specification ledger validator
python scripts/verify_test_ledger.py

# Run master claim register validator
python scripts/validate_claim_register.py --input manifests/claim_register.csv

# Run specialist evidence validator
python scripts/validate_specialist_evidence.py

# Run clean-clone reproduction test
python scripts/clean_clone_reproduction.py --tag sih-round2-candidate-v1

# Run frontend tests & production build
npm test --prefix frontend -- --run
npm run build --prefix frontend

# Run Dedicated Phase 09 Submission Gate
python scripts/gate_test_phase9.py
```
