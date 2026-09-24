# Phase E — Tropical cyclone reliability specialist

**Blueprint gate:** Gate 4 / P1

## Goal
Implement separate cyclone track, intensity, rapid-intensification, landfall-location, landfall-timing and track-uncertainty targets. Use track spread/clustering, steering flow, moisture, shear, pressure tendency, revision and valid live-contract variables.

## Deliverables
CYCLONE_RELIABILITY_V1; event catalogue; track/intensity/landfall contracts; probabilistic and conformal challenger report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_cyclone_contract.py backend/tests/test_cyclone_targets.py backend/tests/test_hazard_specific_engines.py -q
python scripts/evaluate_hazard_engines.py --hazards cyclone --bootstrap cycle
python scripts/evaluate_conditional_coverage.py --hazard cyclone --bootstrap cycle
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not collapse cyclone failure into one opaque score. Do not use unavailable ocean or future observation variables. Reject conformal or sequence challengers that fail coverage, reproducibility or OOT tests.

## Completion gate
Track, intensity, rapid-intensification, timing and landfall outputs have separate labels, uncertainty, OOT and geographic evidence.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase E - tropical-cyclone-reliability-specialist"
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
