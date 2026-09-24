# Phase 9 — Post-submission empirical specialist program

## Objective

Conduct scientific promotion work after the safe software base exists, without destabilizing the V3 incumbent.

## Inputs from Repository A

No specialist artifacts are accepted as equivalent. A contributes only safety, disclosure, and evaluation-boundary patterns.

## Inputs from Repository B

- Formula baselines and contracts from all six specialist modules.
- Spatial, compound, common-mode, and transfer prototypes.
- Hazard target/event JSON.
- Specialist manifests.
- Calibration registry.
- Evaluation and replay scripts.

## Step-by-step work

1. Define the actual forecast source, reference truth, issue time, valid time, and permissible data horizon for each hazard.
2. Build leakage-safe train/validation/out-of-time/event/OOD splits.
3. Produce real trained artifacts, calibrators, feature schemas, model IDs, and hashes.
4. Compare each challenger against frozen V3 and a documented baseline ladder.
5. Reproduce Brier, BSS, ECE, slope/intercept, PR-AUC, FAR, detection, warning lead, interval coverage, and bootstrap uncertainty.
6. Evaluate by hazard, horizon, geography, season, regime, and provider.
7. Evaluate abstention and risk-coverage under held-out shifts.
8. Re-run spatial, compound, common-mode, and cross-system evaluation with independent truth.
9. Test historical replay without synthetic progression.
10. Promote only a challenger that demonstrates incremental value under the same evaluation contract as V3.
11. If the challenger fails, retain V3 unchanged and record the failure.

## Outputs

- Per-hazard empirical evidence package.
- Reproducible model/calibrator artifacts.
- OOT/OOD/uncertainty reports.
- Promotion or rejection decision.
- Updated claim register.

## Failure conditions

- Future leakage.
- No paired truth or permission.
- No incremental value over V3.
- Calibration or coverage failure.
- No reproducible artifact chain.

## Promotion gate

A specialist is promoted only after independent reproduction and explicit acceptance by the incumbent/challenger gate. Software integration alone cannot promote it.

# Complete asset collection plan

## Repository A — collect, preserve, adapt, or reject

| Family | Exact paths/modules | Treatment | Validation before use |
|---|---|---|---|
| Core V3 | `models/v3/feature_names.json`; `training_manifest.json`; `v3_evaluation_manifest.json`; `backend/app/builder2/v3_model_adapter.py`; `v3_feature_pipeline.py`; `backend/app/api/v1/endpoints/predict.py`; `models/day4/*` | Informative/adapt; reject A pointer binaries | Feature-order diff; no artifact overwrite; safe-load test |
| Reliability | `backend/app/core/time_contract.py`; `revision_store.py`; `backend/app/services/revision_service.py`; `backend/app/builder2/instability_fingerprint.py`; `backend/app/core/replay_harness.py`; `golden_replay_matrix.py` | Adapt or reimplement | Restart/reload, sealed truth, episode-safe replay |
| Hazard/spatial/provider | `backend/app/services/spatial_service.py`; spatial endpoint/schema/tests; provider adapters/disagreement services/tests | Adapt selected safety behavior | B contract tests; no invented specialist equivalence |
| Calibration/OOD | `backend/app/core/certification_policy.py`; `ood_policy.py`; V3 failure-safety/calibration/certification tests | Canonical pattern/adapt | Preserve abstain/null semantics; diagnostic vs active OOD |
| Evidence/explanation | `backend/app/builder2/instability_fingerprint.py`; `Audits/VEYRA_*`; `backend/app/core/release_manifest.*` | Informative/adapt; reject stale claims | Non-causal wording; current-SHA review; rebuild release manifest |
| Backend/frontend/demo | Provider/certification/revision/spatial endpoints and schemas; `frontend/src/test`; `frontend/src/components/ModelCatalog.tsx`; `ModelEvaluationView.tsx`; `vercel.json` | Adapt behavior only | API diff; browser E2E; no duplicate app tree |
| Testing/release | `backend/tests/test_v3_*`; `test_day34_time_contract_revision_store.py`; `test_day35_independent_replay_release_manifest.py`; `test_day37_provider_adapters.py`; `test_day38_cross_provider_disagreement.py`; `test_scientific_certification.py`; `pytest.ini`; `requirements.txt`; frontend locks | Port tests and intent | Fail-before/fix-pass-after; lock dependencies |
| Documentation | `BUILDER_1_BUILDER_2_INTEGRATION_CONTRACT.md`; `BUILDER_2_HANDOFF.md`; `docs/HORIZON_REQUEST_CONTRACT.md`; relevant `Audits/*`; current code-tied README sections | Preserve with evidence labels | Tie every retained claim to destination path/test/SHA |

