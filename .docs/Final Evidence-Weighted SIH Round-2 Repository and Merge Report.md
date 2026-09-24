# Final Evidence-Weighted SIH Round-2 Repository and Merge Report

**Audit scope:** Repository A and Repository B at the supplied, already-audited upstream default-branch heads  
**Audited Repository A SHA:** `b9f52d3eeec8676e06b1879f05b404605e2501be`  
**Audited Repository B SHA:** `82eded8194151e37fb9b3eecf273010dc62d7b29`  
**Audit date:** 2026-09-21  
**Reviewer role:** Independent senior scientific-ML reviewer, software architect, release auditor, and integration planner  
**Author:** Manus AI  
**Evidence order:** reproduced execution > current source and committed artifacts > machine-readable outputs > code-tied technical documents > README/presentation claims > roadmap

## Executive verdict

**Repository B is the stronger base, the overall technical winner, the stronger current scientific foundation, the broader research architecture, and the better immediate candidate of the two. Neither repository is ready for unchanged SIH Round-2 submission.** Repository A's default V3 path cannot load because its two committed `.joblib` files are Git LFS pointer text rather than the expected binaries. Exact on-disk hashes fail, replay fails, and serving correctly returns `MODEL_NOT_READY`. Repository B contains the expected, loadable V3 model and isotonic calibrator and reproduced **758 passing backend tests plus 58 passing frontend tests**, but its V3 feature-contract checksum fails. Its hazard specialists are deterministic formulas or baselines without specialist trained artifacts, and its certification, coverage, warning-lead, cross-system, common-mode, and replay claims exceed reproduced evidence.[3] [4]

The immediate decision is **`NO_REPOSITORY_READY_YET`**. The lower-risk pre-submission path is to repair and harden Repository B in place, not merge application trees. The long-term decision is **`KEEP_B_AS_BASE_IMPORT_FROM_A`**, implemented only as a selective adaptation of Repository A's safe-failure, certification-boundary, live-versus-fixture disclosure, time-contract, and durable revision patterns. A monolithic merge would duplicate model-selection surfaces, APIs, frontends, data stores, tests, documentation, and deployment assumptions while creating no missing scientific evidence.

The final weighted scores remain **47.90/100 for Repository A** and **65.48/100 for Repository B**. Independent arithmetic verification gives weights totaling 100, Repository A `47.90`, Repository B `65.48`, and a B lead of `17.58`. No new observed evidence justifies changing the established category scores.[3] [4]

> **Submission rule:** Keep Repository B's frozen V3 as incumbent only after the feature-manifest chain passes. Treat specialist formulas, synthetic replay, cross-system metrics, coverage figures, warning-lead claims, and every `CERTIFIED` label as experimental or rejected until independently revalidated. Reject Repository A's pointer files as deployable binaries.

## 1. Audit method, status vocabulary, and scientific boundaries

The supplied documentation is a **target map**, not proof that either implementation satisfies it. Duplicate documents were not double-counted. The consolidated master specification, 120-file research study pack, hazard blueprint, 500-test specification, Docs-vs-Research-vs-Live comparison, Phase A–L material, repository evidence reports, and current source paths were interpreted through the same evidence hierarchy.[1] [2] [5] [6] [7] [8]

### 1.1 Status and claim classes

