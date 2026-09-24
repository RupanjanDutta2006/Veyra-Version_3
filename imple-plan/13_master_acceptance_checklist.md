# Implementation Plan — Master Acceptance Checklist and Decision Tree

## Purpose

This is the final gate-keeping document. Use this checklist before creating a submission tag. Every item must be checked.

---

## Artifact Integrity

- [ ] V3 model hash matches the canonical release manifest
- [ ] Isotonic calibrator hash and type match
- [ ] Feature schema has exactly 50 entries in canonical order
- [ ] Feature-file hash and declared hash agree
- [ ] Model ID, threshold, fallback, environment, and route are bound in one manifest
- [ ] Clean clone loads the model and calibrator
- [ ] Missing/corrupt artifacts produce safe abstention (NOT silent fallback)

## Scientific Correctness

- [ ] `P(BUST)` is not hazard probability (these are separate fields)
- [ ] Issue-time feature lineage is documented and tested
- [ ] No future observation, future reanalysis, future error, label, or verifying imagery enters the issue-time feature vector
- [ ] Calibration, OOD, abstention, uncertainty, provider disagreement, and continuous error remain separate
- [ ] Specialist formulas are labeled as formulas until empirical gates pass
- [ ] No certification wording exceeds the evidence class

## Reliability and Replay

- [ ] Revision records preserve issue UTC, valid UTC, provider, target, forecast version, and truth-sealing state
- [ ] Restart/reload retains exact-target history
- [ ] Failure Memory and Motifs consume sealed episodes
- [ ] Historical replay uses immutable forecasts and independent truth
- [ ] Synthetic replay is a separate visible mode
- [ ] Replay metrics are internally consistent

## API and Frontend

- [ ] One route-to-model authority exists
- [ ] OpenAPI and consumer tests pass
- [ ] Live, cached, fixture, fallback, synthetic, and unavailable states are explicit
- [ ] UI has correct trust/provenance banners
- [ ] Ready, abstain, OOD, unavailable, and provider-failure states have browser E2E tests
- [ ] Hazard, bust, OOD, uncertainty, and provider fields cannot be confused

## Test and Release Engineering

- [ ] Backend tests run from a clean clone
- [ ] Frontend tests and build pass
- [ ] Artifact verifier exits 0
- [ ] Leakage, calibration, OOD, replay, provider, security, and rollback gates run in CI
- [ ] 500-test ID ledger exists with explicit dispositions
- [ ] A failed scientific gate blocks deployment
- [ ] A tagged release and rollback record exist
- [ ] An independent reviewer reproduces the release

---

## Decision Tree for Execution

```text
Start
  |
  v
Phase 0 inventory complete?
  | no → stop and repair inventory
  v yes
Phase 1 claim register complete?
  | no → stop and correct claims
  v yes
Phase 2 one B destination branch?
  | no → remove duplicate trees and enforce branch controls
  v yes
Phase 3 G1–G3 artifact and incumbent gates pass?
  | no → do not merge safety/specialist code; repair B artifact chain
  v yes
Phase 4 safety/provenance parity passes?
  | no → revert semantic or output drift
  v yes
Phase 5 durable revision and replay gates pass?
  | no → keep replay experimental and rebuild history layer
  v yes
Phase 6 specialist modules isolated and labeled?
  | no → quarantine promotion paths and claims
  v yes
Phase 7 CI/release gates pass?
  | no → no deployment or submission tag
  v yes
Phase 8 independent submission review passes?
  | no → remain NO_REPOSITORY_READY_YET
  v yes
Tag truthful SIH Round-2 candidate
  |
  v
Phase 9 empirical specialist program after submission
```

## Gate Summary Table

