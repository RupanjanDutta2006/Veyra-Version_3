# Final Evidence-Weighted SIH Round-2 Audit

**Audit scope:** Repository A and Repository B at their current upstream default-branch heads  
**Audit date:** 2026-09-21  
**Reviewer role:** Lead independent reviewer  
**Author:** Manus AI  
**Decision standard:** reproduced execution > current code/artifacts > machine-readable manifests > code-tied technical documents > README > roadmap

## Executive conclusion

**Repository B is the overall technical winner, has the stronger currently usable scientific foundation, has the broader research architecture, and is the better immediate candidate of the two. Neither repository is ready for unchanged SIH Round-2 submission.** Repository A's default V3 path cannot load because the two committed `.joblib` files are Git LFS pointer text, so exact disk hashes fail, replay fails, and the serving path safely returns `MODEL_NOT_READY`. Repository B loads the expected V3 model and isotonic calibrator and reproduced **758 passing backend tests plus 58 passing frontend tests**, but its V3 feature-contract checksum fails, its six specialist implementations are deterministic formulas or baselines without specialist trained artifacts, and several certification, coverage, warning-lead, cross-system, and replay claims exceed the reproduced evidence.[3] [4]

The immediate decision is therefore **`NO_REPOSITORY_READY_YET`**. The shortest defensible route is to repair and harden Repository B, not to perform a broad merge before submission. The long-term decision is **`KEEP_B_AS_BASE_IMPORT_FROM_A`**, limited to selectively adapting Repository A's useful safety and operational patterns. A monolithic merge would combine two model-selection surfaces, duplicate backends/frontends, conflicting release assumptions, and incompatible test histories; it would increase validation burden before it increased scientific confidence.

The final weighted scores are **47.90/100 for Repository A** and **65.48/100 for Repository B**. Both totals use the same 13 categories, weights, evidence caps, and penalty rules. Repository B's lead is **17.58 points**. It comes primarily from loadable V3 artifacts, completed test execution, and broader implemented architecture—not from repository naming, README polish, file count, or claims of certification.

## 1. Audit protocol, truth boundaries, and terminology

The five supplied project documents were treated as a specification corpus rather than implementation proof. Their strongest common boundaries are that Veyra is a **forecast-reliability layer**, hazard occurrence is not a forecast bust, public-proxy GEFS/WeatherBench 2 and ERA5 work is not NCMRWF/NEPS validation, and V3 remains the incumbent until a challenger passes equivalent leakage, calibration, subgroup, uncertainty, OOD, and certification gates.[1] [2]

Repository evidence was assessed at the audited SHA. Tests, hashes, builds, replay commands, and local API smoke tests outrank source and manifests. Source and committed artifacts outrank prose. A passing unit test was credited as software evidence only; it was not converted into empirical scientific validation. Metrics in JSON or Markdown were classified as artifact or documentation support unless independently regenerated.

### 1.1 Implementation status vocabulary

