# Veyra SIH Round-2 Complete Integration Roadmap

## Evidence basis and operating decision

This roadmap is derived from the authoritative `MASTER PROMPT.txt`, the supplied SIH26079 documentation and research pack, the current audited checkouts, and the evidence-weighted comparison report. It is an implementation plan, not a claim that the repositories are already submission-ready.

The operating decision is:

- **Base:** Repository B.
- **Integration mode:** `SELECTIVE_MERGE_ONLY`.
- **Immediate submission status:** `NO_REPOSITORY_READY_YET`.
- **Long-term technical decision:** `KEEP_B_AS_BASE_IMPORT_FROM_A`.
- **Repository A contribution:** selected safety, provenance, UTC, certification-boundary, provider-disclosure, replay-invariant, revision-store, and test patterns.
- **Repository A exclusions:** its Git LFS pointer files are not deployable V3 binaries; historical duplicate application trees are not imported wholesale.
- **Repository B contribution:** its loadable V3 incumbent, destination backend/frontend, broader reliability architecture, test suites, manifests, and experimental specialist interfaces.
- **Repository B restrictions:** deterministic specialist formulas, synthetic replay, unsupported certification, coverage, warning-lead, cross-system, common-mode, and digital-twin claims remain experimental until independently reproduced.

The audited evidence was:

| Repository | Audited HEAD | Score | Immediate interpretation |
|---|---|---:|---|
| Repository A | `b9f52d3eeec8676e06b1879f05b404605e2501be` | 47.90/100 | Useful safety patterns, but the committed V3 model and calibrator are LFS pointer text and cannot load. |
| Repository B | `82eded8194151e37fb9b3eecf273010dc62d7b29` | 65.48/100 | Stronger destination: loadable V3 model/calibrator, completed software suites, broader architecture; feature checksum and science-governance blockers remain. |

## Non-negotiable integration rules

1. **Keep one active application base.** Repository B is the only destination application. Do not combine two FastAPI applications, two React applications, or two model registries.
2. **Keep the frozen incumbent immutable until gates pass.** The V3 model, isotonic calibrator, 50-feature order, target definition, calibrated probability semantics, and serving threshold must not be silently replaced.
3. **Never copy Repository A’s pointer artifacts as binaries.** They are evidence of missing LFS payloads, not deployable models.
4. **Use one authoritative release manifest.** It must bind model ID, model file, calibrator, feature schema, feature order, hashes, environment, threshold, fallback, route, and provenance.
5. **Separate software completeness from scientific validation.** A deterministic specialist may be retained as a formula baseline, but it may not be called trained, certified, calibrated, or production-ready without an empirical package.
6. **Keep probability concepts separate.** Hazard probability, `P(BUST)`, continuous error, interval coverage, ensemble dispersion, provider disagreement, OOD, confidence heuristics, and certification are different fields and different gates.
7. **Preserve issue-time safety.** Features at issue time may use only information available at or before issue time. Future observations, future reanalysis, verifying imagery, future errors, labels, and post-valid-time data are prohibited.
8. **Make data provenance visible.** Every response must distinguish live, cached, fixture, fallback, synthetic, and unavailable states, including provider and UTC identity.
9. **Do not promote by documentation.** A README, JSON metric, roadmap item, or `CERTIFIED` string cannot satisfy a scientific gate by itself.
10. **Stop on failed P0 gates.** No downstream merge, UI promotion, or submission packaging proceeds while a P0 integrity or claim blocker remains.

## Target merged-system shape

The target is a single Repository B-derived modular monolith with the following boundaries:

```text
                    +-------------------------------+
                    |  React/Vite SIH demonstration |
                    |  provenance + trust banners   |
                    +---------------+---------------+
                                    |
                              versioned API
                                    |
                    +---------------v---------------+
                    | FastAPI destination services   |
                    | one route/model authority     |
                    +---+-----------+-----------+----+
                        |           |           |
                +-------v--+ +------v------+ +--v-----------+
                | V3 model | | Safety/OOD | | Evidence and |
                | registry | | abstention | | explanations |
                +-------+--+ +------+-----+ +--+-----------+
                        |           |           |
                +-------v-----------v-----------v--------+
                | Frozen artifact + feature + target     |
                | contracts and release manifest        |
                +------------------+---------------------+
                                   |
             +---------------------v----------------------+
             | Durable revision/history and replay layer |
             | exact-target records, UTC, provider ID,   |
             | independent truth, sealed historical mode |
             +---------------------+----------------------+
                                   |
      +----------------------------v-----------------------------+
      | Experimental registry: hazard, spatial, compound,      |
      | common-mode, transfer, drift, and specialist formulas   |
      | isolated from incumbent promotion                       |
      +---------------------------------------------------------+
```

