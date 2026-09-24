# Phase D — Failure dynamics: motifs, hazard and recovery

**Blueprint levels:** 5,9,10,26,34,44    
**Current status:** **MISSING**

## Goal
Build episodes and trajectory tensors; learn Failure Motifs; build dependent hazard/survival and recovery transitions; add phase portraits and cascades only after ablations.

## Deliverables
episode builder; motif catalog; motif similarity; hazard/recovery models; replay trajectory APIs

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
python -m pytest backend/tests/test_failure_episodes.py backend/tests/test_failure_motifs.py -q
python -m pytest backend/tests/test_hazard_engine.py backend/tests/test_recovery_engine.py -q
python scripts/evaluate_trajectory_models.py --event-held-out --bootstrap cycle
```

## Failure and rollback
Do not turn threshold-derived time-to-failure into a hazard claim. Reject unstable motifs and fall back to independent horizons.

## Completion gate
Learned transitions reproduce held-out event chronology with uncertainty and honest state labels.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase D - failure dynamics: motifs, hazard and recovery"
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