| Status | Meaning in this audit |
|---|---|
| `VERIFIED` | Reproduced directly at the audited SHA, within the stated scope. |
| `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | Current code exists, but scientific or operational validation was not independently reproduced. |
| `PARTIAL` | Material implementation exists, but the required capability, evidence chain, or scope is incomplete. |
| `PROTOTYPE_ONLY` | Demonstration or deterministic research implementation; not a validated production-science capability. |
| `DOCUMENTED_ONLY` | Present only in technical prose or roadmap material. |
| `MISSING` | Required implementation or evidence is absent. |
| `N/A — uncovered/missing` | The 500-test-suite rule applied where the final repository has no named target; no equivalent was invented. |
| `FUTURE_BY_DESIGN` | Explicitly deferred by the governing specification. |
| `CONTRADICTED` | Higher-ranked execution or artifact evidence conflicts with the claim. |
| `UNVERIFIED` | Evidence was unavailable or insufficient to decide. |

### 1.2 Scientific claim classes

| Claim class | Meaning in this audit |
|---|---|
| `REPRODUCED` | Directly regenerated or observed in current execution. |
| `SUPPORTED_BY_ARTIFACT` | Supported by a committed manifest or frozen output, but not regenerated. |
| `SUPPORTED_BY_CODE_ONLY` | Source implements the behavior, without independent scientific validation. |
| `SUPPORTED_BY_TEST_FIXTURE_ONLY` | Demonstrated only with mocks, fixtures, or simulation. |
| `DOCUMENTATION_ONLY` | Asserted only in prose. |
| `CONTRADICTED` | Current higher-ranked evidence disproves or materially conflicts with it. |
| `UNVERIFIED` | The audit could not establish the claim. |

## 2. Table A — Repository snapshot

The upstream default branch for both repositories was resolved with `git ls-remote --symref` during this review. Each remote still pointed to the inspected local SHA. The master prompt supplied no separate prompt-time SHA; that field is therefore recorded as **not provided**, not inferred.

| Item | Repository A | Repository B |
|---|---|---|
| Current upstream default branch | `main` | `main` |
| Prompt-time SHA | Not provided in the master prompt | Not provided in the master prompt |
| Audit-time/current upstream HEAD | `b9f52d3eeec8676e06b1879f05b404605e2501be` | `82eded8194151e37fb9b3eecf273010dc62d7b29` |
| Commit timestamp | `2026-09-21T09:44:50+05:30` | `2026-09-21T00:02:06+05:30` |
| Upstream moved after checkout? | No; remote HEAD matched audited SHA | No; remote HEAD matched audited SHA |
| Initial checkout size recorded by analyst | 15 MiB | 8.0 MiB |
| Tracked files / tracked worktree bytes | 866 / 8,832,697 bytes | 448 / 5,233,492 bytes |
| Final local checkout size | 173 MiB after dependency/test state | 168 MiB after dependency/test state |
| Working tree | Clean for tracked files | Clean for tracked files |
| Visible branch/history depth | `main`; shallow/grafted; one visible merge commit | `main`; shallow/grafted; one visible commit |
| Recent visible commit | Merge of PR #55 for human-verification fixes | README scientific-workflow documentation update |
| Branch/PR governance | A PR merge is visible; protection and full PR history are unverified | Only direct `main` deployment behavior is visible; PR/protection history unverified |
| CI/workflow | No current `.github/workflows` observed | GitHub Pages frontend build/deploy on push to `main`; no backend/scientific gate |
| Open failure visible in audit | V3 hash/load failure; targeted suite has failures/errors | Artifact verifier exits 1 on feature-contract hash |
| Backend | FastAPI under `backend/app`; broad routes/services | FastAPI under `backend/app`; versioned routes/services |
| Frontend | React/Vite under `frontend`; 9 test files | React/Vite under `frontend`; 4 test files |
| Models/artifacts | V3 pointer files; Day-4 and other historical assets | Loadable V3, Day-4, logistic baseline; hazard JSON manifests |
| Data/manifests | Historical/training trees, V3 manifests, SQLite revision DB | Extensive target, hazard, spatial, drift, evaluation, and reference manifests |
| Scripts | Training and smoke scripts; no artifact verifier gate reproduced | Verification, evaluation, replay, benchmark, and operational-gate scripts |
| Deployment | `vercel.json`; deployment not independently exercised | Pages workflow plus external API URL; deployment not independently exercised |

**Repository-size note.** The initial sizes from the analyst reports are the best clean-checkout measurements. The later `du` values include installed dependencies and generated local state. File count and size received no scoring credit by themselves.

## 3. Table B — Documents vs code vs tests vs runtime

| Evidence layer | Repository A | Repository B | Audit disposition |
|---|---|---|---|
| README and roadmap | Root README still advertises a stale 92-test suite; many historical trees and audit documents coexist | README claims 816 passing tests, six certified specialists, transfer metrics, and broad Phase A–L completion | README language was credited only where code or execution agreed |
| Current code | Strict V3 adapter, issue-time contracts, certification/OOD policy, SQLite/WAL revision store, replay harness, broad API/UI | Loadable V3 adapter, specialist modules, hazard/spatial/common-mode services, API/UI, middleware, evaluation scripts | Implementation credit only; formulas are not trained empirical models |
| Current artifacts | V3 feature and evaluation manifests; V3 `.joblib` files are LFS pointer text | V3 model/calibrator binaries load and match expected hashes; 50-feature file exists; many specialist JSON manifests | A's core artifact claim is contradicted; B's model/calibrator are reproduced but its feature-hash chain is contradicted |
| Machine-readable metrics | V3 benchmark metrics in manifests | V3 and specialist metrics, coverage, transfer, and frontier outputs in JSON | `SUPPORTED_BY_ARTIFACT`, not reproduced science |
| Backend tests | 684 collected; no full completed run; targeted failures and replay errors | 758 passed, 60 warnings, 343.24 s | Software evidence; only B has a complete reproduced backend result |
| Frontend tests | 109 passed in 9 files; React `act(...)` warnings | 58 passed in 4 files | Reproduced UI behavior, not scientific validation |
| Frontend build | Passed in 3.90 s; 698.05 kB chunk warning | Passed in 4.39 s; 655.97 kB chunk warning | Reproduced with performance-warning debt |
| Runtime/API | `/v1/health`, `/v1/metrics`, `/v1/ood/policy` returned 200; health stayed green while model was not ready | `/`, `/v1/health`, `/openapi.json` returned 200 | Local process smoke only; no public deployment certification |
| Artifact verification | Exact V3 disk hashes fail; `joblib.load` raises `KeyError: 118`; release/replay checks fail | Model and calibrator pass; feature checksum fails and verifier exits 1 | Release blocker in both, more severe in A because inference cannot load |
| Replay | Independent replay structure exists but cannot execute with pointer artifacts | Six-cycle script executes; source explicitly synthesizes progression and output has a Brier inconsistency | A: current executable claim contradicted; B: fixture/simulation only |
| Live data | Open-Meteo adapter and successful upstream fetch appeared in one test; second provider explicitly fixture-only | Open-Meteo request code exists; synthetic fallback/risk map/replay paths also exist | No national-system paired history or fully audited live prediction in either |
| Clean-clone reproducibility | Not reproduced; Git LFS payload unavailable and no CI | Dependencies had to be installed; tests then ran; version warnings and verifier failure remain | Partial for B, contradicted for A's frozen-core release |

## 4. Exact test, build, and runtime record

Test counts are reported per command because Repository A's completed commands overlap. They must not be summed into a unique executed-test total.

| Measurement | Repository A | Repository B |
|---|---|---|
| README test claim | 92 tests in root README; historical repair docs also report 684 backend + 109 frontend | 816 total: 758 backend + 58 frontend, 100% pass |
| Discovered backend test files | 51 under active `backend/tests`; 144 test-like files checkout-wide because historical/duplicate trees exist | 85 under active `backend/tests` |
| Backend collection | **684 collected in 0.23 s** | **758 outcomes in completed run**; source scan found 740 top-level functions and 22 test classes, not an outcome count |
| Completed backend run 1 | **28 passed, 1 failed, 1 warning, 6.69 s**; stopped on first failure | Not applicable |
| Completed targeted backend run | **69 passed, 4 failed, 1 skipped, 9 errors, 1 warning, 0.73 s** | Not applicable |
| Full backend run | Two bounded runs terminated at 180 s (~31%) and 120 s (~10%); exact executed outcome totals unavailable | **758 passed, 0 failed, 0 skipped, 0 xfail, 60 warnings, 343.24 s** |
| Unique backend tests executed | **Not derivable** because completed targeted runs overlap and bounded runs lack final totals | **758** in the completed full run |
| Frontend | **109 passed, 0 failed** in 9 files; no skips/xfails reported; 5.54 s Vitest duration; repeated uncounted React `act(...)` warnings | **58 passed, 0 failed** in 4 files; no skips/xfails reported; 4.30 s Vitest duration |
| Combined exact completed full-suite count | **Unavailable**; backend did not complete | **816 passed** across completed backend and frontend suites |
| Build | Passed, 1,930 modules, 3.90 s; 698.05 kB JS warning | Passed, 1,931 modules, 4.39 s; 655.97 kB JS warning |
| API smoke | Three endpoints 200; two expected observability routes returned 404 | Three endpoints 200 |
| Scientific limitation | Passing tests cannot restore missing model binaries or prove empirical metrics | 816 passing tests do not validate hand-coded specialist coefficients or reported scientific metrics |

Repository A's targeted failures included exact model/calibrator hash checks, release-manifest disk validation, provider-disagreement behavior, and nine replay errors caused by trying to deserialize LFS pointer text. Repository B's warnings included Starlette/httpx deprecation, scikit-learn 1.9.0-to-1.9.1 deserialization warnings, NumPy empty/all-NaN-slice warnings in compatibility paths, and a deprecated HTTP status constant.[3] [4]

## 5. Table C — Major capability comparison

| Capability | Repository A | Repository B | Evidence-weighted comparison |
|---|---|---|---|
| Reliability-layer mission | `VERIFIED` as product contract | `VERIFIED` as product contract | Tie; neither is credited as a weather forecaster |
| Public-proxy boundary | Explicit GEFS/Open-Meteo and fixture disclosure | Open-Meteo code plus national-provider names in docs/manifests | A is more conservative in disclosure; neither proves NCMRWF/NEPS validation |
| Frozen V3 core | `CONTRADICTED` at runtime: pointer files cannot load | `PARTIAL`: expected model/calibrator load; feature checksum fails | B clearly preferable |
| 50-feature contract | `SUPPORTED_BY_ARTIFACT`/code; binary parity unavailable | Count reproduced; checksum chain contradicted | B preferable after checksum repair |
| Isotonic calibration | Manifest claim only; calibrator cannot load | Type and hash reproduced, with version warning | B preferable |
| Issue-time/leakage controls | Code/tests and UTC contracts; full lineage not regenerated | Contracts, split manifests, leakage tests; full lineage not regenerated | Similar `PARTIAL` evidence |
| Baseline ladder | Legacy and V3 assets; limited reproducible comparison | Logistic, Day-4, V3 assets and scripts; metrics not rerun | B broader; empirical ladder still partial |
| Revision intelligence | SQLite/WAL store and exact-target semantics; live single-cycle revisions zeroed | Revision features and Zarr storage; restart/durable cycle proof absent | A pattern preferable for durability; both partial |
| Failure Memory | Code-level modules, no persisted live demonstration | Services/terminology/tests, provenance incomplete | Neither scientifically established |
| Failure Motifs | Deterministic fingerprint labels | Motif catalogue/services/tests | B broader; both unvalidated |
| Multi-horizon/recovery | Timeline and horizon contracts; no reproduced recovery science | Horizon/recovery engines and API fields | B broader; scientific status partial |
| Precipitation specialist | `N/A — uncovered/missing` | Deterministic specialist with manifests/tests | B implementation preferable; not certified science |
| Cyclone specialist | `N/A — uncovered/missing` | Deterministic track/intensity reliability logic | B implementation preferable; not certified science |
| Monsoon/LPS specialist | `N/A — uncovered/missing` | Hand-coded target/regime logic | B implementation preferable; not certified science |
| Western disturbance specialist | `N/A — uncovered/missing` | Fixed decomposed probabilities/OOD thresholds | B implementation preferable; not certified science |
| Heatwave specialist | `N/A — uncovered/missing` | Explicit fixed logistic equations | B implementation preferable as a prototype only |
| Severe-wind specialist | Wind variable is not a specialist | Partial compound/heatwave-linked path; no independent trained artifact | B is broader but still `PARTIAL` |
| Spatial reliability | Endpoints/UI/tests; no scientific benchmark rerun | 25-station graph, fixed weights, tests/manifests | B broader; empirical certification unverified |
| Compound/common-mode | `N/A — uncovered/missing` | Code/manifests with fixed logic | B prototype only |
| Multi-provider/cross-system | Live primary plus explicit fixture second provider | Cross-system engine/manifests; true paired transfer not reproduced | Neither proves transfer; A's fixture disclosure is safer |
| OOD/abstention | OOD is diagnostic-only; model-load failure safely abstains | Hazard paths actively abstain under fixed thresholds | B broader; both lack representative OOD validation |
| Drift/independent truth | Mostly future/documented | Monitors and ledgers exist; independent evaluation not rerun | B implementation lead |
| Explainability/evidence graph | Reason codes/fingerprints | Explainability, evidence graph, provenance paths | B broader; causality not established |
| Digital twin/replay | Harness structure but current execution blocked | Executable synthetic six-cycle replay | B demo lead; neither supplies independent historical science |
| Backend/API | Broad FastAPI surface; readiness observability gaps | Broad versioned API; completed suite and smoke | B preferable |
| Frontend/demo | 109 tests and passing build | 58 tests and passing build; broader Phase A–L surfaces | Close: A stronger reproduced UI test depth; B broader integrated demo |
| Release engineering | No CI; invalid current release manifest | Partial CI; verifier failure; no backend gate/tags | B preferable but not release-ready |
| Security/operations | Middleware/configuration code, no external test | Middleware, auth/RBAC paths, security tests, no external assessment | B has stronger test evidence |

## 6. Table D — Main-doc and research requirement coverage

The source codes below refer to the supplied corpus: **S1** main Forecast-Bust Sentinel specification; **S2** 120 study briefs; **S3** 500-Test Master Suite; **S4** hazard blueprint; **S5** prior Docs-vs-Research-vs-Live comparison; **MP** master audit prompt. Duplicate copies were not double-counted. In Repository A, active root/backend/frontend paths outranked historical `Builder-2`, `Parinidhi`, `Frontend-Original`, `Overview`, and archived audits. In Repository B, `.round2-roadmap/updatedone` was treated as the current roadmap family; duplicate blueprint filenames and `oldone` phases remained planning history.

| Requirement/capability | Source | Repository A evidence / status | Repository B evidence / status | Importance | Preferable | Merge recommendation |
|---|---|---|---|---|---|---|
| Mission, scope, SIH alignment | S1 §3; S4 §1 | Reliability-layer API/UI; `VERIFIED` as scope | Same; `VERIFIED` as scope | Critical | Tie | Preserve wording |
| Bust definition and labels | S1 §8; S4 contracts | V3 manifests/label code; `PARTIAL` | Multi-target manifest; `PARTIAL` | Critical | B breadth; neither fully rerun | Freeze versioned target definitions |
| Public-proxy vs national systems | S1; S2 | Open-Meteo/GEFS and fixture disclosed; `PARTIAL` | Provider names exceed observed paired data; `PARTIAL` | Critical | A honesty | Adopt explicit provider/data gate |
| Data sources and engineering | S1 data sections; S3 DATA | Historical/QC/live adapter code; `PARTIAL` | Data/reference/hazard manifests and live-service code; `PARTIAL` | Critical | B | Keep B, import A disclosure rules |
| Issue-time safety and leakage | S1 §9; S4 §2 | Time contract and anti-leakage tests; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | Forbidden-feature/split/leakage tests; `PARTIAL` | Critical | Tie | Revalidate lineage from raw data |
| Feature engineering/order | S1 §9; MP §12 | 50 names and strict adapter; binary unavailable; `PARTIAL` | 50 names/loadable model; feature hash conflict; `PARTIAL` | Critical | B | Repair hash, retain strict order gate |
| Models and baseline ladder | S1 §10; S4 §5 | Legacy/V3 assets; current incumbent unavailable; `PARTIAL` | Logistic/Day-4/V3 plus scripts; `PARTIAL` | High | B | Keep frozen B V3; isolate challengers |
| V3 incumbent/artifact identity | S4 §2.1; MP §12 | Pointer files; `CONTRADICTED` | Model/calibrator reproduced; chain checksum fails; `PARTIAL` | Critical | B | Reject A pointer payloads |
| Evaluation science | S1 evaluation; S4 §5 | Frozen metrics only; `SUPPORTED_BY_ARTIFACT` | V3/specialist metrics only; `SUPPORTED_BY_ARTIFACT` | Critical | Neither | Reproduce raw evaluation |
| Calibration and uncertainty separation | S1 §11; MP §3.6 | Semantics separated; calibrator unavailable; `PARTIAL` | Isotonic loads; specialists unvalidated; `PARTIAL` | Critical | B | Keep separate fields and calibrators |
| Revision/historical intelligence | S4 §6; S3 REV | SQLite/WAL; live features zeroed; `PARTIAL` | Revision features/Zarr; durability unclear; `PARTIAL` | High | A pattern | Adapt storage contract into B |
| Failure Memory | S4 §6.1; S3 FMEM | Code-level only; `PARTIAL` | Services/tests, provenance incomplete; `PARTIAL` | High | Neither | Reimplement against durable history |
| Failure Motifs | S4 §6.2; S3 FMOT | Heuristic fingerprints; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | Catalogue/services/tests; same status | Medium | B breadth | Import only with episode-safe validation |
| Multi-horizon/time-to-bust/recovery | S4 §6.4; S3 HAZ | Timeline/horizon code; `PARTIAL` | Engines/API fields; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | High | B | Retain as experimental |
| Precipitation specialist | S4 §7; Phase D | No named specialist; `N/A — uncovered/missing` | Formula/baseline module; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | P0/Critical | B | Keep isolated; require real-data gate |
| Cyclone specialist | S4 §8; Phase E | `N/A — uncovered/missing` | Deterministic module; `PROTOTYPE_ONLY` scientifically | High | B | Keep experimental |
| Monsoon/LPS specialist | S4 §9; Phase F | Docs/utilities only; `N/A — uncovered/missing` | Deterministic module; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | High | B | Keep experimental |
| Western disturbance specialist | S4 §10; Phase G | `N/A — uncovered/missing` | Deterministic module; `PROTOTYPE_ONLY` scientifically | High | B | Keep experimental |
| Heatwave specialist | S4 §11; Phase H | `N/A — uncovered/missing` | Fixed logistic equations; `SUPPORTED_BY_CODE_ONLY` | High | B | Keep as named formula baseline |
| Severe wind | S4 §12; Phase H | Generic wind variable only; `N/A — uncovered/missing` | Partial compound path; `PARTIAL` | Data-dependent | B narrowly | Do not claim independent specialist |
| Spatial reliability | S4 §§14–19; S3 SPAT | API/UI/tests; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | Graph engine/tests; same status | High | B | Revalidate with real spatial truth |
| Compound/common-mode failure | S4; Phase I | `N/A — uncovered/missing` | Fixed/coplanar logic; `PROTOTYPE_ONLY` | High | B | Keep experimental |
| Multi-provider/cross-system | S1 E8; S3 MULTI; Phase K | Second provider fixture only; `PARTIAL` | Engine/manifests; true transfer `DOCUMENTED_ONLY` | High | Neither scientifically | Build aligned paired-system evaluation |
| Drift/independent truth | S4; Phase J | OOD policy; independent truth future; `PARTIAL` | Drift ledger/monitor; independent metrics not rerun; `PARTIAL` | Critical | B implementation | Revalidate held-out shifts |
| Explainability/evidence graph | S1; Phase L | Fingerprints/reason codes; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | Explainability/evidence graph; same status | Medium | B breadth | Preserve non-causal wording |
| Digital twin/replay/counterfactuals | S4; Phase L | Harness blocked by artifacts; `CONTRADICTED` current execution | Synthetic script; `PROTOTYPE_ONLY` | Medium | B demo | Label simulation; rebuild real replay |
| API/backend | S3 API/OPS | Smoke partial, broad code; `PARTIAL` | Smoke and 758-test suite; `VERIFIED` for local behavior | High | B | B as destination |
| Frontend/SIH demo | S3 UI | 109 tests/build; `VERIFIED` locally | 58 tests/build; `VERIFIED` locally | High | Close | Port only proven UX/tests |
| Reproducibility/release | S3 GOV/ML/OPS; MP §8 | LFS payload absent; no CI; `CONTRADICTED` release | Verifier fails one checksum; CI partial; `PARTIAL` | Critical | B | Repair before integration |
| Security/robustness/operations | S3 OPS | Code only plus selected tests; `PARTIAL` | Security tests/middleware; `PARTIAL` operationally | High | B | Add required CI/load/security gates |
| Test-suite coverage | S3 all domains | 684 collect, incomplete execution; `PARTIAL` | 816 completed tests; domain equivalence not proven; `PARTIAL` vs 500-spec | High | B | Map each named domain explicitly |
| Live/runtime checks | MP §8 | Process health while model unavailable; `CONTRADICTED` readiness | Local startup smoke; external deployment unverified; `PARTIAL` | Critical | B | Add model-ready/live provenance checks |
| Documentation drift audit | S1 §30; S5 | Stale 92-test README and historical duplication; `CONTRADICTED` in places | Certified wording and replay drift; `CONTRADICTED` in places | High | Neither | Establish claim register |
| Scientific claim audit | MP §7 | Conservative safety, but frozen-core claim currently fails | Broader claims exceed empirical evidence | Critical | A in honesty; B in usable core | Apply one claim taxonomy |
| Scoring/decision logic | MP §§9,19 | Independently scored with evidence caps | Same | High | Not applicable | Keep external to code claims |
| Combine/integration safety | MP §§14–16 | Useful safety/storage patterns, incompatible artifacts | Better base, conflicting thresholds and labels | Critical | B as base | Selective adaptation only |

### 6.1 Phase A–L coverage

| Phase | Repository A | Repository B | Evidence-weighted finding |
|---|---|---|---|
| A — V3 certification and hazard data contracts | `CONTRADICTED` by unavailable binaries | `PARTIAL`; V3 model/calibrator pass, feature hash fails | B closer; neither completes the gate |
| B — Reliability core and benchmark ladder | `PARTIAL` | `PARTIAL` | B broader; benchmarks not rerun |
| C — Multi-horizon, motifs, recovery | `PARTIAL` | `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | B lead |
| D — Precipitation specialist | `N/A — uncovered/missing` | `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | B code, no empirical specialist artifact |
| E — Cyclone specialist | `N/A — uncovered/missing` | `PROTOTYPE_ONLY` | B code, not certified science |
| F — Monsoon/LPS specialist | `N/A — uncovered/missing` | `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | B code, metrics unreplicated |
| G — Western disturbance specialist | `N/A — uncovered/missing` | `PROTOTYPE_ONLY` | B code, metrics unreplicated |
| H — Heatwave/severe wind | `N/A — uncovered/missing` | Heatwave code; wind `PARTIAL` | B lead, no independent wind artifact |
| I — Spatial/compound/common-mode | Spatial `PARTIAL`; compound missing | `PROTOTYPE_ONLY` to implemented/code-only | B lead, science unvalidated |
| J — Calibration/OOD/drift/independent truth | OOD diagnostic; truth future | Active fixed OOD/drift code; truth unreplicated | B implementation lead |
| K — Transfer/operations/promotion | Fixture second provider; no promotion gate | Transfer artifacts and partial CI; no reproduced transfer | B breadth; neither passes promotion |
| L — Frontier challengers/digital twin | Replay blocked | Executable simulation only | B demo lead; neither supplies real digital-twin evidence |

