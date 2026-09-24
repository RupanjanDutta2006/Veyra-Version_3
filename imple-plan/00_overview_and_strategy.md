# Veyra SIH26079 Round-2 — Master Implementation Overview & Strategy

## Project Summary

**Veyra** is a forecast-reliability layer for SIH26079 that estimates whether an already-issued NWP (Numerical Weather Prediction) forecast may fail badly, and communicates uncertainty, evidence boundaries, and abstention honestly. This is **not** a weather forecaster — it is a *forecast-bust sentinel*.

Two repositories evolved independently:

| Property | Repository A | Repository B |
|---|---|---|
| URL | `RupanjanDutta2006/Veyra-Know-When-Forecasts-May-Fail` | `adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2` |
| Audited SHA | `b9f52d3` | `82eded8` |
| Weighted Score | **47.90/100** | **65.48/100** |
| Strengths | Safety patterns, UTC contracts, certification boundaries, provider disclosure, replay invariants | Loadable V3 model/calibrator, broader architecture, specialist modules, testing, manifests |
| Critical Weakness | V3 model files are Git LFS pointers — cannot load | Feature checksum mismatch, unsupported certification claims, science-governance gaps |

## Operating Decision

| Decision | Value |
|---|---|
| **Base Repository** | Repository B |
| **Integration Mode** | `SELECTIVE_MERGE_ONLY` |
| **Immediate Submission** | `NO_REPOSITORY_READY_YET` |
| **Long-term Path** | `KEEP_B_AS_BASE_IMPORT_FROM_A` |
| **Merge Recommendation** | `SELECTIVE_MERGE_ONLY` |

## 10 Non-Negotiable Integration Rules

1. **One active application base** — Repository B only
2. **Frozen incumbent immutable** until gates pass
3. **Never copy A's pointer artifacts** as binaries
4. **One authoritative release manifest**
5. **Separate software completeness from scientific validation**
6. **Keep probability concepts separate** (hazard ≠ bust ≠ OOD ≠ confidence)
7. **Preserve issue-time safety** — no future information leakage
8. **Make data provenance visible** — live/cached/fixture/fallback/synthetic/unavailable
9. **Do not promote by documentation** alone
10. **Stop on failed P0 gates** — no downstream work proceeds

## Phase Execution Order

```text
Step 1 → Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9
  |          |          |          |          |          |          |          |          |          |          |
Clone    Freeze     Truth     Branch    Artifact   Safety    Revision  Specialist  CI/Test  Submission  Post-sub
& Audit  Inventory  Align     Control   Repair     Graft     & Replay  Contain    Release  Readiness   Empirical
```

> **IMPORTANT:** Each phase has **entry criteria** and **compulsory gate tests**. A phase is NOT complete until its gate test passes and logs are archived. **No phase can be skipped.**

## Evidence Hierarchy (Truth Discipline)

1. Reproduced executable evidence (tests, builds, hashes, replays)
2. Current source code and committed artifacts at audited SHA
3. Machine-readable manifests / frozen evaluation outputs
4. Technical docs tied to code
5. README claims and presentation claims
6. Roadmap / blueprint / intended future architecture

> A planned item is NOT an implemented item. A `CERTIFIED` string in code is NOT certification.

## Target Architecture

```text
+-------------------------------+
|  React/Vite SIH Demo          |
|  Provenance + Trust Banners   |
+---------------+---------------+
                |
          versioned API
                |
+---------------v---------------+
| FastAPI destination services   |
| One route/model authority     |
+---+-----------+-----------+---+
    |           |           |
+---v---+ +----v-----+ +---v----------+
| V3    | | Safety/  | | Evidence &   |
| Model | | OOD      | | Explanations |
| Reg.  | | Abstain  | |              |
+---+---+ +----+-----+ +---+----------+
    |           |           |
+---v-----------v-----------v-------+
| Frozen artifact + feature +       |
| target contracts + release manifest|
+------------------+----------------+
                   |
+------------------v-------------------+
| Durable revision/history/replay      |
| UTC, provider ID, sealed truth       |
+------------------+-------------------+
                   |
+------------------v-------------------+
| Experimental registry: hazard,       |
| spatial, compound, common-mode,      |
| transfer, drift, specialist formulas |
| (isolated from incumbent promotion)  |
+--------------------------------------+
```

## Files in This Implementation Plan Folder

| File | Covers |
|---|---|
| `00_overview_and_strategy.md` | This document — master overview |
| `01_step1_clone_and_workspace.md` | Step 1: Clone, freeze, audit workspace |
| `02_phase0_freeze_and_inventory.md` | Phase 0: Immutable evidence baseline |
| `03_phase1_truth_alignment.md` | Phase 1: Claim register and truth alignment |
| `04_phase2_base_selection.md` | Phase 2: Branch controls and destination |
| `05_phase3_artifact_repair.md` | Phase 3: V3 incumbent artifact repair |
| `06_phase4_safety_grafting.md` | Phase 4: Selective safety patterns from A |
| `07_phase5_revision_replay.md` | Phase 5: Durable revision store and replay |
| `08_phase6_specialist_containment.md` | Phase 6: Experimental module boundaries |
| `09_phase7_ci_test_release.md` | Phase 7: CI, testing, release consolidation |
| `10_phase8_submission_readiness.md` | Phase 8: Final submission candidate |
| `11_phase9_post_submission.md` | Phase 9: Post-submission empirical program |
| `12_asset_collection_plan.md` | Complete file-level import/reject matrix |
| `13_master_acceptance_checklist.md` | Master checklist and decision tree |

---

*Generated from `.docs` and `.roadmapdocs` analysis. All phases must be executed sequentially with gate verification.*
