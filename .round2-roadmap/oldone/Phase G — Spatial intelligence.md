# Phase G — Spatial intelligence

**Blueprint levels:** 11,12,13,32    
**Current status:** **MISSING**

## Goal
Build learned location graph, lagged failure relationships, propagation/waves, upstream signals and validated regional fields.

## Deliverables
spatial graph; propagation edges; wave detector; upstream signal; regional field schema

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
python -m pytest backend/tests/test_spatial_graph.py backend/tests/test_propagation.py -q
python -m pytest backend/tests/test_spatial_leakage.py backend/tests/test_spatial_metrics.py -q
python scripts/evaluate_spatial_propagation.py --unseen-region --bootstrap cycle
```

## Failure and rollback
Never call graph relationships causal. Reject nearby-truth or future-node leakage. Label unlearned fields DEMO_SYNTHETIC.

## Completion gate
Unseen-region/time-held-out propagation evidence, lag uncertainty and false-propagation analysis.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase G - spatial intelligence"
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
