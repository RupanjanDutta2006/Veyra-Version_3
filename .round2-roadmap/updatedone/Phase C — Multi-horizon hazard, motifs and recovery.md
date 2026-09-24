# Phase C — Multi-horizon hazard, motifs and recovery

**Blueprint gate:** Gate 2

## Goal
Build Failure Memory retrieval, failure episodes, trajectory representation, data-derived motifs, multi-horizon risk curves, time-to-bust, survival, recovery state, lead-wise calibration and abstention-aware transitions.

## Deliverables
HAZARD_ENGINE_V1; motif catalog; retrieval evidence; hazard/survival/recovery APIs; state-transition report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_failure_episodes.py backend/tests/test_failure_motifs.py backend/tests/test_hazard_engine.py backend/tests/test_recovery_engine.py -q
python scripts/evaluate_trajectory_models.py --event-held-out --bootstrap cycle
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not treat threshold-derived time-to-failure as learned hazard. Reject unstable motifs, future-period analogs, pre-truth calibration, and UI-only recovery labels.

## Completion gate
Held-out event chronology supports learned hazard/recovery; state transitions are historical; evidence includes support counts, uncertainty and provenance.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase C - multi-horizon-hazard,-motifs-and-recovery"
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
