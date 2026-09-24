# Implementation Plan — Complete Asset Collection Plan

## Purpose

This document provides the exact file-level import/reject/adapt/quarantine matrix for both repositories. Every file that may be involved in the integration is listed with its treatment and validation requirements.

---

## Repository A — Collect, Preserve, Adapt, or Reject

### Core V3 Assets

| Path | Treatment | Validation Before Use |
|---|---|---|
| `models/v3/feature_names.json` | **Informative/adapt** — compare with B's version | Feature-order diff against B |
| `training_manifest.json` | **Informative** — reference only | No artifact overwrite |
| `v3_evaluation_manifest.json` | **Informative** — reference only | No artifact overwrite |
| `backend/app/builder2/v3_model_adapter.py` | **Adapt** — port safe-fail patterns only | Safe-load test; no output change |
| `backend/app/builder2/v3_feature_pipeline.py` | **Adapt** — port feature-order checks | Feature-order diff |
| `backend/app/api/v1/endpoints/predict.py` | **Adapt** — port safe-fail behavior | No output change |
| `models/day4/*` | **Informative** — baseline comparison reference | Do not deploy |

### Reliability Assets

| Path | Treatment | Validation |
|---|---|---|
| `backend/app/core/time_contract.py` | **Adapt or reimplement** | Restart/reload, sealed truth |
| `revision_store.py` | **Adapt or reimplement** | Episode-safe replay |
| `backend/app/services/revision_service.py` | **Adapt or reimplement** | Restart/reload |
| `backend/app/builder2/instability_fingerprint.py` | **Adapt** | — |
| `backend/app/core/replay_harness.py` | **Adapt** | Episode-safe replay |
| `golden_replay_matrix.py` | **Adapt** | Replay invariants |

### Hazard/Spatial/Provider Assets

| Path | Treatment | Validation |
|---|---|---|
| `backend/app/services/spatial_service.py` | **Adapt selected safety behavior** | B contract tests |
| Spatial endpoint/schema/tests | **Adapt** | No invented specialist equivalence |
| Provider adapters/disagreement services | **Adapt** | B contract tests |
| Provider disagreement tests | **Port** | Test intent preserved |

### Calibration/OOD Assets

| Path | Treatment | Validation |
|---|---|---|
| `backend/app/core/certification_policy.py` | **Canonical pattern/adapt** | Scope boundary only |
| `backend/app/core/ood_policy.py` | **Adapt** | Diagnostic vs active OOD |
| V3 failure-safety/calibration tests | **Port** | Preserve abstain/null semantics |

### Evidence/Explanation Assets

| Path | Treatment | Validation |
|---|---|---|
| `backend/app/builder2/instability_fingerprint.py` | **Informative/adapt** | Non-causal wording |
| `Audits/VEYRA_*` | **Informative** | Current-SHA review |
| `backend/app/core/release_manifest.*` | **Adapt** | Rebuild release manifest |

### Backend/Frontend/Demo Assets

| Path | Treatment | Validation |
|---|---|---|
| Provider/certification/revision endpoints | **Adapt behavior only** | API diff; no duplicate tree |
| `frontend/src/test` | **Adapt** | Browser E2E |
| `frontend/src/components/ModelCatalog.tsx` | **Adapt** | — |
| `frontend/src/components/ModelEvaluationView.tsx` | **Adapt** | — |
| `vercel.json` | **Informative** | — |

### Testing/Release Assets

| Path | Treatment | Validation |
|---|---|---|
| `backend/tests/test_v3_*` | **Port tests and intent** | Fail-before/fix-pass-after |
| `test_day34_time_contract_revision_store.py` | **Port** | Test intent |
| `test_day35_independent_replay_release_manifest.py` | **Port** | Test intent |
| `test_day37_provider_adapters.py` | **Port** | Test intent |
| `test_day38_cross_provider_disagreement.py` | **Port** | Test intent |
| `test_scientific_certification.py` | **Port** | Test intent |
| `pytest.ini` | **Adapt** | — |
| `requirements.txt` | **Adapt** | Lock dependencies |
| Frontend lock files | **Adapt** | — |

### Documentation Assets

| Path | Treatment | Validation |
|---|---|---|
| `BUILDER_1_BUILDER_2_INTEGRATION_CONTRACT.md` | **Preserve with evidence labels** | Tie to destination path/test/SHA |
| `BUILDER_2_HANDOFF.md` | **Preserve with evidence labels** | Tie to destination |
| `docs/HORIZON_REQUEST_CONTRACT.md` | **Preserve with evidence labels** | Tie to destination |
| Relevant `Audits/*` | **Preserve** | — |
| Current code-tied README sections | **Preserve with evidence labels** | — |

### Repository A — EXPLICIT REJECTS

| Item | Reason |
|---|---|
| `models/v3/lightgbm_v3_challenger.joblib` | Git LFS pointer text, NOT deployable binary |
| `models/v3/probability_calibrator_v3.joblib` | Git LFS pointer text, NOT deployable binary |
| `Builder-2/` wholesale | Duplicate application tree |
| `Parinidhi/` wholesale | Duplicate application tree |
| `Frontend-Original/` wholesale | Duplicate application tree |
| `Overview/` wholesale | Historical tree |
| Unresolved-base-commit release manifest | NOT the final authority |
| Fixture second provider as live evidence | Scientific misrepresentation |

