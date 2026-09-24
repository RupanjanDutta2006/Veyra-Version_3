# Veyra SIH Round-2 Evaluator Demonstration Script

## Executive Overview
**Veyra** predicts when Numerical Weather Prediction (NWP) forecasts are prone to catastrophic failure ("forecast bust"). This script provides evaluators with a 5-minute interactive verification walkthrough of the system across its scientific trust states.

---

## Interactive Demonstrations

### Demo 1: Verified V3 Incumbent Prediction (Kolkata Temperature 24h)
1. **Navigate:** Open the frontend dashboard (`http://localhost:5173` or deployed URL).
2. **Inputs:**
   - Station: `Kolkata` (`22.5726° N, 88.3639° E`)
   - Variable: `2m Temperature`
   - Horizon: `24 hours`
3. **Execution:** Click **"Evaluate Reliability"**.
4. **Expected Outcome:**
   - Status: `CERTIFIED`
   - Model Version: `veyra-v3-benchmark-lightgbm` (SHA256: `00a84107...`)
   - Bust Probability: Displays exact calibrated posterior probability `P(BUST)`.
   - Provenance Badge: Green `LIVE / CACHED PROVENANCE` with valid UTC issue and validity timestamps.

---

### Demo 2: Safe Selective Prediction Abstention
1. **Inputs:** Select an unsupported combination or pass an anomalous coordinate (`Latitude: 99.9° N`).
2. **Execution:** Click **"Evaluate Reliability"**.
3. **Expected Outcome:**
   - Status: `ABSTAIN` (Safe Abstention triggered).
   - Abstention Reason: `UNSUPPORTED_TARGET_SPECIFICATION` or `INSUFFICIENT_EVIDENCE`.
   - Crucial Invariant: The system **does NOT invent** fallback fake probabilities (`0.0%`) or falsely display `SUPPORTED`.

---

### Demo 3: Out-of-Distribution (OOD) Diagnostics
1. **Inputs:**
   - Station: `Kolkata`
   - Variable: `2m Temperature`
   - Value Override / Anomalous input: `Temperature = 350 K (77°C)`
2. **Execution:** Submit request.
3. **Expected Outcome:**
   - Status: Displays `OOD_WARNING` badge.
   - Diagnostic Report: Flags thermodynamic bounds violation.
   - Invariant: Diagnostic OOD warning remains separate from model inference posteriors.

---

### Demo 4: Replay Mode Separation (Historical vs Synthetic Twin)
1. **CLI Verification:**
   ```bash
   # 1. Historical Replay (Immutable forecasts + Independent truth)
   python scripts/replay_historical.py --mode historical
   
   # 2. Synthetic Digital Twin Replay (Simulated progression)
   python scripts/replay_digital_twin.py --mode synthetic
   ```
2. **Expected Invariant:**
   - Replay harness outputs explicit `[NOTICE] SYNTHETIC DIGITAL TWIN` when running simulations.
   - Rejects synthetic progression when `--mode historical` is specified.

---

## Known Scientific Boundaries & Limitations
1. **Hazard Specialists:** The 6 regional specialists (Precipitation, Cyclone, Monsoon, Heatwave, Western Disturbance, Severe Wind) are deterministic formula baselines and heuristics, NOT certified empirical ML models.
2. **Incumbent Model:** The sole certified empirical model is the frozen V3 LightGBM benchmark model trained on historical NOAA GEFSv12 benchmark records.
3. **Multi-Provider Demonstration:** Open-Meteo acts as an operational public proxy; ECMWF/NCMRWF multi-model comparisons are experimental demonstrations.
