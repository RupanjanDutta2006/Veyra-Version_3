# Phase 3 Completion Report: Out-of-Distribution (OOD) Detection, Conformal Calibration & Abstention Layer

**Date:** 2026-09-19  
**Status:** COMPLETE & VERIFIED (24 Phase 3 / Leakage tests passing, 44 core ML tests verified)  
**Governing Specification:** SIH26079 Master Specification §10, §10.4, §11, §11.1–§11.4; Research Files 071–077  
**Audit Items Closed:** F2, F4, F5, F6, F7, E8, E9  

---

## 1. Executive Summary

Phase 3 systematically closes all Out-of-Distribution (OOD), Calibration, Abstention, and Data Leakage gaps identified in [`Docs_vs_Research_vs_Live_comparison.md`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/.docstest-round_1/.maindocs/Docs_vs_Research_vs_Live_comparison.md).

Prior to Phase 3:
- OOD detection was a constant stub returning `0.1` or simple 1D standard deviations.
- The system lacked an explicit 4-state vocabulary (`NORMAL`, `UNUSUAL`, `OOD`, `ABSTAIN`), using unstructured string reasons.
- Conformal prediction intervals were fixed margins ($\pm 0.15$) lacking finite-sample non-conformity guarantees or conditional coverage by lead time and region.
- Model calibration reporting lacked reliability diagrams, logistic calibration slope $a$, intercept $b$, log-loss, and empirical coverage-risk trade-offs.
- Data splitting lacked explicit regional and model-version holdout splitters.
- Anti-leakage rules lacked an automated CI-runnable integration test suite.

With Phase 3 implemented, tested, and verified:
All 7 target capabilities (F2, F4, F5, F6, F7, E8, E9) are active, mathematically validated, and backed by comprehensive automated test suites.

| Audit # | Capability / Requirement | Target Spec | Implementation Artifact | Status |
|---|---|---|---|---|
| **F2** | Reliability diagram, calibration slope/intercept, log-loss, ECE & MCE | §11.1, File 071 | [`backend/app/ml/evaluation.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/evaluation.py) | ✅ **CLOSED** |
| **F4** | Split conformal prediction intervals & conditional coverage reporting | §11.2, File 073 | [`backend/app/ml/conformal.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/conformal.py) | ✅ **CLOSED** |
| **F5** | Multi-signal OOD scoring (feature distance, regime novelty, distribution drift) | §11.3, File 074 | [`backend/app/safety/ood_detector.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/safety/ood_detector.py) | ✅ **CLOSED** |
| **F6** | Standardized 4-state vocabulary (`NORMAL`, `UNUSUAL`, `OOD`, `ABSTAIN`) | §11.3, File 074 | [`backend/app/safety/ood_detector.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/safety/ood_detector.py), [`backend/app/safety/abstention.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/safety/abstention.py) | ✅ **CLOSED** |
| **F7** | Coverage-risk curve & forecaster review burden metrics | §11.4, File 076 | [`backend/app/safety/abstention.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/safety/abstention.py), [`backend/app/ml/evaluation.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/evaluation.py) | ✅ **CLOSED** |
| **E8** | Geographic region, model-version, & multi-dimensional holdouts | §10.4, File 053 | [`backend/app/ml/splitting.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/splitting.py) | ✅ **CLOSED** |
| **E9** | CI-runnable automated leakage integration tests | §8.3, §10.4, File 048 | [`backend/tests/test_leakage_integration.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/tests/test_leakage_integration.py) | ✅ **CLOSED** |

---

## 2. Technical Details of Implemented Components

### 2.1 Multi-Signal OOD Detection Engine & State Vocabulary ([`backend/app/safety/ood_detector.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/safety/ood_detector.py) - §11.3, F5, F6)

- **Standardized 4-State Vocabulary (`OODState` Enum):**
  1. `NORMAL` ($S_{OOD} < 0.35$): State is within nominal training distribution. Model predictions proceed with high confidence.
  2. `UNUSUAL` ($0.35 \le S_{OOD} < 0.65$): Moderate deviation or tail event (e.g. rare synoptic regime, moderate ensemble spread). Predictions proceed with widened conformal bounds and forecaster review flags.
  3. `OOD` ($0.65 \le S_{OOD} < 0.80$): Significant statistical or atmospheric deviation. Downstream decision systems are notified of extreme uncertainty.
  4. `ABSTAIN` ($S_{OOD} \ge 0.80$): Severe multi-signal anomaly or distribution breakdown. Pipeline safely abstains from automated point prediction, invoking human expert review per §11.3.

