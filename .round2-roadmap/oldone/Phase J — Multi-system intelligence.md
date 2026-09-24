# Phase J — Multi-system intelligence

**Blueprint levels:** 14,15,23,24,41,43    
**Current status:** **MISSING/PARTIAL**

## Goal
Add forecast-system challengers, common-mode detector, cross-system transfer, version-shift tests and foundation representations as shadow challengers.

## Deliverables
multi-system contract; common-mode detector; transfer matrix; version-shift report; challenger registry

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
python -m pytest backend/tests/test_multi_system.py backend/tests/test_model_version_shift.py -q
python scripts/evaluate_cross_system.py --train-source ge fs --test-sources challenger --bootstrap cycle
python scripts/run_ablation.py --base v3 --family multi_system --bootstrap cycle
```

## Failure and rollback
Agreement is not confidence without regime evidence. Reject failed transfer and keep challengers shadow-only until rollback is tested.

## Completion gate
Unseen-source/version results, calibrated common-mode risk and no challenger replacement without incremental evidence.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase J - multi-system intelligence"
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
