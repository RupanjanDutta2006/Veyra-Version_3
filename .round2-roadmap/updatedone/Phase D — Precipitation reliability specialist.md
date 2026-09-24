# Phase D — Precipitation reliability specialist

**Blueprint gate:** Gate 3 / P0 mandatory

## Goal
Implement precipitation failure for occurrence, amount, threshold, heavy rain, extreme rain, timing, spatial displacement and distinct 6/12/24/48/72-hour accumulations. Progress from target/data audit to climatology, raw ensemble, spread logistic, V3 plus precipitation features, continuous error, heavy-rain specialist, sequence/spatial challengers, independent reference, calibration/OOD, integration.

## Deliverables
PRECIP_RELIABILITY_V1; precipitation target/threshold manifest; specialist model; benchmark/ablation/calibration report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_precipitation_contract.py backend/tests/test_precipitation_targets.py backend/tests/test_hazard_specific_engines.py -q
python scripts/evaluate_hazard_engines.py --hazards precipitation --bootstrap cycle
python scripts/evaluate_conditional_coverage.py --hazard precipitation --bootstrap cycle
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not call rainfall reliability flood probability. Unsupported amount, timing, spatial or extreme fields remain null. Keep heavy/extreme results research-only when sample size is inadequate.

## Completion gate
Precipitation specialist beats or justifiably rejects each baseline; occurrence/amount/timing/spatial outputs are separate; tail counts, uncertainty, OOD and reference sensitivity are reported.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase D - precipitation-reliability-specialist"
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