## 7. Table E — Hazard specialist evidence

| Specialist | Repository A evidence / status | Repository B implementation | Repository B scientific provenance | Preferred current source |
|---|---|---|---|---|
| Precipitation | No named hazard-conditional trained specialist; `N/A — uncovered/missing` | Deterministic baseline ladder and score/probability logic | Metrics and coverage in manifests; no specialist joblib, feature-order file, training data, or rerun | B, as prototype only |
| Tropical cyclone | No active specialist; `N/A — uncovered/missing` | Deterministic track/intensity reliability logic with constants | Held-out/certification assertions not reproduced | B, as prototype only |
| Monsoon/LPS | Terms in docs/utilities, no active trained specialist; `N/A — uncovered/missing` | Hand-coded target/regime logic and thresholds | Metrics are artifact claims; no trained artifact | B, experimental |
| Western disturbance | No active specialist; `N/A — uncovered/missing` | Decomposed fixed probabilities, OOD rules, thresholds | Reported 200-cycle/bootstrap evidence not rerun | B, prototype only |
| Heatwave | No active specialist; `N/A — uncovered/missing` | Explicit fixed logistic equations, including fixed coefficients | Empirical coefficient provenance absent | B, formula baseline only |
| Severe/high wind | Generic V3 wind variable is not a specialist; `N/A — uncovered/missing` | Incorporated in heatwave/compound paths; no independent model artifact | No independently trained or calibrated wind specialist | Neither for certification |
| Spatial reliability | Endpoints/UI/tests, no empirical benchmark; `IMPLEMENTED_NOT_INDEPENDENTLY_VALIDATED` | 25-station graph, inverse-distance weights, fixed robustness/OOD values | Empirical covariance and held-out bounds not reproduced | B for architecture only |

