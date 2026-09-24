# Phase H — Safety and self-audit

**Blueprint levels:** 7,8,27,28,29    
**Current status:** **PARTIAL**

## Goal
Implement fragility, reliability margin, forecast crash test, eight-channel OOD, truthful drift lifecycle and selective abstention.

## Deliverables
fragility/margin engines; crash-test harness; OOD report; drift ledger; coverage-risk report

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
python -m pytest backend/tests/test_v3_failure_safety.py backend/tests/test_ood_detector.py backend/tests/test_abstention.py -q
python -m pytest backend/tests/test_drift_monitor.py backend/tests/test_production_hardening.py -q
python scripts/run_crash_test.py --perturbations ensemble,analog,physical --seed 42
```

## Failure and rollback
Unstable perturbation results downgrade trust and abstain. Stale drift baselines block retraining. OOD never emits confident probability.

## Completion gate
Quantified fragility/margin; bounded perturbations; measured OOD, drift, abstention, latency and outage paths.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase H - safety and self-audit"
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
