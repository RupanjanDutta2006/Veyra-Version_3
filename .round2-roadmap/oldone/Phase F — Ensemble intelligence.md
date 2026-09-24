# Phase F — Ensemble intelligence

**Blueprint levels:** 6,14,15    
**Current status:** **PARTIAL**

## Goal
Audit members; compute covariance, eigenvalues, anisotropy, effective dimension, clustering, spread growth, divergence and structured disagreement.

## Deliverables
member audit; geometry schema; predictability pressure; disagreement report

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
python -m pytest backend/tests/test_member_completeness.py backend/tests/test_ml_features.py -q
python -m pytest backend/tests/test_ensemble_geometry.py backend/tests/test_disagreement.py -q
python scripts/run_ablation.py --base v3 --family member_geometry --bootstrap cycle
```

## Failure and rollback
For too few members abstain or use a documented degraded mode. Remove geometry if it adds no stable incremental value.

## Completion gate
Permutation-invariant, issue-time-safe geometry with member-starvation behavior and an ablation decision.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase F - ensemble intelligence"
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