The final system must have one authoritative model path per route, one schema for bust probability and uncertainty, one provenance contract, one revision-history contract, and one release gate pipeline.

# Step 1 — Clone both repositories and create the audit workspace

This is the first operational step. Do not begin by copying modules, merging branches, installing dependencies into an untracked directory, or editing either upstream repository. Clone both repositories into separate directories, preserve the upstream state, and perform all integration work in a new destination branch derived from Repository B.

## 1.1 Create the workspace

Run these commands from a clean shell with Git, Python, Node.js, and package-management tools available:

```bash
set -euo pipefail

export WORKSPACE="$HOME/veyra-sih-round2"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE"/{repos,artifacts,logs,docs,manifests,builds}
cd "$WORKSPACE"
```

Do not use a path that already contains uncommitted work. If an existing workspace must be retained, use a new directory instead of deleting it.

## 1.2 Clone Repository A and Repository B separately

```bash
cd "$WORKSPACE/repos"

git clone https://github.com/RupanjanDutta2006/Veyra-Know-When-Forecasts-May-Fail repo_a
git clone https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2 repo_b

git -C repo_a remote -v
git -C repo_b remote -v
git -C repo_a branch --show-current
git -C repo_b branch --show-current
git -C repo_a rev-parse HEAD
git -C repo_b rev-parse HEAD
```

At the audited state, the expected branches and SHAs are:

```text
Repository A: main / b9f52d3eeec8676e06b1879f05b404605e2501be
Repository B: main / 82eded8194151e37fb9b3eecf273010dc62d7b29
```

If either remote has moved, do not silently substitute the new code. Record the new SHA, timestamp, and reason, then repeat the artifact, test, and source inventory.

## 1.3 Preserve the cloned states

```bash
cd "$WORKSPACE/repos"
git -C repo_a status --short
git -C repo_b status --short
git -C repo_a log -1 --format='%H%n%cI%n%s' > "$WORKSPACE/manifests/repo_a_head.txt"
git -C repo_b log -1 --format='%H%n%cI%n%s' > "$WORKSPACE/manifests/repo_b_head.txt"
git -C repo_a tag -a audit-repo-a-b9f52d3 -m 'Frozen SIH Round-2 audit state' b9f52d3eeec8676e06b1879f05b404605e2501be
git -C repo_b tag -a audit-repo-b-82eded8 -m 'Frozen SIH Round-2 audit state' 82eded8194151e37fb9b3eecf273010dc62d7b29
```

If tagging is not permitted, create annotated archive metadata under `$WORKSPACE/manifests`. Never rewrite either upstream `main` branch.

## 1.4 Check Git LFS and record artifact state

Repository A’s V3 paths were observed as Git LFS pointer text rather than loadable binaries. Record that state before any attempt to merge:

```bash
git lfs version || true
git -C "$WORKSPACE/repos/repo_a" lfs ls-files || true
file "$WORKSPACE/repos/repo_a/models/v3/lightgbm_v3_challenger.joblib" || true
file "$WORKSPACE/repos/repo_a/models/v3/probability_calibrator_v3.joblib" || true
sha256sum "$WORKSPACE/repos/repo_a/models/v3/lightgbm_v3_challenger.joblib" || true
sha256sum "$WORKSPACE/repos/repo_a/models/v3/probability_calibrator_v3.joblib" || true
```

Do not run `git lfs pull` and treat the result as the same evidence without recording payload source, object ID, size, SHA256, and authorization. A recovered payload is a new artifact requiring provenance and revalidation.

## 1.5 Create the documentation and evidence bundle

Place the supplied archive, authoritative `MASTER PROMPT.txt`, research pack, 500-test suite, blueprint, main specification, and previous comparison report under `$WORKSPACE/docs`. Record their hashes:

