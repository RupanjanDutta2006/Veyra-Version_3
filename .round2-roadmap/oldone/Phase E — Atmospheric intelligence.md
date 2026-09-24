# Phase E — Atmospheric intelligence

**Blueprint levels:** 17,18,20,35,36    
**Current status:** **PARTIAL/MISSING**

## Goal
Add synoptic regimes, transitions, pressure-level vertical structure, terrain features and an extreme-event track; keep proxies distinct from validated physics.

## Deliverables
regime/vertical/terrain contracts; extreme label protocol; subgroup matrix

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
python -m pytest backend/tests/test_regime_features.py backend/tests/test_vertical_features.py backend/tests/test_terrain_features.py -q
python scripts/evaluate_regime_slices.py --oot --bootstrap cycle
python scripts/evaluate_extreme_track.py --held-out-events
```

## Failure and rollback
If data are unavailable, return explicit missingness. If tail results are unstable, keep the specialist research-only.

## Completion gate
Issue-time-safe features; one-family ablations; regime and extreme distributions with intervals.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase E - atmospheric intelligence"
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
