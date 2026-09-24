# Phase H — Heatwave and data-dependent severe-wind specialists

**Blueprint gate:** Gate 7 plus P2 extension

## Goal
Implement heatwave threshold, peak, onset, cessation, duration, spatial extent, persistence and nighttime targets. Add severe/high-wind only when paired forecast/reference data support defensible labels.

## Deliverables
HEATWAVE_RELIABILITY_V1; heatwave event/threshold contract; wind activation decision; specialist reports

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_heatwave_contract.py backend/tests/test_heatwave_targets.py backend/tests/test_hazard_specific_engines.py -q
python scripts/evaluate_hazard_engines.py --hazards heatwave --bootstrap cycle
python scripts/evaluate_hazard_engines.py --hazards severe_wind --bootstrap cycle
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not activate severe wind without paired data. Do not hide small extreme samples. Reject persistence models that fail geographic or seasonal holdouts.

## Completion gate
Heatwave threshold/timing/duration/persistence outputs are calibrated and OOT-tested; severe wind is CERTIFIED only if data and labels pass Gate 0.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase H - heatwave-and-data-dependent-severe-wind-specialists"
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
