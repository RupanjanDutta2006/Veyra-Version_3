# Phase A — V3 certification and hazard data contracts

**Blueprint gate:** Gate 0

## Goal
Certify the frozen V3 before new model work. Resolve artifact hashes, canonical data, labels, splits, variables, units, references, Builder 1/2 parity, SQLAlchemy dependency, truthful readiness, and hazard availability. Create one operational contract per hazard with provider, variable, units, grid, issue/valid time, ensemble size, missingness, latency, reference, label and thresholds.

## Deliverables
V3_CERTIFIED; hazard_availability_matrix; data/target/reference manifests; unit and schema contracts; leakage report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pip install -r requirements.txt
python -m pytest backend/tests/test_v3_artifact_integrity.py backend/tests/test_v3_reference_parity.py backend/tests/test_leakage_integration.py -q
python -m pytest backend/tests/test_deployment_readiness.py backend/tests/test_vercel_entrypoint.py -q
cd frontend && npm ci && npm test -- --run && npm run build
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not build hazard models if V3 artifacts, canonical data, targets, reference, units or issue-time availability are unresolved. Mark a hazard ABSTAINED or FUTURE instead of fabricating data.

## Completion gate
V3 loads from a clean clone; authoritative metrics reproduce; all contracts are versioned; all tests exit 0; no future information is used.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase A - v3-certification-and-hazard-data-contracts"
git push origin main
```

If any command fails, do not push. Fix the failure, rerun every phase command, and push only after zero errors.

## Drop-in phase report

- Status: COMPLETE / PARTIAL / BLOCKED
- Commit, environment, commands and logs
- Test totals and failed test names
- Metrics and confidence intervals by hazard/lead/season/location/regime/severity/OOD/reference
- Leakage, ablation, negative-control and independent-truth results
- Failure cases, status taxonomy, rollback decision and next-phase authorization