### Repository A explicit rejects

- `models/v3/lightgbm_v3_challenger.joblib` as a deployable binary.
- `models/v3/probability_calibrator_v3.joblib` as a deployable binary.
- Wholesale import of `Builder-2`, `Parinidhi`, `Frontend-Original`, or `Overview` historical trees.
- Unresolved-base-commit release manifest as the final authority.
- Fixture second provider as live scientific evidence.

## Repository B — collect, preserve, adapt, or quarantine

| Family | Exact paths/modules | Treatment | Validation before use |
|---|---|---|---|
| Core V3 | `models/v3/lightgbm_v3_challenger.joblib`; `probability_calibrator_v3.joblib`; `feature_names.json`; `artifact_manifest.json`; `training_manifest.json`; `v3_evaluation_manifest.json`; `v3_comprehensive_evaluation.json`; `models/day4/*`; `models/baseline_logistic_v1*`; `backend/app/builder2/v3_model_adapter.py` | Canonical after repair/keep | Feature hash, 50-order, types, threshold, fallback, clean clone |
| Reliability | `failure_memory.py`; `failure_motifs.py`; recovery/horizon services/tests; `backend/app/data/zarr_store.py`; `backend/app/services/drift_monitor.py`; `independent_truth_audit.py`; motif/ledger data | Keep/adapt as experimental | Durable history, issue-time safety, episode holdouts, restart |
| Hazard specialists | Six `backend/app/builder2/*specialist.py` paths; `spatial_reliability_engine.py`; `compound_hazard_engine.py`; `common_mode_detector.py`; `cross_system_transfer_engine.py`; hazard target/event JSON; `data/spatial_network_topology.json`; specialist JSON manifests | Keep isolated as experimental | Per-hazard data, split, artifact, calibration, bootstrap, OOT rerun |
| Calibration/OOD | `builder2/calibrator.py`; `conditional_calibration_engine.py`; `data/hazard_calibration_registry.json`; `backend/app/safety/ood_detector.py`; `ood_enforcement.py`; `data/counterfactual_crash_test_report.json`; prediction schemas | Adapt/consolidate | Held-out shifts; risk-coverage; unsafe-input abstention |
| Evidence/explanation | `evidence_graph_engine.py`; `explainer.py`; `services/explainability_service.py`; provenance schemas/endpoints; `data/cross_system_evidence.json`; replay outputs | Keep interface; reject unsupported conclusions | Source traceability; artifact-vs-reproduced labels; non-causal language |
| Backend/frontend/demo | `backend/app`; versioned routes; `frontend/src`; build/test scripts; `.github/workflows/deploy.yml`; Open-Meteo and fallback services | Keep as destination | OpenAPI diff; live/cache/fixture/synthetic badges; E2E |
| Testing/release | `backend/tests`; frontend tests/locks; `scripts/verify_artifacts.py`; `replay_digital_twin.py`; `evaluate_cross_system.py`; `evaluate_spatial_propagation.py`; smoke scripts; `requirements.txt`; `pyproject.toml`; `pytest.ini` | Keep/extend | Verifier exit 0; exact environment; scientific/replay/security gates |
| Documentation | `ARCHITECTURE.md`; `REPRODUCIBILITY_PACKAGE.md`; `docs/*`; `.round2-roadmap/*`; `round2-report/*`; current README sections | Adapt after claim cleanup | Claim register; synthetic labels; archive stale text |

### Repository B quarantine list

Do not promote specialist JSON metrics, cross-system values, conformal/coverage figures, warning-lead numbers, common-mode claims, or digital-twin conclusions as reproduced science. Do not let `fallback_service.py` synthetic cycles or deterministic risk-map outputs appear as live observations. Do not retain conflicting feature hashes or multiple undocumented serving thresholds.

# Master acceptance checklist

## Artifact integrity

- [ ] V3 model hash matches the canonical release manifest.
- [ ] Isotonic calibrator hash and type match.
- [ ] Feature schema has exactly 50 entries in canonical order.
- [ ] Feature-file hash and declared hash agree.
- [ ] Model ID, threshold, fallback, environment, and route are bound in one manifest.
- [ ] Clean clone loads the model and calibrator.
- [ ] Missing/corrupt artifacts produce safe abstention.

## Scientific correctness

