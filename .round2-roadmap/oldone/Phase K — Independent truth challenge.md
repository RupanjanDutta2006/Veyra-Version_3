# Phase K — Independent truth challenge

**Blueprint levels:** 21,22    
**Current status:** **MISSING**

## Goal
Add station, radiosonde, GNSS/satellite/radar verification; compare ERA5 with independent truth; expose reference uncertainty/disagreement.

## Deliverables
independent-truth manifest; collocation/QC; reference agreement score; reference state

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
python -m pytest backend/tests/test_independent_truth.py backend/tests/test_reference_uncertainty.py -q
python scripts/evaluate_reference_challenge.py --references era5,station --event-held-out --bootstrap cycle
```

## Failure and rollback
Do not use future/interpolated truth as issue-time features. If observations are sparse, report REFERENCE_UNAVAILABLE and do not claim operational validation.

## Completion gate
Versioned, quality-controlled references; performance distributions by reference and uncertainty state.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase K - independent truth challenge"
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
