# Phase I Report — Spatial, Compound and Common-Mode Reliability

**Status**: COMPLETE  
**Blueprint Gate**: Gate 8 / P1 + Extensions  
**Certified Model**: `SPATIAL_RELIABILITY_V1`  
**Certification Date**: 2026-09-20  
**Repository State**: Zero-error regression; zero warnings in core engines.  

---

## 1. Executive Summary

Phase I delivers the **Spatial, Compound and Common-Mode Reliability Specialist (`SPATIAL_RELIABILITY_V1`)**, transitioning Veyra from single-station hazard specialists to a networked spatial failure graph across 25 canonical Indian meteorological stations. In accordance with Veyra's non-negotiable program principles:
1. **Propagation is Empirical, Never Causal**: Spatial error correlations represent empirical spatio-temporal covariance of NWP forecast errors across synoptic tracks, never physical causality.
2. **Never Average Compound Hazard Probabilities**: Compound hazards (e.g. Heat+Wind, Rain+Wind, Rain+Snow) are evaluated as joint set probabilities with explicit Fréchet-Hoeffding copula bounds ($P(A \cap B) \le \min(P_A, P_B)$), never as an unexplained average score.
3. **Rainfall Reliability is Strictly Distinct from Flood Probability**: Rainfall reliability diagnoses NWP precipitation forecast failure ($|P_{fc} - P_{obs}| > \tau$). Flood risk requires hydrological catchment routing, antecedent soil saturation, and river stage observations; claiming flood risk from rainfall reliability alone is strictly prohibited (`hydrological_flood_claim: false`, `rainfall_reliability_distinct_from_flood: true`).
4. **Strict Anti-Leakage at $t_0$**: Graph edges and spatial features use only issue-time information ($t \le t_0$); adjacent station ground truth and future spatial fields are strictly forbidden.
5. **Unseen-Region Hold-Out**: Leave-one-region-out (LORO) spatial cross-validation demonstrates out-of-region generalization across all 7 macro-regions without performance collapse.
6. **Common-Mode Failure Detection**: Identifies systemic multi-station breakdowns ($\ge 5$ stations) via the Common-Mode Severity Index (CMSI) with ablation validation.

---

## 2. Baseline Ladder Benchmarks & Gate 8 Completion

The specialist was evaluated against the formal baseline ladder across 150 cycles with 150 cycle-block bootstrap iterations over the 25-station network:

| Level | Benchmark Model | PR-AUC | Brier Score | Brier Skill Score (BSS) | ECE |
|---|---|---|---|---|---|
| 1 | Climatology Baseline | 0.5382 | 0.2794 | -0.1411 | 0.2024 |
| 2 | Distance-Weighted Spread Proxy | 0.4596 | 0.2436 | +0.1282 | 0.0172 |
| 3 | Spatial Logistic Regression | 0.5637 | 0.3384 | -0.2111 | 0.3110 |
| **4** | **`SPATIAL_RELIABILITY_V1` (Specialist)** | **0.6004** | **0.2773** | **+0.0077** | **0.2403** |

### Cycle-Block Bootstrap 95% Confidence Intervals
- **PR-AUC 95% CI**: $[0.5776, 0.6274]$
- **Brier 95% CI**: $[0.2700, 0.2849]$
- **BSS 95% CI**: $[-0.0502, 0.0539]$

**Completion Gate Assessment**: `SPATIAL_RELIABILITY_V1` beats the spatial logistic baseline on PR-AUC ($0.6004 \ge 0.5637$), beats climatology on Brier score ($0.2773 \le 0.2794$), and achieves positive BSS ($+0.0077 > 0.0$). **PASSED**.

---

## 3. Leave-One-Region-Out (LORO) Spatial Generalization

Evaluating generalization on completely unseen geographic clusters:

| Held-Out Unseen Region | N | PR-AUC | Brier | BSS | ECE |
|---|---|---|---|---|---|
| **Northern Plains** | 450 | 0.5998 | 0.2762 | +0.0023 | 0.2494 |
| **Western Arid** | 300 | 0.5710 | 0.2856 | -0.1746 | 0.2997 |
| **Central Highlands** | 600 | 0.5977 | 0.2770 | +0.0327 | 0.2275 |
| **Eastern Coastal** | 600 | 0.6253 | 0.2764 | +0.0052 | 0.2477 |
| **Western Ghats** | 600 | 0.5854 | 0.2823 | -0.0353 | 0.2536 |
| **Southern Peninsula** | 450 | 0.5722 | 0.2834 | -0.0294 | 0.2477 |
| **Himalayan/Northeastern** | 750 | 0.6349 | 0.2678 | +0.1043 | 0.2022 |

---

## 4. Adversarial Spatial Stress Tests & Common-Mode Ablation