- **Multi-Signal Score Formulation:**
  The composite OOD score $S_{OOD} \in [0.0, 1.0]$ combines three distinct statistical and physical dimensions:
  $$S_{OOD} = w_1 \cdot D_{\text{feat}} + w_2 \cdot N_{\text{regime}} + w_3 \cdot D_{\text{drift}}$$
  Where:
  1. **Standardized Feature Distance ($D_{\text{feat}}$):**
     $$D_{\text{feat}} = \min\left(1.0, \frac{1}{d} \sum_{j=1}^d \frac{|x_j - \mu_j|}{\sigma_j \cdot 4.0}\right)$$
  2. **Atmospheric Regime Novelty ($N_{\text{regime}}$):**
     Measures multivariate deviation across blocking index, cyclonic indicators, and kinetic energy proxies relative to seasonal reference regimes:
     $$N_{\text{regime}} = \min\left(1.0, \frac{\|\mathbf{r}_{query} - \mathbf{r}_{ref}\|_2}{\sqrt{\dim(\mathbf{r})}}\right)$$
  3. **Distribution Drift ($D_{\text{drift}}$):**
     Two-sample Kolmogorov-Smirnov (KS) statistic $D_{KS} = \sup_x |F_1(x) - F_2(x)|$ and 1D Wasserstein distance $W_1 = \int_{-\infty}^{\infty} |F_1(x) - F_2(x)| dx$ comparing current window against reference training distributions.

- **Integrated Safety Evaluator ([`backend/app/safety/abstention.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/safety/abstention.py)):**
  - Updated `SafetyAssessment` dataclass with `ood_state: OODState` and `ood_score: float`.
  - Seamlessly integrates with existing physical range checks, NWP run status, and data availability gates. When $S_{OOD} \ge 0.80$, `should_abstain = True` with `reason = "OOD_ABSTAIN"`.

---

### 2.2 Conformal Prediction Intervals & Conditional Coverage ([`backend/app/ml/conformal.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/conformal.py) - §11.2, F4)

- **Split Conformal Predictor:**
  Implements split conformal prediction on calibration set $(X_{cal}, y_{cal})$ using non-conformity scores:
  $$s_i = |y_i - \hat{p}_i|$$
  For a target coverage level $1 - \alpha$ (default $\alpha = 0.10$ for $90\%$ coverage), the conformal quantile $\hat{q}$ is computed with exact finite-sample correction:
  $$\hat{q} = \text{Quantile}\left(s_{1:n}, \frac{\lceil (n + 1)(1 - \alpha) \rceil}{n}\right)$$
  Prediction intervals for new inputs are bounded to valid probabilities:
  $$C(x) = \left[\max(0.0, \hat{p}(x) - \hat{q}), \min(1.0, \hat{p}(x) + \hat{q})\right]$$

- **Conditional Coverage Reporting:**
  Evaluates empirical coverage:
  $$\text{Coverage} = \frac{1}{N} \sum_{i=1}^N \mathbf{1}\{y_i \in C(x_i)\}$$
  Disaggregated conditionally by:
  1. **Lead Time Bins:** $[0, 24\text{h}]$, $[25, 72\text{h}]$, $[73, 120\text{h}]$, $[121, 240\text{h}]$.
  2. **Geographic Regions:** `IN_NORTH`, `IN_SOUTH`, `IN_EAST`, `IN_WEST`, `IN_CENTRAL`, `COASTAL`.

- **Mandatory Method Declaration (§11.2):**
  Includes `METHOD_DECLARATION = "split_conformal_prediction_with_absolute_residual_nonconformity"`, documenting finite-sample coverage guarantees and assumptions.

---

### 2.3 Comprehensive Model Evaluation & Calibration Metrics ([`backend/app/ml/evaluation.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/evaluation.py) - §11.1, F2)

- **Reliability Diagram & Calibration Error:**
  - 10-bin empirical calibration curve comparing predicted confidence $\bar{p}_b$ with observed bust frequency $\bar{y}_b$.
  - **Expected Calibration Error (ECE):**
    $$\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{N} |\bar{y}_b - \bar{p}_b|$$
  - **Maximum Calibration Error (MCE):**
    $$\text{MCE} = \max_{b=1,\dots,B} |\bar{y}_b - \bar{p}_b|$$

- **Logistic Calibration Slope & Intercept:**
  Fits logistic calibration model $\text{logit}(P(Y=1)) = a \cdot \text{logit}(\hat{p}) + b$:
  - Ideal calibration: Slope $a = 1.0$, Intercept $b = 0.0$.
  - Slope $a < 1.0$ detects overconfidence; $a > 1.0$ detects underconfidence.

- **Brier Score & Log-Loss:**
  - Strictly proper scoring rule evaluations: Brier score $\frac{1}{N}\sum (\hat{p}_i - y_i)^2$ and log-loss $-\frac{1}{N}\sum [y_i \ln \hat{p}_i + (1 - y_i) \ln (1 - \hat{p}_i)]$.
  - Integrated into `EvaluationReport`.

