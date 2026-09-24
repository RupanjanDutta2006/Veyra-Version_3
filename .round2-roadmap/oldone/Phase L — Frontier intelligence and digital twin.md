# Phase L — Frontier intelligence and digital twin

**Blueprint levels:** 37,38,39,40,43,44    
**Current status:** **MISSING**

## Goal
Build information value, self-critic consistency, evidence graph, counterfactuals, frontier fields, graph models and digital twin only when prior phases justify them.

## Deliverables
information-value engine; conflict state; evidence graph; counterfactual report; frontier registry; twin replay

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
python -m pytest backend/tests/test_evidence_graph.py backend/tests/test_self_critic.py backend/tests/test_counterfactual_reliability.py -q
python scripts/run_frontier_ablation.py --base full-validated-veyra --bootstrap cycle
python scripts/replay_digital_twin.py --event cyclone_tauktae --compare raw,v3,full
```

## Failure and rollback
Reject frontier components with no incremental information, unsafe uncertainty, excessive cost/latency or no rollback. Label generated fields as simulations.

## Completion gate
Traceable evidence graph, successful release gates and a tested rollback path.

## End-of-phase test and Git push

The phase is complete only when **all commands above exit with code 0, all tests pass, and the final report contains zero errors**.

```bash
# Run this only after every command above exits 0 and the test report says 0 failed.
git add docs/phase-3
git commit -m "docs: complete phase L - frontier intelligence and digital twin"
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
