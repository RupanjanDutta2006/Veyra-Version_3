# Implementation Plan — Phase 3: Frozen Incumbent Artifact Repair

## Objective

Repair Repository B's feature-contract integrity while preserving the loadable V3 LightGBM model and isotonic calibrator. Establish one authoritative release manifest binding all model artifacts.

## Entry Criteria

- [ ] Phase 2 complete: single destination established, branch controls in place
- [ ] Repository B is the integration branch base
- [ ] No duplicate application trees present

## Known Incumbent Contract (Golden Reference)

| Item | Required Value |
|---|---|
| V3 Model Path | `models/v3/lightgbm_v3_challenger.joblib` |
| Model SHA256 | `00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660` |
| Calibrator Path | `models/v3/probability_calibrator_v3.joblib` |
| Calibrator SHA256 | `9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531` |
| Feature Count | **50** |
| Calibrator Type | `IsotonicRegression` |
| V3 Threshold | `0.060` |
| Legacy Day-4 Threshold | `0.280` |

## Key Problem to Solve

Repository B has a **feature checksum mismatch**: the committed `feature_names.json` hash doesn't match the declared hash in the manifest. This must be resolved before any downstream work.

## Implementation Steps

### Step 3.1 — Determine Feature Authority

**Decision required:** Is the committed `feature_names.json` file or its declared hash in the manifest the authoritative source?

```python
# Compare committed file hash vs manifest-declared hash
import hashlib, json

with open('models/v3/feature_names.json', 'rb') as f:
    committed_hash = hashlib.sha256(f.read()).hexdigest()

with open('artifact_manifest.json') as f:
    manifest = json.load(f)
    declared_hash = manifest.get('feature_names_sha256', 'NOT_FOUND')

print(f"Committed file hash: {committed_hash}")
print(f"Manifest declared hash: {declared_hash}")
print(f"Match: {committed_hash == declared_hash}")
```

**Rule:** Do NOT alter the model or calibrator to make a hash pass.

### Step 3.2 — Resolve Feature Hash Conflict

**If the committed file is canonical:**
1. Verify it has exactly 50 features
2. Verify feature order matches the model's expected input
3. Regenerate the manifest hash from the exact committed file
4. Record the decision and reason

**If the manifest hash is canonical:**
1. Locate the exact feature file from a verified source
2. Verify provenance
3. Replace the committed file
4. Record provenance chain

### Step 3.3 — Pin Compatible Environment

```bash
# Required versions for V3 model serialization compatibility
pip install scikit-learn==<EXACT_VERSION> lightgbm==<EXACT_VERSION> joblib==<EXACT_VERSION>

# Record exact environment
pip freeze > requirements_v3_verified.txt
```

The exact versions must be determined by loading the model and checking deserialization compatibility.

### Step 3.4 — Clean Clone Load Test

```python
# Must run from a fresh clone with only pinned dependencies
from pathlib import Path
import joblib

model_path = Path('models/v3/lightgbm_v3_challenger.joblib')
cal_path = Path('models/v3/probability_calibrator_v3.joblib')

assert model_path.exists(), f"Model not found: {model_path}"
assert cal_path.exists(), f"Calibrator not found: {cal_path}"

model = joblib.load(model_path)
calibrator = joblib.load(cal_path)

print(f"Model type: {type(model).__name__}")
print(f"Calibrator type: {type(calibrator).__name__}")
assert type(calibrator).__name__ == 'IsotonicRegression', "Calibrator must be IsotonicRegression"
```

### Step 3.5 — Full Contract Verification

Verify ALL of these match the golden reference:

| Check | Method |
|---|---|
| Model type | `type(model).__name__` |
| Calibrator type | Must be `IsotonicRegression` |
| Feature count | `len(json.load(open('models/v3/feature_names.json')))` must be 50 |
| Feature order | Compare ordered list against model's expected input |
| Model SHA256 | `sha256sum models/v3/lightgbm_v3_challenger.joblib` |
| Calibrator SHA256 | `sha256sum models/v3/probability_calibrator_v3.joblib` |
| V3 threshold | `0.060` documented and enforced |
| Day-4 threshold | `0.280` documented (legacy, separate) |
| Model ID | Bound in release manifest |
| Fallback policy | Documented and tested |

### Step 3.6 — Create Authoritative Release Manifest

Create `manifests/v3_release_manifest.json`:

