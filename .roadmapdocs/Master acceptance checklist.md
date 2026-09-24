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