- [ ] `P(BUST)` is not hazard probability.
- [ ] Issue-time feature lineage is documented and tested.
- [ ] No future observation, future reanalysis, future error, label, or verifying imagery enters the issue-time feature vector.
- [ ] Calibration, OOD, abstention, uncertainty, provider disagreement, and continuous error remain separate.
- [ ] Specialist formulas are labeled as formulas until empirical gates pass.
- [ ] No certification wording exceeds the evidence class.

## Reliability and replay

- [ ] Revision records preserve issue UTC, valid UTC, provider, target, forecast version, and truth-sealing state.
- [ ] Restart/reload retains exact-target history.
- [ ] Failure Memory and Motifs consume sealed episodes.
- [ ] Historical replay uses immutable forecasts and independent truth.
- [ ] Synthetic replay is a separate visible mode.
- [ ] Replay metrics are internally consistent.

## API and frontend

- [ ] One route-to-model authority exists.
- [ ] OpenAPI and consumer tests pass.
- [ ] Live, cached, fixture, fallback, synthetic, and unavailable states are explicit.
- [ ] UI has correct trust/provenance banners.
- [ ] Ready, abstain, OOD, unavailable, and provider-failure states have browser E2E tests.
- [ ] Hazard, bust, OOD, uncertainty, and provider fields cannot be confused.

## Test and release engineering

- [ ] Backend tests run from a clean clone.
- [ ] Frontend tests and build pass.
- [ ] Artifact verifier exits 0.
- [ ] Leakage, calibration, OOD, replay, provider, security, and rollback gates run in CI.
- [ ] 500-test ID ledger exists with explicit dispositions.
- [ ] A failed scientific gate blocks deployment.
- [ ] A tagged release and rollback record exist.
- [ ] An independent reviewer reproduces the release.

# Decision tree for execution

```text
Start
  |
  v
Phase 0 inventory complete?
  | no -> stop and repair inventory
  v yes
Phase 1 claim register complete?
  | no -> stop and correct claims
  v yes
Phase 2 one B destination branch?
  | no -> remove duplicate trees and enforce branch controls
  v yes
Phase 3 G1–G3 artifact and incumbent gates pass?
  | no -> do not merge safety/specialist code; repair B artifact chain
  v yes
Phase 4 safety/provenance parity passes?
  | no -> revert semantic or output drift
  v yes
Phase 5 durable revision and replay gates pass?
  | no -> keep replay experimental and rebuild history layer
  v yes
Phase 6 specialist modules isolated and labeled?
  | no -> quarantine promotion paths and claims
  v yes
Phase 7 CI/release gates pass?
  | no -> no deployment or submission tag
  v yes
Phase 8 independent submission review passes?
  | no -> remain NO_REPOSITORY_READY_YET
  v yes
Tag truthful SIH Round-2 candidate
  |
  v
Phase 9 empirical specialist program after submission
```

# Final recommendation

Use Repository B as the sole destination only after its V3 feature-contract checksum is repaired and its release authority is consolidated. Port Repository A’s safety and operational patterns selectively, with tests and provenance, rather than copying its application trees or pointer artifacts. Keep all Repository B specialists, synthetic replay, transfer, coverage, common-mode, and certification claims behind explicit experimental boundaries. Do not submit either repository unchanged. The correct integration strategy is a staged, gate-driven selective merge in which software integration happens before scientific promotion and every promoted claim must be independently reproduced.

## References

[1]: `/home/ubuntu/sih26079_task/MASTER PROMPT.txt` "Authoritative master prompt"
[2]: `/home/ubuntu/audit_workspace/final_veyra_sih_round2_merge_report.md` "Evidence-weighted comparison and merge report"
[3]: `/home/ubuntu/audit_workspace/repos/repo_a` "Repository A audited checkout"
[4]: `/home/ubuntu/audit_workspace/repos/repo_b` "Repository B audited checkout"
[5]: `/home/ubuntu/sih26079_task/VEYRA_500_Test_Master_Suite (1).md` "500-Test Master Suite"

## Compulsory test for Phase 9 — empirical specialist promotion

Run the per-hazard promotion gate for each candidate specialist:

```bash
set -euo pipefail
python scripts/evaluate_specialist.py --hazard precipitation --split out_of_time --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py --hazard cyclone --split out_of_time --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py --hazard monsoon_lps --split out_of_time --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py --hazard western_disturbance --split out_of_time --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py --hazard heatwave --split out_of_time --require-issue-time-lineage --bootstrap 2000
```

**Pass condition:** each promoted specialist has a reproducible trained artifact, target and feature contract, leakage-safe split, calibration/uncertainty/OOD report, and independent review. If any candidate fails, retain V3 and keep the specialist experimental.
