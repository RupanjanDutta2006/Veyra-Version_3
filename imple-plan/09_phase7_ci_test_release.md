# Implementation Plan — Phase 7: Test, CI, Reproducibility, and Release Consolidation

## Objective

Turn all evidence requirements from Phases 0–6 into required, automated release gates. Build a CI pipeline that blocks deployment if any P0 gate fails.

## Entry Criteria

- [ ] Phase 6 complete: specialist containment operational, G8 gate enforced
- [ ] All experimental modules behind feature flags
- [ ] Specialist registry operational

## Implementation Steps

### Step 7.1 — Create Reproducible Environment Specification

Create a single, pinned environment that covers:

```
# requirements.txt (backend)
# Pinned for V3 model compatibility
scikit-learn==<EXACT_VERSION>
lightgbm==<EXACT_VERSION>
joblib==<EXACT_VERSION>
fastapi==<EXACT_VERSION>
uvicorn==<EXACT_VERSION>
pydantic==<EXACT_VERSION>
numpy==<EXACT_VERSION>
pandas==<EXACT_VERSION>
pytest==<EXACT_VERSION>
httpx==<EXACT_VERSION>
# ... all other dependencies pinned
```

```json
// package.json (frontend) — lock file must be committed
```

### Step 7.2 — Add Backend CI Pipeline

Update `.github/workflows/deploy.yml` (or create `ci.yml`):

```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main, integration/*]
  pull_request:
    branches: [main, integration/*]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.10' }
      - run: pip install -r requirements.txt
      - run: pytest -q backend/tests/
      
  artifact-verification:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: python scripts/verify_artifacts.py
      
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci --prefix frontend
      - run: npm test --prefix frontend -- --run
      - run: npm run build --prefix frontend
      
  release-gates:
    needs: [backend-tests, artifact-verification, frontend-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/run_release_gates.py --require-all
```

### Step 7.3 — Add Artifact Verification as Required Check

```python
# scripts/verify_artifacts.py must check:
# 1. V3 model hash matches release manifest
# 2. Calibrator hash matches release manifest
# 3. Feature schema has 50 entries
# 4. Feature hash matches release manifest
# 5. Model loads successfully
# 6. Calibrator loads as IsotonicRegression
# 7. Model ID matches
# 8. Threshold is documented
```

### Step 7.4 — Add Feature-Contract and Model Load Checks

```python
# Tests that must be in CI:
def test_feature_contract():
    features = json.load(open('models/v3/feature_names.json'))
    assert len(features) == 50
    # Verify order matches model expectations

def test_model_loads():
    model = joblib.load('models/v3/lightgbm_v3_challenger.joblib')
    assert model is not None

def test_calibrator_loads():
    cal = joblib.load('models/v3/probability_calibrator_v3.joblib')
    assert type(cal).__name__ == 'IsotonicRegression'
```

### Step 7.5 — Add Leakage and Issue-Time Checks

Tests that verify no future information enters predictions:
- Feature vector only uses data available at issue time
- No future observation features
- No future reanalysis features
- No future error features

### Step 7.6 — Add Calibration and Risk-Coverage Checks

When frozen evaluation inputs are available:
- Verify calibration curve
- Check risk-coverage metrics
- Validate ECE

### Step 7.7 — Add OOD and Safe-Abstention Tests

- OOD detection returns appropriate signal
- Abstention triggers at correct threshold
- Diagnostic OOD ≠ active abstention

### Step 7.8 — Add Revision, Replay, Provider Checks

- Revision records survive restart
- Truth sealing works correctly
- Provider identity is preserved
- Replay separates historical from synthetic

### Step 7.9 — Add API OpenAPI Compatibility Tests

```python
def test_openapi_backward_compatible():
    """Ensure API schema doesn't break existing consumers."""
    current_spec = get_current_openapi_spec()
    baseline_spec = load_baseline_openapi_spec()
    diff = compute_breaking_changes(current_spec, baseline_spec)
    assert len(diff.breaking_changes) == 0
```

### Step 7.10 — Add Frontend E2E State Tests

Test all trust/provenance states in the browser:

