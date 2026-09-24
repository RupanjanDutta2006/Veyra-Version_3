# Phase 8 — Submission readiness

## Objective

Produce a truthful, demonstrable, reproducible SIH Round-2 candidate.

## Inputs from Repository A

- Conservative claim language.
- Scope and certification policy.
- Safe failure and provenance UI checks.
- Selected migrated tests.

## Inputs from Repository B

- Repaired V3 artifacts and manifest.
- B destination backend/frontend.
- Passing required test and build reports.
- Experimental specialist registry.
- Evidence package and demo assets.

## Step-by-step work

1. Freeze the candidate SHA and release manifest.
2. Run clean-clone setup from documented locks.
3. Run artifact verification and model/calibrator loading.
4. Run golden V3 parity.
5. Run backend, frontend, API, security, replay, and smoke suites.
6. Run the 500-ID ledger generation.
7. Verify every public claim against the claim register.
8. Run browser E2E across all trust/provenance states.
9. Verify that no UI says live, certified, historical, or trained when the evidence class does not support that wording.
10. Produce a judge-facing demo script that demonstrates both normal output and safe abstention.
11. Produce a risk register and known-limitations sheet.
12. Obtain independent reviewer sign-off.
13. Tag the submission candidate and preserve the exact environment and evidence bundle.

## Outputs

- Submission candidate tag.
- Final claim sheet.
- Demo script and screenshots/video inputs.
- Test/build/artifact/replay evidence bundle.
- Limitations and risk register.
- Rollback tag.

## Failure conditions

- Any P0 blocker remains.
- V3 is unavailable or checksum-invalid.
- A specialist is presented as certified without Gate G8.
- Synthetic or fixture output is shown as live or historical.
- Independent review cannot reproduce the release.

## Final submission gate

The release is suitable only if all P0 blockers are closed, G0–G17 are either passed or explicitly justified as out of scope, the claim register matches the final UI/API/docs, and the independent reviewer can reproduce the artifacts, tests, build, smoke, and replay boundaries.

## Compulsory test for Phase 8 — submission dry run

Run from a fresh clone of the candidate tag:

```bash
set -euo pipefail
./scripts/clean_clone_reproduction.sh --tag "$CANDIDATE_TAG" --log-dir artifacts/submission_reproduction
python scripts/validate_claim_register.py --input manifests/claim_register.csv --require-final-ui-api-match
python scripts/run_submission_smoke.py --states ready,abstain,ood,live,cached,fixture,fallback,synthetic,unavailable
```

**Pass condition:** an independent clean-clone run reproduces the hashes, tests, build, smoke, provenance states, claim register, and rollback metadata with no unresolved P0 blocker.
