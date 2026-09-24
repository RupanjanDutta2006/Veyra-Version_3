# Implementation Plan — Phase 8: Submission Readiness

## Objective

Produce a truthful, demonstrable, reproducible SIH Round-2 submission candidate. This is the final pre-submission verification and packaging phase.

## Entry Criteria

- [ ] Phase 7 complete: ALL CI/release gates passing (G1–G17)
- [ ] No P0 blockers remaining
- [ ] 500-test ID ledger built
- [ ] Tagged release exists with rollback capability

## Implementation Steps

### Step 8.1 — Freeze Candidate SHA and Release Manifest

```bash
# Create the submission candidate
git tag -a "sih-round2-candidate-v1" -m "SIH Round-2 submission candidate"
git rev-parse HEAD > manifests/candidate_sha.txt

# Verify release manifest is complete and frozen
python -c "
import json
manifest = json.load(open('manifests/v3_release_manifest.json'))
required = ['model_id', 'model_path', 'model_sha256', 'calibrator_path', 
            'calibrator_sha256', 'feature_count', 'v3_threshold']
for r in required:
    assert r in manifest, f'Missing: {r}'
print('Release manifest complete')
"
```

### Step 8.2 — Clean-Clone Reproduction Test

```bash
# From a FRESH directory, simulate what a reviewer would do:
CANDIDATE_TAG="sih-round2-candidate-v1"
FRESH_DIR=$(mktemp -d)
cd "$FRESH_DIR"

git clone https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2 .
git checkout "$CANDIDATE_TAG"

# Install from locks
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify everything works
python scripts/verify_artifacts.py
```

### Step 8.3 — Run Artifact Verification and Model Loading

```bash
python scripts/verify_artifacts.py
python -c "
import joblib
model = joblib.load('models/v3/lightgbm_v3_challenger.joblib')
cal = joblib.load('models/v3/probability_calibrator_v3.joblib')
print(f'Model: {type(model).__name__}')
print(f'Calibrator: {type(cal).__name__}')
assert type(cal).__name__ == 'IsotonicRegression'
print('PASS')
"
```

### Step 8.4 — Run Golden V3 Parity

```bash
python scripts/compare_golden_v3_outputs.py \
  --baseline artifacts/golden_v3_before.json \
  --candidate artifacts/golden_v3_after.json
```

### Step 8.5 — Run Full Test Suites

```bash
# Backend
pytest -q backend/tests/ --tb=short --junitxml=artifacts/backend_test_report.xml

# Frontend
npm ci --prefix frontend
npm test --prefix frontend -- --run
npm run build --prefix frontend

# API tests
pytest -q backend/tests/test_api_*.py

# Security
# (run security scanning tools)

# Replay
python scripts/replay_historical.py --mode historical --fixtures artifacts/immutable_forecast_truth_fixture

# Smoke
python scripts/run_submission_smoke.py
```

### Step 8.6 — Generate 500-ID Ledger

```bash
python scripts/generate_500_test_ledger.py \
  --output manifests/test_500_id_ledger.csv \
  --test-results artifacts/backend_test_report.xml
```

### Step 8.7 — Verify Claims Against Register

```bash
python scripts/validate_claim_register.py \
  --input manifests/claim_register.csv \
  --require-final-ui-api-match
```

Every public claim must match:
- Current code behavior
- Current API schema
- Current UI text
- Evidence class assignment

### Step 8.8 — Browser E2E Across Trust States

Run browser E2E tests for all states:

| State | Expected UI Behavior |
|---|---|
| `ready` | Shows prediction with green provenance banner |
| `abstain` | Shows abstention message with reason |
| `ood` | Shows OOD warning with diagnostic info |
| `unavailable` | Shows safe unavailable message |
| `live` | Shows live data indicator |
| `cached` | Shows cached data indicator with timestamp |
| `fixture` | Shows fixture disclosure banner |
| `fallback` | Shows fallback mode indicator |
| `synthetic` | Shows synthetic data warning |

### Step 8.9 — Verify UI Wording Compliance

**Rule:** No UI text says "live", "certified", "historical", or "trained" when the evidence class does not support that wording.

```python
# Scan frontend source for forbidden wording
FORBIDDEN_PATTERNS = [
    r'certified(?!.*experimental)',
    r'live historical',
    r'NCMRWF validated',
    r'trained specialist(?!.*formula)',
]
```

