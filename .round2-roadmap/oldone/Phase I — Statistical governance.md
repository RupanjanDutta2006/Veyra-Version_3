# Phase I — Statistical governance

**Blueprint levels:** 2,3,30,31    
**Current status:** **PARTIAL/MISSING**

## Goal
Implement conditional calibration, delayed-truth conformal updates, miscoverage memory/prediction, risk control and tail coverage.

## Deliverables
slice calibration tables; miscoverage memory; update ledger; risk-control policy; tail report

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
python -m pytest backend/tests/test_phase3_ood_calibration.py backend/tests/test_v3_calibration.py -q
python -m pytest backend/tests/test_conditional_calibration.py backend/tests/test_miscoverage_engine.py -q
python scripts/evaluate_conditional_coverage.py --slices season,lead,location,regime,ood --bootstrap cycle
```

## Failure and rollback
Never claim universal conditional coverage. Block pre-truth updates. Preserve the previous calibrator on tail/OOD degradation.

## Completion gate
Every slice reports sample size, coverage, interval, CI and shift assumption; updates are delayed, bounded, versioned and reversible.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase I - statistical governance"
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
