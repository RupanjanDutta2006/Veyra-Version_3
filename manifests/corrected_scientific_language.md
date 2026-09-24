# Veyra Scientific Communication & Certification Boundary Guide

## 1. Truth in Terminology Standards

To ensure scientific honesty and maintain alignment with the evidence hierarchy:

| Forbidden / Misleading Term | Approved Honest Term | Scientific Reason |
|---|---|---|
| "6 Certified Meteorological Hazard Specialists" | "6 Prototype Hazard Reliability Heuristic Engines" | The specialist modules use deterministic formulas/rules, not trained, independently calibrated machine learning models. |
| "Certified P(Bust) Predictor" | "Calibrated Forecast Bust Sentinel (V3 LightGBM Incumbent)" | Certification requires independent operational body authority. Veyra provides well-calibrated statistical uncertainty. |
| "Live NCMRWF / NEPS / IMD Operational Feed" | "Demonstration Feed via Open-Meteo Public NWP (National Adaptor Architecture Ready)" | Only Open-Meteo live API is connected. National agency feeds are architected as stub/adapter endpoints. |
| "Digital Twin Atmospheric Simulation" | "Interactive Synthetic Progression Demonstration" | The replay scripts deterministically simulate scenario metrics for UI evaluation, not physical atmospheric physics. |
| "Empirical Guarantee of >=90% Conformal Coverage" | "Prototype Conformal Calibration Layer (Tested on Fixtures)" | True coverage guarantees require extensive out-of-distribution real-world validation. |
| "Dual Live Ensemble Disagreement" | "Cross-Provider Disagreement Engine (Provider A Live, Provider B Fixture)" | Only Provider A is live; Provider B runs against test fixtures. |

## 2. Separate Semantic Concepts Standard

Code and UI must never conflate the following 9 distinct concepts:
1. `calibrated_p_bust`: Calibrated probability (0.0 to 1.0) that issued forecast error exceeds critical threshold.
2. `hazard_probability`: Probability of severe meteorological event occurrence (e.g. rain > 65mm).
3. `continuous_error_estimate`: Predicted magnitude of parameter deviation (e.g. +/- 4.2 C).
4. `conformal_interval`: Validated coverage interval at 1 - alpha significance.
5. `ensemble_dispersion`: Spread among NWP ensemble members.
6. `provider_disagreement`: Quantitative divergence between independent forecast models (e.g. ECMWF vs GFS).
7. `ood_novelty_score`: Distance of current atmospheric state from model training manifold.
8. `confidence_heuristic`: Composite operational heuristic score.
9. `certification_status`: Explicit declaration of whether model meets formal boundary standards.