No evidence supports the statement that either repository currently contains **six independently certified empirical meteorological hazard specialists**. Repository B contains six broad specialist software paths, but the observed implementations are deterministic formulas or baselines. That distinction is central: **software completeness and scientific validation are scored separately**.

## 8. Table F — 500-Test domain coverage

The supplied master suite defines **20 domains × 25 tests = 500 named specifications**. Neither repository contains a one-to-one certification record mapping all 500 IDs to executed results. The table below maps observed evidence by domain; it does not translate generic tests into named master-suite coverage.[2]

| Domain | Repository A | Repository B | Coverage conclusion |
|---|---|---|---|
| API | Broad routes and endpoint tests; full suite incomplete | Dedicated API/contract tests passed in full run | A `PARTIAL`; B `PARTIAL` against the named 25 |
| DATA | Historical pathway/QC and one named data test family | Data contracts, services, two named data test families | Both `PARTIAL`; raw lineage not fully reproduced |
| ENS | Ensemble-derived features and a named test family | Ensemble service/tests | Both `PARTIAL` |
| LOC | Location/certification tests and repaired coordinates | Location tests/catalogues | Both `PARTIAL` |
| V3 | Seven named V3 test files; current artifact tests fail | Seven named V3 files pass, but external verifier fails feature hash | A `CONTRADICTED`; B `PARTIAL` |
| CAL | Calibration manifest/test; calibrator unavailable | Four calibration-related test files; isotonic loads | A `PARTIAL`; B `PARTIAL` scientifically |
| REL | Reliability schemas and a named test family | Three reliability test families | Both `PARTIAL`; B broader |
| HAZ | Horizon test/timeline code; specialists absent | Horizon/recovery/hazard routing tests | A `PARTIAL`; B `PARTIAL` |
| REV | Two revision test families and SQLite store | Revision features/storage, no clearly dedicated filename mapping | Both `PARTIAL`; named mapping uncertain |
| FMEM | No dedicated named test mapping; code-level evidence | No dedicated filename mapping; services/fixtures | `N/A — uncovered/missing` for exact mapping in both |
| FMOT | Heuristic fingerprints; no dedicated filename mapping | Motif test/catalogue | A `N/A — uncovered/missing`; B `PARTIAL` |
| SPAT | One spatial test family | Three spatial test families | A `PARTIAL`; B `PARTIAL` |
| VERT | No dedicated vertical test found | No dedicated vertical test found | `N/A — uncovered/missing` in both for exact domain mapping |
| PREC | No dedicated specialist tests | Two precipitation test families | A `N/A — uncovered/missing`; B `PARTIAL` |
| HAZSP | No cyclone/monsoon/WD/heatwave specialist tests | Multiple cyclone, monsoon, western-disturbance, heatwave and routing tests | A `N/A — uncovered/missing`; B `PARTIAL`; formulas are not empirical validation |
| GOV | OOD/release/replay tests; release checks fail | OOD/calibration/drift/independent-truth and hardening tests; artifact gate fails | A `CONTRADICTED` for release; B `PARTIAL` |
| MULTI | Fixture-based provider-disagreement tests | Multi-system tests and transfer artifacts | Both `PARTIAL`; no paired live-system science |
| ML | Feature pipeline, historical anti-leakage code; complete suite unavailable | Leakage tests, split/training manifests, baseline assets | Both `PARTIAL`; training matrix not regenerated |
| UI | 109 tests pass; build passes | 58 tests pass; build passes | Reproduced local UI subsets; neither is a 25-ID certification record |
| OPS | Middleware and deployment config; no CI, artifact/replay failure | Security/production tests and partial Pages CI; no backend gate | A `PARTIAL`; B `PARTIAL` |

