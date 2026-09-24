# Veyra Sentinel: Scientific Evidence & Promotion Register (Phase 06)

This directory houses the authoritative scientific evidence packages, promotion boundaries, and evaluation ledgers for all meteorological hazard reliability specialists in Veyra Sentinel.

---

## 1. Specialist Evidence Ledger

The authoritative status of all specialists and experimental engines is tracked in [`specialist_evidence_ledger.csv`](file:///c:/Users/adity/OneDrive/Desktop/SIH26079-RIII/repos/repo_b/docs/science-evidence/specialist_evidence_ledger.csv):

| Specialist / Engine | Hazard Family | Nature | Evidence Tier | Target Manifest | Evidence Package | Promotion Status | Active in Production |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Precipitation** | `precipitation` | Formula | `FORMULA_BASELINE` | `data/precipitation_target_manifest.json` | [`pilot_evidence_package_precipitation.md`](pilot_evidence_package_precipitation.md) | `UNPROMOTED_FORMULA` | **False** |
| **Cyclone** | `cyclone` | Formula | `FORMULA_BASELINE` | `data/cyclone_target_manifest.json` | *Pending authorized radar/AWS* | `UNPROMOTED_FORMULA` | **False** |
| **Monsoon/LPS** | `monsoon_lps` | Formula | `FORMULA_BASELINE` | `data/monsoon_target_manifest.json` | *Pending authorized radar/AWS* | `UNPROMOTED_FORMULA` | **False** |
| **Western Disturbance**| `western_disturbance` | Formula | `FORMULA_BASELINE` | `data/western_disturbance_target_manifest.json`| *Pending authorized radar/AWS* | `UNPROMOTED_FORMULA` | **False** |
| **Heatwave** | `heatwave` | Formula | `FORMULA_BASELINE` | `data/heatwave_target_manifest.json` | *Pending authorized radar/AWS* | `UNPROMOTED_FORMULA` | **False** |
| **Spatial Reliability** | `spatial_error_field` | Heuristic | `EXPERIMENTAL_HEURISTIC`| `data/spatial_target_manifest.json` | *Simulation research candidate* | `EXPERIMENTAL_RESEARCH` | **False** |
| **Compound Hazard** | `compound_events` | Heuristic | `EXPERIMENTAL_HEURISTIC`| N/A | *Simulation research candidate* | `EXPERIMENTAL_RESEARCH` | **False** |
| **Common Mode** | `common_mode_failure` | Heuristic | `EXPERIMENTAL_HEURISTIC`| N/A | *Simulation research candidate* | `EXPERIMENTAL_RESEARCH` | **False** |
| **Cross-System** | `cross_system_transfer`| Heuristic | `EXPERIMENTAL_HEURISTIC`| N/A | *Simulation research candidate* | `EXPERIMENTAL_RESEARCH` | **False** |
| **Severe Wind** | `severe_wind` | Stub | `QUARANTINED` | N/A | *Quarantined (missing package)* | `QUARANTINED_MISSING_PACKAGE` | **False** |

---

## 2. Gate G8 Scientific Promotion Invariants

To eliminate false scientific claims and maintain uncompromising academic and operational honesty:

1. **Deterministic Heuristics are NEVER labeled as Trained ML Models:** All five active hazard modules (`precipitation`, `cyclone`, `monsoon`, `western_disturbance`, `heatwave`) operate as physics-informed heuristics and formula baselines using verified meteorological thresholds (e.g. CAPE, moisture flux, shear, temperature anomalies).
2. **Hazard Occurrence is Strictly Separated from Forecast Bust Probability:** Predicting whether extreme weather will happen ($P(\text{Hazard})$) is fundamentally decoupled from predicting whether the NWP guidance will catastrophically fail ($P(\text{Bust} \mid \text{Hazard})$).
3. **Zero Unvalidated Promotions into Production:** No specialist output is permitted to alter, override, or enter the production incumbent V3 prediction pipeline without a certified empirical evidence package, verified model binary SHA-256 hash, and independent reviewer sign-off.
4. **Non-Causal Explanation Policy:** In compliance with `ExplanationPolicy`, all system explanations avoid unverified causal assertions (e.g. *"caused by"*, *"triggers"*, *"due to"*), using strictly observational framing (e.g. *"associated with"*, *"co-occurring with"*, *"indicative of"*).

---

## 3. Pilot Evidence Package: Precipitation

For complete architectural and empirical methodology, refer to the pilot dossier:
- [`pilot_evidence_package_precipitation.md`](pilot_evidence_package_precipitation.md): Comprehensive documentation covering target formulation, zero-leakage issue-time features, non-overlapping temporal splits, 6-tier baseline ladder validation, selective prediction risk-coverage curves, and cryptographic truth sealing.