```bash
find "$WORKSPACE/docs" -type f -print0 | sort -z | xargs -0 sha256sum > "$WORKSPACE/manifests/supplied_docs.sha256"
```

Do not double-count duplicate copies. Select one authoritative copy per document and record duplicate paths in a duplicate-disposition ledger.

## 1.6 Inventory both repositories before installing or editing

```bash
for repo in repo_a repo_b; do
  (
    cd "$WORKSPACE/repos/$repo"
    find . -maxdepth 3 -type f | sort > "$WORKSPACE/manifests/${repo}_tree.txt"
    find . -type f \( -name '*.joblib' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.lock' \) -print0 | sort -z | xargs -0 sha256sum > "$WORKSPACE/manifests/${repo}_artifact_hashes.sha256" || true
    du -sh . > "$WORKSPACE/manifests/${repo}_size.txt"
  )
done
```

Record backend, frontend, model, data, scripts, tests, docs, CI, deployment, and release paths separately. Installation-generated files must not be mixed with the clean-checkout inventory.

## 1.7 Create the destination integration branch

Only after both repositories are recorded:

```bash
cd "$WORKSPACE/repos/repo_b"
git switch -c integration/sih-round2-selective-merge
git status --short
```

Repository A remains a read-only evidence source. Repository B is the only application destination. Every imported file must be recorded in the asset ledger with source SHA, destination path, action, owner, and validation gate.

## 1.8 Install dependencies in isolated environments

Do not install dependencies globally or modify either clean clone. Use separate environments for initial reproduction:

```bash
python3 -m venv "$WORKSPACE/builds/repo_a_venv"
python3 -m venv "$WORKSPACE/builds/repo_b_venv"
python3 -m venv "$WORKSPACE/builds/integration_venv"
source "$WORKSPACE/builds/integration_venv/bin/activate"
python -m pip install --upgrade pip
```

Install only from declared requirements/lock files after the clean inventory. Record Python, Node, npm/pnpm, LightGBM, scikit-learn, and model-serialization versions.

## 1.9 Reproduce before merge

Before copying a file from either repository, run the available artifact verification, test collection, bounded tests, frontend build, startup smoke, and release/replay commands in the original checkout. Save stdout, stderr, exit code, warnings, and runtime under `$WORKSPACE/logs`. This prevents a merged system from hiding a pre-existing failure.

## Step 1 exit criteria

- [ ] Both repositories cloned separately.
- [ ] Default branches and SHAs recorded.
- [ ] Clean tracked worktrees confirmed.
- [ ] Git LFS/pointer state recorded.
- [ ] Supplied documentation hashes recorded.
- [ ] Repository trees, artifact hashes, sizes, and dependency manifests recorded.
- [ ] Repository B integration branch created.
- [ ] Repository A marked read-only evidence source.
- [ ] Pre-merge reproduction logs saved.

Only after every item passes should Phase 0 begin.

# Phase 0 — Freeze and inventory

## Objective

Freeze both audited states and create an immutable evidence baseline before any integration edit.

## Entry criteria

- Read-only clones are available.
- The two audited SHAs are recorded.
- The supplied documentation archive is preserved.
- No integration branch has been created from unrecorded working-tree changes.

## Inputs from Repository A

- SHA `b9f52d3eeec8676e06b1879f05b404605e2501be`.
- `models/v3/feature_names.json`.
- `models/v3/lightgbm_v3_challenger.joblib` and `models/v3/probability_calibrator_v3.joblib` as pointer-file evidence only.
- `training_manifest.json` and `v3_evaluation_manifest.json`.
- `backend/app/core/release_manifest.*`.
- `backend/app/builder2/v3_model_adapter.py`.
- `backend/app/builder2/v3_feature_pipeline.py`.
- `backend/app/api/v1/endpoints/predict.py`.
- Test and build logs already recorded by the audit.

## Inputs from Repository B

- SHA `82eded8194151e37fb9b3eecf273010dc62d7b29`.
- `models/v3/lightgbm_v3_challenger.joblib`.
- `models/v3/probability_calibrator_v3.joblib`.
- `models/v3/feature_names.json`.
- `artifact_manifest.json`, `training_manifest.json`, `v3_evaluation_manifest.json`, and `v3_comprehensive_evaluation.json`.
- `models/day4/*` and `models/baseline_logistic_v1*`.
- `backend/app/builder2/v3_model_adapter.py`.
- `scripts/verify_artifacts.py`.
- Backend/frontend test and build logs.

