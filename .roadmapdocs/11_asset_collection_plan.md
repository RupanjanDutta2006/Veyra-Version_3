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
