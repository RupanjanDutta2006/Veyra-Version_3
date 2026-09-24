# SIH26079 — Deterministic Judging Demo Guide (§20)

**Problem Statement:** SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Organization:** Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)  
**Theme:** Disaster Management  
**Case Study:** Extremely Severe Cyclonic Storm Tauktae (May 14–17, 2021) — Rapid Intensification Forecast Bust  

---

## 1. Overview & Demonstration Objective

This 12-step demo plan guides judges and reviewers through the deterministic evaluation of **Veyra Sentinel** against a high-impact historical forecast failure: the rapid intensification of **Cyclone Tauktae** along the Gujarat coastline in May 2021.

### Key Capabilities Demonstrated:
1. **Advance Warning Lead-Time Gain (+24h to +48h)**: Veyra detects revision acceleration and synoptic regime instability at 72h/48h lead, flagging elevated bust risk when raw ensemble spread remains dangerously narrow.
2. **Sealed Future Truth**: Ground truth observations (ERA5 analysis) are sealed during evaluation, preventing lookahead leakage.
3. **Auditable Reason Codes & SHAP Attribution**: Transparent, non-causal evidence linking risk to atmospheric mechanisms.
4. **Authoritative Null-State Handling**: Transparent handling of "No eligible analog found" and OOD abstention.

---

## 2. The 12-Step Judging Demo Script

| Step | Action | Interface / Endpoint | Expected Outcome | Scientific Rationale |
|---|---|---|---|---|
| **1** | Open Sentinel Dashboard | Browser `http://localhost:5173` | Full interactive UI loads with Leaflet map, risk gauge, and telemetry. | Initial state shows system health and active model `builder2_v3`. |
| **2** | Navigate to "Historical Replay" Tab | Top navigation bar | Replay viewer displays Cyclone Tauktae case study selector. | Deterministic case library prevents ad-hoc test cherry-picking. |
| **3** | Inspect Cycle 1 (132h Lead) | Stepper: Step 1 (`2021-05-12T00Z`) | **GREEN Band** ($p=0.18$, Low Risk). High confidence. | Ensemble members agree on nominal tropical depression; error growth not yet initiated. |
| **4** | Step to Cycle 2 (96h Lead) | Stepper: Step 2 (`2021-05-13T12Z`) | **YELLOW Band** ($p=0.42$, Moderate Risk). Reason: `REVISION_ACCELERATION`. | Early cycle-to-cycle revision acceleration detected before spread widens. |
| **5** | Step to Cycle 3 (72h Lead) | Stepper: Step 3 (`2021-05-14T12Z`) | **ORANGE Band** ($p=0.68$, High Risk). Reason: `SPREAD_COLLAPSE_HIGH_BIAS`. | Track begins shifting eastward; ensemble dispersion under-represents intensification. |
| **6** | Step to Cycle 4 (48h Lead) | Stepper: Step 4 (`2021-05-15T12Z`) | **RED Band** ($p=0.88$, Critical Risk). Advance alert triggered. | **Crucial Moment**: Veyra sounds critical bust alert **24h before** traditional NWP spread widens. |
| **7** | Toggle Model vs Baseline | "Compare Spread-Only Baseline" button | Side-by-side card highlights **+24.0h Lead-Time Gain** over spread-only baseline. | Proves added value of revision trajectory and regime features beyond spread alone. |
| **8** | Inspect Evidence & Attribution Panel | "Explainability" tab / panel | Signed SHAP bars show `revision_acceleration` ($+0.312$) and `convective_regime` ($+0.185$). | Proves zero future leakage (`availability_time <= issue_time`). |
| **9** | Click "Reveal Ground Truth Verification" | "Reveal Ground Truth" button | ERA5 ground truth unsealed: actual wind $51.4\text{ m/s}$ ($185\text{ km/h}$) vs forecast $32.0\text{ m/s}$. | Confirms actual severe bust occurred; validates Veyra's advance warning. |
| **10** | Explore Analog Explorer | "Analog Explorer" tab | Displays top historical Arabian Sea cyclone analogs with similarity $> 0.70$. | Verifies B6 event-exclusion rule (no cases from same episode). |
| **11** | Test Negative Control / Abstention | Query `location="Pacific Ocean"` or `lat=80.0` | **ABSTAIN Banner**: *"I don't know — human review required"*; probability suppressed. | Proves K4 safety invariant: extreme OOD cases never receive confident numbers. |
| **12** | Review Provenance Drawer | "Data Provenance" drawer | Displays SHA-256 artifact checksums, pipeline lineage, and ERA5 verification invariant. | Demonstrates full compliance with MoES/NCMRWF scientific reproducibility standards. |

---

## 3. Terminal Replay Verification (CLI Mode)

To verify the replay case programmatically via the Python API:

```python
import json

with open("demo/replay_case/cyclone_tauktae_may2021.json", "r") as f:
    replay_data = json.load(f)

print(f"Loaded Case: {replay_data['title']}")
for cycle in replay_data["cycles"]:
    print(f"Step {cycle['step']} ({cycle['lead_hours']}h lead): P(Bust)={cycle['bust_probability']:.2f} [{cycle['color_band']}] - Driver: {cycle['primary_driver']}")

print(f"\nAdvance Warning Lead-Time Gain: +{replay_data['summary']['advance_warning_gain_hours']} hours")
```

---

## 4. Key Takeaways for Evaluation Panel

1. **Not a Weather Model**: Veyra Sentinel does not attempt to forecast the weather; it monitors the NWP forecasting system itself.
2. **Actionable Decision Support**: By warning 24 to 48 hours earlier of potential forecast failure, disaster management authorities gain vital lead time for cyclone evacuations and emergency positioning.
3. **Rigorous Scientific Integrity**: Strict adherence to no-lookahead invariants, honest spread-only baseline comparisons, and explicit abstention when out-of-distribution.
