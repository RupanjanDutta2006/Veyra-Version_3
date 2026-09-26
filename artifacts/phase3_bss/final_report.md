# Veyra Version-3 Phase 3 — BSS Remediation & Scientific Integrity Report

## Executive Summary
- **Branch**: `phase-3-bss-remediation`
- **Final Disposition**: **`PHASE_3_BLOCKED_DATA_PROVENANCE`**
- **Evidence Classification**: **`REPRODUCED_SYNTHETIC_FIXTURE`**
- **Evaluation Set**: Untouched Test Split ($N = 3,750$ records, period: 2024-11-15 to 2024-12-31)

---

## 1. Metric Performance Comparison (Untouched Test Split)

| Scientific Metric | Old Frozen Pipeline | Remediated Candidate (Frozen_Booster_Platt_Calibrated) | Training Climatology Baseline | 95% Bootstrap CI | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Brier Score** | `0.0808` | `0.0729` | `0.072029` | `[0.0656, 0.0809]` | `REMEDIATED` |
| **Brier Skill Score (BSS)** | `-0.1224` | `-0.0114` | `0.0000` | `[-0.1234, +0.0893]` | `REMEDIATED` |
| **Expected Calibration Error (ECE)** | `0.0704` | `0.0070` | N/A | `[0.0006, 0.0164]` | `IMPROVED` |
| **ROC-AUC** | `0.5638` | `0.5629` | `0.5000` | `[0.5269, 0.5958]` | `ANALYZED` |
| **PR-AUC** | `0.0996` | `0.1016` | `0.0781` | `[0.0864, 0.1235]` | `ANALYZED` |
| **Log Loss** | `0.3353` | `0.2763` | N/A | N/A | `IMPROVED` |

$$BSS = 1 - \frac{\text{Brier}_{\text{model}}}{\text{Brier}_{\text{baseline}}} = 1 - \frac{0.0729}{0.072029} = -0.0114$$

---

## 2. Root Cause Diagnostics of Negative BSS
The negative BSS in the initial Phase 3 report was driven by two distinct factors:
1. **Uncalibrated Probability Offset**: The frozen `probability_calibrator_v3.joblib` artifact predicted an average bust probability of `0.1666`, which was more than **2.0x the actual base rate ($p = 0.0802$)**. This systematic bias contributed **$\text{Bias}^2 = (0.1666 - 0.0802)^2 = 0.0075$** directly into the Brier score.
2. **Fixture Signal vs. Climatology Penalty**: When model probabilities systematically overpredict the true base rate, the squared error penalty exceeds that of predicting the constant mean climatology $\bar{p}_{\text{train}} = 0.0781$.
3. **Remediation**: Recalibration on the out-of-time validation split aligned model predictions with the base rate, reducing the Brier score from `0.0808` to `0.0729` and improving ECE from `0.0704` to `0.0070`.

---

## 3. Data Provenance Audit & Evidence Classification
- **Raw Payloads Audited**: `data/raw_sources/gefs_v12_raw_cycles_2024.json` (1,060 B), `era5_reanalysis_obs_2024.json` (720 B), `imd_aws_surface_obs_2024.json` (609 B).
- **Finding**: These payload files contain JSON metadata descriptors and access coordinates rather than full external binary meteorological archives (which are multi-gigabyte GRIB2/NetCDF files).
- **Honest Governance Rule**: Per prompt directives, a few hundred bytes cannot substantiate 15,000 live external observations. The dataset is strictly classified as **`REPRODUCED_SYNTHETIC_FIXTURE`** and the real-data release gate is blocked under **`PHASE_3_BLOCKED_DATA_PROVENANCE`**.

---

## 4. Release Gate Audit Table

| Gate # | Gate Description | Target Criterion | Achieved Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **1** | BSS on untouched test split | $> 0.00$ | `-0.0114` | `FAIL` |
| **2** | ROC-AUC discrimination | $> 0.50$ | `0.5629` | `PASS` |
| **3** | PR-AUC vs Climatology | $> 0.0781$ | `0.1016` | `PASS` |
| **4** | ECE Improvement | $\le 0.0704$ | `0.0070` | `PASS` |
| **5** | Zero Anti-Leakage Violations | 0 violations | `0 violations` | `PASS` |
| **6** | External Data Provenance | Real payload files | Descriptor seeds | `FAIL (BLOCKED)` |
