# Phase J — Hazard-specific calibration, OOD, drift and independent truth

**Blueprint gate:** Gates 9 plus calibration/OOD

## Goal
Report global, lead, season, location, regime, severity, OOD and reference metrics for every hazard. Add conditional/conformal governance, risk-coverage, drift and abstention. Compare ERA5 against station, radiosonde, satellite, GNSS or other legitimate independent evidence.

## Deliverables
INDEPENDENT_TRUTH_AUDIT; hazard calibration registry; OOD/drift ledger; abstention policy; reference sensitivity report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_hazard_calibration_ood.py backend/tests/test_conditional_calibration.py backend/tests/test_independent_truth.py backend/tests/test_reference_uncertainty.py -q
python scripts/evaluate_conditional_coverage.py --all-hazards --slices lead,season,location,regime,severity,ood,reference --bootstrap cycle
python scripts/evaluate_reference_challenge.py --references era5,station --event-held-out --bootstrap cycle
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Never claim universal conditional coverage. Block online updates before legitimate truth arrival. If independent observations are sparse, report REFERENCE_UNAVAILABLE rather than operational validation.

## Completion gate
Every hazard has calibrated reliability diagrams, risk-coverage, OOD/drift behavior, reference sensitivity, tail/event counts and explicit abstention.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase J - hazard-specific-calibration,-ood,-drift-and-independent"
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
