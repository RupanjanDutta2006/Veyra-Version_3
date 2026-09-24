# Phase 1 — Truth alignment and claim register

## Objective

Make documentation, source code, artifacts, tests, and runtime claims agree before moving code.

## Inputs from Repository A

- `backend/app/core/certification_policy.py`.
- `backend/app/core/time_contract.py`.
- `backend/app/core/ood_policy.py`.
- Provider adapter and disagreement tests.
- `Audits/VEYRA_*` material.
- Current README and integration contracts.

## Inputs from Repository B

- `ARCHITECTURE.md`.
- `REPRODUCIBILITY_PACKAGE.md`.
- `docs/*`.
- `.round2-roadmap/*`.
- `round2-report/*`.
- `backend/app/builder2/*specialist.py` modules.
- Specialist JSON metrics and certification manifests.
- `cross_system_transfer_engine.py` and digital-twin material.

## Step-by-step work

1. Create a claim register with columns: claim, source file, code path, artifact path, test command, runtime observation, evidence class, current status, owner, and correction.
2. Classify every major claim as `REPRODUCED`, `SUPPORTED_BY_ARTIFACT`, `SUPPORTED_BY_CODE_ONLY`, `SUPPORTED_BY_TEST_FIXTURE_ONLY`, `DOCUMENTATION_ONLY`, `CONTRADICTED`, or `UNVERIFIED`.
3. Remove or qualify broad `CERTIFIED` language where independent scientific evidence is absent.
4. Label deterministic specialist formulas as formula baselines.
5. Label digital-twin synthetic progression as synthetic or fixture behavior.
6. Label fallback, risk-map, cached, and fixture paths in both API and UI terms.
7. Separate hazard occurrence claims from forecast-bust claims.
8. Separate calibration, OOD, abstention, provider disagreement, uncertainty, and forecast error in schemas and prose.
9. Mark NCMRWF, NEPS, IMD, DWR, INSAT, and cross-system statements as future or documentation-only unless paired data, metadata, permission, and replay evidence exist.
10. Correct stale test counts and never turn total test counts into 500-test certification.
11. Add a documentation-drift disposition: retain, rewrite, archive, or reject.

## Outputs

- Master claim register.
- Stale/contradicted documentation list.
- Corrected README and release-language draft.
- Evidence-class labels for all public claims.
- UI/API provenance wording specification.

## Failure conditions

- Unsupported certification remains in current production-facing text.
- Synthetic outputs can still be interpreted as historical or live.
- Hazard probability is exposed as `P(BUST)` without a separate target definition.
- A metric is labeled reproduced without a rerun or valid frozen artifact chain.

## Gate P0-1

Every public scientific claim must map to an evidence class and a current owner. No undocumented claim can be promoted in later phases.

## Compulsory test for Phase 1 — claim register completeness

Run the claim-register audit before importing any module:

```bash
set -euo pipefail
test -s manifests/claim_register.csv
python3 scripts/validate_claim_register.py --input manifests/claim_register.csv --required-classes REPRODUCED,SUPPORTED_BY_ARTIFACT,SUPPORTED_BY_CODE_ONLY,SUPPORTED_BY_TEST_FIXTURE_ONLY,DOCUMENTATION_ONLY,CONTRADICTED,UNVERIFIED
! grep -RInE '(^|[^A-Za-z])(CERTIFIED|live historical|NCMRWF validated)' docs README.md 2>/dev/null | grep -vE 'DOCUMENTATION_ONLY|UNVERIFIED|experimental' || true
```

**Pass condition:** every major claim has an evidence class, source path, owner, and correction; unsupported certification and live-science wording is removed or explicitly qualified.