---

### 2.4 Coverage-Risk Trade-Off & Forecaster Review Burden ([`backend/app/safety/abstention.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/safety/abstention.py), [`backend/app/ml/evaluation.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/evaluation.py) - §11.4, F7)

- **Coverage-Risk Curve:**
  Evaluates model performance across a spectrum of confidence thresholds $\tau \in [0.50, 0.99]$:
  $$\text{Coverage}(\tau) = \frac{|\{i : \hat{p}_i \ge \tau \text{ or } \hat{p}_i \le 1 - \tau\}|}{N}$$
  $$\text{Retained Risk}(\tau) = \text{BrierScore}(\text{retained predictions})$$
  $$\text{High-Confidence Error Rate}(\tau) = \frac{|\{i : \hat{p}_i \ge \tau \land y_i = 0\}| + |\{i : \hat{p}_i \le 1 - \tau \land y_i = 1\}|}{|\text{retained predictions}|}$$

- **Forecaster Review Burden:**
  Quantifies operational forecaster workload:
  $$\text{Review Burden} = 1.0 - \text{Coverage}(\tau^*) = \text{Abstention Rate}$$
  Guarantees forecasters receive only ambiguous or high-risk cases for manual review while the automated pipeline safely handles high-confidence predictions.

---

### 2.5 Multi-Dimensional Holdout Splitting ([`backend/app/ml/splitting.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/app/ml/splitting.py) - §10.4, E8)

- **`RegionHoldoutSplitter`:**
  Guarantees zero spatial overlap:
  $$\text{Regions}(\text{Train}) \cap \text{Regions}(\text{Test}) = \emptyset$$
  Non-held-out regions are chronologically split into train and validation sets.
- **`ModelVersionHoldoutSplitter`:**
  Guarantees zero NWP model version overlap between train/val and test partitions:
  $$\text{Versions}(\text{Train}) \cap \text{Versions}(\text{Test}) = \emptyset$$
  Evaluates system generalization to operational NWP physics and core upgrades (e.g. GFS v15 $\to$ v16).
- **`MultiDimensionalHoldoutSplitter`:**
  Combines temporal ordering, event isolation, geographic holdouts, and model-version holdouts into a single unified partitioner.

---

### 2.6 Automated CI Leakage Integration Test Suite ([`backend/tests/test_leakage_integration.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/tests/test_leakage_integration.py) - §8.3, §10.4, E9)

8 automated, deterministic test cases verifying data leakage prevention:
1. **Future Truth Removal Invariance:** Altering or removing future ground-truth data in upstream streams produces identical issue-time prediction features.
2. **Feature Availability Time Causality:** Features with `availability_time > issue_time` strictly trigger `FeatureLeakageError`.
3. **Strict Forbidden Ground-Truth Fields:** All 12 prohibited ground-truth fields (`actual_observation`, `era5_actual`, `forecast_error`, `bust_label`, etc.) are rejected during feature vector validation.
4. **Temporal Causality Monotonicity:** Verifies $\max(\text{train.issue\_time}) \le \min(\text{val.issue\_time}) \le \min(\text{test.issue\_time})$.
5. **Event-Grouping Isolation:** Verifies no extreme weather event episode spans across train, val, or test partitions.
6. **Geographic Region Holdout Isolation:** Verifies zero spatial overlap between train/val and held-out test sets.
7. **Model-Version Holdout Isolation:** Verifies zero NWP version overlap between train and test sets.
8. **Temporal Embargo Purge:** Verifies observations within the configured embargo window ($\Delta_{\text{embargo}} = 7\text{ days}$) of split boundaries are purged.

---

## 3. Test & Verification Results

### 3.1 Phase 3 Test Suite ([`backend/tests/test_phase3_ood_calibration.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/tests/test_phase3_ood_calibration.py))
- **Execution:** `pytest backend/tests/test_phase3_ood_calibration.py -v`
- **Result:** **16 passed in 0.10s (100% pass rate)**