**500-test conclusion:** Repository A executed no complete active backend suite and has no 500-ID map. Repository B executed 816 repository tests, but **test quantity is not identity**: the audit cannot claim that the 500 specified tests were each implemented, mapped, and passed. Missing exact mappings remain `N/A — uncovered/missing` rather than inferred coverage.

## 9. Table G — Scientific claims: claimed vs proven

| Major claim | Repository A classification and result | Repository B classification and result |
|---|---|---|
| Frozen V3 model hash/identity | `CONTRADICTED`: on-disk pointer hash differs; load fails | `REPRODUCED`: expected model hash and Booster load |
| Frozen calibrator hash/type | `CONTRADICTED` for disk identity; manifest says isotonic | `REPRODUCED`: expected hash and `IsotonicRegression` load; version warning |
| 50-feature contract | `SUPPORTED_BY_ARTIFACT`/code; binary parity unavailable | Count `REPRODUCED`; complete chain `CONTRADICTED` by feature checksum |
| V3 Brier/ROC/ECE values | `SUPPORTED_BY_ARTIFACT`; not regenerated | `SUPPORTED_BY_ARTIFACT`; not regenerated |
| 25-station, 3-variable, ≤240 h scope | `SUPPORTED_BY_CODE_ONLY` and artifact; current model unavailable | `SUPPORTED_BY_ARTIFACT`/code; evaluation not rerun |
| >240 h operation | `SUPPORTED_BY_CODE_ONLY`; correctly labeled uncertified | `SUPPORTED_BY_CODE_ONLY`; endpoint/model authority needs freezing |
| Six certified hazard specialists | `UNVERIFIED`/missing | Software `SUPPORTED_BY_CODE_ONLY`; certification `DOCUMENTATION_ONLY` |
| Specialist Brier/ECE/PR-AUC | `UNVERIFIED` | `SUPPORTED_BY_ARTIFACT`; no raw rerun or trained artifacts |
| Conditional/conformal ≥90% coverage | `UNVERIFIED` | `SUPPORTED_BY_ARTIFACT`; not independently reproduced |
| +24 h to +96 h advance warning | `UNVERIFIED` | `SUPPORTED_BY_TEST_FIXTURE_ONLY`; replay progression is synthetic |
| NCMRWF/NEPS/IMD/DWR/INSAT ingestion | `UNVERIFIED`; names are insufficient | `DOCUMENTATION_ONLY`/code references; paired operational use not evidenced |
| Open-Meteo/GEFS live path | `SUPPORTED_BY_CODE_ONLY`; one upstream fetch appeared during a test | `SUPPORTED_BY_CODE_ONLY`; audit did not use an external live prediction as evidence |
| GEFS N=31 equivalence | `DOCUMENTATION_ONLY` limitation: explicitly uncertified | `UNVERIFIED`; no equivalence reproduction |
| Cross-system transferability | Fixture-only second-provider behavior; no transfer proof | `SUPPORTED_BY_ARTIFACT`; declared transfer matrix not rerun |
| Common-mode/compound certification | `UNVERIFIED`/missing | `SUPPORTED_BY_CODE_ONLY` for logic; empirical certification unverified |
| OOD safety | Diagnostic-only policy plus fixture tests; does not automatically abstain | Software crash safety `REPRODUCED`; threshold calibration unvalidated |
| Revision-store durability | SQLite/WAL code `SUPPORTED_BY_CODE_ONLY`; restart recovery not rerun | Zarr/code `SUPPORTED_BY_CODE_ONLY`; complete successive-cycle restart proof absent |
| Replay independence | `CONTRADICTED` as current execution due pointer artifacts | `SUPPORTED_BY_TEST_FIXTURE_ONLY`; source explicitly synthesizes cycles |
| Digital-twin scientific conclusions | `UNVERIFIED` | `SUPPORTED_BY_TEST_FIXTURE_ONLY`; displayed/rationale Brier inconsistency |
| Release-manifest integrity | `CONTRADICTED`: disk validation fails and base commit unresolved in shallow checkout | `CONTRADICTED`: feature checksum causes verifier exit 1 |
| Scientific explanations | `SUPPORTED_BY_CODE_ONLY`; deterministic fingerprints, not causality | `SUPPORTED_BY_CODE_ONLY`; evidence graph/reason codes, not causality |
| Human-verification certification/coordinate fixes | `SUPPORTED_BY_CODE_ONLY` plus passing frontend tests | No equivalent inherited claim credited | 
| README test count | `CONTRADICTED`/stale: 92 in README; 684 now collects, full run incomplete | `REPRODUCED` for 758+58 software results |

## 10. Table H — 13-category raw and weighted scorecard

Weighted contribution equals `raw score × category weight ÷ 100`. Scientific categories were capped where only code, fixtures, or documents exist. A score of 90 or above was never awarded on documentation alone.

| Category | Weight | A raw | A weighted | A confidence | B raw | B weighted | B confidence | Short evidence reason |
|---|---:|---:|---:|---|---:|---:|---|---|
| 1. Scientific correctness, claim discipline & leakage safety | 15 | 58 | 8.70 | Medium | 58 | 8.70 | Medium | A is conservative but unavailable; B has contracts/tests but overclaims specialist validation |
| 2. SIH26079 docs/research alignment | 8 | 62 | 4.96 | Medium | 78 | 6.24 | Medium | B covers more required phases; breadth is not certification |
| 3. Core V3/baseline, calibration & artifact reproducibility | 10 | 25 | 2.50 | High | 82 | 8.20 | High/Medium | A cannot load binaries; B loads model/calibrator but feature hash fails |
| 4. Data pipeline, issue-time contracts, provenance & QC | 7 | 62 | 4.34 | Medium | 62 | 4.34 | Medium | Both implement controls; neither proves national paired data or full raw lineage |
| 5. Revisions, Failure Memory, Motifs, multi-horizon/recovery | 8 | 48 | 3.84 | Medium | 68 | 5.44 | Medium/Low | A has durable-store design; B has broader modules; neither fully validates live history |
| 6. Hazard specialists and empirical validation | 10 | 12 | 1.20 | High | 45 | 4.50 | High | A lacks named specialists; B has deterministic specialists without trained artifacts |
| 7. Certification, OOD, abstention, drift & independent truth | 9 | 58 | 5.22 | Medium | 62 | 5.58 | Medium | A safely abstains but OOD is diagnostic; B has active paths without representative validation |
| 8. Spatial, ensemble, provider & cross-system intelligence | 6 | 55 | 3.30 | Medium | 55 | 3.30 | Medium/Low | A is fixture-honest; B is broader; neither proves transfer |
| 9. Backend/API architecture & robustness | 6 | 65 | 3.90 | Medium | 78 | 4.68 | High/Medium | B completed its suite and smoke; production operations remain untested |
| 10. Frontend/demo & scientific communication | 5 | 78 | 3.90 | High | 74 | 3.70 | High | Both build; A has 109 reproduced tests, B 58 and broader features |
| 11. Testing, reproducibility, replay & release engineering | 8 | 30 | 2.40 | High | 76 | 6.08 | High/Medium | A's backend/replay fail; B's full suites pass but verifier/CI are incomplete |
| 12. Documentation accuracy, traceability & maintainability | 4 | 56 | 2.24 | Medium | 60 | 2.40 | Medium | A has stale counts/duplicate history; B has certification and replay drift |
| 13. SIH Round-2 submission readiness | 4 | 35 | 1.40 | High | 58 | 2.32 | Medium | A default inference is unavailable; B needs integrity and claim cleanup |
| **Exact total** | **100** | — | **47.90** | **Medium overall** | — | **65.48** | **Medium overall** | **Repository B leads by 17.58 points** |

## 11. Table I — Weighted total and ten diagnostic scorecards

### 11.1 Weighted totals

| Repository | Weighted score | Interpretation |
|---|---:|---|
| Repository A | **47.90/100** | Partial / mostly prototype; safety scaffolding exists, but the incumbent artifact path is release-blocked |
| Repository B | **65.48/100** | Functional but incomplete or weakly evidenced; demonstrable software with unresolved scientific and release claims |

### 11.2 Diagnostic scores

These 0–100 diagnostics expose trade-offs and do not replace the weighted result.

