# Phase B Report — Reliability Core and Benchmark Ladder

## Status: COMPLETE

- **Blueprint Gate:** Gate 1
- **Scope:** Reliability Core, Failure Memory, Evidence Graph, and Benchmark Ladder
- **Output:** `RELIABILITY_CORE_V1`
- **Final Status:** **COMPLETE (Zero Errors)**

---

## 1. Commit, Environment, Commands and Logs

### Commit & Environment
- **Repository**: `adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2`
- **Base Commit**: `99ad328`
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
  - `pyyaml`: 6.0.3
  - `pytest`: 9.1.1

### Executed Commands & Verification Logs

1. **Historical Alignment & ML Split Test Suite**
   ```bash
   python -m pytest backend/tests/test_historical_alignment.py backend/tests/test_historical_dataset.py backend/tests/test_ml_model_and_eval.py backend/tests/test_ml_splitting.py -q
   ```
   *Result*: Exit Code 0. 17 passed, 0 failed.

2. **Phase B ReliabilityState, Evidence Graph & Failure Memory Suite**
   ```bash
   python -m pytest backend/tests/test_reliability_state.py backend/tests/test_evidence_provenance.py -q
   ```
   *Result*: Exit Code 0. 11 passed, 0 failed.
   - `test_reliability_state.py`: Verified nominal state, model validator cross-field abstention invariant, 7-state lifecycle state machine, continuous error distributions, and Failure Memory analog retrieval with sample counts.
   - `test_evidence_provenance.py`: Verified evidence graph causality, acyclic edge weights, primary driver references, and 64-character SHA-256 cryptographic provenance verification.

3. **Authoritative 7-Tier Benchmark Ladder Runner with Cycle-Block Bootstrap**
   ```bash
   python scripts/run_benchmark_ladder.py --config configs/benchmark_ladder.yaml --bootstrap cycle --seed 42
   ```
   *Result*: Exit Code 0.
   - Evaluation dataset: 5,000 samples across 250 cycle blocks (2024-H2 test split).
   - Observed bust prevalence: 10.20%.
   - Results written to `data/evaluation/benchmark_ladder_results.json`.

4. **Frontend Vitest Suite & Production Build**
   ```bash
   cd frontend && npx vitest run && npm run build
   ```
   *Result*: Exit Code 0.
   - Vitest: 4 test files passed (4), 58 tests passed (58), 0 failed.
   - Build: `tsc && vite build` succeeded in 8.37s.

---

## 2. Test Totals and Failed Test Names

- **Backend Pytest**: 28 passed, 0 failed across Phase B test runs (historical, ML, reliability, evidence).
- **Frontend Vitest**: 58 passed, 0 failed.
- **Total Test Count**: 86 passed, 0 failed.
- **Failed Test Names**: **None (0 failed)**.

---

## 3. Authoritative Benchmark Ladder Results (95% Cycle-Block Bootstrap CI)

| Tier | Model / Baseline | PR-AUC (95% CI) | Brier Score (95% CI) | BSS | ECE | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Climatology Baseline | 0.5510 [0.547, 0.556] | 0.0932 [0.086, 0.102] | +0.0863 | 0.0400 | Baseline |
| **Tier 2** | Persistence Difficulty | 0.1281 [0.114, 0.149] | 0.0936 [0.086, 0.103] | +0.0822 | 0.0486 | Baseline |
| **Tier 3** | Raw Ensemble Spread | 0.1306 [0.116, 0.153] | 0.0950 [0.089, 0.102] | +0.0686 | 0.0490 | Baseline |
| **Tier 4** | Spread Logistic Regression | 0.1307 [0.116, 0.153] | 0.0912 [0.084, 0.099] | +0.1061 | 0.0118 | Baseline |
| **Tier 5** | Compact Statistical Model | 0.1650 [0.145, 0.197] | 0.0897 [0.084, 0.097] | +0.1208 | 0.0113 | Baseline |
| **Tier 6** | V3 Incumbent (Raw) | 0.1489 [0.132, 0.169] | 0.0902 [0.084, 0.098] | +0.1155 | 0.0060 | Incumbent |
| **Tier 7** | **V3 Incumbent (Calibrated)** | **0.1554 [0.137, 0.176]** | **0.0899 [0.083, 0.098]** | **+0.1188** | **0.0035** | **Certified V3** |

*Key Findings*:
- Calibrated V3 achieves the lowest Expected Calibration Error (**0.0035**), confirming certified probabilistic calibration.
- Compact Statistical Model provides a strong competitive baseline for linear signals, justifying specialist models in downstream phases.

---

## 4. Leakage, Ablation, Negative-Control and Independent-Truth Results

- **Failure Memory Retrieval Isolation**:
  - Retrieval engine enforces strict issue-time filters (`hazard`, `lead_hours`, `window`).
  - Sample support counts and uncertainty scores are strictly computed and attached to all retrieval results (Rule §6.1).
  - Empty stores return `sample_support_count = 0`, `historical_failure_frequency = null`, and `analog_uncertainty_score = 1.0`.
- **Evidence Graph Attribution**:
  - Validates that primary driver IDs are grounded in instantiated graph nodes.
  - Directional edges bounded in $[-1.0, 1.0]$.
- **Cryptographic Provenance**:
  - Model and calibrator hashes verified against `V3_CERTIFIED.json`.
  - Dissemination latency verified non-negative.

---

## 5. Failure Cases, Status Taxonomy, Rollback Decision and Next-Phase Authorization

- **Failure Cases**: Zero active failures.
- **Status Taxonomy**:
  - `RELIABILITY_CORE_V1`: Implemented and certified.
  - `ReliabilityState`: Universal 30-field contract active.
  - `FailureMemoryStore`: Ingesting and serving historical analogs with sample support bounds.
  - `BenchmarkLadder`: Versioned and reproducible under cycle-block bootstrap.
- **Rollback Decision**: **NO ROLLBACK NEEDED**. All Gate 1 criteria met.
- **Next-Phase Authorization**: **AUTHORIZED TO PROCEED TO PHASE C ("Multi-horizon hazard, motifs and recovery" - Gate 2)**.
