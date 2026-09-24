# Phase 4 — Selective safety grafting

## Objective

Port only Repository A patterns that improve operational honesty and failure safety without changing the V3 incumbent.

## Inputs from Repository A

- `backend/app/core/time_contract.py`.
- `backend/app/core/certification_policy.py`.
- `backend/app/core/ood_policy.py`.
- `backend/app/builder2/v3_model_adapter.py`.
- `backend/app/api/v1/endpoints/predict.py`.
- `backend/app/services/revision_service.py`.
- Provider adapters and disagreement tests.
- `test_day34_time_contract_revision_store.py`.
- `test_day35_independent_replay_release_manifest.py`.
- `test_day37_provider_adapters.py`.
- `test_day38_cross_provider_disagreement.py`.
- `test_scientific_certification.py`.
- Relevant `backend/tests/test_v3_*`.

## Inputs from Repository B

- `backend/app/builder2/v3_model_adapter.py`.
- `backend/app/safety/ood_detector.py`.
- `backend/app/safety/ood_enforcement.py`.
- `builder2/calibrator.py`.
- `conditional_calibration_engine.py`.
- `data/hazard_calibration_registry.json`.
- B prediction schemas and versioned routes.
- B frontend provenance and trust-state components.

## Step-by-step work

1. Port A’s UTC and issue-time contract into B’s canonical data contract.
2. Port safe model-unavailable behavior without changing B’s successful V3 output.
3. Define explicit response states: ready, abstain, OOD, unavailable, live, cached, fixture, fallback, and synthetic.
4. Port certification policy as a scope and wording policy, not as proof of certification.
5. Consolidate OOD behavior so diagnostic OOD and active abstention are separate fields and code paths.
6. Port provider identity and fixture disclosure into B’s response schema.
7. Port revision semantics only after agreeing on a canonical storage contract.
8. Port A tests into B’s destination test style, maintaining test intent and source traceability.
9. Add API schema-diff tests.
10. Run V3 golden parity after every safety change.
11. Add failure-path tests for missing model, corrupted model, missing provider, stale data, and invalid timestamps.

## Outputs

- B-native safety modules.
- Unified trust/provenance response schema.
- Migrated safety and disclosure tests.
- Explicit OOD/abstention contract.
- Certification wording and UI policy.

## Failure conditions

- Probability fields change semantics.
- Provider identity or UTC identity is dropped.
- A diagnostic OOD signal becomes an active abstention without a documented gate.
- Safety changes alter golden V3 results.
- A fixture is exposed as live.

## Gates

- V3 parity remains green.
- Issue-time leakage tests pass.
- Missing-model behavior abstains safely.
- API schemas preserve separate bust, hazard, OOD, uncertainty, and provenance fields.

## Compulsory test for Phase 4 — safety and semantic parity

Run the migrated safety tests and the golden V3 parity check:

```bash
set -euo pipefail
pytest -q backend/tests/test_v3_* backend/tests/test_scientific_certification.py
pytest -q backend/tests/test_day34_time_contract_revision_store.py backend/tests/test_day37_provider_adapters.py backend/tests/test_day38_cross_provider_disagreement.py
python scripts/compare_golden_v3_outputs.py --baseline artifacts/golden_v3_before.json --candidate artifacts/golden_v3_after.json
```

**Pass condition:** tests pass, missing-model behavior abstains safely, UTC/provider/provenance fields remain present, and golden calibrated V3 outputs remain within the declared tolerance.