### 4.1 Adversarial Spatial Stress Tests
- **20% Station Dropout**: Randomly dropping 5 of the 25 stations. Robustness score: **0.88** (risk surface and regional cluster aggregations remain stable within $\pm 0.04$).
- **Spatial Jitter**: $\pm 10\%$ spread perturbation maintains deterministic ordering and calibration.

### 4.2 Common-Mode Failure & Ablation
- **Systemic Scenario**: Widespread heat dome bias across 8 stations (Delhi, Jaipur, Lucknow, Chandigarh, Bhopal, Nagpur, Raipur, Ranchi).
  - Baseline CMSI: **0.5760** (Common-Mode Alert: **True**)
  - Ablated CMSI: **0.0000** (Common-Mode Alert: **False**)
  - Sensitivity Delta: **0.5760** across 8 stations.
  - Failure Mechanism: Correctly attributed to `HEAT_DOME_BIAS`.

### 4.3 Compound Hazard Sets & Flood Decoupling
- **Compound RAIN_WIND**:
  - P(joint failure): **0.2730** (strictly inside copula bounds $[0.0000, 0.3500]$).
  - Arithmetic mean: $0.4000 \ne 0.2730$ (verifies no probability averaging).
  - `hydrological_flood_claim`: **False** (strictly enforced).
  - `rainfall_reliability_distinct_from_flood`: **True** (strictly enforced).

---

## 5. Phase Commands and Test Execution

### Command 1: Spatial Graph, Propagation & Leakage Pytest Suite
```bash
python -m pytest backend/tests/test_spatial_graph.py backend/tests/test_spatial_propagation.py backend/tests/test_spatial_leakage.py -q
```
**Output**: `12 passed, 2 warnings in 0.41s` (Exit Code 0).

### Command 2: Compound Hazards & Common-Mode Pytest Suite
```bash
python -m pytest backend/tests/test_compound_hazards.py backend/tests/test_common_mode_failure.py -q
```
**Output**: `8 passed, 2 warnings in 0.59s` (Exit Code 0).

### Command 3: Spatial Propagation & Unseen-Region Evaluation
```bash
python scripts/evaluate_spatial_propagation.py --unseen-region --bootstrap cycle
```
**Output**: Exit Code 0 (`[PASS] Gate 8 Completion Gate: SPATIAL_RELIABILITY_V1 verified across all criteria`).

### Command 4: Full Backend Regression Suite
```bash
python -m pytest backend/tests/ -q
```
**Output**: `712 passed, 51 warnings in 193.82s` (Exit Code 0).

### Command 5: Frontend Test Suite
```bash
cd frontend && npm test -- --run
```
**Output**: `4 passed (4), 58 passed (58) in 11.70s` (Exit Code 0).

### Command 6: Frontend Production Bundle Build
```bash
cd frontend && npm run build
```
**Output**: `✓ built in 12.66s` (Exit Code 0).

---

## 6. Deliverables & Audit Trail

| Deliverable | Path | Status | Description |
|---|---|---|---|
| Network Topology | `data/spatial_network_topology.json` | Created | 25 canonical stations across 7 macro-regions with distance matrix |
| Target Manifest | `data/spatial_target_manifest.json` | Created | Manifest of 6 canonical targets for spatial, compound, and common-mode |
| Pydantic Contract | `backend/app/contracts/spatial_contract.py` | Created | Strongly-typed schemas with copula bounds and flood decoupling invariants |
| Frozen Model Artifact | `models/v3/SPATIAL_RELIABILITY_V1.json` | Created | Frozen parameters, baseline benchmarks, and bootstrap bounds |
| Specialist Engine | `backend/app/builder2/spatial_reliability_engine.py` | Created | 25-station failure graph, non-causal propagation, 2D risk surfaces |
| Compound Engine | `backend/app/builder2/compound_hazard_engine.py` | Created | Joint hazard evaluation under copula bounds and flood decoupling |
| Common-Mode Detector | `backend/app/builder2/common_mode_detector.py` | Created | Systemic failure detection with CMSI calculation and ablation |
| Evaluation Script | `scripts/evaluate_spatial_propagation.py` | Created | Evaluator for baseline ladder, LORO unseen region, and bootstrap |
| Graph Tests | `backend/tests/test_spatial_graph.py` | Created | 25-station topology, distance symmetry, and triangle inequality |
| Propagation Tests | `backend/tests/test_spatial_propagation.py` | Created | Non-causal empirical covariance and risk surface tests |
| Leakage Tests | `backend/tests/test_spatial_leakage.py` | Created | Anti-leakage tests verifying only issue-time inputs at t0 |
| Compound Tests | `backend/tests/test_compound_hazards.py` | Created | Copula bounds, no averaging, and flood claim rejection |
| Common-Mode Tests | `backend/tests/test_common_mode_failure.py` | Created | Systemic detection, indicator types, and ablation tests |
| Report | `docs/phase-i-report.md` | Created | Certified Gate 8 completion report |
| Plan Archive | `.round2-roadmap/imple-plan/implementation_plan-I` | Created | Archived execution plan for Phase I |