| Diagnostic | Repository A | Repository B | Evidence-weighted interpretation |
|---|---:|---:|---|
| Scientific maturity | 39 | 57 | B has a loadable incumbent; neither reproduces specialist science |
| Software engineering maturity | 68 | 78 | B has a completed backend suite and broader modular surface |
| Research breadth | 58 | 88 | B implements substantially more of Phases A–L |
| Reproducibility | 25 | 67 | A lacks usable V3 payloads; B has one failed checksum and environment warnings |
| Operational honesty | 72 | 55 | A discloses fixtures and safely abstains; B's `CERTIFIED` wording outruns evidence |
| Demo/presentation readiness | 75 | 76 | Both build; A's model unavailable, B's broader demo needs clearer simulation labels |
| Documentation quality | 70 | 68 | A has detailed audit notes but stale root text; B is extensive but claim-drifted |
| Long-term extensibility | 74 | 84 | B's modules and schemas provide the broader base |
| Immediate SIH submission readiness | 35 | 58 | B is closer, but neither is ready unchanged |
| Mergeability/integration compatibility | 58 | 62 | Both are modular, but model paths, schemas, thresholds, and evidence labels conflict |

## 12. Table M — Graph/scoreboard summary

### 12.1 Overall weighted score comparison

**Axis: 0 to 100; each block is approximately 2 points. Exact labels control.**

```text
Repository A | ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░ | 47.90
Repository B | █████████████████████████████████░░░░░░░░░░░░░░░░░ | 65.48
               0        20        40        60        80       100
```

### 12.2 Weighted category contributions

**Each full block is approximately 0.5 weighted point; exact contributions are printed.**

```text
Category                                      Repository A                 Repository B
1 Scientific correctness (15)                 █████████████████  8.70      █████████████████  8.70
2 Docs/research alignment (8)                 ██████████         4.96      ████████████        6.24
3 V3/artifact reproducibility (10)            █████              2.50      ████████████████    8.20
4 Data/issue-time/provenance (7)              █████████          4.34      █████████           4.34
5 Reliability intelligence (8)               ████████           3.84      ███████████         5.44
6 Hazard specialists (10)                    ██                 1.20      █████████           4.50
7 Certification/OOD/drift (9)                ██████████         5.22      ███████████         5.58
8 Spatial/provider/cross-system (6)          ███████            3.30      ███████             3.30
9 Backend/API (6)                            ████████           3.90      █████████           4.68
10 Frontend/demo (5)                         ████████           3.90      ███████             3.70
11 Tests/replay/release (8)                  █████              2.40      ████████████        6.08
12 Documentation (4)                         ████               2.24      █████               2.40
13 Submission readiness (4)                  ███                1.40      █████               2.32
```

**Compact conclusion:** Repository B wins the weighted comparison because its V3 model and calibrator are present and loadable and its full software suites complete. Its advantage does not validate the reported specialist science.

## 13. Table K — Submission blockers

| Priority | Repository | Blocker | Evidence | Required disposition |
|---|---|---|---|---|
| P0 | A | V3 model/calibrator payloads absent | LFS pointer text, wrong disk hashes, `joblib.load` failure | Restore exact binaries and verify in a clean clone |
| P0 | A | Default prediction path unavailable | Startup logs hash mismatch; API returns safe `MODEL_NOT_READY` | Do not submit unchanged |
| P0 | A | Backend/replay/release evidence does not pass | Completed targeted run has 4 failures and 9 errors | Complete full suite and golden replay after artifact restoration |
| P0 | B | V3 feature-contract checksum mismatch | Actual `702ff415...02031e`; declared `265cffbb...5335`; verifier exits 1 | Reconcile authoritative file/hash and make verifier exit 0 |
| P0 | B | Specialist certification language exceeds evidence | Deterministic formulas; no specialist trained artifacts or reproducible training provenance | Rename as formula baselines/prototypes or supply full empirical packages |
| P0 | B | Specialist metrics/coverage not reproduced | JSON/phase reports only | Supply raw evaluation inputs, seeds, code, hashes, bootstrap outputs, rerun logs |
| P1 | Both | Public-proxy evidence can be confused with national-system validation | No real paired NCMRWF/NEPS archive, metadata, permission, and truth shown | Use exact public-proxy wording and visible provider identity |
| P1 | B | Synthetic replay can be mistaken for historical replay | Source says synthetic progression; output Brier values conflict | Label simulation in API/UI and rebuild immutable historical replay |
| P1 | B | CI omits backend and artifact gates | Pages workflow builds/deploys frontend only | Add required backend, artifact, replay, security, no-network smoke gates |
| P1 | B | Multiple serving thresholds/model paths | V3 0.060 and legacy Day-4 0.280 appear in separate services | Freeze one route-to-model/threshold/fallback manifest |
| P1 | A | Health status can mask model unavailability | `/v1/health` 200 while V3 is not ready | Add model/readiness and release-integrity health |
| P1 | Both | No one-to-one 500-test certification map | Repository tests are not mapped to all master IDs | Publish passed/failed/blocked/N/A record by exact test ID |
| P2 | Both | Frontend bundle warning | 698.05 kB A; 655.97 kB B | Code-split or formally accept with performance test |
| P2 | B | Scikit-learn serialization version warning | 1.9.0 artifact loaded under 1.9.1 | Pin or rebuild with exact recorded environment |

## 14. Immediate suitability as-is

### 14.1 Required immediate path

**`NO_REPOSITORY_READY_YET`**

Repository A is not suitable unchanged because its incumbent model path is unavailable in the audited checkout. The safe abstention is correct behavior, but a submission whose central scientific model cannot load is not demonstrable as a working V3 release.

Repository B is the better candidate, but it is not suitable unchanged because its own artifact verifier fails, specialist certification wording is unsupported by trained specialist provenance, and its digital-twin and cross-system material is not reproduced science. Submitting B unchanged creates a material judge-facing risk: a reviewer can run the verifier, inspect fixed specialist equations, and demonstrate that claimed certification is stronger than the evidence.

Choosing Repository A merely because its language is more conservative would ignore the reproduced model failure. Choosing Repository B unchanged merely because it is broader and has more passing tests would confuse software breadth with scientific validity. A pre-submission repair sprint on Repository B is lower risk than either unchanged submission or a cross-repository merge.

## 15. Table J — Selective Integration Matrix

The matrix describes a long-term selective plan. It is **not** a recommendation to merge before the immediate submission gates are repaired.