## Step-by-step work

1. Create read-only tags or archive references for both audited SHAs.
2. Record default branch, commit timestamp, remote URL, working-tree status, and visible history depth.
3. Produce a complete path inventory for code, models, calibrators, manifests, tests, scripts, docs, deployment, and data.
4. Compute SHA256 for every model, calibrator, feature schema, manifest, lock file, and release artifact.
5. Record whether each file is a real payload, pointer text, fixture, generated output, or documentation.
6. Preserve the exact audit test logs, warnings, runtimes, failures, skipped tests, and errors.
7. Create a source-to-destination ledger with one row per candidate asset.
8. Record all duplicate trees in Repository A and mark them as historical or noncanonical until proven otherwise.
9. Freeze the current comparison scores and evidence classes.
10. Create an integration branch based on Repository B only.

## Outputs

- Signed or otherwise integrity-protected inventory.
- SHA/path ledger for both repositories.
- Candidate asset ledger.
- Baseline test/build/runtime evidence bundle.
- Immutable audit snapshot.

## Failure conditions

- Any source or artifact changes without a new hash and reason.
- Missing audit logs.
- Ambiguous source of a copied file.
- A pointer file being recorded as a deployable model.

## Gate P0-0

The inventory must reproduce the two audited SHAs and must identify every model, calibrator, feature schema, manifest, test root, deployment file, and duplicate application tree.

# Phase 1 — Truth alignment and claim register

## Objective

Make documentation, source code, artifacts, tests, and runtime claims agree before moving code.

## Inputs from Repository A

- `backend/app/core/certification_policy.py`.
- `backend/app/core/time_contract.py`.
- `backend/app/core/ood_policy.py`.
- Provider adapter and disagreement tests.
- `Audits/VEYRA_*` material.
- Current README and integration contracts.

## Inputs from Repository B

- `ARCHITECTURE.md`.
- `REPRODUCIBILITY_PACKAGE.md`.
- `docs/*`.
- `.round2-roadmap/*`.
- `round2-report/*`.
- `backend/app/builder2/*specialist.py` modules.
- Specialist JSON metrics and certification manifests.
- `cross_system_transfer_engine.py` and digital-twin material.

## Step-by-step work

1. Create a claim register with columns: claim, source file, code path, artifact path, test command, runtime observation, evidence class, current status, owner, and correction.
2. Classify every major claim as `REPRODUCED`, `SUPPORTED_BY_ARTIFACT`, `SUPPORTED_BY_CODE_ONLY`, `SUPPORTED_BY_TEST_FIXTURE_ONLY`, `DOCUMENTATION_ONLY`, `CONTRADICTED`, or `UNVERIFIED`.
3. Remove or qualify broad `CERTIFIED` language where independent scientific evidence is absent.
4. Label deterministic specialist formulas as formula baselines.
5. Label digital-twin synthetic progression as synthetic or fixture behavior.
6. Label fallback, risk-map, cached, and fixture paths in both API and UI terms.
7. Separate hazard occurrence claims from forecast-bust claims.
8. Separate calibration, OOD, abstention, provider disagreement, uncertainty, and forecast error in schemas and prose.
9. Mark NCMRWF, NEPS, IMD, DWR, INSAT, and cross-system statements as future or documentation-only unless paired data, metadata, permission, and replay evidence exist.
10. Correct stale test counts and never turn total test counts into 500-test certification.
11. Add a documentation-drift disposition: retain, rewrite, archive, or reject.

## Outputs

- Master claim register.
- Stale/contradicted documentation list.
- Corrected README and release-language draft.
- Evidence-class labels for all public claims.
- UI/API provenance wording specification.

## Failure conditions

- Unsupported certification remains in current production-facing text.
- Synthetic outputs can still be interpreted as historical or live.
- Hazard probability is exposed as `P(BUST)` without a separate target definition.
- A metric is labeled reproduced without a rerun or valid frozen artifact chain.

## Gate P0-1

Every public scientific claim must map to an evidence class and a current owner. No undocumented claim can be promoted in later phases.

# Phase 2 — Base selection and branch controls

## Objective

Establish Repository B as the sole destination and prevent a monolithic merge.

