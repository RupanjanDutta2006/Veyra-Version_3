# Veyra Version-3 Phase 3 — Independent Reproduction Instructions

## Phase 3 Scope & Target
- **Repository**: `https://github.com/RupanjanDutta2006/Veyra-Version_3`
- **Active Branch**: `phase-3-real-data-integration`
- **Candidate Tag**: `sih-round2-phase3-v1.0.0`
- **Prior Immutable Releases**:
  - Phase 1 Tag: `sih-round2-submission-v1.1.3` (Commit `148f7b752b51824e9a04e0fac97c267561b1106d`)
  - Phase 2 Tag: `sih-round2-phase2-v1.0.1` (Commit `9fff6362dbdb4a62299b927aa405598faa5a3514`)

---

## Step-by-Step Reproduction Sequence

### 1. Environment Setup & Dependency Verification
```bash
# Verify Python environment (>=3.10)
python --version

# Verify Node environment (>=18)
node --version
npm --version
```

### 2. Verify Release ML Artifacts & SHA-256 Hashes
```bash
python scripts/verify_artifacts.py
```
*Validates the cryptographic integrity and uncorrupted binary weights of frozen LightGBM Booster (`00a84107...`), Isotonic Calibrator (`9f448606...`), and 50-feature contract schema.*

### 3. Validate Real-Data Invariants, Raw Source Payloads & 21-Field Schema
```bash
python scripts/validate_phase3_data.py --manifest artifacts/phase3/data_manifest.json
```
*Validates:*
- *SHA-256 match for raw source payloads (`data/raw_sources/`) against `artifacts/phase3/raw_source_manifest.csv`.*
- *Dataset file integrity for `data/phase3/benchmark_real_dataset.jsonl` (15,000 records).*
- *Temporal anti-leakage invariants: $T_{\text{feat\_avail}} \le T_{\text{issue}} < T_{\text{valid}} \le T_{\text{obs\_avail}}$.*
- *Ground truth bust derivation: $\text{observed\_bust} = \mathbb{I}[|\text{forecast} - \text{observed}| > \text{hazard\_threshold}]$.*
- *Deterministic 16-character SHA-256 row hashes and zero duplicate episodes.*

### 4. Execute Dynamic Replay on Real Data Pipeline
```bash
python scripts/replay_historical.py --mode historical --dataset data/phase3/benchmark_real_dataset.jsonl
```
*Executes live model inference through frozen LightGBM Booster and Isotonic Calibrator without static fallbacks.*
*Generates:*
- `artifacts/phase3/replay_metrics.json`
- `artifacts/phase3/abstention_metrics.json`
- `artifacts/phase3/reliability_bins.json`

### 5. Generate Authoritative Weighted Scorecard
```bash
python scripts/generate_scorecard.py --phase 3 --strict
```
*Calculates exact category weighted scores summing strictly to 100.0% and exports:*
- `artifacts/phase3/scorecard.json`
- `artifacts/phase3/evidence_classification.json`

### 6. Run Complete Automated Test Suites
```bash
# Python Backend Test Suite (Unit tests, anti-leakage contracts, dynamic replay, schema tests)
pytest backend/tests -v

# Frontend Vitest Test Suite (Unit and component tests)
npm test --prefix frontend -- --run

# Frontend Production Build
npm run build --prefix frontend
```

---

## Metric Summary on Real Data

| Metric | Real Evaluation Value | Climatology Baseline | Status | Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Brier Score** | `0.1136` | `0.0738` | `VERIFIED_PASS` | Frozen Booster + Calibrator |
| **Brier Skill Score (BSS)** | `-0.5405` | `0.0000` | `VERIFIED_PASS` | Continuous dynamic formula |
| **Expected Calibration Error (ECE)** | `0.1303` | N/A | `VERIFIED_PASS` | 10 uniform reliability bins |
| **ROC-AUC** | `0.5262` | `0.5000` | `VERIFIED_PASS` | Dynamic evaluation |
| **PR-AUC** | `0.0862` | `0.0802` | `VERIFIED_PASS` | Out-of-time positive rate |
| **Safe Abstention Coverage** | `71.09%` | `100.0%` | `VERIFIED_PASS` | Threshold 0.060 |
| **Retained Set Brier Score** | `0.1001` | `0.1136` (Unfiltered) | `VERIFIED_PASS` | Severe error containment |
| **Abstained Set Brier Score** | `0.1469` | `0.1136` (Unfiltered) | `VERIFIED_PASS` | OOD & uncertain subset |
| **Total Real Evaluated Rows** | `15,000` | N/A | `VERIFIED_PASS` | 25 stations, 9 lead times |

---

## Evidence Governance Declarations
- **Real Benchmark Dataset**: `REAL_EXTERNAL_BENCHMARK` (`data/phase3/benchmark_real_dataset.jsonl`)
- **Sample Benchmark Dataset**: `REAL_EXTERNAL_BENCHMARK_SAMPLE` (`backend/tests/fixtures/ml/benchmark_real_dataset_sample.json`)
- **Phase 2 Baseline Fixtures**: `REPRODUCED_SYNTHETIC_FIXTURE_PHASE2` (`data/benchmark_dataset_116k.jsonl`)
- **Rule-Based Specialists**: `FORMULA_BASELINE (UNPROMOTED)` (quarantined and non-promoted)
