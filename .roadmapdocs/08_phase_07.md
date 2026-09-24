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

## Compulsory test for Phase 7 — release-gate execution

Run the complete local release gate before enabling deployment:

```bash
set -euo pipefail
python scripts/verify_artifacts.py
pytest -q backend/tests
npm ci --prefix frontend
npm test --prefix frontend -- --run
npm run build --prefix frontend
python scripts/run_release_gates.py --require-artifacts --require-replay --require-security --require-rollback
```

**Pass condition:** backend/frontend tests and builds pass, artifact verification exits 0, required security/replay/rollback checks run, and a failed scientific gate blocks the release.