## Inputs from Repository A

Only the selected pattern list:

- safe model-unavailable behavior;
- UTC and issue-time contract;
- certification-scope boundaries;
- provider/fixture disclosure;
- revision-store semantics;
- replay invariants;
- selected safety and release tests.

Do not import Repository A’s application trees wholesale.

## Inputs from Repository B

- Current `backend/app` and versioned routes.
- Current `frontend/src`.
- Current model services and registries.
- Current `.github/workflows/deploy.yml`.
- Current test and lock files.

## Step-by-step work

1. Create a protected integration branch from Repository B.
2. Require pull requests and required checks for the integration branch.
3. Define the canonical destination directories.
4. Define a no-duplicate policy for backend, frontend, model, data, and deployment trees.
5. Create an import allowlist from Tables K and L.
6. Create an import denylist for pointer artifacts, duplicate trees, unverified metrics, synthetic outputs presented as live, and stale claims.
7. Define module ownership and code owners for model registry, safety, data history, API, UI, tests, and documentation.
8. Establish a single dependency lock and a single Python/Node build path.
9. Add a merge-check that rejects files copied outside the allowlist without an owner and validation plan.

## Outputs

- Protected integration branch.
- Canonical directory map.
- Import allowlist/denylist.
- Module ownership map.
- Initial Repository B-based branch.

## Failure conditions

- A second app tree is introduced.
- Repository A’s historical trees are copied without disposition.
- Model-serving code is copied into multiple competing paths.
- The branch can deploy without required checks.

## Gate P0-2

The destination must have one backend, one frontend, one model registry, one release manifest location, and one route-to-model authority.

# Phase 3 — Frozen incumbent artifact repair

## Objective

Repair Repository B’s feature-contract integrity while preserving the loadable V3 model and isotonic calibrator.

## Inputs from Repository A

- Strict feature-order checks in `v3_feature_pipeline.py`.
- Model-unavailable and no-silent-fallback behavior from `v3_model_adapter.py` and `predict.py`.
- Expected production hashes from the frozen contract.
- Artifact/release test patterns.

## Inputs from Repository B

- `models/v3/lightgbm_v3_challenger.joblib`.
- `models/v3/probability_calibrator_v3.joblib`.
- `models/v3/feature_names.json`.
- `artifact_manifest.json`.
- `training_manifest.json`.
- `v3_evaluation_manifest.json`.
- `v3_comprehensive_evaluation.json`.
- `scripts/verify_artifacts.py`.
- `backend/app/builder2/v3_model_adapter.py`.
- `models/day4/*` and `models/baseline_logistic_v1*` for explicit baseline comparison only.

## Known incumbent contract

| Item | Required value |
|---|---|
| V3 model | `models/v3/lightgbm_v3_challenger.joblib` |
| Model SHA256 | `00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660` |
| Calibrator | `models/v3/probability_calibrator_v3.joblib` |
| Calibrator SHA256 | `9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531` |
| Feature count | 50 |
| Calibrator type | `IsotonicRegression` |

## Step-by-step work

1. Determine whether the committed `feature_names.json` or its declared hash is authoritative.
2. Do not alter the model or calibrator to make a hash pass.
3. If the feature file is canonical, regenerate the manifest from that exact file and record the decision.
4. If the manifest is canonical, restore the exact feature file from a verified source and record provenance.
5. Pin the compatible scikit-learn and LightGBM environment.
6. Load the model and calibrator in a clean clone.
7. Verify model type, calibrator type, feature count, feature order, threshold, model ID, and fallback policy.
8. Create one release manifest binding all of those values.
9. Consolidate V3 threshold `0.060` and legacy Day-4 threshold `0.280` into an explicit model-version map; do not silently choose one.
10. Make `scripts/verify_artifacts.py` exit 0.
11. Add a clean-clone artifact test.
12. Add a golden-input prediction parity test before and after all safety grafts.
13. Verify that missing or corrupt artifacts produce a safe abstention and never an unannounced model substitution.

## Outputs

- One authoritative V3 release manifest.
- Verified hashes and environment lock.
- Route-to-model/threshold/fallback map.
- Clean-clone verifier result with exit code 0.
- Golden V3 output fixture and parity test.
- Artifact provenance record.

## Failure conditions

