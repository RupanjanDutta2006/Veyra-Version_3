# Phase F — Monsoon and low-pressure-system reliability

**Blueprint gate:** Gate 5 / P1

## Goal
Cover low-pressure systems, depressions, deep depressions, monsoon depressions, active/break regimes, system location, propagation speed, rainfall placement/intensity, deepening and regime transitions. Combine system dynamics, precipitation and transition reliability without one opaque score.

## Deliverables
MONSOON_RELIABILITY_V1; event/regime catalogue; track/rainfall/transition targets; specialist and motif report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_monsoon_contract.py backend/tests/test_monsoon_targets.py backend/tests/test_hazard_specific_engines.py -q
python scripts/evaluate_hazard_engines.py --hazards monsoon,lps --bootstrap cycle
python scripts/evaluate_regime_slices.py --hazards monsoon,lps --bootstrap cycle
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not label monsoon dynamics from a UI regime alone. Reject models without enough events for active/break or transition slices.

## Completion gate
System dynamics, precipitation and regime-transition failure are separately calibrated and validated across seasons, regions and unseen periods.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase F - monsoon-and-low-pressure-system-reliability"
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