| Term | Meaning in this report |
|---|---|
| `VERIFIED` | Directly reproduced at the audited SHA, within the stated scope. |
| `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | Current code exists, but scientific or operational validity was not independently reproduced. |
| `PARTIAL` | Material implementation exists, but the required capability or evidence chain is incomplete. |
| `PROTOTYPE_ONLY` | Demonstration, heuristic, or deterministic research implementation; not validated production science. |
| `DOCUMENTED_ONLY` | Present in prose or roadmap, not established by current implementation evidence. |
| `MISSING` | Required implementation or evidence is absent. |
| `N/A — uncovered/missing` | The final repository has no named target; no equivalent is invented. |
| `FUTURE_BY_DESIGN` | Explicitly deferred by the governing specification. |
| `CONTRADICTED` | Higher-ranked executable or artifact evidence conflicts with the claim. |
| `UNVERIFIED` | Evidence is unavailable or insufficient to decide. |

Scientific claims use `REPRODUCED`, `SUPPORTED_BY_ARTIFACT`, `SUPPORTED_BY_CODE_ONLY`, `SUPPORTED_BY_TEST_FIXTURE_ONLY`, `DOCUMENTATION_ONLY`, `CONTRADICTED`, or `UNVERIFIED`. A passing software test does not become empirical scientific validation. A JSON metric is artifact support, not a reproduced result. A `CERTIFIED` string is not certification.

### 1.2 Non-negotiable scientific boundaries

Veyra is a **forecast-reliability and bust-detection layer**, not a replacement weather forecaster. Hazard occurrence probability is not forecast-bust probability. Calibration, uncertainty, OOD, abstention, provider disagreement, ensemble spread, confidence, and certification are distinct concepts. Features must be available no later than issue time. A frozen incumbent may be replaced only after a challenger passes equivalent leakage, calibration, subgroup, uncertainty, OOD, and promotion gates.[1] [2]

The prototype evidence boundary remains **public-proxy GEFS/Open-Meteo or WeatherBench 2 with ERA5/reference-analysis framing**. Neither repository proves paired NCMRWF/NEPS operational validation merely by naming NCMRWF, IMD, DWR, INSAT, ECMWF, or other systems. Rainfall reliability is not flood probability. Explanations identify predictive contributions or coded reason rules, not physical causality.[5]

## 2. Repository forensics and executable record

### Table A — Repository Snapshot

| Item | Repository A | Repository B |
|---|---|---|
| Neutral identifier | Repository A | Repository B |
| Upstream default branch | `main` | `main` |
| Audited/current upstream HEAD | `b9f52d3eeec8676e06b1879f05b404605e2501be` | `82eded8194151e37fb9b3eecf273010dc62d7b29` |
| HEAD timestamp | `2026-09-21T09:44:50+05:30` | `2026-09-21T00:02:06+05:30` |
| Visible HEAD subject | Merge of PR #55 for human-verification fixes | README scientific-workflow documentation update |
| Working tree at audit | Clean tracked tree | Clean tracked tree |
| Checkout/history depth | Shallow/grafted; one visible merge commit | Shallow/grafted; one visible commit |
| Branch/PR governance | One PR merge visible; protection/full history unverified | Direct push-to-`main` deployment visible; protection/PR history unverified |
| CI/workflow | No current `.github/workflows` | `.github/workflows/deploy.yml` builds/deploys frontend only |
| Initial clean-checkout size | 15 MiB | 8.0 MiB |
| Tracked files / tracked bytes | 866 / 8,832,697 | 448 / 5,233,492 |
| Top-level implementation | `backend`, `frontend`, `models`, `data`, `scripts`; many historical/duplicate trees | `backend`, `frontend`, `models`, `data`, `scripts`, `docs`, `.round2-roadmap` |
| Backend | FastAPI under `backend/app`; broad endpoints/services | FastAPI under `backend/app`; versioned endpoints/services |
| Frontend | React/Vite; 9 executed test files | React/Vite; 4 executed test files |
| Model/artifact directories | `models/v3`, `models/day4`; V3 binary paths contain pointer text | `models/v3`, `models/day4`, baseline logistic; V3 binaries load |
| Tests | Active pytest root `backend/tests`; 684 collected | `backend/tests`; complete run produced 758 passes |
| Deployment | `vercel.json`; not independently deployed in audit | Pages workflow with external API URL; deployed environment unverified |
| Open release failure | V3 hash/load/replay/release failures | Feature-contract hash failure; verifier exits 1 |

File count, history depth, branding, README length, and number of future modules received no independent quality credit. Repository A's visible PR merge and Repository B's direct-main Pages deployment are governance signals only; neither proves protected-branch policy.

### Table B — Docs vs Code vs Tests vs Runtime

| Evidence layer | Repository A | Repository B | Disposition |
|---|---|---|---|
| README/roadmap | Root README retains stale 92-test language; historical trees coexist | README claims 816 tests and broad specialist certification/completion | Prose credited only where current code/execution agrees |
| Current source | Strict V3 adapter; issue-time contracts; certification/OOD policy; SQLite/WAL revision store; replay harness | Loadable V3 adapter; hazard, spatial, common-mode, evidence, drift, replay, and API/UI modules | Implementation credit only; formulas are not trained models |
| Committed artifacts | `models/v3/*.joblib` are LFS pointer text; manifests and feature file exist | Expected V3 model/calibrator binaries load; 50-feature file and many JSON manifests exist | A core identity contradicted; B model/calibrator reproduced, complete chain contradicted |
| Backend tests | 684 collected; no complete passing run; targeted run had failures/errors | **758 passed**, 60 warnings, 343.24 s | B result is reproduced software evidence, not 758 scientific validations |
| Frontend tests/build | **109 passed**; build passed; React `act(...)` and 698.05 kB chunk warnings | **58 passed**; build passed; 655.97 kB chunk warning | Reproduced UI/build evidence |
| API smoke | `/v1/health`, `/v1/metrics`, `/v1/ood/policy` returned 200; health remained green while model unavailable | `/`, `/v1/health`, `/openapi.json` returned 200 | Local startup only; A health is not model readiness |
| Artifact verification | Model/calibrator on-disk hashes fail; `joblib.load` raises `KeyError: 118` | Model and calibrator pass; feature hash fails | Release blocker in both; decisive inference blocker in A |
| Replay | Independent harness structure, but current execution blocked by pointer files | Six-cycle script executes with source-declared synthetic progression and inconsistent Brier text | A current release claim contradicted; B fixture/simulation only |
| Live-vs-fixture | Open-Meteo live adapter; second provider explicitly fixture-only | Open-Meteo request code; synthetic fallback, deterministic risk map, and synthetic replay | No paired national-system validation in either |
| Clean clone/release | LFS payload unavailable; no CI; release manifest disk validation fails | Dependencies install and suites run; verifier/version/CI gaps remain | A contradicted for frozen release; B partial |

Repository A's completed targeted backend run was **69 passed, 4 failed, 1 skipped, 9 errors**; a first-failure run was **28 passed, 1 failed**. Two bounded full runs did not finish, so no full-backend outcome is inferred. Repository B's backend run completed with **758 passed, zero failed/skipped/xfail**, and its frontend completed with **58 passed**. Repository A's frontend completed with **109 passed**. Test quantities are reported by command and are not treated as master-suite identity.[3] [4]

## 3. Model and artifact audit

Repository A's paths `models/v3/lightgbm_v3_challenger.joblib` and `models/v3/probability_calibrator_v3.joblib` exist, but contain Git LFS pointer text. Their observed file hashes are `a6f97f085189f6c9f66dec162ba2052176b71d760656f4e6be1c95d51382d5d0` and `db4ba1d44201072322c0979abdd3a94f0497f9bc550558dcebd936d6ab832aa6`, not the expected model/calibrator hashes. Pointer OIDs matching expected hashes do not make the checkout files loadable artifacts. `backend/app/builder2/v3_model_adapter.py` detects the mismatch and safely marks the model unavailable. `backend/app/api/v1/endpoints/predict.py` does not silently substitute the legacy Day-4 model.[3]

Repository B's V3 model hash matches `00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660`; the model loads as a LightGBM Booster. Its calibrator hash matches `9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531`; it loads as `IsotonicRegression`, with a scikit-learn 1.9.0-to-1.9.1 warning. The 50-feature file exists, but its actual hash `702ff4153fd95d8c9de3bbd01461d65fde0ef207099f7f3a8e7f5c8bac02031e` conflicts with declared `265cffbbd157a2b8b8b46d3702438050980043b5ed3a6a646a7969cdb985335`. `scripts/verify_artifacts.py` therefore exits 1.[4]

Repository B also contains `models/day4/lightgbm_bust_model.joblib`, a Day-4 calibrator, and `models/baseline_logistic_v1.joblib`. The V3 adapter uses threshold `0.060`, while a legacy Day-4 service uses `0.280`. These values may both be legitimate in different model contexts, but release authority is ambiguous until a versioned route-to-model/threshold/fallback manifest defines which path serves each endpoint.

### Table C — Major Capability Comparison

| Capability | Repository A | Repository B | Evidence-weighted finding |
|---|---|---|---|
| Reliability-layer mission | `VERIFIED` as product contract | `VERIFIED` as product contract | Tie; no credit as a replacement forecaster |
| Public-proxy boundary | Explicit live/fixture disclosure | Provider names plus live and synthetic paths | A is more conservative; neither proves national-system validation |
| Frozen V3 core | `CONTRADICTED`: pointer files cannot load | `PARTIAL`: model/calibrator load, feature checksum fails | B clearly preferable after integrity repair |
| Feature order/calibration | Strict 50-feature checks; calibrator unavailable | 50 entries; isotonic loads; chain mismatch | B preferable, not fully release-valid |
| Issue-time/leakage safety | UTC contract and anti-leakage tests; full lineage not regenerated | Split manifests, forbidden-feature tests; full lineage not regenerated | Similar `PARTIAL` evidence |
| Baseline ladder | V3/legacy assets, incumbent unavailable | Logistic, Day-4, V3 artifacts and scripts | B broader; evaluation still needs rerun |
| Revision intelligence | SQLite/WAL exact-target pattern; live single-cycle revision features zeroed | Revision features and Zarr store; durability/restart proof absent | A pattern preferable; both partial |
| Failure Memory/motifs | Revision/fingerprint modules; no live validated memory | Dedicated memory/motif modules and catalogue | B broader; neither scientifically established |
| Multi-horizon/recovery | Timeline/horizon code; no recovery validation | Horizon/recovery engines and API fields | B broader, unvalidated scientifically |
| Hazard specialists | Named empirical specialists absent | Six broad deterministic/formula paths | B architecture only; no certification credit |
| Spatial/compound/common-mode | Spatial endpoint/UI; compound/common-mode missing | Graph, compound, common-mode modules with fixed logic | B broader prototype |
| Provider/cross-system | Live primary plus explicit fixture second provider | Cross-system engine and evidence JSON | Neither proves paired transfer; A disclosure safer |
| OOD/abstention | OOD diagnostic-only; model failure safely abstains | Active hazard OOD/abstention with fixed thresholds | B broader; representative calibration missing |
| Drift/independent truth | Mostly planned | Monitor, ledger, independent-truth code | B implementation lead, evidence incomplete |
| Explanation/evidence graph | Deterministic fingerprints/reason codes | Explanation and evidence-graph modules | B broader; neither establishes causality |
| Replay/digital twin | Stronger harness concept, blocked at runtime | Executable synthetic replay | B demo lead; neither proves historical replay science |
| Backend/API | Broad but incomplete execution/readiness observability | Broad, local smoke, completed suite | B preferable |
| Frontend/demo | 109 passes and build | 58 passes, build, broader surfaces | A has deeper reproduced UI tests; B has broader integration |
| Release/security/operations | No CI; release manifest invalid | Partial frontend CI; security tests; verifier invalid | B preferable but not ready |

## 4. Document-to-code and Phase A–L coverage

Source abbreviations are: **S1** main Forecast-Bust Sentinel specification; **S2** 120-file research study pack; **S3** 500-Test Master Suite; **S4** hazard blueprint; **S5** Docs-vs-Research-vs-Live comparison; **MP** authoritative master prompt. Exact subsection-to-module mapping is marked uncertain where the evidence does not establish it.

### Table D — Main Docs Requirement Coverage

| Requirement/capability | Source | Repository A evidence / status | Repository B evidence / status | Importance | Preferable | Merge recommendation |
|---|---|---|---|---|---|---|
| Mission, scope, SIH alignment | S1 §3; S4 §1 | Reliability API/UI; `VERIFIED` as scope | Same; `VERIFIED` as scope | Critical | Tie | Preserve wording |
| Bust definition/labels | S1 §8; S4 contracts | V3 manifests/label code; `PARTIAL` | `data/target_manifest.json` and hazard targets; `PARTIAL` | Critical | B breadth | Freeze versioned target definitions |
| Data sources/engineering | S1 data; S3 DATA | Historical/QC/live adapters; `PARTIAL` | Data/reference/hazard manifests and Open-Meteo service; `PARTIAL` | Critical | B | Import A disclosure discipline |
| Feature engineering/order | S1 §9; MP model audit | Strict adapter and 50 names; binary parity unavailable; `PARTIAL` | Loadable V3 and 50 names; checksum conflict; `PARTIAL` | Critical | B | Repair checksum; keep strict order gate |
| Models/baseline ladder | S1 §10; S4 §5 | Legacy/V3 paths; incumbent unavailable; `PARTIAL` | Logistic/Day-4/V3; `PARTIAL` | High | B | Keep B incumbent; isolate challengers |
| Evaluation science | S1 evaluation; S4 §5 | Frozen metric manifests only; `SUPPORTED_BY_ARTIFACT` | V3/specialist JSON metrics; `SUPPORTED_BY_ARTIFACT` | Critical | Neither | Reproduce from immutable inputs |
| Revision/historical intelligence | S4 §6; S3 REV | `revision_store.py`; live features zeroed; `PARTIAL` | Zarr/revision features; restart proof missing; `PARTIAL` | High | A pattern | Reimplement durable service in B |
| Failure Memory | S4 §6.1; S3 FMEM | Modules/history concepts; `PARTIAL` | `failure_memory.py`; provenance incomplete; `PARTIAL` | High | Neither scientifically | Rebuild against durable history |
| Failure Motifs | S4 §6.2; S3 FMOT | Heuristic `instability_fingerprint.py`; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | `failure_motifs.py` and catalogue; same status | Medium | B breadth | Episode-safe validation required |
| Multi-horizon/time-to-bust/recovery | S4 §6.4; S3 HAZ | Timeline/horizon contracts; `PARTIAL` | Horizon/recovery tests/services; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | High | B | Retain as experimental |
| Precipitation reliability | S4 §7; Phase D | No named specialist; `N/A — uncovered/missing` | Formula/baseline specialist; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | P0/Critical | B code | Require real-data empirical gate |
| Cyclone reliability | S4 §8; Phase E | `N/A — uncovered/missing` | Deterministic track/intensity logic; `PROTOTYPE_ONLY` | High | B code | Keep experimental |
| Monsoon/LPS reliability | S4 §9; Phase F | Docs/utilities only; `N/A — uncovered/missing` | Hand-coded target/regime logic; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | High | B code | Keep experimental |
| Western disturbance | S4 §10; Phase G | `N/A — uncovered/missing` | Fixed decomposed probabilities/OOD; `PROTOTYPE_ONLY` | High | B code | Keep experimental |
| Heatwave | S4 §11; Phase H | `N/A — uncovered/missing` | Explicit fixed logistic equations; `SUPPORTED_BY_CODE_ONLY` | High | B formula baseline | Do not call trained/certified |
| Severe wind | S4 §12; Phase H | Generic wind variable only; `N/A — uncovered/missing` | Compound/heatwave-linked path; `PARTIAL` | Data-dependent | Neither for certification | Reject independent-specialist claim |
| Spatial reliability | S4 §§14–19; S3 SPAT | Endpoint/UI/tests; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | Graph engine/topology/tests; same status | High | B architecture | Revalidate on real spatial truth |
| Compound/common-mode | S4; Phase I | `N/A — uncovered/missing` | Fixed/copula/common-mode logic; `PROTOTYPE_ONLY` | High | B code | Isolate as experimental |
| Multi-provider/cross-system | S1 E8; S3 MULTI; Phase K | Fixture second provider; `PARTIAL` | Engine/artifact; transfer `DOCUMENTED_ONLY`/artifact-only | High | Neither scientifically | Build paired-system evaluation |
| Drift/independent truth | S4; Phase J | OOD policy; truth future; `PARTIAL` | Monitor/ledger/audit module; `PARTIAL` | Critical | B code | Revalidate held-out shifts |
| Explainability/evidence graph | S1; Phase L | Fingerprints/reason codes; code-only | Evidence graph/explainer; code-only | Medium | B breadth | Preserve non-causal wording |
| Digital twin/replay/counterfactual | S4; Phase L | Harness blocked; `CONTRADICTED` current execution | Synthetic replay; `PROTOTYPE_ONLY` | Medium | Neither unchanged | Reimplement immutable replay |
| API/backend | S3 API/OPS | Broad code, partial smoke; `PARTIAL` | Smoke and 758-test run; `VERIFIED` locally | High | B | B is destination |
| Frontend/SIH demo | S3 UI | 109 tests/build; `VERIFIED` locally | 58 tests/build; `VERIFIED` locally | High | Close | Port only proven behavior |
| Reproducibility/release | S3 GOV/ML/OPS | LFS payload absent, no CI; `CONTRADICTED` | Verifier fails, CI partial; `PARTIAL` | Critical | B | Repair before integration |
| Security/robustness/operations | S3 OPS | Middleware/configuration and selected tests; `PARTIAL` | Middleware/auth/RBAC/security tests; `PARTIAL` operationally | High | B | Add CI/load/security gates |
| Test-suite coverage | S3 all domains | 684 collect, full run incomplete; `PARTIAL` | 816 passes, no exact 500-ID map; `PARTIAL` | High | B execution | Map named IDs explicitly |
| Live/runtime checks | MP hardened checks | Process health masks model unavailable; readiness `CONTRADICTED` | Local startup; deployment/live provider unverified; `PARTIAL` | Critical | B | Add model-ready and provenance checks |
| Documentation drift audit | S1 §30; S5 | Stale test count and duplicate histories; `CONTRADICTED` in places | Certification/replay drift; `CONTRADICTED` in places | High | Neither | Establish claim register |
| Scientific claim audit | MP scientific audit | Safer wording; incumbent fails | Usable core; specialist claims exceed proof | Critical | A honesty; B core | Apply one claim taxonomy |
| Scoring/decision logic | MP rubric | Same weights/evidence caps | Same weights/evidence caps | High | N/A | Keep independent of product claims |
| Combine/integration safety | MP merge rules | Useful patterns; incompatible artifacts | Better base; conflicting labels/thresholds | Critical | B as base | Selective adaptation only |

**Phase A–L disposition.** Phase A is `CONTRADICTED` in A and `PARTIAL` in B because neither has a clean V3 artifact chain. Phases B and C are partial in both, with B broader. Phases D–H are missing as named specialists in A and implemented only as deterministic or formula-based prototypes in B; severe wind remains partial. Phase I is mostly absent in A and prototype/code-only in B. Phase J is diagnostic/future in A and implemented but unvalidated in B. Phase K lacks paired transfer and complete promotion evidence in both. Phase L is blocked in A and synthetic in B. This mapping does not equate roadmap text with execution.[5]

## 5. Hazard and 500-test evidence

### Table E — Hazard Specialist Evidence

| Specialist | Repository A | Repository B implementation | Empirical provenance | Current disposition |
|---|---|---|---|---|
| Precipitation | No named hazard-conditional trained specialist; `N/A — uncovered/missing` | `backend/app/builder2/precipitation_specialist.py` contains deterministic baseline/score logic | JSON metrics/coverage only; no specialist trained artifact, feature order, training data, or rerun | Keep B only as experimental baseline |
| Tropical cyclone | `N/A — uncovered/missing` | `cyclone_specialist.py` contains deterministic track/intensity rules and constants | Held-out/certification assertions not reproduced | Prototype only |
| Monsoon/LPS | Docs/utilities only; `N/A — uncovered/missing` | `monsoon_specialist.py` contains hand-coded target/regime logic | Metrics are artifact claims; no trained artifact | Experimental only |
| Western disturbance | `N/A — uncovered/missing` | `western_disturbance_specialist.py` contains decomposed fixed probabilities and thresholds | Reported cycle/bootstrap values not rerun | Prototype only |
| Heatwave | `N/A — uncovered/missing` | `heatwave_specialist.py` contains fixed logistic equations | Coefficient provenance absent | Formula baseline only |
| Severe/high wind | Generic V3 wind variable is not a specialist | No independent trained specialist; wind appears in compound/heatwave paths | No independent model/calibrator/evaluation package | Reject certification claim |
| Spatial reliability | Endpoint/UI/tests; no benchmark rerun | `spatial_reliability_engine.py`, graph/topology, inverse-distance/fixed values | Empirical covariance and held-out bounds not reproduced | Architecture only |

**No current evidence supports six independently certified empirical meteorological hazard specialists in either repository.** Repository B has broader executable software, but software completeness and scientific validation are separate.

### Table F — 500-Test Domain Coverage

| Domain | Repository A | Repository B | Coverage finding |
|---|---|---|---|
| API | Broad route tests; full suite incomplete | Dedicated API/contract tests in passing suite | Both `PARTIAL` against named 25 IDs |
| DATA | Historical/QC test families | Data contracts/services/test families | Both `PARTIAL`; raw lineage not regenerated |
| ENS | Ensemble-derived features/tests | Ensemble service/tests | Both `PARTIAL` |
| LOC | Location/certification tests | Location tests/catalogues | Both `PARTIAL` |
| V3 | Dedicated tests; current artifact tests fail | Tests pass, external verifier fails feature hash | A `CONTRADICTED`; B `PARTIAL` |
| CAL | Calibrator unavailable | Isotonic loads; calibration tests/metrics not empirically rerun | A `PARTIAL`; B `PARTIAL` scientifically |
| REL | Schemas/test family | Multiple reliability tests | Both `PARTIAL`; B broader |
| HAZ | Horizon/UI code; named specialists absent | Horizon/recovery/routing tests | Both `PARTIAL` |
| REV | SQLite store and revision tests | Features/storage; exact named mapping uncertain | Both `PARTIAL` |
| FMEM | Code; no exact dedicated 25-ID map | Services/fixtures; no exact 25-ID map | `N/A — uncovered/missing` for exact mapping |
| FMOT | Heuristic fingerprints; no exact domain map | Motif tests/catalogue | A uncovered; B `PARTIAL` |
| SPAT | One named test family | Graph/leakage/propagation tests | Both `PARTIAL`; B broader |
| VERT | No dedicated vertical-domain map found | No dedicated vertical-domain map found | `N/A — uncovered/missing` in both |
| PREC | No named specialist tests | Precipitation contract/target tests | A uncovered; B `PARTIAL` |
| HAZSP | Named specialist suites absent | Cyclone/monsoon/WD/heatwave/compound tests | A uncovered; B `PARTIAL`; no empirical upgrade |
| GOV | OOD/release/replay tests; release fails | OOD/drift/truth/security tests; artifact gate fails | A `CONTRADICTED`; B `PARTIAL` |
| MULTI | Fixture-based disagreement tests | Multi-system tests and transfer artifact | Both `PARTIAL`; no paired live science |
| ML | Feature/leakage code; complete run unavailable | Leakage/split manifests/baselines | Both `PARTIAL`; training matrix not rebuilt |
| UI | 109 passes and build | 58 passes and build | Reproduced local subsets; no 25-ID certification |
| OPS | Middleware/deploy config; no CI; release failure | Security tests/partial CI; no backend gate | Both `PARTIAL` |

The 500-test specification defines **20 domains × 25 tests**. Repository B's 816 completed tests are genuine software evidence, but test quantity is not identity. Neither repository has a one-to-one record for all 500 specified IDs with passed, failed, blocked, skipped, xfail, and `N/A — uncovered/missing` outcomes.[2]

## 6. Scientific claims: claimed versus proven

### Table G — Scientific Claims: Claimed vs Proven

| Major claim | Repository A | Repository B | Required disposition |
|---|---|---|---|
| Frozen V3 model identity | `CONTRADICTED`: pointer hash differs; load fails | `REPRODUCED`: expected hash and Booster load | Use B binary only after full chain passes |
| Frozen calibrator identity/type | `CONTRADICTED` on disk; manifest says isotonic | `REPRODUCED`: expected hash and `IsotonicRegression`; version warning | Pin environment; rerun |
| 50-feature contract | `SUPPORTED_BY_ARTIFACT`/code; binary parity unavailable | Count `REPRODUCED`; chain `CONTRADICTED` by checksum | Reconcile canonical file/hash |
| V3 Brier/ROC/ECE | `SUPPORTED_BY_ARTIFACT` | `SUPPORTED_BY_ARTIFACT` | Reproduce from frozen evaluation rows |
| 25-station, 3-variable, ≤240 h scope | Code/artifact only; model unavailable | Code/artifact only; evaluation not rerun | Preserve as bounded claim, not fresh certification |
| Operational >240 h | Code-only and labeled uncertified | Code-only; model authority ambiguous | Keep explicitly uncertified |
| Six certified specialists | Missing/unverified | Software code-only; certification `DOCUMENTATION_ONLY` | Remove/relabel unless full evidence package exists |
| Specialist Brier/ECE/PR-AUC | `UNVERIFIED` | `SUPPORTED_BY_ARTIFACT` | Independent rerun required |
| Conditional/conformal ≥90% coverage | `UNVERIFIED` | `SUPPORTED_BY_ARTIFACT` | Reject production claim pending rerun |
| +24 h to +96 h warning | `UNVERIFIED` | `SUPPORTED_BY_TEST_FIXTURE_ONLY` | Synthetic progression cannot support claim |
| NCMRWF/NEPS/IMD/DWR/INSAT ingestion | `UNVERIFIED` | `DOCUMENTATION_ONLY`/code references | Require actual paired data/metadata/permission |
| Open-Meteo/GEFS path | Code-only; one upstream fetch occurred in test | Code-only; external live prediction not audit evidence | Label provider/live/cache/fallback on every response |
| Cross-system transferability | Fixture-only second provider | Transfer JSON `SUPPORTED_BY_ARTIFACT` | Paired-system independent rerun required |
| Common-mode/compound certification | Missing | Logic code-only; certification unverified | Experimental only |
| OOD safety | Diagnostic policy/test fixtures; not auto-abstaining | Crash behavior reproduced in tests; thresholds unvalidated | Distinguish diagnostic from active OOD |
| Revision durability | SQLite/WAL code-only; restart not rerun | Zarr/code-only; restart not demonstrated | Rebuild and test exact-target restart behavior |
| Historical replay independence | Current execution `CONTRADICTED` by pointers | `SUPPORTED_BY_TEST_FIXTURE_ONLY`; cycles explicitly synthetic | Reimplement with immutable forecasts/truth |
| Digital-twin scientific conclusion | `UNVERIFIED` | Fixture-only; Brier text conflicts | Reject scientific conclusion |
| Release integrity | `CONTRADICTED` | `CONTRADICTED` at feature checksum | No release claim until verifier passes |
| README test claim | Stale/`CONTRADICTED` | 758+58 reproduced | Keep counts command-specific |

## 7. Scores and diagnostic trade-offs

### Table H — 0–100 Scoring

Weighted contribution equals `raw × weight ÷ 100`. Science-heavy rows are capped where evidence is code-, fixture-, or document-only.

| Category | Weight | A raw | A weighted | A confidence | B raw | B weighted | B confidence | Evidence reason |
|---|---:|---:|---:|---|---:|---:|---|---|
| 1. Scientific correctness, claim discipline & leakage safety | 15 | 58 | 8.70 | Medium | 58 | 8.70 | Medium | A is conservative but unavailable; B overstates specialist validation |
| 2. SIH26079 docs/research alignment | 8 | 62 | 4.96 | Medium | 78 | 6.24 | Medium | B covers more phases; breadth is not certification |
| 3. Core V3/baseline, calibration & artifact reproducibility | 10 | 25 | 2.50 | High | 82 | 8.20 | High/Medium | A cannot load binaries; B loads two artifacts but feature hash fails |
| 4. Data pipeline, issue-time contracts, provenance & QC | 7 | 62 | 4.34 | Medium | 62 | 4.34 | Medium | Controls exist; raw lineage/national paired data absent |
| 5. Revisions, Failure Memory, Motifs, multi-horizon/recovery | 8 | 48 | 3.84 | Medium | 68 | 5.44 | Medium/Low | A has durable design; B broader modules; neither proves live history |
| 6. Hazard specialists and empirical validation | 10 | 12 | 1.20 | High | 45 | 4.50 | High | A lacks specialists; B specialists are deterministic/formula-based |
| 7. Certification, OOD, abstention, drift & independent truth | 9 | 58 | 5.22 | Medium | 62 | 5.58 | Medium | Safety paths exist; representative validation absent |
| 8. Spatial, ensemble, provider & cross-system intelligence | 6 | 55 | 3.30 | Medium | 55 | 3.30 | Medium/Low | A is fixture-honest; B broader; neither proves transfer |
| 9. Backend/API architecture & robustness | 6 | 65 | 3.90 | Medium | 78 | 4.68 | High/Medium | B completed suite/smoke; production operations untested |
| 10. Frontend/demo & scientific communication | 5 | 78 | 3.90 | High | 74 | 3.70 | High | Both build; A has 109 tests, B broader surfaces |
| 11. Testing, reproducibility, replay & release engineering | 8 | 30 | 2.40 | High | 76 | 6.08 | High/Medium | A backend/replay fail; B suites pass but verifier/CI incomplete |
| 12. Documentation accuracy, traceability & maintainability | 4 | 56 | 2.24 | Medium | 60 | 2.40 | Medium | A stale/duplicated; B certification/replay drift |
| 13. SIH Round-2 submission readiness | 4 | 35 | 1.40 | High | 58 | 2.32 | Medium | A inference unavailable; B needs integrity/claim cleanup |
| **Total** | **100** | — | **47.90** | **Medium** | — | **65.48** | **Medium** | **B leads by 17.58** |

### Table I — Weighted Total

| Result | Repository A | Repository B | Interpretation |
|---|---:|---:|---|
| Final weighted score | **47.90/100** | **65.48/100** | A: partial/mostly prototype; B: functional but incomplete or weakly evidenced |
| Scientific maturity | 39 | 57 | B has a loadable incumbent; neither reproduces specialist science |
| Software engineering maturity | 68 | 78 | B has complete backend execution and broader modularity |
| Research breadth | 58 | 88 | B implements more Phase A–L surfaces |
| Reproducibility | 25 | 67 | A lacks usable V3 payloads; B has checksum/version issues |
| Operational honesty | 72 | 55 | A is clearer about fixtures/scope; B overuses certification language |
| Demo/presentation readiness | 75 | 76 | Both build; B is broader but needs simulation labels |
| Documentation quality | 70 | 68 | A is detailed but stale; B is extensive but claim-drifted |
| Long-term extensibility | 74 | 84 | B's modules/schemas are the broader base |
| Immediate SIH submission readiness | 35 | 58 | B is closer; neither is ready unchanged |
| Mergeability/integration compatibility | 58 | 62 | Modular, but contracts, thresholds, stores, and labels conflict |

## 8. Immediate base selection and split combine decision

### Q1 — Which repository is the stronger base?

**Repository B.** It has the expected loadable V3 model and calibrator, a completed backend and frontend test record, broader current modules, a functioning local API, and a more suitable destination architecture. The selection is not an endorsement of its specialist science. Repository A remains useful as a source of operational safety patterns, but a base whose default incumbent cannot deserialize is not the stronger current base.

### Immediate suitability as-is

**Required choice: `NO_REPOSITORY_READY_YET`.** Repository A cannot demonstrate its central scientific model. Repository B can demonstrate V3 inference components and broad software, but its own verifier exits 1, specialist certification exceeds provenance, synthetic replay can be mistaken for historical evidence, CI omits backend/scientific gates, and model-selection authority is not frozen. The correct short path is a bounded Repository B repair sprint, not unchanged submission or a pre-submission cross-repository merge.

### Hypothetical combined-system outcome

A raw merge would first make the system **less reproducible and maintainable** by duplicating FastAPI applications, React frontends, model services, stores, test suites, docs, and deployment assumptions. It would not repair A's absent binary payloads, B's feature checksum, B's specialist provenance, or either repository's missing paired national-system validation.

A selective combination can improve the system if Repository B remains the sole active base. Keep B's loadable V3, broad API, test suite, and experimental specialist architecture. Adapt from A only the safe `MODEL_NOT_READY` behavior, explicit certification-scope policy, fixture-provider disclosure, UTC/time contract, release/replay invariants, and exact-target SQLite/WAL revision semantics. Rebuild the release manifest, provider registry, revision service, and real replay rather than copying conflicting implementations. Revalidate every serving, calibration, leakage, OOD, provider, revision, and UI contract. The combination is worth the risk **only after immediate B blockers are fixed and only as selective integration**.

### Table J — Selective Integration Matrix

| Capability | Best source | Exact source modules | Scientific status | Action | Dependency risk | API/schema risk | Model/data risk | Validation required | Priority |
|---|---|---|---|---|---|---|---|---|---|
| Frozen V3 binaries | B | `models/v3/lightgbm_v3_challenger.joblib`; `probability_calibrator_v3.joblib` | Identity reproduced | Keep | Medium: sklearn pin | Medium: feature contract | High until checksum fixed | Clean-clone hash/type/order/inference parity | P0 |
| V3/release manifest | Neither unchanged | B `models/v3/*manifest*.json`; A `backend/app/core/release_manifest.*` | Both chains fail | Reimplement | Medium | High: IDs/thresholds | High | One manifest; verifier exit 0 | P0 |
| Serving authority | B destination | B `v3_model_adapter.py`, model registry/services; A `predict.py` failure semantics | Implemented, authority ambiguous | Reimplement | Medium | High | High: thresholds/fallbacks | Route-by-route replay and schema diff | P0 |
| Issue-time/UTC contract | A pattern + B manifests | A `backend/app/core/time_contract.py`; B training/target manifests | Code/artifact only | Adapt | Low | Medium | High: lineage | Raw-to-feature availability audit | P0 |
| Safe missing-model behavior | A | A `v3_model_adapter.py` and prediction safety layer | Runtime failure reproduced | Adapt | Low | Medium: trust fields | Low | Startup/route failure tests | P0 |
| Certification boundary | A | `backend/app/core/certification_policy.py`; certification endpoint/tests/UI repairs | Scope code-only | Adapt | Low | High: B labels | High: specialist scope | Claim register and UI E2E | P0 |
| Hazard specialists | B | `backend/app/builder2/*specialist.py` | Deterministic prototypes | Keep isolated/Adapt | Low | Medium | High: no trained artifacts | Per-hazard empirical package | P1 |
| Severe-wind specialist | Neither | B compound/heatwave pathways only | Independent specialist absent | Reject current claim | Unknown | High | High | New data/target/model gate | P2 |
| Revision durability | A pattern | A `revision_store.py`; B `backend/app/data/zarr_store.py` | Both partial | Reimplement | High: SQLite/Zarr | High: record keys | High: history provenance | Restart/reload/truth-sealing test | P1 |
| Failure Memory/motifs | B architecture | B `failure_memory.py`, `failure_motifs.py`; A `instability_fingerprint.py` | Heuristic/code-only | Adapt | Medium | Medium | High: episode truth | Held-out episode evaluation | P2 |
| Spatial reliability | B | `spatial_reliability_engine.py`; `data/spatial_network_topology.json` | Unvalidated implementation | Keep isolated | Medium | Medium | High: fixed vs empirical weights | Real spatial calibration/objects | P1 |
| Provider/cross-system | Neither unchanged | A provider adapters/disagreement; B `cross_system_transfer_engine.py` | Fixture/artifact-only | Reimplement | Medium | High: provider IDs | High: no paired archive | Paired-system replay | P1 |
| OOD/abstention | B destination, A scope tests | A `ood_policy.py`; B `safety/ood_*`, hazard modules | Software safety only | Adapt | Medium | High: diagnostic vs active | High: threshold validity | Held-out shift risk-coverage | P0 |
| Explanation/evidence graph | B | `evidence_graph_engine.py`, `explainer.py`, explanation service | Predictive explanation only | Keep/Adapt | Low | Medium | Medium | Semantic and comprehension review | P2 |
| Historical replay | Neither unchanged | A replay harness/golden matrix; B digital twin/script | A blocked; B synthetic | Reimplement | High | High | High: independent truth absent | Immutable event replay parity | P2 |
| Backend/API | B | `backend/app`, versioned routes/services | Locally reproduced | Keep | Medium | High during migration | Medium | OpenAPI/consumer regression suite | P1 |
| Frontend | B destination; selected A behaviors | Both `frontend/src` trees | Builds/tests reproduced | Adapt behavior only | Medium | High | Medium: provenance badges | Browser E2E in all trust states | P1 |
| CI/release gates | Neither complete | B `.github/workflows/deploy.yml`; A no workflow | Incomplete | Reimplement | Medium | Low | High: artifact storage | Required clean-clone pipeline/rollback | P0 |
| 500-test record | Neither | Existing tests plus S3 IDs | No exact map | Reimplement ledger | Low | Low | Medium | Exact ID disposition and run | P1 |

## 9. Exact collection plans

The collection lists preserve evidence without implying that collected material is production-ready. **Canonical** means the item should be the destination's source of truth after validation. **Informative** means it supports adaptation or audit but must not be copied as authority.

### Table K — Mergeable Assets from Repository A

| Family | Exact assets/modules to collect | Why needed | Role/action | Validation before use |
|---|---|---|---|---|
| **A. Core baseline/frozen V3** | `models/v3/feature_names.json`; `training_manifest.json`; `v3_evaluation_manifest.json`; `backend/app/builder2/v3_model_adapter.py`; `v3_feature_pipeline.py`; `backend/app/api/v1/endpoints/predict.py`; `models/day4/*` | Compare strict schema/order, safe load failure, serving selection, historical baseline | **Informative; Adapt.** Reject A V3 `.joblib` pointer files as binaries | Diff feature order; verify no artifact overwrite; port only tested failure semantics |
| **B. Reliability intelligence** | `backend/app/core/time_contract.py`; `revision_store.py`; `backend/app/services/revision_service.py`; `backend/app/builder2/instability_fingerprint.py`; `backend/app/core/replay_harness.py`; `golden_replay_matrix.py` | UTC identity, SQLite/WAL exact-target history, replay invariants, heuristic fingerprints | **Informative; Adapt/Reimplement** | Successive-cycle persistence, restart/reload, sealed truth, episode-safe replay |
| **C. Hazard specialists** | `backend/app/services/spatial_service.py`; spatial endpoint/schema/tests; provider-disagreement service/tests | A has no named hazard specialists; collect only useful spatial/provider safety behavior | **Informative; Adapt.** Mark specialist families `N/A — uncovered/missing` | Do not infer missing hazard equivalents; run B destination contract tests |
| **D. Calibration/OOD/abstention** | `backend/app/core/certification_policy.py`; `ood_policy.py`; V3 failure-safety/calibration/certification tests | Bounded scope, safe model-unavailable response, diagnostic OOD semantics | **Canonical pattern; Adapt** | Preserve null probability/abstain semantics; distinguish diagnostic from active OOD |
| **E. Evidence/explanation** | `backend/app/builder2/instability_fingerprint.py`; `Audits/VEYRA_*`; `backend/app/core/release_manifest.*` | Reason-code pattern, prior artifact/release analysis, declared release checks | **Informative; Adapt/Reject stale claims** | Non-causal language; current-SHA claim review; release manifest must be rebuilt |
| **F. Backend/frontend/demo** | Provider/certification/revision/spatial endpoints and schemas; `frontend/src/test`; `frontend/src/components/ModelCatalog.tsx`; `ModelEvaluationView.tsx`; `vercel.json` | Proven UI behavior, scope labels, trust-state tests, deployment comparison | **Informative; Adapt behavior only** | API schema diff; browser E2E; no blind snapshots or duplicate frontend |
| **G. Testing/reproducibility/release** | `backend/tests/test_v3_*`; `test_day34_time_contract_revision_store.py`; `test_day35_independent_replay_release_manifest.py`; `test_day37_provider_adapters.py`; `test_day38_cross_provider_disagreement.py`; `test_scientific_certification.py`; `pytest.ini`; `requirements.txt`; frontend locks | Migrate safety and disclosure assertions missing from B | **Canonical tests after port; Adapt** | Tests must fail before fix/pass after; pin dependencies; no counts summed across overlaps |
| **H. Documentation** | `BUILDER_1_BUILDER_2_INTEGRATION_CONTRACT.md`; `BUILDER_2_HANDOFF.md`; `docs/HORIZON_REQUEST_CONTRACT.md`; relevant `Audits/*`; current code-tied README sections | Preserve contracts and lessons, identify historical/stale statements | **Informative; Preserve with labels** | Tie each retained claim to destination path/test/SHA; delete or archive stale text |

**Repository A explicit rejects:** do not collect its two V3 pointer files as deployable artifacts; do not import historical duplicate application trees (`Builder-2`, `Parinidhi`, `Frontend-Original`, `Overview`) wholesale; do not reuse the unresolved base-commit release manifest as authoritative; do not count the fixture second provider as live.

### Table L — Mergeable Assets from Repository B

| Family | Exact assets/modules to collect | Why needed | Role/action | Validation before use |
|---|---|---|---|---|
| **A. Core baseline/frozen V3** | `models/v3/lightgbm_v3_challenger.joblib`; `probability_calibrator_v3.joblib`; `feature_names.json`; `artifact_manifest.json`; `training_manifest.json`; `v3_evaluation_manifest.json`; `v3_comprehensive_evaluation.json`; `models/day4/*`; `models/baseline_logistic_v1*`; `backend/app/builder2/v3_model_adapter.py` | Preserve loadable incumbent, baselines, model/calibration metadata | **Canonical after repair; Keep** | Reconcile feature hash; pin sklearn; verify 50-order, types, threshold, fallback, clean clone |
| **B. Reliability intelligence** | `failure_memory.py`; `failure_motifs.py`; recovery/horizon services/tests; `backend/app/data/zarr_store.py`; `backend/app/services/drift_monitor.py`; `independent_truth_audit.py`; motif/ledger data | Broad shared reliability architecture | **Canonical experimental base; Keep/Adapt** | Durable history, issue-time safety, episode holdouts, restart and truth latency |
| **C. Hazard specialists** | Six `backend/app/builder2/*specialist.py` paths; `spatial_reliability_engine.py`; `compound_hazard_engine.py`; `common_mode_detector.py`; `cross_system_transfer_engine.py`; hazard target/event JSON; `data/spatial_network_topology.json`; specialist JSON manifests | Preserve current prototype surface and contracts | **Experimental; Keep isolated** | Explicit formula-baseline labels; per-hazard raw data, splits, artifacts, calibration, bootstrap, OOT rerun |
| **D. Calibration/OOD/abstention** | `builder2/calibrator.py`; `conditional_calibration_engine.py`; `data/hazard_calibration_registry.json`; `backend/app/safety/ood_detector.py`; `ood_enforcement.py`; `data/counterfactual_crash_test_report.json`; prediction schemas | Consolidate active safety behavior | **Canonical implementation candidate; Adapt** | Representative held-out shifts; risk-coverage; failure behavior; probability-bound tests |
| **E. Evidence/explanation** | `evidence_graph_engine.py`; `explainer.py`; `services/explainability_service.py`; provenance schemas/endpoints; `data/cross_system_evidence.json`; replay outputs | Keep provenance and non-causal explanation interface | **Canonical UI/API pattern; Reject unsupported conclusions** | Trace every edge to source; mark artifacts vs reproduced; remove causal/certified inflation |
| **F. Backend/frontend/demo** | `backend/app`; versioned routes; `frontend/src`; build/test scripts; `.github/workflows/deploy.yml`; Open-Meteo and fallback services | Destination application and demo | **Canonical base; Keep** | OpenAPI diff; live/cache/fixture/synthetic badges; deployed failure-path E2E; bundle review |
| **G. Testing/reproducibility/release** | `backend/tests`; frontend tests/locks; `scripts/verify_artifacts.py`; `replay_digital_twin.py`; `evaluate_cross_system.py`; `evaluate_spatial_propagation.py`; smoke scripts; `requirements.txt`; `pyproject.toml`; `pytest.ini` | Preserve reproduced suites and build the required gates | **Canonical after correction; Keep/Extend** | Verifier exit 0; exact environment; backend/frontend/security/replay gates; tagged rollback |
| **H. Documentation** | `ARCHITECTURE.md`; `REPRODUCIBILITY_PACKAGE.md`; `docs/*`; `.round2-roadmap/*`; `round2-report/*`; current README sections | Base architecture and roadmap evidence | **Informative until claim cleanup; Adapt** | Claim register; replace `CERTIFIED` where unsupported; mark synthetic replay; archive stale phase text |

**Repository B explicit rejects or quarantines:** do not promote specialist JSON metrics, cross-system values, conformal/coverage figures, warning-lead numbers, common-mode claims, or digital-twin conclusions as reproduced science. Do not let `fallback_service.py` synthetic cycles or deterministic risk-map outputs appear as live observations. Do not retain conflicting feature hashes or multiple undocumented serving thresholds.

## 10. Actual phased integration roadmap

The roadmap starts only after the immediate Repository B repair decision. Each phase corresponds to observed work; none assumes unavailable national or specialist data.

### Table M — Merge Roadmap

| Phase | Goal | Input from A | Input from B | Dependencies | Outputs | Failure conditions | Revalidation gate |
|---|---|---|---|---|---|---|---|
| **0 — Freeze and inventory** | Freeze both SHAs and evidence before edits | SHA, hashes, pointer evidence, manifests, test logs | SHA, hashes, manifests, test/replay logs | Read-only clones; artifact inventory tool | Signed inventory, path ledger, baseline scores | Any unrecorded artifact/source mutation | Recompute hashes/status; independent inventory review |
| **1 — Truth alignment** | Make claims match current evidence | Fixture/scope language; stale-README findings | Specialist/replay/transfer claims and docs | Claim taxonomy; source-to-claim owner | Claim register; stale/contradicted text list | Unsupported `CERTIFIED`, live, historical, or national-validation language remains | Reviewer maps every major claim to class/evidence |
| **2 — Base selection and branch controls** | Establish B as sole destination and required checks | Selected pattern list only | Current B application tree | Clean Phase 0; protected integration branch | Base decision record; no duplicate app trees | A application tree or artifacts imported wholesale | Clean tree; branch/check policy verified |
| **3 — Incumbent artifact repair** | Make frozen V3 chain authoritative without changing model | A strict failure/order test patterns | B model, calibrator, feature file/manifests, verifier | Exact environment; canonical feature decision | One release manifest; one model ID/threshold/fallback map; verifier exit 0 | Hash/type/order mismatch; silent fallback; unexplained artifact change | G1–G3: clean-clone integrity and golden parity |
| **4 — Selective safety grafting** | Adapt only A patterns that reduce operational risk | Time contract, safe failure, certification boundary, fixture disclosure, revision semantics | B registries, schemas, services, UI | Phase 3 frozen incumbent; schema design | B-native safety modules and migrated tests | Probability semantics change; provider/UTC identity lost; model output changes | API diff, V3 parity, failure-path and leakage tests |
| **5 — Reliability-store and replay rebuild** | Create durable history and honest historical replay | SQLite/WAL exact-target design; replay invariants | B Zarr/history modules; synthetic engine as fixture only | Immutable event inputs; truth-latency contract | Durable revision service; separate fixture and historical replay modes | Fabricated cycles, unsealed truth, restart loss, metric inconsistency | G9/G11 restart, truth-sealing, immutable replay |
| **6 — Experimental module containment** | Keep B breadth without overclaiming | A certification/display boundaries | B specialists, spatial, compound, common-mode, transfer, evidence graph | Namespaced experimental registry; feature flags | Formula-baseline labels; promotion templates; disabled production promotion | Any module enters incumbent path without empirical package | Per-hazard G8; provider G10; OOD G7 |
| **7 — Test, CI, and release consolidation** | Turn evidence checks into required release gates | Ported A safety/release/provider/UI tests | B 758+58 suites, verifier, workflow, locks | Stable merged schemas; exact test map | CI for backend/frontend/build/artifacts/security/replay; 500-ID ledger; rollback | Deployment possible after failed gate; unmapped critical behavior | G14–G17 complete; clean clone rerun |
| **8 — Submission readiness** | Produce a truthful, demonstrable release | Conservative claim language and UI scope checks | Repaired B demo, API, manifests, evidence package | All P0 gates; bounded demo script | Tagged candidate; judge-facing claim sheet; risk register | Any P0 blocker; false live/certified label; model not ready | Independent reviewer reruns hashes, tests, build, smoke, replay, claims |
| **9 — Post-submission empirical program** | Decide whether any specialist deserves promotion | No A specialist artifacts | B formula baselines and contracts | Real issue-time forecast/reference data and governance | Per-hazard challenger reports; promote or reject | Leakage, unavailable data, no baseline gain, calibration/coverage failure | Out-of-time/event/OOD/uncertainty gates; incumbent unchanged on failure |

The roadmap deliberately separates **software integration** from **scientific promotion**. A specialist can be integrated as an experimental formula baseline while still failing the evidence needed for operational certification.

## 11. Validation gates and merge blockers

### Table N — Validation Gates

| Gate | Required evidence | Acceptance criterion |
|---|---|---|
| G0 Clean baseline | Fresh B clone at tagged commit and frozen A evidence bundle | Clean tree; dependencies from locked manifests; inventories match |
| G1 Artifact integrity | One manifest covering model, calibrator, feature order, environment, ID, threshold, fallback | Every SHA/type matches; `scripts/verify_artifacts.py` exits 0 |
| G2 Incumbent parity | Golden inputs before/after integration | Identical calibrated V3 outputs within declared tolerance; no silent fallback |
| G3 Model authority | Route-to-model/threshold/fallback map | Exactly one authoritative model path per route; V3 remains incumbent |
| G4 Issue-time leakage | Raw-to-feature lineage and availability timestamps | No future observation, reanalysis, error, label, verifying imagery, or post-valid-time data |
| G5 Target semantics | Versioned generic/hazard contracts | Hazard occurrence never substitutes for bust; continuous error separate |
| G6 Calibration | Frozen OOT inputs/outputs | Brier, BSS, ECE, slope/intercept, reliability data, intervals reproduced |
| G7 OOD/abstention | Held-out shifts plus crash inputs | Risk-coverage reported; unsafe inputs abstain; diagnostic/active OOD distinct |
| G8 Specialist promotion | Per-hazard artifact/data/split/seed/bootstrap package | No `CERTIFIED`/production status until independent reproduction |
| G9 Revision durability | Multiple issue cycles, restart, truth sealing, exact-target lookup | Records reload with correct UTC/provider identity; no fabricated history |
| G10 Provider/cross-system | Aligned paired systems, metadata, independent truth | Live/fixture explicit; transfer metrics independently rerun |
| G11 Replay/digital twin | Immutable forecasts and independent truth | Historical mode contains no synthetic progression; metrics internally consistent |
| G12 API/schema compatibility | OpenAPI diff and consumer tests | No semantic drift; probability/uncertainty fields remain separate |
| G13 Frontend communication | Browser E2E for ready, abstain, OOD, live, cached, fixture, synthetic, unavailable | Correct scope/provenance banners; no false certification |
| G14 Test migration | Legacy-to-destination ledger and exact master-suite ID map | Critical tests pass; skipped/xfail/N/A justified; no generic substitution |
| G15 Security/operations | Required CI, secret/dependency scan, concurrency/rate/recovery tests | CI gates deployment; multi-worker limitations handled; rollback smoke passes |
| G16 Release governance | Required checks, signed/tagged release, rollback record | Failed science gate cannot deploy; prior version recoverable |
| G17 Independent review | Reviewer reruns hashes, tests, replay, build, smoke, claim register | Submission statements match evidence classes exactly |

### Table O — Merge Blockers

| Priority | Blocker | Evidence | Required resolution |
|---|---|---|---|
| P0 | A V3 binaries absent | Pointer text, wrong disk hashes, deserialization failure | Restore only for A archival verification; never copy pointers into B |
| P0 | B V3 feature checksum fails | Actual `702ff415...`; declared `265cffbb...`; verifier exit 1 | Decide authoritative file/hash; regenerate manifest; clean-clone pass |
| P0 | Specialist formulas lack empirical provenance | No specialist model/calibrator/training package | Relabel as formulas/prototypes or supply full evidence and rerun |
| P0 | Certification/coverage claims exceed evidence | JSON/docs only; no independent result | Remove/restrict claims until G6/G8 passes |
| P0 | Serving authority is ambiguous | V3 threshold `0.060`, legacy Day-4 `0.280`, multiple services | One versioned route/model/threshold/fallback manifest |
| P1 | Synthetic replay may look historical | Source declares synthetic progression; Brier text conflicts | Separate modes; visible labels; immutable historical replay |
| P1 | CI lacks scientific/backend gates | B deploy workflow builds frontend only; A has no workflow | Required tests, verifier, security, replay, build, smoke before deploy |
| P1 | Live/fixture/provider boundaries can be lost | A second provider is fixture; B has fallbacks/simulation | Provider provenance field and UI badge on every response |
| P1 | Revision stores conflict | A SQLite/WAL vs B Zarr; key/sealing semantics differ | New canonical contract and restart migration tests |
| P1 | API/probability semantics may drift | Duplicate schemas and hazard/bust/OOD fields | Contract-first migration and semantic assertions |
| P1 | No exact 500-test map | Repository tests are not 500 named-ID certification | Produce ID-level outcome ledger |
| P2 | Serialized-version warning | B calibrator created under sklearn 1.9.0, loaded under 1.9.1 | Pin or rebuild under recorded compatible environment |
| P2 | Frontend bundle warnings | A 698.05 kB; B 655.97 kB | Code-split or accept through measured performance gate |
| P2 | Governance evidence limited | Shallow histories; no verified protection/rollback | Required checks, tags, provenance, rollback record |

## 12. Scoreboard and readiness visualization

### Table P — Graph / Scoreboard Summary

#### Overall weighted score

```text
Repository A | ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░ | 47.90
Repository B | █████████████████████████████████░░░░░░░░░░░░░░░░░ | 65.48
               0        20        40        60        80       100
```

#### Top weighted contributions

```text
Category                                  Repository A               Repository B
Scientific correctness (15)               █████████████████ 8.70     █████████████████ 8.70
V3/artifact reproducibility (10)          █████             2.50     ████████████████  8.20
Docs/research alignment (8)               ██████████        4.96     ████████████      6.24
Tests/replay/release (8)                  █████             2.40     ████████████      6.08
Certification/OOD/drift (9)              ██████████        5.22     ███████████       5.58
Reliability intelligence (8)             ████████          3.84     ███████████       5.44
Hazard specialists (10)                  ██                1.20     █████████         4.50
```

#### Blockers/readiness

```text
Scale: 0 = blocked, 5 = gate-ready; bars summarize reproduced readiness, not ambition.

                                    A       B
Incumbent artifact chain            █░░░░ 1  ███░░ 3
Complete software test execution    ██░░░ 2  ████░ 4
Scientific specialist evidence      ░░░░░ 0  █░░░░ 1
Claim/replay honesty                 ████░ 4  ██░░░ 2
CI/release governance               █░░░░ 1  ██░░░ 2
Immediate submission readiness      ██░░░ 2  ███░░ 3
```

**Compact conclusion:** Repository B leads because its V3 model/calibrator load and its complete software suites execute. That lead does not validate its specialists. Both remain blocked from unchanged submission.

## 13. Symmetry check and required decisions

Identical scores, evidence caps, leakage rules, and scientific semantics were applied. B's deterministic specialists earned implementation credit but no trained-model or certification credit; the same cap would apply in A. Both failed release chains are marked contradicted, but A is penalized more because inference cannot deserialize, whereas B's model/calibrator work and only the feature-manifest chain fails. A receives higher frontend-test and operational-honesty credit even though B wins overall. B's 816 passes are not converted into 816 scientific validations. A's uncompleted backend run is not assigned an inferred pass count.

If labels were swapped but evidence stayed attached to the codebases, the codebase with loadable expected V3 binaries, 758 backend passes, 58 frontend passes, and broader modules would still win. The codebase with pointer-only V3 files, failing targeted release/replay checks, and no completed backend run would still lose. The conclusion does not depend on identity, branding, file count, README polish, prior human verification, or architectural ambition.

| Required decision | Result | Basis |
|---|---|---|
| Overall Technical Winner | **Repository B** | `65.48` vs `47.90`; loadable incumbent, completed suites, broader implementation |
| Stronger Scientific Foundation | **Repository B** | Reproduced model/calibrator identity; A incumbent cannot load; specialist award excluded |
| Broader Research/Feature Architecture | **Repository B** | Wider Phase A–L code surface and schemas |
| Better Immediate SIH Candidate | **Repository B** | Closer after bounded repairs; not ready unchanged |
| Immediate Round-2 decision | **`NO_REPOSITORY_READY_YET`** | A core unavailable; B integrity and claim gates fail |
| Long-term decision | **`KEEP_B_AS_BASE_IMPORT_FROM_A`** | B is usable destination; A contributes selected safety patterns |
| Merge decision | **`SELECTIVE_MERGE_ONLY`** | Broad merge raises regression burden without adding evidence |

## 14. Answers to Q1–Q5

**Q1 — Stronger base:** Repository B, for the loadable expected V3 artifacts, completed test execution, local runtime evidence, and broader modular architecture. This is an evidence decision, not an architecture or branding preference.

**Q2 — What to merge and not merge:** Keep B's V3 binaries, destination API/frontend, tests, and experimental module interfaces. Adapt A's model-not-ready handling, certification scope, live/fixture disclosure, UTC contract, replay invariants, and revision-store semantics. Reimplement the release manifest, route/model registry, provider registry, revision service, historical replay, and CI gates. Reject A's pointer artifacts and wholesale duplicate trees. Reject promotion of B specialist formulas, synthetic replay conclusions, and unsupported certification/transfer/coverage claims.

**Q3 — Actual roadmap:** Execute Phases 0–8 in Table M for a submission-quality selective integration, with Phase 9 reserved for post-submission empirical specialist work. Stop at any failure condition. Do not begin safety grafting until B's incumbent chain passes G1–G3.

**Q4 — Exact materials to collect:** Tables K and L provide the A–H collection plans with paths, canonical/informative status, action, and validation. The minimum A package is safety/time/certification/provider/revision/replay code plus its tests and code-tied contracts. The minimum B package is the V3/baseline artifact family, destination app, tests, specialist modules as experimental sources, manifests, scripts, locks, and architecture/reproducibility docs.

**Q5 — Final target:** A single Repository B-derived modular monolith with one authoritative V3 model registry and release manifest; strict issue-time and UTC/provider identity; safe model-unavailable behavior; durable exact-target revision history; explicitly separated live, cached, fixture, fallback, and synthetic states; experimental specialists isolated behind promotion gates; non-causal explanations; immutable real historical replay; mapped 500-test evidence; required CI, tagged rollback, and a claim register. No module may call itself certified without reproduced empirical evidence.

## References

[1]: file:///home/ubuntu/sih26079_task/MASTER%20PROMPT.txt "Authoritative master prompt — zero-bias dual-repository comparison and merge roadmap"
[2]: file:///home/ubuntu/sih26079_task/VEYRA_500_Test_Master_Suite%20%281%29.md "VEYRA 500-Test Master Suite"
[3]: file:///home/ubuntu/audit_workspace/reports/repo_a_evidence.md "Repository A — Independent Evidence Audit"
[4]: file:///home/ubuntu/audit_workspace/reports/repo_b_evidence.md "Repository B — Independent Scientific-ML and Software Audit Evidence"
[5]: file:///home/ubuntu/audit_workspace/reports/docs_evidence.md "Supplied Source Documents — Neutral Evidence Audit"
[6]: file:///home/ubuntu/sih26079_task/SIH26079%20%E2%80%94%20Forecast-Bust%20Sentinel%20%281%29%20%281%29%20%281%29.md "SIH26079 — Forecast-Bust Sentinel"
[7]: file:///home/ubuntu/sih26079_task/SIH26079_120_RESEARCH_PAPERS_MERGED%20%281%29.md "SIH26079 120 research study briefs merged"
[8]: file:///home/ubuntu/sih26079_task/VEYRA_Hazard_Specific_Reliability_Implementation_Blueprint.md "VEYRA Hazard-Specific Reliability Implementation Blueprint"
[9]: file:///home/ubuntu/sih26079_task/Docs_vs_Research_vs_Live_comparison%20%281%29.md "Docs vs Research vs Live comparison"
[10]: file:///home/ubuntu/audit_workspace/final_veyra_sih_round2_audit.md "Prior evidence-weighted SIH Round-2 audit"
[11]: file:///home/ubuntu/audit_workspace/repos/repo_a "Repository A audited checkout"
[12]: file:///home/ubuntu/audit_workspace/repos/repo_b "Repository B audited checkout"

```text
AUDITED_REPO_A_SHA: b9f52d3eeec8676e06b1879f05b404605e2501be
AUDITED_REPO_B_SHA: 82eded8194151e37fb9b3eecf273010dc62d7b29

STRONGER_BASE_REPO: Repository B
MERGE_DECISION:
- `SELECTIVE_MERGE_ONLY`

REPO_A_FINAL_WEIGHTED_SCORE: 47.90/100
REPO_B_FINAL_WEIGHTED_SCORE: 65.48/100

WHAT_TO_COLLECT_FROM_REPO_A:
- `backend/app/core/time_contract.py`, `revision_store.py`, `certification_policy.py`, `ood_policy.py`, `replay_harness.py`, and `golden_replay_matrix.py`
- `backend/app/builder2/v3_model_adapter.py`, `v3_feature_pipeline.py`, and `instability_fingerprint.py` as safety/design references, not artifact authority
- `backend/app/adapters/openmeteo_adapter.py`, `fixture_second_provider_adapter.py`, and provider-disagreement modules/tests for explicit live-versus-fixture provenance
- V3 failure-safety, certification, UTC/revision, provider-disclosure, replay/release, and frontend scope-label tests
- Current integration contracts and code-tied audit documents; reject stale claims and duplicate application trees
- Do not collect Repository A's V3 `.joblib` pointer files as deployable binaries

WHAT_TO_COLLECT_FROM_REPO_B:
- `models/v3/lightgbm_v3_challenger.joblib`, `probability_calibrator_v3.joblib`, `feature_names.json`, manifests, V3 evaluation outputs, Day-4 artifacts, and logistic baseline
- `backend/app` as the destination application, including the V3 adapter, registry/services, API, schemas, safety modules, and Open-Meteo/fallback paths
- Hazard, spatial, compound, common-mode, cross-system, drift, independent-truth, explanation, and digital-twin modules as isolated experimental sources only
- `backend/tests`, frontend tests/build configuration, `scripts/verify_artifacts.py`, smoke/evaluation scripts, dependency manifests, and `.github/workflows/deploy.yml`
- `ARCHITECTURE.md`, `REPRODUCIBILITY_PACKAGE.md`, current roadmap/report files, and claim-audit inputs after stale/overclaimed language is corrected

TOP_MERGE_PRIORITIES:
1. Repair Repository B's authoritative feature-contract hash and make the complete V3 artifact verifier exit 0 in a clean clone.
2. Freeze one route-to-model, model-ID, threshold, calibrator, feature-order, and fallback manifest while retaining V3 as incumbent.
3. Adapt Repository A's safe model-unavailable, certification-boundary, UTC/provider-identity, and live-versus-fixture patterns into Repository B.
4. Rebuild durable revision history and immutable historical replay with independent truth; keep synthetic replay in an explicitly labeled fixture mode.
5. Gate deployment on mapped backend/frontend tests, artifact integrity, leakage checks, replay parity, security, documentation truth, and rollback.

TOP_MERGE_BLOCKERS:
1. Repository A's V3 files are Git LFS pointer text, not loadable binaries; its release and replay checks fail.
2. Repository B's feature checksum disagrees with its manifests, so the complete frozen-core artifact chain is not integrity-valid.
3. Repository B's specialists use deterministic formulas/fixed coefficients without trained artifacts or reproduced empirical provenance.
4. Synthetic replay, cross-system values, coverage figures, warning-lead claims, common-mode claims, and certification language exceed the reproduced evidence.
5. Model thresholds, API schemas, OOD semantics, provider identities, revision stores, dependency pins, CI gates, and the 500-test mapping are not yet unified.

HYPOTHETICAL_MERGED_SYSTEM_OUTCOME:
- A raw merge would initially weaken reproducibility and maintainability by duplicating model services, APIs, frontends, data stores, tests, documentation, and release assumptions.
- The fundamental benefit of a selective integration is Repository B's loadable V3 and broad implementation combined with Repository A's safer failure, certification-scope, fixture-disclosure, UTC, and durable revision patterns.
- The fundamental risks are feature/target drift, future leakage, probability-semantic conflation, calibration loss, model/threshold ambiguity, dependency conflict, regression, and inflated certification.
- Major conflicts include feature/release manifests, V3 versus legacy serving thresholds, diagnostic versus active OOD, provider IDs, SQLite versus Zarr history, response schemas, and overlapping UI/API routes.
- Required revalidation includes exact hashes and 50-feature order, calibrated V3 parity, issue-time lineage, every merged route, OOD risk-coverage, specialist empirical packages, paired-provider transfer, revision durability, immutable replay, and exact test-ID coverage.
- The merge is worth it only as staged selective adaptation after Repository B's immediate P0 blockers are repaired; a monolithic pre-submission merge is not worth the risk.

FINAL_ONE_PARAGRAPH_RECOMMENDATION: Do not submit either repository unchanged and do not merge for the sake of merging. Repair Repository B's feature-manifest integrity, pin its artifact environment, freeze one authoritative serving manifest, remove or qualify unsupported certification language, visibly distinguish live, cached, fixture, fallback, and synthetic outputs, and add backend/scientific release gates; then use Repository B as the candidate with frozen V3 retained as incumbent. Treat every specialist formula, conformal or coverage number, warning-lead claim, cross-system result, common-mode claim, and digital-twin conclusion as experimental until independently reproduced. After those immediate gates pass, selectively adapt Repository A's safe-failure, certification-boundary, provider-disclosure, UTC, replay-invariant, and durable revision patterns under Tables J, M, and N; reject Repository A's pointer artifacts and both repositories' stale or inflated claims.
```