| Capability | Best source | Source files/modules | Scientific status | Destination | Dependency conflict | API/schema conflict | Data/model conflict | Test migration | Revalidation | Risk | Priority | Action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Frozen V3 binaries | B | `models/v3/lightgbm_v3_challenger.joblib`; `probability_calibrator_v3.joblib` | Model/calibrator identity `REPRODUCED` | B incumbent registry | sklearn version pin | Feature contract/hash must be canonical | Feature hash mismatch | Keep B integrity tests | Full clean-clone parity | Medium | P0 | Keep |
| V3 feature/release manifest | Neither unchanged | Both repositories' `models/v3/*manifest*.json`; A release manifest | Both chains currently fail | New single B release manifest | Version and path differences | Model IDs/thresholds differ | A pointers vs B binaries | Consolidate tests | Exact hash/load/replay | High | P0 | Reimplement |
| Serving model selection | B | B V3 adapter and legacy service | Implemented; authority ambiguous | Versioned endpoint-to-model registry | Threshold/library versions | Route response fields must be frozen | Conflicting thresholds/fallbacks | Migrate routing/failure tests | Endpoint-by-endpoint replay | High | P0 | Reimplement |
| Issue-time/time identity | Neither | A `time_contract.py`; B target/training manifests | Code-level controls | B shared data contract | Datetime/version behavior | Timestamp/provider fields differ | Availability lineage unproven | Combine anti-leakage tests | Raw-feature lineage audit | Medium | P0 | Adapt |
| Safe failure on missing model | A | A V3 adapter and safety layer | Runtime failure behavior `REPRODUCED` | B model registry | Exception types | Trust-state fields differ | None | Port failure-path tests | Startup and route smoke | Low | P0 | Adapt |
| Certification boundary | A | A `certification_policy.py` and UI repair tests | Scope encoded; science artifact-limited | B policy/UI | None material | B broad `CERTIFIED` labels conflict | Specialist scope conflicts | Port scope-label tests | Reviewer-approved claim register | Medium | P0 | Adapt |
| Hazard specialist modules | B | `backend/app/builder2/*specialist.py` | Deterministic prototypes, not certified models | B experimental namespace | Scientific-stack overlap low | Probability/abstention schemas vary | No trained specialist artifacts | Keep B unit tests | Full per-hazard empirical package | High | P1 | Adapt |
| Severe-wind specialist claim | Neither | B heatwave/compound paths | Independent specialist absent | Future module | Unknown data dependencies | Target schema incomplete | Required data unavailable | New tests | Full data gate | High | P2 | Reject current claim |
| Revision store | A | A `revision_store.py`; B `zarr_store.py` | Both partial | B durable revision service | SQLite vs Zarr | Record keys/history semantics differ | Successive-cycle provenance | Migrate durability tests | Restart/reload and sealing | High | P1 | Reimplement |
| Failure Memory/motifs | B | B motif/services; A fingerprints | Heuristic/code-only | B experimental service | Module duplication | Motif IDs/reason codes differ | Episode-safe truth absent | Consolidate tests | Held-out episode evaluation | High | P2 | Adapt |
| Spatial reliability | B | B spatial engine/topology | Implemented, not empirically validated | B experimental spatial service | Numeric/geospatial versions | A/B spatial response shapes | Fixed weights vs real covariance | Keep B tests; port useful A UI tests | Real spatial calibration | High | P1 | Adapt |
| Provider disagreement | Neither | A fixture adapter; B cross-system modules | Fixture/code-only | B provider registry | Provider client overlap | Provider IDs/provenance differ | No paired national archive | Port disclosure tests | Paired-system replay | High | P1 | Reimplement |
| OOD and abstention | B | A `ood_policy.py`; B hazard OOD modules | Software behavior, scientific thresholds unvalidated | B safety service | Threshold implementations conflict | Diagnostic vs active abstention | Shifted-distribution evidence absent | Consolidate crash/scope tests | Risk-coverage on held-out shifts | High | P0 | Adapt |
| Explainability/evidence graph | B | B explanation/evidence graph; A fingerprints | Predictive explanation only | B UI/API | None major | Reason-code vocabularies differ | No causal validation | Migrate UI/API tests | Human comprehension study | Medium | P2 | Keep/Adapt |
| Digital twin/replay | Neither unchanged | A independent harness; B synthetic engine/script | A blocked; B fixture only | New immutable replay subsystem | Data-loading differences | Replay schemas differ | Independent truth absent | Combine harness invariants, discard synthetic conclusions | Event-data replay parity | High | P2 | Reimplement |
| Backend/API | B | B FastAPI routes/services | Locally reproduced | B | Duplicate package trees | Endpoint names and models differ | Model selection conflict | Port only missing safety tests | Full contract/regression suite | Medium | P1 | Keep |
| Frontend | B | Both `frontend/src` trees | Builds/tests reproduced | B frontend | React package versions close but must lock | API schemas differ | Live/fixture badges inconsistent | Port behavior, not snapshots blindly | Browser E2E with live/fixture states | Medium | P1 | Adapt |
| CI/release gates | Neither complete | B `.github/workflows/deploy.yml`; A has no workflow | Incomplete | B required checks | Node/Python matrix | None | Artifact storage/LFS policy | New clean-clone pipeline | Rollback and deployment smoke | High | P0 | Reimplement |
| 500-test certification map | Neither | Existing backend/frontend tests | No exact ID mapping | B release evidence package | Test naming differences | None | Missing domain targets | Map, do not renumber generically | Independent certification run | Medium | P1 | Reimplement |

## 16. Hypothetical combined-system outcome

A raw repository merge would probably make the system **weaker before it became stronger**. Architecturally, it would duplicate FastAPI applications, React frontends, V3 adapters, legacy model services, data stores, tests, documentation families, and deployment assumptions. Scientifically, the merge would not create missing evidence: deterministic specialist equations would remain deterministic, A's absent LFS payloads would remain absent, B's feature checksum would remain wrong, and neither national-system validation nor specialist evaluation would appear through code combination.

The combined system could improve if it uses Repository B as the only active base, keeps B's loadable V3 binaries and broad modular surface, and imports narrowly selected patterns from A: strict safe failure, certification-scope presentation, explicit live-versus-fixture labeling, and durable exact-target revision semantics. It should not import A's pointer artifacts, historical duplicate trees, stale README claims, or unusable release manifest. It should not inherit B's broad `CERTIFIED` labels, synthetic replay conclusions, unresolved threshold plurality, or transfer claims.

The main conflicts would be model authority and thresholds, feature/release manifests, response schemas, OOD semantics, provider identities, revision-store technology, dependency pins, and overlapping tests. Every merged model-serving path would need replay and calibration revalidation. Every probability field would need semantic review to ensure hazard probability, `P(BUST)`, spread, OOD, disagreement, confidence, and certification remain separate. All UTC identities, provider identities, and fixture/synthetic markers must survive migration.

**Would it be worth the added risk?** Only as a selective, staged, post-submission hardening program. It is not worth performing a broad merge before the immediate acceptance gates. The recommended merge status is **`SELECTIVE_MERGE_ONLY`**.

## 17. Table L — Post-merge acceptance gates

| Gate | Required evidence | Acceptance criterion |
|---|---|---|
| G0 Clean source baseline | Fresh clone of chosen B base at a tagged commit | Clean tree; all dependencies installed from locked manifests |
| G1 Artifact integrity | One authoritative manifest covering model, calibrator, feature order, environment, model ID, threshold, fallback | Every SHA matches; verifier exits 0; types and 50-feature order load exactly |
| G2 Incumbent parity | Golden input matrix run before and after integration | Identical calibrated V3 outputs within an explicit numerical tolerance; no silent fallback |
| G3 Model authority | Route-to-model/threshold/fallback map | One unambiguous model per route; V3 remains incumbent until a challenger passes gates |
| G4 Issue-time leakage | Raw-to-feature lineage with availability timestamps | No future observation, reanalysis, error, label, verifying imagery, or post-valid-time data |
| G5 Target semantics | Versioned target contracts per generic V3 and hazard | Hazard occurrence never substitutes for bust; continuous error retained separately |
| G6 Calibration | Frozen OOT inputs and calibration outputs | Brier, BSS, ECE, slope/intercept, reliability data and uncertainty intervals reproduced |
| G7 OOD/abstention | Held-out and shifted distributions plus crash inputs | Risk-coverage/selective performance reported; unsafe inputs abstain; diagnostic and active OOD distinguished |
| G8 Specialist promotion | Per-hazard artifact/data/split/seed/bootstrap package | No specialist enters production or uses `CERTIFIED` until independently reproduced |
| G9 Revision durability | Successive issue cycles, process restart, truth sealing, exact-target retrieval | Same records reload with correct UTC/provider identity; no fabricated history |
| G10 Provider/cross-system | Aligned paired systems with metadata and independent truth | Fixture and live providers visibly distinguished; transfer metrics independently rerun |
| G11 Replay/digital twin | Immutable historical forecasts and independent verification truth | No synthetic progression in historical mode; output metrics internally consistent |
| G12 API/schema compatibility | OpenAPI diff and consumer contract suite | No semantic field drift; probability/uncertainty concepts remain separate |
| G13 Frontend communication | Browser E2E across ready, abstain, OOD, fixture, live, cached, synthetic, unavailable states | Correct scope and provenance banners; no false certification |
| G14 Test migration | Exact legacy-to-destination test ledger and master-suite ID map | All critical tests pass; skipped/xfail/N/A justified; no generic-test substitution |
| G15 Security/operations | Required CI, secret scan, dependency scan, rate-limit/concurrency tests, recovery smoke | CI gates deployment; multi-worker limitations addressed; rollback demonstrated |
| G16 Release governance | Protected release branch or required checks, signed/tagged release, rollback record | No deployment on failing scientific gate; prior version recoverable |
| G17 Independent review | Reviewer reruns hashes, tests, replay, and claim register | Submission claims match evidence classes exactly |

