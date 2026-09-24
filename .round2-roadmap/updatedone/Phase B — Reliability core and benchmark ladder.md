# Phase B — Reliability core and benchmark ladder

**Blueprint gate:** Gate 1

## Goal
Build the common ReliabilityState, evidence/provenance contract, Failure Memory schema, episode builder, retrieval API, and baseline ladder shared by every hazard. Benchmark climatology, persistence, spread, logistic/statistical model, V3 and calibrated V3 before specialist models.

## Deliverables
RELIABILITY_CORE_V1; ReliabilityState schema; evidence graph contract; benchmark runner; cycle-block bootstrap evaluator

## Work order
1. Freeze the operational hazard contract, target, reference, units and issue-time feature boundary.
2. Build the simplest baseline before V3/hazard challengers.
3. Add one feature family or specialist at a time.
4. Run temporal, geographic, seasonal, severity, OOD, reference and leakage checks.
5. Promote only after the completion gate; otherwise keep the result experimental, diagnostic, abstained, rejected or future.

## Phase commands
```bash
cd /home/ubuntu/work/veyra
python -m pytest backend/tests/test_historical_alignment.py backend/tests/test_historical_dataset.py backend/tests/test_ml_model_and_eval.py backend/tests/test_ml_splitting.py -q
python -m pytest backend/tests/test_reliability_state.py backend/tests/test_evidence_provenance.py -q
python scripts/run_benchmark_ladder.py --config configs/benchmark_ladder.yaml --bootstrap cycle --seed 42
```

If a named future test or script does not exist, create it in this phase before claiming completion.

## Failure and rollback
If a simple baseline matches V3, stop complexity and identify missing information. No specialist may bypass the common target, split, metric, evidence or provenance contract.

## Completion gate
Every hazard has comparable baselines, PR-AUC/Brier/BSS/ECE/CRPS where relevant, risk-coverage, lead/season/location/regime/extreme/OOD/reference slices, and bootstrap intervals.

## Shared rules
Use the frozen V3 incumbent. Do not use future truth, future calibration, future cycles, future model versions, future analogs, nearby truth or target-derived features at issue time. Keep `P(error threshold)`, interval miscoverage, continuous error, Veyra uncertainty and OOD separate. Unsupported output is `null` or explicit abstention, never an invented value.

## End-of-phase test and Git push

The phase is complete only when every command exits with code 0, every test passes, the report contains zero errors, and the completion gate is satisfied.

```bash
# Run only after the complete phase test is zero-error.
git add docs/phase-3
git commit -m "docs: complete phase B - reliability-core-and-benchmark-ladder"
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
