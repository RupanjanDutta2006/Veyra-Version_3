# Phase G — Western disturbance reliability

**Blueprint gate:** Gate 6 / P1

## Goal
Build a reproducible western-disturbance event catalogue, regime detector, historical errors, motifs, jet/vertical features, terrain conditioning and specialist model for arrival, track, precipitation, displacement, duration, intensity and rain/snow partition only when observations support it.

## Deliverables
WD_RELIABILITY_V1; event catalogue; regime/target contract; terrain-conditioned validation report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_western_disturbance_contract.py backend/tests/test_western_disturbance_targets.py backend/tests/test_hazard_specific_engines.py -q
python scripts/evaluate_hazard_engines.py --hazards western_disturbance --bootstrap cycle
python scripts/evaluate_regime_slices.py --hazards western_disturbance --bootstrap cycle
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not build before event labels and references reproduce. Do not infer rain/snow failure without suitable observations.

## Completion gate
Arrival, position, precipitation, displacement and duration/intensity outputs pass event-held-out and terrain-conditioned tests.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase G - western-disturbance-reliability"
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