- Feature hash remains inconsistent.
- Model or calibrator is changed without an approved provenance record.
- Multiple thresholds or fallback paths remain undocumented.
- Silent fallback changes the calibrated output.
- Clean-clone load fails.

## Gates G1–G3

- **G1 Artifact integrity:** all hashes, types, feature order, environment, ID, threshold, and fallback match.
- **G2 Incumbent parity:** golden calibrated V3 outputs remain identical within declared tolerance.
- **G3 Model authority:** exactly one authoritative model path per route.

No safety grafting or specialist integration proceeds if G1–G3 fail.

# Phase 4 — Selective safety grafting

## Objective

Port only Repository A patterns that improve operational honesty and failure safety without changing the V3 incumbent.

## Inputs from Repository A

- `backend/app/core/time_contract.py`.
- `backend/app/core/certification_policy.py`.
- `backend/app/core/ood_policy.py`.
- `backend/app/builder2/v3_model_adapter.py`.
- `backend/app/api/v1/endpoints/predict.py`.
- `backend/app/services/revision_service.py`.
- Provider adapters and disagreement tests.
- `test_day34_time_contract_revision_store.py`.
- `test_day35_independent_replay_release_manifest.py`.
- `test_day37_provider_adapters.py`.
- `test_day38_cross_provider_disagreement.py`.
- `test_scientific_certification.py`.
- Relevant `backend/tests/test_v3_*`.

## Inputs from Repository B

- `backend/app/builder2/v3_model_adapter.py`.
- `backend/app/safety/ood_detector.py`.
- `backend/app/safety/ood_enforcement.py`.
- `builder2/calibrator.py`.
- `conditional_calibration_engine.py`.
- `data/hazard_calibration_registry.json`.
- B prediction schemas and versioned routes.
- B frontend provenance and trust-state components.

## Step-by-step work

1. Port A’s UTC and issue-time contract into B’s canonical data contract.
2. Port safe model-unavailable behavior without changing B’s successful V3 output.
3. Define explicit response states: ready, abstain, OOD, unavailable, live, cached, fixture, fallback, and synthetic.
4. Port certification policy as a scope and wording policy, not as proof of certification.
5. Consolidate OOD behavior so diagnostic OOD and active abstention are separate fields and code paths.
6. Port provider identity and fixture disclosure into B’s response schema.
7. Port revision semantics only after agreeing on a canonical storage contract.
8. Port A tests into B’s destination test style, maintaining test intent and source traceability.
9. Add API schema-diff tests.
10. Run V3 golden parity after every safety change.
11. Add failure-path tests for missing model, corrupted model, missing provider, stale data, and invalid timestamps.

## Outputs

- B-native safety modules.
- Unified trust/provenance response schema.
- Migrated safety and disclosure tests.
- Explicit OOD/abstention contract.
- Certification wording and UI policy.

## Failure conditions

- Probability fields change semantics.
- Provider identity or UTC identity is dropped.
- A diagnostic OOD signal becomes an active abstention without a documented gate.
- Safety changes alter golden V3 results.
- A fixture is exposed as live.

## Gates

- V3 parity remains green.
- Issue-time leakage tests pass.
- Missing-model behavior abstains safely.
- API schemas preserve separate bust, hazard, OOD, uncertainty, and provenance fields.

# Phase 5 — Durable revision store and honest replay rebuild

## Objective

Build one durable history and replay layer that can distinguish real historical replay from synthetic demonstration.

## Inputs from Repository A

- `backend/app/core/time_contract.py`.
- `revision_store.py`.
- `backend/app/services/revision_service.py`.
- SQLite/WAL exact-target design.
- `backend/app/core/replay_harness.py`.
- `golden_replay_matrix.py`.
- Replay and revision tests.

## Inputs from Repository B

- `backend/app/data/zarr_store.py`.
- Revision feature services.
- `failure_memory.py`.
- `failure_motifs.py`.
- `independent_truth_audit.py`.
- `replay_digital_twin.py`.
- Existing history and motif data.

## Step-by-step work