## 18. Symmetry audit and label-swap invariance

The audit applied identical weights, evidence caps, and scientific rules to both repositories. A deterministic specialist module received implementation credit in B but not empirical-validation credit; the same code-only cap would have applied had that module existed in A. A failing artifact chain was penalized in both: A lost substantially more because the current binaries cannot load, while B retained partial credit because its model and calibrator load and match the expected hashes even though the feature checksum fails. Frontend test depth was credited to A despite its lower overall score. Operational honesty was also scored higher for A despite B's architecture lead.

Potential asymmetries were reviewed category by category:

1. **Test quantity:** B's 816 completed passes were not equated with 816 scientific validations. A's 109 frontend passes were credited equally as UI evidence. A's uncompleted backend run received no implied pass total.
2. **Artifact failures:** Both release chains were marked contradicted where verification fails. The difference in score follows severity: A cannot deserialize the incumbent; B can deserialize and predict but cannot validate the complete manifest chain.
3. **Documentation:** B's broader Phase A–L documentation increased alignment/breadth only where corresponding code exists. Certification and metric language was not upgraded by presentation quality. A's detailed repair documents were likewise not allowed to override current runtime failure.
4. **Hazard coverage:** A's absent named specialists were marked `N/A — uncovered/missing`. B's present modules were credited as implementations but capped below full scientific maturity because their empirical provenance is absent.
5. **Governance:** A's visible PR merge and B's visible direct-main deployment were both treated as limited checkout evidence; neither received branch-protection credit.

**Label-swap invariance result:** If the repository labels were exchanged while the evidence remained attached to each codebase, the scores and decisions would follow the evidence unchanged. The codebase with loadable expected V3 binaries, 758 completed backend passes, 58 completed frontend passes, and broader implemented phases would still win; the codebase with pointer-only V3 artifacts and an incomplete failing backend run would still lose. No conclusion depends on author identity, repository name, chronology, README polish, or prior human verification. The symmetry audit found no unresolved evidence-standard asymmetry.

## 19. Required decisions

| Decision | Result | Evidence basis |
|---|---|---|
| Overall Technical Winner | **Repository B** | 65.48 vs 47.90; usable V3 binaries, completed test suites, broader current implementation |
| Stronger Scientific Foundation | **Repository B** | The incumbent model/calibrator identity is reproduced; A's incumbent cannot load. This award does not extend to B's specialists |
| Broader Research/Feature Architecture | **Repository B** | Implemented Phase A–L surface, six prototype specialist paths, spatial/common-mode/drift/frontier modules |
| Better Immediate SIH Round-2 Candidate | **Repository B** | Closer to demonstrable after bounded fixes; not ready unchanged |
| Immediate Round-2 decision | **`NO_REPOSITORY_READY_YET`** | A's core is unavailable; B fails integrity and claim-discipline gates |
| Long-term technical decision | **`KEEP_B_AS_BASE_IMPORT_FROM_A`** | B has the usable incumbent and broader architecture; selectively import A safety/disclosure/revision patterns |
| Merge recommendation | **`SELECTIVE_MERGE_ONLY`** | A full merge adds duplicate surfaces and revalidation burden without creating missing evidence |

## 20. Final recommendation

Repair Repository B in place before submission. Make the feature-contract verifier pass, pin the model environment, freeze a single model/threshold/fallback manifest, relabel all deterministic hazard modules as prototypes or formula baselines, clearly mark synthetic replay and fallback output, add backend/artifact gates to CI, and publish an exact test/evidence ledger. Retain V3 as the incumbent. Do not claim NCMRWF/NEPS validation, specialist certification, conformal coverage, warning lead, transferability, common-mode certification, or digital-twin scientific conclusions until each is independently reproduced. After those immediate gates, selectively import Repository A's strongest safety patterns rather than its artifacts or duplicate application trees.

## References

[1]: file:///home/ubuntu/audit_workspace/supplied/SIH26079%20%E2%80%94%20Forecast-Bust%20Sentinel%20%281%29%20%281%29%20%281%29.md "SIH26079 — Forecast-Bust Sentinel"
[2]: file:///home/ubuntu/audit_workspace/supplied/VEYRA_500_Test_Master_Suite%20%281%29.md "VEYRA 500-Test Master Suite"
[3]: file:///home/ubuntu/audit_workspace/reports/repo_a_evidence.md "Repository A — Independent Evidence Audit"
[4]: file:///home/ubuntu/audit_workspace/reports/repo_b_evidence.md "Repository B — Independent Scientific-ML and Software Audit Evidence"
[5]: file:///home/ubuntu/audit_workspace/reports/docs_evidence.md "Supplied Source Documents — Neutral Evidence Audit"
[6]: file:///home/ubuntu/upload/pasted_content.txt "Master prompt — blind, zero-bias dual-repository SIH Round-2 audit"
[7]: file:///home/ubuntu/audit_workspace/supplied/SIH26079_120_RESEARCH_PAPERS_MERGED%20%281%29.md "SIH26079 120 research study briefs merged"
[8]: file:///home/ubuntu/audit_workspace/supplied/VEYRA_Hazard_Specific_Reliability_Implementation_Blueprint.md "Hazard-Specific Forecast Reliability Implementation Blueprint"
[9]: file:///home/ubuntu/audit_workspace/supplied/Docs_vs_Research_vs_Live_comparison%20%281%29.md "Docs vs Research vs Live comparison"
[10]: file:///home/ubuntu/audit_workspace/repos/repo_a "Repository A audited checkout"
[11]: file:///home/ubuntu/audit_workspace/repos/repo_b "Repository B audited checkout"

```text
AUDITED_REPO_A_SHA: b9f52d3eeec8676e06b1879f05b404605e2501be
AUDITED_REPO_B_SHA: 82eded8194151e37fb9b3eecf273010dc62d7b29

REPO_A_FINAL_WEIGHTED_SCORE: 47.90/100
REPO_B_FINAL_WEIGHTED_SCORE: 65.48/100

OVERALL_TECHNICAL_WINNER: Repository B
STRONGER_SCIENTIFIC_FOUNDATION: Repository B
BROADER_RESEARCH_ARCHITECTURE: Repository B
BETTER_IMMEDIATE_SIH_ROUND2_CANDIDATE: Repository B

IMMEDIATE_DECISION:
- `NO_REPOSITORY_READY_YET`

LONG_TERM_DECISION:
- `KEEP_B_AS_BASE_IMPORT_FROM_A`

HYPOTHETICAL_MERGED_SYSTEM_OUTCOME:
- A raw merge would initially weaken reproducibility and maintainability by duplicating model services, APIs, frontends, stores, tests, and release assumptions.
- The fundamental benefit is B's loadable V3 and broad modules combined with A's safer failure, certification-scope, fixture-disclosure, and revision-store patterns.
- The fundamental risks are semantic probability conflation, leakage, threshold/model-selection ambiguity, dependency conflict, regression, and inflated certification.
- Major conflicts include feature/release manifests, V3 versus legacy thresholds, OOD semantics, provider identity, revision storage, response schemas, and duplicated UI/API paths.
- Required revalidation includes exact hashes, 50-feature order, calibrated replay parity, all merged routes, issue-time lineage, OOD risk-coverage, every specialist, provider transfer, revision durability, and the mapped test suite.
- Merge is worth it only as staged selective adaptation after Repository B's immediate release blockers are fixed; a monolithic pre-submission merge is not worth the risk.

MERGE_RECOMMENDATION:
- `SELECTIVE_MERGE_ONLY`

FINAL_ONE_PARAGRAPH_RECOMMENDATION: Do not submit either repository unchanged. Repair Repository B's feature-manifest integrity, scientific claim language, model authority, replay labeling, environment pinning, and CI gates, then use it as the submission candidate with frozen V3 as incumbent. Treat every hazard specialist, transfer result, coverage figure, warning-lead claim, common-mode claim, and digital-twin conclusion as experimental until independently reproduced. For long-term development, keep Repository B as the base and selectively adapt Repository A's safe-failure, certification-boundary, provider-disclosure, and durable revision patterns under the post-merge acceptance gates; do not merge artifacts or application trees wholesale.
```
