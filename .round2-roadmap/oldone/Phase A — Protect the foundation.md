# Phase A — Protect the foundation

**Blueprint levels:** 0,25,28,29,41,42    
**Current status:** **PARTIAL/BLOCKED**

## Goal
Resolve V3 artifact provenance; freeze data, labels, splits and metrics; repair dependencies; make readiness truthful; reproduce baseline; attack leakage.

## Deliverables
artifact_manifest; data_manifest; label/split contracts; authoritative benchmark; clean-install CI

## Work order
1. Freeze the input, target, provenance and schema.
2. Implement the smallest safe version.
3. Add tests and leakage/negative controls.
4. Compare against the frozen baseline.
5. Integrate only when the end-of-phase test is zero-error.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
cd /home/ubuntu/work/veyra
python -m pip install -r requirements.txt
python -m pytest backend/tests/test_v3_artifact_integrity.py backend/tests/test_v3_reference_parity.py backend/tests/test_leakage_integration.py -q
python -m pytest backend/tests/test_deployment_readiness.py backend/tests/test_vercel_entrypoint.py -q
cd frontend && npm ci && npm test -- --run && npm run build
```

## Failure and rollback
Block all downstream modeling if artifacts, data, hashes, target or splits disagree. Roll back to the last verified release. Never report SERVING from hard-coded metadata.

## Completion gate
Clean clone installs; V3 hashes and loading pass; one benchmark source is authoritative; leakage and CI pass.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase A - protect the foundation"
git push origin main
```

If any command fails, **do not push**. Fix the failure, rerun the complete phase test, and push only after the result is zero-error.

## Drop-in phase report
- Status: COMPLETE / PARTIAL / BLOCKED
- Commit, environment, commands and logs
- Test totals and failed test names
- Metrics with confidence intervals
- Leakage, ablation and negative-control results
- Failure cases, rollback decision and next-phase authorization