1. Define the canonical revision record: issue UTC, valid UTC, provider ID, forecast version, target ID, feature snapshot, truth availability, calibration state, and sealing state.
2. Choose one durable store contract; do not retain SQLite/WAL and Zarr as competing authorities.
3. Define exact-target lookup and idempotency keys.
4. Define truth-sealing rules so future truth cannot alter an already-issued feature snapshot.
5. Implement restart/reload tests across multiple issue cycles.
6. Separate synthetic digital-twin cycles from historical replay at code, API, UI, and storage levels.
7. Reject fabricated history and synthetic progression in historical mode.
8. Require immutable forecast and independent truth inputs for historical replay.
9. Port A replay invariants and B history modules selectively into the canonical service.
10. Rebuild Failure Memory and Failure Motifs on sealed episode records.
11. Ensure replay metrics are internally consistent and state their data mode.

## Outputs

- Canonical durable revision service.
- Exact-target and restart test suite.
- Historical replay mode.
- Clearly labeled synthetic/fixture mode.
- Sealed Failure Memory and Motif input contract.
- Replay provenance ledger.

## Failure conditions

- Restart loses records.
- Provider or UTC identity is missing.
- Truth is available before the declared latency.
- Synthetic cycles appear as historical observations.
- Replay metrics conflict with their source rows.

## Gates G9 and G11

- **G9 Revision durability:** records survive restart, preserve exact target/provider/time identity, and seal truth correctly.
- **G11 Replay:** historical mode uses immutable forecasts and independent truth; synthetic mode is visibly separate.

# Phase 6 — Experimental module containment and scientific promotion boundary

## Objective

Keep Repository B’s broad architecture without allowing unvalidated specialists to enter the incumbent path.

## Inputs from Repository A

- `backend/app/core/certification_policy.py`.
- Scope labels and certification-boundary tests.
- Provider disclosure and safety UI patterns.
- `backend/app/services/spatial_service.py` and spatial schemas/tests.

## Inputs from Repository B

- `backend/app/builder2/precipitation_specialist.py`.
- `cyclone_specialist.py`.
- `monsoon_specialist.py`.
- `western_disturbance_specialist.py`.
- `heatwave_specialist.py`.
- `spatial_reliability_engine.py`.
- `compound_hazard_engine.py`.
- `common_mode_detector.py`.
- `cross_system_transfer_engine.py`.
- `evidence_graph_engine.py`.
- `explainer.py`.
- `services/explainability_service.py`.
- Hazard target/event JSON and specialist JSON manifests.
- `data/spatial_network_topology.json`.

## Step-by-step work

1. Register every specialist as `experimental`, `formula_baseline`, or `candidate`, never automatically `certified`.
2. Put specialists behind feature flags and explicit route/configuration boundaries.
3. Keep formula outputs separate from trained model outputs.
4. Add provenance fields for coefficients, thresholds, input data, and model artifacts.
5. Add per-hazard target definitions, data splits, seeds, artifact IDs, and evaluation manifests.
6. Define promotion gates for Brier, BSS, ECE, calibration slope/intercept, PR-AUC, warning lead, interval coverage, bootstrap uncertainty, OOD, and out-of-time performance.
7. Require hazard occurrence and forecast-bust targets to be separate.
8. Quarantine unsupported JSON metrics and certification labels.
9. Keep spatial, compound, common-mode, and cross-system paths experimental.
10. Ensure evidence-graph and explanation outputs use non-causal wording unless causal evidence exists.
11. Reject severe-wind certification until an independent specialist package exists.
12. Add an independent reviewer gate before any specialist is promoted.

## Outputs

- Experimental module registry.
- Formula-baseline labels.
- Per-hazard promotion template.
- Specialist evidence package schema.
- Quarantined unsupported claims.
- Non-causal explanation contract.

## Failure conditions

- Any formula is called trained or certified.
- A specialist changes the incumbent output without passing promotion gates.
- A hazard probability is surfaced as `P(BUST)`.
- A JSON metric is treated as reproduced without rerun.
- Cross-system or common-mode claims rely only on fixtures.

## Gate G8

No specialist enters the production path until an independent package contains: source data provenance, issue-time split, target definition, feature schema, trained artifact, calibrator if used, model hash, evaluation script, raw outputs, bootstrap/OOT/OOD results, and reviewer sign-off.

# Phase 7 — Test, CI, reproducibility, and release consolidation

## Objective

Turn the evidence requirements into required automated release gates.

## Inputs from Repository A

- `pytest.ini`.
- `requirements.txt`.
- V3, time-contract, revision, replay, provider, certification, release, and frontend test files.
- A frontend lock file.
- A’s safe failure and disclosure assertions.

