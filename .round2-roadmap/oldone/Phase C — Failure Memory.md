# Phase C — Failure Memory

**Blueprint levels:** 4    
**Current status:** **PARTIAL**

## Goal
Replace the eight-case analog scaffold with leakage-safe historical reliability memory, retrieval, outcome summaries and analog calibration.

## Deliverables
failure_memory store/index; retrieval contract; calibrated outcome cards; no-match state

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
python -m pytest backend/tests/test_historical_alignment.py backend/tests/test_historical_dataset.py -q
python -m pytest backend/tests/test_analog_memory.py backend/tests/test_analog_leakage.py -q
python scripts/evaluate_failure_memory.py --split test --block-bootstrap cycle
```

## Failure and rollback
Invalidate any retrieval from future verification periods. Disable memory if it does not beat climatology or introduces location leakage.

## Completion gate
Eligible historical retrieval only; uncertainty intervals; held-out improvement; provenance and no-match behavior.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase C - failure memory"
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
