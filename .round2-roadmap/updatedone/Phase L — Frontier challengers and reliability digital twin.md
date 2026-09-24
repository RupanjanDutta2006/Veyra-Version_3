# Phase L — Frontier challengers and reliability digital twin

**Blueprint gate:** Gate 11

## Goal
Only after core and hazard gates pass, test foundation representations, temporal/spatial/graph models, generative spatial reliability fields, counterfactual crash tests, evidence graph, self-critic consistency and Reliability Digital Twin replay.

## Deliverables
FRONTIER_CHALLENGER_REPORT; digital-twin replay; information-gain and counterfactual report

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_frontier_challengers.py backend/tests/test_evidence_graph.py backend/tests/test_counterfactual_reliability.py -q
python scripts/run_frontier_ablation.py --base all-certified-hazards --bootstrap cycle
python scripts/replay_digital_twin.py --event historical --compare raw,v3,certified-veyra,frontier
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
Do not replace certified hazard modules with a larger architecture without incremental information, uncertainty, reproducibility, latency and rollback evidence. Generated fields are simulations.

## Completion gate
Frontier components beat a relevant certified baseline under the complete temporal/geographic/seasonal/severity/OOD/reference matrix or are rejected and archived.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase L - frontier-challengers-and-reliability-digital-twin"
git push origin main
```

If any command fails, do not push. Fix the failure, rerun every phase command, and push only after zero errors.

## Drop-in phase report

- Status: COMPLETE / PARTIAL / BLOCKED
- Commit, environment, commands and logs
- Test totals and failed test names
- Metrics and confidence intervals by hazard/lead/season/location/regime/severity/OOD/reference
- Leakage, ablation, negative-control and independent-truth results
- Failure cases, status taxonomy, rollback decision and next-phase authorization