## Inputs from Repository B

- `backend/tests`.
- Frontend tests and lock files.
- `scripts/verify_artifacts.py`.
- `replay_digital_twin.py`.
- `evaluate_cross_system.py`.
- `evaluate_spatial_propagation.py`.
- Smoke scripts.
- `requirements.txt`.
- `pyproject.toml`.
- `pytest.ini`.
- `.github/workflows/deploy.yml`.

## Step-by-step work

1. Create one reproducible environment specification for backend, frontend, model serialization, and chart/report generation.
2. Add backend dependency installation and test execution to CI.
3. Add artifact verification as a required check.
4. Add feature-contract and model/calibrator load checks.
5. Add leakage and issue-time checks.
6. Add calibration and risk-coverage checks when frozen evaluation inputs are available.
7. Add OOD and safe-abstention tests.
8. Add revision restart, truth-sealing, provider identity, and replay checks.
9. Add API OpenAPI compatibility and consumer tests.
10. Add frontend E2E states for ready, abstain, OOD, live, cached, fixture, fallback, synthetic, and unavailable.
11. Add security, secret, dependency, concurrency, rate, recovery, and rollback checks.
12. Build a 500-test ID ledger with outcomes: pass, fail, blocked, skipped, xfail, or `N/A — uncovered/missing`.
13. Keep discovered test counts separate from named 500-test identity.
14. Add a tagged release and rollback record.
15. Block deployment if any P0 gate fails.

## Outputs

- Required CI workflow.
- Reproducible environment lock.
- Artifact/release gate.
- Backend/frontend/scientific test reports.
- 500-ID outcome ledger.
- OpenAPI and browser regression reports.
- Tagged rollback-ready release.

## Failure conditions

- Frontend-only CI remains the only deployment gate.
- Scientific integrity checks are optional.
- Test counts are used as a substitute for named-domain coverage.
- Failed science gates do not block deployment.
- A release cannot be rolled back.

## Gates G14–G17

- **G14 Test migration:** critical behaviors have a traceable destination test and justified dispositions.
- **G15 Security/operations:** required scans and recovery checks pass.
- **G16 Release governance:** signed/tagged release and rollback record exist.
- **G17 Independent review:** an independent reviewer reruns hashes, tests, build, smoke, replay, and claims.

# Phase 8 — Submission readiness

## Objective

Produce a truthful, demonstrable, reproducible SIH Round-2 candidate.

## Inputs from Repository A

- Conservative claim language.
- Scope and certification policy.
- Safe failure and provenance UI checks.
- Selected migrated tests.

## Inputs from Repository B

- Repaired V3 artifacts and manifest.
- B destination backend/frontend.
- Passing required test and build reports.
- Experimental specialist registry.
- Evidence package and demo assets.

## Step-by-step work

1. Freeze the candidate SHA and release manifest.
2. Run clean-clone setup from documented locks.
3. Run artifact verification and model/calibrator loading.
4. Run golden V3 parity.
5. Run backend, frontend, API, security, replay, and smoke suites.
6. Run the 500-ID ledger generation.
7. Verify every public claim against the claim register.
8. Run browser E2E across all trust/provenance states.
9. Verify that no UI says live, certified, historical, or trained when the evidence class does not support that wording.
10. Produce a judge-facing demo script that demonstrates both normal output and safe abstention.
11. Produce a risk register and known-limitations sheet.
12. Obtain independent reviewer sign-off.
13. Tag the submission candidate and preserve the exact environment and evidence bundle.

## Outputs

- Submission candidate tag.
- Final claim sheet.
- Demo script and screenshots/video inputs.
- Test/build/artifact/replay evidence bundle.
- Limitations and risk register.
- Rollback tag.

## Failure conditions

- Any P0 blocker remains.
- V3 is unavailable or checksum-invalid.
- A specialist is presented as certified without Gate G8.
- Synthetic or fixture output is shown as live or historical.
- Independent review cannot reproduce the release.

## Final submission gate

The release is suitable only if all P0 blockers are closed, G0–G17 are either passed or explicitly justified as out of scope, the claim register matches the final UI/API/docs, and the independent reviewer can reproduce the artifacts, tests, build, smoke, and replay boundaries.

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
