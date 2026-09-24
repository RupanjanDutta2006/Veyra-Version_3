# Phase 6 — Experimental module containment and scientific promotion boundary

## Objective

Keep Repository B’s broad architecture without allowing unvalidated specialists to enter the incumbent path.

## Inputs from Repository A

- `backend/app/core/certification_policy.py`.
- Scope labels and certification-boundary tests.
- Provider disclosure and safety UI patterns.
- `backend/app/services/spatial_service.py` and spatial schemas/tests.

## Inputs from Repository B

- `backend/app/builder2/precipitation_specialist.py`.
- `cyclone_specialist.py`.
- `monsoon_specialist.py`.
- `western_disturbance_specialist.py`.
- `heatwave_specialist.py`.
- `spatial_reliability_engine.py`.
- `compound_hazard_engine.py`.
- `common_mode_detector.py`.
- `cross_system_transfer_engine.py`.
- `evidence_graph_engine.py`.
- `explainer.py`.
- `services/explainability_service.py`.
- Hazard target/event JSON and specialist JSON manifests.
- `data/spatial_network_topology.json`.

## Step-by-step work

1. Register every specialist as `experimental`, `formula_baseline`, or `candidate`, never automatically `certified`.
2. Put specialists behind feature flags and explicit route/configuration boundaries.
3. Keep formula outputs separate from trained model outputs.
4. Add provenance fields for coefficients, thresholds, input data, and model artifacts.
5. Add per-hazard target definitions, data splits, seeds, artifact IDs, and evaluation manifests.
6. Define promotion gates for Brier, BSS, ECE, calibration slope/intercept, PR-AUC, warning lead, interval coverage, bootstrap uncertainty, OOD, and out-of-time performance.
7. Require hazard occurrence and forecast-bust targets to be separate.
8. Quarantine unsupported JSON metrics and certification labels.
9. Keep spatial, compound, common-mode, and cross-system paths experimental.
10. Ensure evidence-graph and explanation outputs use non-causal wording unless causal evidence exists.
11. Reject severe-wind certification until an independent specialist package exists.
12. Add an independent reviewer gate before any specialist is promoted.

## Outputs

- Experimental module registry.
- Formula-baseline labels.
- Per-hazard promotion template.
- Specialist evidence package schema.
- Quarantined unsupported claims.
- Non-causal explanation contract.

## Failure conditions

- Any formula is called trained or certified.
- A specialist changes the incumbent output without passing promotion gates.
- A hazard probability is surfaced as `P(BUST)`.
- A JSON metric is treated as reproduced without rerun.
- Cross-system or common-mode claims rely only on fixtures.

## Gate G8

No specialist enters the production path until an independent package contains: source data provenance, issue-time split, target definition, feature schema, trained artifact, calibrator if used, model hash, evaluation script, raw outputs, bootstrap/OOT/OOD results, and reviewer sign-off.

## Compulsory test for Phase 6 — specialist containment

Run the promotion-boundary test:

```bash
set -euo pipefail
pytest -q backend/tests/test_specialist_registry.py backend/tests/test_experimental_feature_flags.py backend/tests/test_claim_boundaries.py
python scripts/check_production_specialists.py --fail-on-unvalidated-promotion
```

**Pass condition:** every deterministic specialist is labeled experimental or formula baseline, no unsupported `CERTIFIED` promotion is possible, and specialist outputs cannot silently replace the V3 incumbent.
