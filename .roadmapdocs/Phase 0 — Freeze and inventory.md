# Phase 0 — Freeze and inventory

## Objective

Freeze both audited states and create an immutable evidence baseline before any integration edit.

## Entry criteria

- Read-only clones are available.
- The two audited SHAs are recorded.
- The supplied documentation archive is preserved.
- No integration branch has been created from unrecorded working-tree changes.

## Inputs from Repository A

- SHA `b9f52d3eeec8676e06b1879f05b404605e2501be`.
- `models/v3/feature_names.json`.
- `models/v3/lightgbm_v3_challenger.joblib` and `models/v3/probability_calibrator_v3.joblib` as pointer-file evidence only.
- `training_manifest.json` and `v3_evaluation_manifest.json`.
- `backend/app/core/release_manifest.*`.
- `backend/app/builder2/v3_model_adapter.py`.
- `backend/app/builder2/v3_feature_pipeline.py`.
- `backend/app/api/v1/endpoints/predict.py`.
- Test and build logs already recorded by the audit.

## Inputs from Repository B

- SHA `82eded8194151e37fb9b3eecf273010dc62d7b29`.
- `models/v3/lightgbm_v3_challenger.joblib`.
- `models/v3/probability_calibrator_v3.joblib`.
- `models/v3/feature_names.json`.
- `artifact_manifest.json`, `training_manifest.json`, `v3_evaluation_manifest.json`, and `v3_comprehensive_evaluation.json`.
- `models/day4/*` and `models/baseline_logistic_v1*`.
- `backend/app/builder2/v3_model_adapter.py`.
- `scripts/verify_artifacts.py`.
- Backend/frontend test and build logs.

## Step-by-step work

1. Create read-only tags or archive references for both audited SHAs.
2. Record default branch, commit timestamp, remote URL, working-tree status, and visible history depth.
3. Produce a complete path inventory for code, models, calibrators, manifests, tests, scripts, docs, deployment, and data.
4. Compute SHA256 for every model, calibrator, feature schema, manifest, lock file, and release artifact.
5. Record whether each file is a real payload, pointer text, fixture, generated output, or documentation.
6. Preserve the exact audit test logs, warnings, runtimes, failures, skipped tests, and errors.
7. Create a source-to-destination ledger with one row per candidate asset.
8. Record all duplicate trees in Repository A and mark them as historical or noncanonical until proven otherwise.
9. Freeze the current comparison scores and evidence classes.
10. Create an integration branch based on Repository B only.

## Outputs

- Signed or otherwise integrity-protected inventory.
- SHA/path ledger for both repositories.
- Candidate asset ledger.
- Baseline test/build/runtime evidence bundle.
- Immutable audit snapshot.

## Failure conditions

- Any source or artifact changes without a new hash and reason.
- Missing audit logs.
- Ambiguous source of a copied file.
- A pointer file being recorded as a deployable model.

## Gate P0-0

The inventory must reproduce the two audited SHAs and must identify every model, calibrator, feature schema, manifest, test root, deployment file, and duplicate application tree.

## Compulsory test for Phase 0 — inventory and freeze

Run from the workspace root after the inventory is generated:

```bash
set -euo pipefail
test "$(git -C repos/repo_a status --porcelain)" = ""
test "$(git -C repos/repo_b status --porcelain)" = ""
git -C repos/repo_a rev-parse HEAD | grep -q '^b9f52d3eeec8676e06b1879f05b404605e2501be$'
git -C repos/repo_b rev-parse HEAD | grep -q '^82eded8194151e37fb9b3eecf273010dc62d7b29$'
test -s manifests/repo_a_artifact_hashes.sha256
test -s manifests/repo_b_artifact_hashes.sha256
```

**Pass condition:** both clean-checkout inventories, SHAs, and artifact-hash manifests exist and match the frozen evidence.