### Step 8.10 — Produce Judge-Facing Demo Script

Create `demo/demo_script.md`:

```markdown
# Veyra SIH Round-2 Demo Script

## Demo 1: Normal Forecast Reliability Assessment
1. Navigate to the dashboard
2. Select a station (e.g., Delhi)
3. Show the reliability prediction with provenance
4. Highlight: data source, model version, confidence level

## Demo 2: Safe Abstention
1. Simulate missing model scenario
2. Show the system's safe abstention behavior
3. Highlight: no silent fallback, clear user messaging

## Demo 3: OOD Detection
1. Provide out-of-distribution input
2. Show OOD detection and appropriate warning
3. Highlight: diagnostic vs active abstention

## Known Limitations
- Specialists are formula baselines, not trained models
- Cross-system claims are experimental
- Digital twin is synthetic, not historical
```

### Step 8.11 — Produce Risk Register

Create `manifests/risk_register.md`:

| Risk ID | Risk | Severity | Mitigation | Status |
|---|---|---|---|---|
| R-001 | Feature hash mismatch not resolved | HIGH | Phase 3 repair | Resolved/Open |
| R-002 | Specialist formulas called "certified" | HIGH | Phase 6 containment | Resolved/Open |
| R-003 | Synthetic data shown as historical | HIGH | Phase 5 separation | Resolved/Open |
| R-004 | No real NCMRWF/NEPS data | MEDIUM | Documented as future work | Accepted |
| R-005 | V3 model environment compatibility | MEDIUM | Pinned environment | Resolved |

### Step 8.12 — Obtain Independent Reviewer Sign-Off

Reviewer must independently verify:
- [ ] Clean-clone reproduction succeeds
- [ ] Artifact hashes match manifest
- [ ] Tests pass
- [ ] Build succeeds
- [ ] Smoke tests pass
- [ ] Claim register matches UI/API
- [ ] No unsupported certification wording

### Step 8.13 — Tag Submission Candidate

```bash
# Final tagging
git tag -a "sih-round2-submission-v1.0.0" \
  -m "SIH Round-2 Final Submission Candidate
  
  Reviewer: <NAME>
  Verification: PASS
  Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
  Gates: G1-G17 all passed
  P0 blockers: 0 remaining"

# Preserve evidence bundle
tar czf "artifacts/submission_evidence_bundle.tar.gz" \
  manifests/ artifacts/ logs/
```

## Outputs Checklist

- [ ] Submission candidate tag
- [ ] Final claim sheet (all claims verified)
- [ ] Demo script and screenshots/video
- [ ] Test/build/artifact/replay evidence bundle
- [ ] Risk register and known-limitations sheet
- [ ] Rollback tag
- [ ] Independent reviewer sign-off recorded

## Failure Conditions — Immediate Stop If:

| Condition | Why |
|---|---|
| Any P0 blocker remains | Not submission-ready |
| V3 unavailable or checksum-invalid | Core model broken |
| Specialist presented as certified without G8 | Misrepresentation |
| Synthetic/fixture shown as live/historical | Scientific dishonesty |
| Independent review cannot reproduce | Not reproducible |

## Final Submission Gate

The release is suitable ONLY if:
1. All P0 blockers closed
2. G0–G17 either passed or explicitly justified as out of scope
3. Claim register matches final UI/API/docs
4. Independent reviewer reproduces artifacts, tests, build, smoke, and replay boundaries

## Compulsory Gate Test

```bash
set -euo pipefail
./scripts/clean_clone_reproduction.sh \
  --tag "$CANDIDATE_TAG" \
  --log-dir artifacts/submission_reproduction
python scripts/validate_claim_register.py \
  --input manifests/claim_register.csv \
  --require-final-ui-api-match
python scripts/run_submission_smoke.py \
  --states ready,abstain,ood,live,cached,fixture,fallback,synthetic,unavailable
```

**Pass condition:** Independent clean-clone run reproduces hashes, tests, build, smoke, provenance states, claim register, and rollback metadata with no unresolved P0 blocker.

---

**Previous:** [Phase 7 — CI, Test, Release](09_phase7_ci_test_release.md)  
**Next:** [Phase 9 — Post-Submission](11_phase9_post_submission.md)
