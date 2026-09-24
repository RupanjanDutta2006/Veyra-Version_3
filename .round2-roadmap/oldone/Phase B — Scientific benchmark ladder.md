# Phase B — Scientific benchmark ladder

**Blueprint levels:** 0,1    
**Current status:** **PARTIAL/MISSING**

## Goal
Implement climatology, persistence, spread, logistic, EMOS, IDR, QRF/probabilistic trees, continuous-error head, V3 and calibrated V3 under identical splits.

## Deliverables
benchmark runner; continuous-error schema; reliability diagrams; coverage-risk curves; go/no-go report

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
python -m pytest backend/tests/test_ml_model_and_eval.py backend/tests/test_ml_splitting.py backend/tests/test_v3_calibration.py -q
python scripts/run_benchmark_ladder.py --config configs/benchmark_ladder.yaml --bootstrap cycle --seed 42
```

## Failure and rollback
If spread-only nearly matches V3, stop complexity and investigate missing information. Keep a continuous head offline if it worsens calibration or tail coverage.

## Completion gate
All baselines use the same OOT split, target, reference and cycle-block bootstrap; challenger improves predefined metrics or is rejected.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase B - scientific benchmark ladder"
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