```json
{
  "model_id": "lightgbm_v3_challenger",
  "model_path": "models/v3/lightgbm_v3_challenger.joblib",
  "model_sha256": "00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660",
  "calibrator_path": "models/v3/probability_calibrator_v3.joblib",
  "calibrator_sha256": "9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531",
  "calibrator_type": "IsotonicRegression",
  "feature_schema_path": "models/v3/feature_names.json",
  "feature_schema_sha256": "<COMPUTED_HASH>",
  "feature_count": 50,
  "v3_threshold": 0.060,
  "legacy_day4_threshold": 0.280,
  "environment": {
    "scikit_learn": "<VERSION>",
    "lightgbm": "<VERSION>",
    "joblib": "<VERSION>",
    "python": "<VERSION>"
  },
  "fallback_policy": "safe_abstention",
  "route_authority": "/api/v1/predict"
}
```

### Step 3.7 — Consolidate Thresholds

Create an explicit model-version map. **Do NOT silently choose one threshold:**

```json
{
  "model_versions": {
    "v3_challenger": {
      "threshold": 0.060,
      "model_path": "models/v3/lightgbm_v3_challenger.joblib",
      "status": "incumbent"
    },
    "day4_legacy": {
      "threshold": 0.280,
      "model_path": "models/day4/...",
      "status": "baseline_comparison_only"
    }
  }
}
```

### Step 3.8 — Fix verify_artifacts.py

Ensure `scripts/verify_artifacts.py` exits 0 with the corrected manifest:

```bash
python scripts/verify_artifacts.py
echo "Exit code: $?"
```

### Step 3.9 — Create Golden-Input Prediction Test

```python
# artifacts/golden_v3_before.json — baseline output to compare against
import json, joblib, numpy as np

model = joblib.load('models/v3/lightgbm_v3_challenger.joblib')
calibrator = joblib.load('models/v3/probability_calibrator_v3.joblib')
features = json.load(open('models/v3/feature_names.json'))

# Create deterministic golden input
np.random.seed(42)
golden_input = np.random.randn(1, 50)

raw_pred = model.predict(golden_input)
cal_pred = calibrator.predict(raw_pred)

golden_output = {
    "raw_prediction": raw_pred.tolist(),
    "calibrated_prediction": cal_pred.tolist(),
    "feature_count": len(features),
    "model_type": type(model).__name__,
    "calibrator_type": type(calibrator).__name__
}

with open('artifacts/golden_v3_before.json', 'w') as f:
    json.dump(golden_output, f, indent=2)
```

### Step 3.10 — Test Safe Abstention on Missing/Corrupt Artifacts

Verify that:
- Missing model → safe abstention (NOT silent fallback)
- Corrupted model → safe abstention
- Missing calibrator → safe abstention
- Wrong feature count → explicit error

## Outputs Checklist

- [ ] One authoritative V3 release manifest
- [ ] Verified SHA256 hashes for model, calibrator, feature schema
- [ ] Environment lock with exact dependency versions
- [ ] Route-to-model/threshold/fallback map
- [ ] `verify_artifacts.py` exits 0
- [ ] Golden V3 output fixture (`artifacts/golden_v3_before.json`)
- [ ] Golden parity test script
- [ ] Artifact provenance record
- [ ] Safe-abstention test for missing/corrupt artifacts

## Failure Conditions — Immediate Stop If:

| Condition | Why |
|---|---|
| Feature hash remains inconsistent | Cannot trust feature contract |
| Model/calibrator changed without provenance record | Breaks artifact integrity |
| Multiple thresholds remain undocumented | Ambiguous model behavior |
| Silent fallback changes calibrated output | Hidden behavior change |
| Clean-clone load fails | Model not deployable |

## Gates G1–G3

| Gate | Requirement |
|---|---|
| **G1 Artifact integrity** | All hashes, types, feature order, environment, ID, threshold, and fallback match |
| **G2 Incumbent parity** | Golden calibrated V3 outputs remain identical within declared tolerance |
| **G3 Model authority** | Exactly one authoritative model path per route |

**NO safety grafting or specialist integration proceeds if G1–G3 fail.**

## Compulsory Gate Test

```bash
set -euo pipefail
python scripts/verify_artifacts.py
python - <<'PY'
from pathlib import Path
import joblib
model = Path('models/v3/lightgbm_v3_challenger.joblib')
cal = Path('models/v3/probability_calibrator_v3.joblib')
assert model.exists() and cal.exists()
joblib.load(cal)
print('model/calibrator paths present and calibrator deserializes')
PY
```

**Pass condition:** Verifier exits 0, hashes match one authoritative manifest, the calibrator loads as `IsotonicRegression`, the feature list has 50 entries, and route/model/threshold/fallback authority is singular.

---

**Previous:** [Phase 2 — Base Selection](04_phase2_base_selection.md)  
**Next:** [Phase 4 — Safety Grafting](06_phase4_safety_grafting.md)