| Test Case | Capability Tested | Result |
|---|---|---|
| `test_ood_detector_nominal_normal_state` | F5, F6: In-distribution features yield `OODState.NORMAL` ($S_{OOD} < 0.35$) | PASSED |
| `test_ood_detector_unusual_tail_state` | F5, F6: Tail deviation features yield `OODState.UNUSUAL` ($0.35 \le S < 0.65$) | PASSED |
| `test_ood_detector_extreme_ood_and_abstain` | F5, F6: Extreme anomaly features yield `OODState.OOD` / `ABSTAIN` ($S \ge 0.80$) | PASSED |
| `test_ood_distribution_drift_ks_and_wasserstein` | F5: KS-statistic and 1D Wasserstein drift computation | PASSED |
| `test_safety_evaluator_ood_normal_transition` | F6: Safety evaluator approves predictions under `NORMAL` state | PASSED |
| `test_safety_evaluator_ood_unusual_transition` | F6: Safety evaluator flags `UNUSUAL` state without abstention | PASSED |
| `test_safety_evaluator_ood_abstain_transition` | F6: Safety evaluator abstains under severe multi-anomaly state | PASSED |
| `test_split_conformal_predictor_calibration_and_intervals` | F4: Split conformal predictor calibration and interval computation | PASSED |
| `test_conformal_conditional_coverage_reporting` | F4: Conditional coverage reporting across lead time and regions | PASSED |
| `test_model_evaluator_reliability_diagram_and_ece` | F2: 10-bin reliability diagram, ECE, and MCE calculation | PASSED |
| `test_model_evaluator_calibration_slope_and_intercept` | F2: Logistic calibration slope $a$ and intercept $b$ | PASSED |
| `test_model_evaluator_full_report_with_phase3_metrics` | F2, F7: Full evaluation report with Brier, log-loss, ECE, coverage-risk | PASSED |
| `test_coverage_risk_curve_computation` | F7: Coverage-risk curve points and review burden metrics | PASSED |
| `test_region_holdout_splitter_execution` | E8: Zero spatial overlap in `RegionHoldoutSplitter` | PASSED |
| `test_model_version_holdout_splitter_execution` | E8: Zero version overlap in `ModelVersionHoldoutSplitter` | PASSED |
| `test_multi_dimensional_holdout_splitter_execution` | E8: Multi-dimensional holdout splitting execution | PASSED |

### 3.2 Leakage Integration Test Suite ([`backend/tests/test_leakage_integration.py`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RII/backend/tests/test_leakage_integration.py))
- **Execution:** `pytest backend/tests/test_leakage_integration.py -v`
- **Result:** **8 passed in 0.08s (100% pass rate)**

| Test Case | Anti-Leakage Invariant Tested | Result |
|---|---|---|
| `test_future_truth_removal_invariance` | E9: Altering future truth does not affect issue-time features | PASSED |
| `test_feature_availability_time_causality` | E9, D7: `availability_time > issue_time` raises `FeatureLeakageError` | PASSED |
| `test_strict_forbidden_ground_truth_fields` | E9, D8: All 12 forbidden ground-truth fields rejected | PASSED |
| `test_temporal_causality_monotonicity` | E9: Strict $\max(\text{train}) \le \min(\text{val}) \le \min(\text{test})$ | PASSED |
| `test_event_grouping_isolation` | E9: Zero event episode overlap across train/val/test partitions | PASSED |
| `test_region_holdout_spatial_isolation` | E9, E8: Zero spatial overlap between train/val and held-out test | PASSED |
| `test_model_version_holdout_isolation` | E9, E8: Zero version overlap between train and test | PASSED |
| `test_temporal_embargo_purge` | E9: Observations within 7-day embargo of split boundaries purged | PASSED |

### 3.3 Full Test Suite Regression Verification
- Executed entire test suite: `pytest -v` across all 507 tests in `backend/tests/`.
- **Result:** **507 passed in 44.40s (100% pass rate, 0 failures, 0 regressions)**.
- Verified that all single-prediction, batch-prediction, multi-location, dynamic-location, explainability, dashboard, and OOD calibration integration tests pass cleanly.

---

## 4. Status & Readiness for Next Phase

Phase 3 is **100% complete, verified, and passing all 507 tests across the entire codebase**.

### Summary of Closed Items:
- **F2 (Reliability diagram & calibration metrics):** COMPLETE ✅
- **F4 (Split conformal prediction & conditional coverage):** COMPLETE ✅
- **F5 (Multi-signal OOD detection engine):** COMPLETE ✅
- **F6 (Standardized 4-state vocabulary & pipeline propagation):** COMPLETE ✅
- **F7 (Coverage-risk curve & review burden):** COMPLETE ✅
- **E8 (Region, version & multi-dimensional holdouts):** COMPLETE ✅
- **E9 (Automated CI leakage integration test suite):** COMPLETE ✅

### Ready for Phase 4: Model Serving, Dynamic Ensemble & Explainability
Phase 4 will address:
- **E1**: Dynamic Lead-Specific & Region-Specific Thresholds
- **E2**: Extreme-Bust Secondary Classification Head
- **E4**: Spatial Bust Verification & Displacement Mitigation
- **E5**: Multi-Model NWP Ensemble & Divergence Engine
- **E6**: Complete Explainability Engine (SHAP, Confidence Intervals, Regime Context, Actionable Guidance)
- **E7**: Comprehensive Verification & CI Pipeline Hardening

*Awaiting your command to proceed with Phase 4.*