| State | Test |
|---|---|
| `ready` | Normal prediction with provenance banner |
| `abstain` | Abstention with explanation |
| `ood` | OOD warning displayed |
| `live` | Live data indicator |
| `cached` | Cached data indicator |
| `fixture` | Fixture disclosure |
| `fallback` | Fallback mode indicator |
| `synthetic` | Synthetic data warning |
| `unavailable` | Unavailable state with safe message |

### Step 7.11 — Add Security and Operations Checks

- [ ] No secrets in committed code
- [ ] Dependencies scanned for vulnerabilities
- [ ] Rate limiting configured
- [ ] Concurrency limits set
- [ ] Recovery/restart tested
- [ ] Rollback procedure documented and tested

### Step 7.12 — Build 500-Test ID Ledger

Create `manifests/test_500_id_ledger.csv`:

| Column | Values |
|---|---|
| `test_id` | Named test identity from 500-test suite |
| `test_file` | Actual test file path |
| `outcome` | `pass` / `fail` / `blocked` / `skipped` / `xfail` / `N/A — uncovered/missing` |
| `domain` | Scientific domain coverage |
| `notes` | Additional context |

**Rule:** Keep discovered test counts SEPARATE from the named 500-test identity.

### Step 7.13 — Add Tagged Release and Rollback

```bash
# Create release tag
git tag -a "v3.0.0-rc1" -m "SIH Round-2 release candidate 1"

# Document rollback procedure
# manifests/rollback_procedure.md
```

### Step 7.14 — Block Deployment on P0 Gate Failure

```python
# scripts/run_release_gates.py
REQUIRED_GATES = [
    "artifact_integrity",      # G1
    "incumbent_parity",        # G2
    "model_authority",         # G3
    "specialist_containment",  # G8
    "revision_durability",     # G9
    "replay_separation",       # G11
    "test_migration",          # G14
    "security_operations",     # G15
    "release_governance",      # G16
]

def run_all_gates():
    results = {}
    for gate in REQUIRED_GATES:
        results[gate] = run_gate(gate)
    
    failed = [g for g, r in results.items() if not r]
    if failed:
        print(f"BLOCKED: {len(failed)} gate(s) failed: {failed}")
        sys.exit(1)
    else:
        print("ALL GATES PASSED — release approved")
        sys.exit(0)
```

## Outputs Checklist

- [ ] Required CI workflow (`.github/workflows/ci.yml`)
- [ ] Reproducible environment lock (`requirements.txt` pinned)
- [ ] Artifact/release gate in CI
- [ ] Backend/frontend/scientific test reports
- [ ] 500-ID outcome ledger
- [ ] OpenAPI and browser regression reports
- [ ] Tagged rollback-ready release
- [ ] Deployment blocked on failed gates

## Failure Conditions — Immediate Stop If:

| Condition | Why |
|---|---|
| Frontend-only CI is the only deployment gate | Backend integrity not checked |
| Scientific integrity checks are optional | Science gates bypassed |
| Test counts substitute for named-domain coverage | False coverage claim |
| Failed science gates don't block deployment | Unsafe release |
| Release cannot be rolled back | No recovery option |

## Gates G14–G17

| Gate | Requirement |
|---|---|
| **G14 Test migration** | Critical behaviors have traceable destination test and justified dispositions |
| **G15 Security/operations** | Required scans and recovery checks pass |
| **G16 Release governance** | Signed/tagged release and rollback record exist |
| **G17 Independent review** | Independent reviewer reruns hashes, tests, build, smoke, replay, claims |

## Compulsory Gate Test

```bash
set -euo pipefail
python scripts/verify_artifacts.py
pytest -q backend/tests
npm ci --prefix frontend
npm test --prefix frontend -- --run
npm run build --prefix frontend
python scripts/run_release_gates.py \
  --require-artifacts --require-replay --require-security --require-rollback
```

**Pass condition:** Backend/frontend tests and builds pass, artifact verification exits 0, required security/replay/rollback checks run, and a failed scientific gate blocks the release.

---

**Previous:** [Phase 6 — Specialist Containment](08_phase6_specialist_containment.md)  
**Next:** [Phase 8 — Submission Readiness](10_phase8_submission_readiness.md)