| Gate | Phase | Description | Blocker Level |
|---|---|---|---|
| P0-0 | 0 | Inventory reproduces audited SHAs | P0 |
| P0-1 | 1 | All claims have evidence class and owner | P0 |
| P0-2 | 2 | One destination, no duplicates | P0 |
| G1 | 3 | Artifact integrity (hashes, types, order) | P0 |
| G2 | 3 | Incumbent parity (golden outputs match) | P0 |
| G3 | 3 | Model authority (one path per route) | P0 |
| G4-G7 | 4 | Safety/provenance parity | P0 |
| G8 | 6 | Specialist promotion requires evidence package | P0 |
| G9 | 5 | Revision durability | P0 |
| G11 | 5 | Replay separation | P0 |
| G14 | 7 | Test migration complete | P0 |
| G15 | 7 | Security/operations pass | P0 |
| G16 | 7 | Release governance (tag + rollback) | P0 |
| G17 | 7 | Independent reviewer verification | P0 |

## Quick Reference — Evidence Classes

| Class | Meaning |
|---|---|
| `REPRODUCED` | Tests run, artifacts loaded, outputs verified now |
| `SUPPORTED_BY_ARTIFACT` | Frozen chain exists but not re-run |
| `SUPPORTED_BY_CODE_ONLY` | Code exists, no independent validation |
| `SUPPORTED_BY_TEST_FIXTURE_ONLY` | Tests pass against fixtures, not real data |
| `DOCUMENTATION_ONLY` | Claim exists only in docs |
| `CONTRADICTED` | Evidence conflicts with the claim |
| `UNVERIFIED` | Cannot determine from available evidence |

## Quick Reference — Specialist Statuses

| Status | Meaning |
|---|---|
| `experimental` | Not validated for production |
| `formula_baseline` | Deterministic formula, not trained |
| `candidate` | Under active evaluation |
| `promoted` | Passed all promotion gates |
| `quarantined` | Evidence issues found |

## Final Recommendation

Use Repository B as the sole destination only after:
1. V3 feature-contract checksum is repaired
2. Release authority is consolidated
3. Safety patterns ported from A with tests
4. All specialists behind experimental boundaries
5. CI pipeline enforces all gates

Port Repository A's safety and operational patterns **selectively, with tests and provenance**, rather than copying application trees or pointer artifacts.

**The correct integration strategy is:** a staged, gate-driven selective merge in which software integration happens before scientific promotion and every promoted claim must be independently reproduced.

---

## Audit Scores Reference

| Category | Weight | Repo A Raw | A Weighted | Repo B Raw | B Weighted |
|---|---|---|---|---|---|
| Scientific correctness, claim discipline & leakage safety | 15 | 58 | 8.70 | 58 | 8.70 |
| Alignment with SIH26079 main docs + research corpus | 8 | 62 | 4.96 | 78 | 6.24 |
| Core V3 / baseline quality, calibration & artifact reproducibility | 10 | 25 | 2.50 | 82 | 8.20 |
| Data pipeline, issue-time contracts, provenance & QC | 7 | 62 | 4.34 | 62 | 4.34 |
| Reliability intelligence: revisions, Failure Memory, Motifs | 8 | 48 | 3.84 | 68 | 5.44 |
| Hazard-specific specialists and empirical validation | 10 | 12 | 1.20 | 45 | 4.50 |
| Certification, OOD, abstention, drift & independent truth | 9 | 58 | 5.22 | 62 | 5.58 |
| Spatial, ensemble, provider and cross-system intelligence | 6 | 55 | 3.30 | 55 | 3.30 |
| Backend/API architecture & robustness | 6 | 65 | 3.90 | 78 | 4.68 |
| Frontend/demo quality & scientific communication | 5 | 78 | 3.90 | 74 | 3.70 |
| Testing, reproducibility, replay & release engineering | 8 | 30 | 2.40 | 76 | 6.08 |
| Documentation accuracy, traceability & maintainability | 4 | 56 | 2.24 | 60 | 2.40 |
| SIH Round-2 submission readiness | 4 | 35 | 1.40 | 58 | 2.32 |
| **TOTAL** | **100** | — | **47.90** | — | **65.48** |

---

*This document is the final reference for acceptance decisions. No submission tag should be created unless every applicable checklist item is checked and every P0 gate is passed.*