---

## Repository B — Collect, Preserve, Adapt, or Quarantine

### Core V3 Assets (Canonical After Repair)

| Path | Treatment | Validation |
|---|---|---|
| `models/v3/lightgbm_v3_challenger.joblib` | **Canonical — keep** | Feature hash, 50-order, types, threshold |
| `models/v3/probability_calibrator_v3.joblib` | **Canonical — keep** | Calibrator type, hash |
| `models/v3/feature_names.json` | **Canonical after repair** | Hash repair in Phase 3 |
| `artifact_manifest.json` | **Keep** | After hash repair |
| `training_manifest.json` | **Keep** | Provenance record |
| `v3_evaluation_manifest.json` | **Keep** | Evaluation record |
| `v3_comprehensive_evaluation.json` | **Keep** | Evaluation record |
| `models/day4/*` | **Keep** | Baseline comparison only |
| `models/baseline_logistic_v1*` | **Keep** | Baseline comparison only |
| `backend/app/builder2/v3_model_adapter.py` | **Keep** | Clean clone load test |

### Reliability Assets

| Path | Treatment | Validation |
|---|---|---|
| `failure_memory.py` | **Keep/adapt as experimental** | Sealed episodes, restart |
| `failure_motifs.py` | **Keep/adapt as experimental** | Episode holdouts |
| Recovery/horizon services/tests | **Keep** | Durable history |
| `backend/app/data/zarr_store.py` | **Keep/adapt** | Issue-time safety |
| `backend/app/services/drift_monitor.py` | **Keep** | — |
| `independent_truth_audit.py` | **Keep** | — |
| Motif/ledger data | **Keep** | — |

### Hazard Specialists (Keep Isolated as Experimental)

| Path | Treatment | Validation |
|---|---|---|
| `precipitation_specialist.py` | **Keep as experimental** | Per-hazard rerun |
| `cyclone_specialist.py` | **Keep as experimental** | Per-hazard rerun |
| `monsoon_specialist.py` | **Keep as experimental** | Per-hazard rerun |
| `western_disturbance_specialist.py` | **Keep as experimental** | Per-hazard rerun |
| `heatwave_specialist.py` | **Keep as experimental** | Per-hazard rerun |
| `spatial_reliability_engine.py` | **Keep as experimental** | OOT rerun |
| `compound_hazard_engine.py` | **Keep as experimental** | Bootstrap rerun |
| `common_mode_detector.py` | **Keep as experimental** | Calibration rerun |
| `cross_system_transfer_engine.py` | **Keep as experimental** | Independent truth |
| Hazard target/event JSON | **Keep** | Target definitions |
| `data/spatial_network_topology.json` | **Keep** | — |
| Specialist JSON manifests | **Keep** | Do not promote as reproduced |

### Calibration/OOD Assets

| Path | Treatment | Validation |
|---|---|---|
| `builder2/calibrator.py` | **Adapt/consolidate** | Held-out shifts |
| `conditional_calibration_engine.py` | **Adapt** | Risk-coverage |
| `data/hazard_calibration_registry.json` | **Adapt** | — |
| `backend/app/safety/ood_detector.py` | **Adapt** | Unsafe-input abstention |
| `backend/app/safety/ood_enforcement.py` | **Adapt** | — |
| `data/counterfactual_crash_test_report.json` | **Keep** | — |
| Prediction schemas | **Keep** | — |

### Backend/Frontend/Demo (Keep as Destination)

| Path | Treatment | Validation |
|---|---|---|
| `backend/app` | **Keep as destination** | OpenAPI diff |
| Versioned routes | **Keep** | — |
| `frontend/src` | **Keep** | Live/cache/fixture badges; E2E |
| Build/test scripts | **Keep** | — |
| `.github/workflows/deploy.yml` | **Keep/extend** | Add backend checks |
| Open-Meteo and fallback services | **Keep** | — |

### Testing/Release (Keep/Extend)

| Path | Treatment | Validation |
|---|---|---|
| `backend/tests` | **Keep/extend** | Verifier exit 0 |
| Frontend tests/locks | **Keep** | — |
| `scripts/verify_artifacts.py` | **Keep** | Exit 0 |
| `replay_digital_twin.py` | **Keep** | Labeled synthetic |
| `evaluate_cross_system.py` | **Keep** | — |
| `evaluate_spatial_propagation.py` | **Keep** | — |
| Smoke scripts | **Keep** | — |
| `requirements.txt` | **Keep** | Exact environment |
| `pyproject.toml` | **Keep** | — |
| `pytest.ini` | **Keep** | — |

### Repository B — QUARANTINE LIST

Do NOT promote as reproduced science:
- Specialist JSON metrics (not independently re-run)
- Cross-system transfer values (no paired data)
- Conformal/coverage figures (no held-out validation)
- Warning-lead numbers (no real event evaluation)
- Common-mode claims (fixture-based only)
- Digital-twin conclusions (synthetic)
- `fallback_service.py` synthetic cycles (not live observations)
- Deterministic risk-map outputs (not live observations)
- Conflicting feature hashes (must be resolved in Phase 3)
- Multiple undocumented serving thresholds (must be consolidated)

---

**Previous:** [Phase 9 — Post-Submission](11_phase9_post_submission.md)  
**Next:** [Master Acceptance Checklist](13_master_acceptance_checklist.md)
